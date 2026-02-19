"""Daily token cap tracking and enforcement, plus multi-window rate limiting.

Issue: #341 - Add JWT authentication to analysis endpoint with daily token cap.
Issue: #364 - Tiered rate limiting with multi-window caps.
"""

from __future__ import annotations

import calendar
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, TypedDict

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

from .models.rate_limit import (
    CounterState,
    RateLimitResult,
    TierConfig,
    UserTier,
    WindowType,
)

logger = logging.getLogger(__name__)

# Default daily cap
DEFAULT_DAILY_CAP = 20

# DynamoDB key constants
CAP_CONFIG_PK = "CONFIG"
CAP_CONFIG_SK = "daily_cap"
COUNTER_SK_PREFIX = "COUNT#"


class TokenCapConfig(TypedDict):
    """Configuration for the daily token cap."""

    daily_cap: int
    updated_at: str
    updated_by: str


def _get_dynamodb_resource():
    """Get DynamoDB resource, respecting endpoint override for testing."""
    region = os.environ.get("AWS_REGION", "us-east-1")
    endpoint_url = os.environ.get("DYNAMODB_ENDPOINT")
    kwargs = {"region_name": region}
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url
    return boto3.resource("dynamodb", **kwargs)


def get_today_key() -> str:
    """Get today's date key in YYYY-MM-DD format (UTC).

    Returns:
        Date string in YYYY-MM-DD format.
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def get_current_cap(table_name: str) -> int:
    """Get the current daily cap setting.

    Reads the cap configuration from DynamoDB. If no configuration
    exists, returns the default cap value.

    Args:
        table_name: Name of the DynamoDB table.

    Returns:
        The current daily cap value.
    """
    try:
        dynamodb = _get_dynamodb_resource()
        table = dynamodb.Table(table_name)

        response = table.get_item(
            Key={
                "PK": CAP_CONFIG_PK,
                "SK": CAP_CONFIG_SK,
            }
        )

        item = response.get("Item")
        if item and "daily_cap" in item:
            return int(item["daily_cap"])

        return DEFAULT_DAILY_CAP

    except ClientError as e:
        logger.error("Failed to get current cap: %s", str(e))
        # Fail closed - return 0 to deny all tokens if we can't read config
        raise


def check_and_increment_cap(table_name: str) -> tuple[bool, int]:
    """Check if under daily cap, increment if so.

    Uses DynamoDB atomic counters (conditional writes) to ensure
    race-safe cap tracking. The counter is incremented only if the
    current count is below the daily cap.

    Args:
        table_name: Name of the DynamoDB table.

    Returns:
        Tuple of (allowed, current_count) where allowed indicates
        whether the token issuance was permitted.
    """
    today = get_today_key()
    counter_sk = f"{COUNTER_SK_PREFIX}{today}"

    try:
        dynamodb = _get_dynamodb_resource()
        table = dynamodb.Table(table_name)

        # Get the current cap
        daily_cap = get_current_cap(table_name)

        # Try to increment the counter atomically
        # First, try to create or update the counter
        try:
            response = table.update_item(
                Key={
                    "PK": "COUNTER",
                    "SK": counter_sk,
                },
                UpdateExpression="SET tokens_issued = if_not_exists(tokens_issued, :zero) + :one, "
                                 "daily_cap = :cap, "
                                 "#ttl = :ttl_val",
                ConditionExpression="attribute_not_exists(tokens_issued) OR tokens_issued < :cap",
                ExpressionAttributeNames={
                    "#ttl": "ttl",
                },
                ExpressionAttributeValues={
                    ":zero": 0,
                    ":one": 1,
                    ":cap": daily_cap,
                    ":ttl_val": _get_ttl_epoch(),
                },
                ReturnValues="ALL_NEW",
            )

            new_count = int(response["Attributes"]["tokens_issued"])
            logger.info(
                "Token cap check: allowed, count=%d, cap=%d, date=%s",
                new_count,
                daily_cap,
                today,
            )
            return (True, new_count)

        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                # Cap exceeded - get current count for reporting
                current = _get_current_count(table, counter_sk)
                logger.warning(
                    "Token cap exceeded: count=%d, cap=%d, date=%s",
                    current,
                    daily_cap,
                    today,
                )
                return (False, current)
            raise

    except ClientError as e:
        if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
            logger.error("DynamoDB error during cap check: %s", str(e))
        # Fail closed - deny token if DynamoDB is unavailable
        raise


def _get_current_count(table, counter_sk: str) -> int:
    """Get the current token count for today.

    Args:
        table: DynamoDB Table resource.
        counter_sk: The sort key for today's counter.

    Returns:
        Current token count.
    """
    try:
        response = table.get_item(
            Key={
                "PK": "COUNTER",
                "SK": counter_sk,
            }
        )
        item = response.get("Item")
        if item and "tokens_issued" in item:
            return int(item["tokens_issued"])
        return 0
    except ClientError:
        return 0


def _get_ttl_epoch() -> int:
    """Get TTL epoch for 7 days from now (auto-cleanup of old counters).

    Returns:
        Unix epoch timestamp 7 days in the future.
    """
    from datetime import timedelta

    future = datetime.now(timezone.utc) + timedelta(days=7)
    return int(future.timestamp())


def set_daily_cap(table_name: str, new_cap: int, admin_id: str) -> bool:
    """Admin function to update the daily cap.

    Updates the cap configuration in DynamoDB with an audit trail.

    Args:
        table_name: Name of the DynamoDB table.
        new_cap: The new daily cap value (must be positive).
        admin_id: Identifier of the admin making the change.

    Returns:
        True if the cap was updated successfully.

    Raises:
        ValueError: If new_cap is not a positive integer.
    """
    if not isinstance(new_cap, int) or new_cap <= 0:
        raise ValueError(f"Daily cap must be a positive integer, got: {new_cap}")

    now = datetime.now(timezone.utc).isoformat()

    try:
        dynamodb = _get_dynamodb_resource()
        table = dynamodb.Table(table_name)

        table.put_item(
            Item={
                "PK": CAP_CONFIG_PK,
                "SK": CAP_CONFIG_SK,
                "daily_cap": new_cap,
                "updated_at": now,
                "updated_by": admin_id,
            }
        )

        logger.info(
            "Daily cap updated: new_cap=%d, admin=%s, timestamp=%s",
            new_cap,
            admin_id,
            now,
        )
        return True

    except ClientError as e:
        logger.error("Failed to update daily cap: %s", str(e))
        raise


# --------------------------------------------------------------------------- #
# Multi-window rate limiting (Issue #364)
# --------------------------------------------------------------------------- #

# TTL durations for counter cleanup
_HOURLY_TTL_SECONDS = 2 * 3600       # 2 hours
_DAILY_TTL_SECONDS = 2 * 86400       # 2 days
_MONTHLY_TTL_SECONDS = 35 * 86400    # 35 days

# Window priority order for reporting which was exceeded first
_WINDOW_PRIORITY = [WindowType.HOURLY, WindowType.DAILY, WindowType.MONTHLY]


class MultiWindowCounter:
    """Atomic multi-window rate limit counter using DynamoDB transactions.

    Checks and increments three counters (hourly, daily, monthly) in a
    single DynamoDB transaction. Uses conditional writes to enforce caps.

    Fail mode is hybrid:
    - Free tier → fail-closed (503) on DynamoDB errors
    - Subscriber/Admin → fail-open (allowed) on DynamoDB errors
    """

    def __init__(
        self,
        table_name: str | None = None,
        dynamodb_client: Any = None,
        timeout_seconds: float = 2.0,
    ) -> None:
        self._table_name = table_name or os.environ.get(
            "TOKEN_CAP_TABLE", "aletheia-token-cap"
        )
        self._client = dynamodb_client
        self._timeout_seconds = timeout_seconds

    def _get_client(self) -> Any:
        """Lazy-initialize DynamoDB client with timeout config."""
        if self._client is None:
            region = os.environ.get("AWS_REGION", "us-east-1")
            endpoint_url = os.environ.get("DYNAMODB_ENDPOINT")
            boto_config = BotoConfig(
                connect_timeout=self._timeout_seconds,
                read_timeout=self._timeout_seconds,
            )
            kwargs: dict[str, Any] = {"region_name": region, "config": boto_config}
            if endpoint_url:
                kwargs["endpoint_url"] = endpoint_url
            self._client = boto3.client("dynamodb", **kwargs)
        return self._client

    def check_and_increment(
        self,
        user_id: str,
        tier_config: TierConfig,
        billing_anchor_day: int = 1,
    ) -> RateLimitResult:
        """Check rate limits and atomically increment all three counters.

        Uses a DynamoDB TransactWriteItems to increment hourly, daily, and
        monthly counters in a single atomic operation. Each counter has a
        conditional check ensuring the current count is below the cap.

        Args:
            user_id: The user's unique identifier.
            tier_config: The user's tier configuration with caps.
            billing_anchor_day: Day of month for monthly window reset.

        Returns:
            RateLimitResult indicating whether the request is allowed.
        """
        now = datetime.now(timezone.utc)
        hourly_window, daily_window, monthly_window = self._get_current_windows(
            billing_anchor_day, now
        )

        pk = f"USER#{user_id}"
        hourly_sk = f"RATE#HOURLY#{hourly_window}"
        daily_sk = f"RATE#DAILY#{daily_window}"
        monthly_sk = f"RATE#MONTHLY#{monthly_window}"

        hourly_ttl = int((now + timedelta(seconds=_HOURLY_TTL_SECONDS)).timestamp())
        daily_ttl = int((now + timedelta(seconds=_DAILY_TTL_SECONDS)).timestamp())
        monthly_ttl = int((now + timedelta(seconds=_MONTHLY_TTL_SECONDS)).timestamp())

        transact_items = [
            {
                "Update": {
                    "TableName": self._table_name,
                    "Key": {"PK": {"S": pk}, "SK": {"S": hourly_sk}},
                    "UpdateExpression": (
                        "SET #cnt = if_not_exists(#cnt, :zero) + :one, #ttl = :ttl_val"
                    ),
                    "ConditionExpression": (
                        "attribute_not_exists(#cnt) OR #cnt < :cap"
                    ),
                    "ExpressionAttributeNames": {"#cnt": "count", "#ttl": "ttl"},
                    "ExpressionAttributeValues": {
                        ":zero": {"N": "0"},
                        ":one": {"N": "1"},
                        ":cap": {"N": str(tier_config["hourly_cap"])},
                        ":ttl_val": {"N": str(hourly_ttl)},
                    },
                }
            },
            {
                "Update": {
                    "TableName": self._table_name,
                    "Key": {"PK": {"S": pk}, "SK": {"S": daily_sk}},
                    "UpdateExpression": (
                        "SET #cnt = if_not_exists(#cnt, :zero) + :one, #ttl = :ttl_val"
                    ),
                    "ConditionExpression": (
                        "attribute_not_exists(#cnt) OR #cnt < :cap"
                    ),
                    "ExpressionAttributeNames": {"#cnt": "count", "#ttl": "ttl"},
                    "ExpressionAttributeValues": {
                        ":zero": {"N": "0"},
                        ":one": {"N": "1"},
                        ":cap": {"N": str(tier_config["daily_cap"])},
                        ":ttl_val": {"N": str(daily_ttl)},
                    },
                }
            },
            {
                "Update": {
                    "TableName": self._table_name,
                    "Key": {"PK": {"S": pk}, "SK": {"S": monthly_sk}},
                    "UpdateExpression": (
                        "SET #cnt = if_not_exists(#cnt, :zero) + :one, #ttl = :ttl_val"
                    ),
                    "ConditionExpression": (
                        "attribute_not_exists(#cnt) OR #cnt < :cap"
                    ),
                    "ExpressionAttributeNames": {"#cnt": "count", "#ttl": "ttl"},
                    "ExpressionAttributeValues": {
                        ":zero": {"N": "0"},
                        ":one": {"N": "1"},
                        ":cap": {"N": str(tier_config["monthly_cap"])},
                        ":ttl_val": {"N": str(monthly_ttl)},
                    },
                }
            },
        ]

        try:
            client = self._get_client()
            client.transact_write_items(TransactItems=transact_items)

            return RateLimitResult(
                allowed=True,
                exceeded_window=None,
                resets_at=None,
                resets_in_seconds=None,
                current_counts={},
            )

        except ClientError as e:
            error_code = e.response["Error"].get("Code", "")

            if error_code == "TransactionCanceledException":
                # Determine which window(s) were exceeded
                reasons = e.response.get("CancellationReasons", [])
                exceeded = self._find_exceeded_window(
                    reasons, hourly_window, daily_window, monthly_window,
                    billing_anchor_day, now,
                )
                return exceeded

            # Non-transaction error: hybrid fail mode
            return self._handle_dynamo_error(e, tier_config, user_id)

        except Exception as e:
            # Any other error (timeout, connection, etc.): hybrid fail mode
            logger.error("Unexpected error in rate limit check: %s", str(e))
            return self._handle_dynamo_error(e, tier_config, user_id)

    def _find_exceeded_window(
        self,
        reasons: list[dict],
        hourly_window: str,
        daily_window: str,
        monthly_window: str,
        billing_anchor_day: int,
        now: datetime,
    ) -> RateLimitResult:
        """Determine which window was exceeded from transaction cancellation reasons.

        Returns the highest-priority (hourly > daily > monthly) exceeded window.
        """
        window_map = {
            0: (WindowType.HOURLY, hourly_window),
            1: (WindowType.DAILY, daily_window),
            2: (WindowType.MONTHLY, monthly_window),
        }

        for idx in range(3):  # Check in priority order: hourly, daily, monthly
            if idx < len(reasons):
                reason = reasons[idx]
                code = reason.get("Code", "")
                if code == "ConditionalCheckFailed":
                    window_type, window_id = window_map[idx]
                    resets_at = self._calculate_reset_time(
                        window_type, window_id, billing_anchor_day, now
                    )
                    resets_in = max(0, int((resets_at - now).total_seconds()))

                    return RateLimitResult(
                        allowed=False,
                        exceeded_window=window_type.value,
                        resets_at=resets_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        resets_in_seconds=resets_in,
                        current_counts={},
                    )

        # Fallback: shouldn't happen but return denied with hourly
        resets_at = self._calculate_reset_time(
            WindowType.HOURLY, hourly_window, billing_anchor_day, now
        )
        resets_in = max(0, int((resets_at - now).total_seconds()))
        return RateLimitResult(
            allowed=False,
            exceeded_window=WindowType.HOURLY.value,
            resets_at=resets_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            resets_in_seconds=resets_in,
            current_counts={},
        )

    def _handle_dynamo_error(
        self, error: Exception, tier_config: TierConfig, user_id: str
    ) -> RateLimitResult:
        """Handle DynamoDB errors with hybrid fail mode.

        Free tier → fail-closed (503 "retry")
        Subscriber/Admin → fail-open (allowed)
        """
        tier = tier_config.get("tier", "free")

        if tier == UserTier.FREE or tier == "free":
            logger.warning(
                "Rate limit DynamoDB error for free user %s, fail-closed: %s",
                user_id, str(error),
            )
            return RateLimitResult(
                allowed=False,
                exceeded_window="SERVICE_UNAVAILABLE",
                resets_at=None,
                resets_in_seconds=None,
                current_counts={},
            )
        else:
            logger.warning(
                "Rate limit DynamoDB error for %s user %s, fail-open: %s",
                tier, user_id, str(error),
            )
            return RateLimitResult(
                allowed=True,
                exceeded_window=None,
                resets_at=None,
                resets_in_seconds=None,
                current_counts={},
            )

    @staticmethod
    def _get_current_windows(
        billing_anchor_day: int = 1,
        now: datetime | None = None,
    ) -> tuple[str, str, str]:
        """Calculate current window identifiers for hourly, daily, monthly.

        Args:
            billing_anchor_day: Day of month when monthly billing resets.
            now: Current UTC datetime (defaults to now).

        Returns:
            Tuple of (hourly_window, daily_window, monthly_window) strings.
        """
        if now is None:
            now = datetime.now(timezone.utc)

        hourly_window = now.strftime("%Y-%m-%dT%H")
        daily_window = now.strftime("%Y-%m-%d")

        # Monthly window: if current day >= anchor, use current month
        # Otherwise, use previous month
        current_day = now.day
        # Clamp anchor to last day of current month
        last_day = calendar.monthrange(now.year, now.month)[1]
        effective_anchor = min(billing_anchor_day, last_day)

        if current_day >= effective_anchor:
            monthly_window = now.strftime("%Y-%m")
        else:
            # Previous month
            prev = now.replace(day=1) - timedelta(days=1)
            monthly_window = prev.strftime("%Y-%m")

        return hourly_window, daily_window, monthly_window

    @staticmethod
    def _calculate_reset_time(
        window_type: WindowType,
        current_window: str,
        billing_anchor_day: int = 1,
        now: datetime | None = None,
    ) -> datetime:
        """Calculate when a rate limit window resets.

        Args:
            window_type: Which window to calculate reset for.
            current_window: Current window identifier string.
            billing_anchor_day: Day of month for monthly reset.
            now: Current UTC datetime.

        Returns:
            datetime when the window resets.
        """
        if now is None:
            now = datetime.now(timezone.utc)

        if window_type == WindowType.HOURLY:
            # Reset at the start of the next hour
            next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            return next_hour

        elif window_type == WindowType.DAILY:
            # Reset at midnight UTC tomorrow
            tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            return tomorrow

        else:  # MONTHLY
            # Reset at the next billing anchor day
            last_day = calendar.monthrange(now.year, now.month)[1]
            effective_anchor = min(billing_anchor_day, last_day)

            if now.day < effective_anchor:
                # Resets later this month
                return now.replace(
                    day=effective_anchor, hour=0, minute=0, second=0, microsecond=0
                )
            else:
                # Resets next month
                next_month = now.replace(day=1) + timedelta(days=last_day)
                next_last = calendar.monthrange(next_month.year, next_month.month)[1]
                anchor = min(billing_anchor_day, next_last)
                return next_month.replace(
                    day=anchor, hour=0, minute=0, second=0, microsecond=0
                )

    def get_counter_state(
        self, user_id: str, billing_anchor_day: int = 1
    ) -> CounterState:
        """Read current counter values without incrementing.

        Args:
            user_id: The user's unique identifier.
            billing_anchor_day: Day of month for monthly window reset.

        Returns:
            CounterState with current counts for all windows.
        """
        now = datetime.now(timezone.utc)
        hourly_window, daily_window, monthly_window = self._get_current_windows(
            billing_anchor_day, now
        )
        pk = f"USER#{user_id}"

        counts: dict[str, int] = {}
        windows = [
            (f"RATE#HOURLY#{hourly_window}", "hourly"),
            (f"RATE#DAILY#{daily_window}", "daily"),
            (f"RATE#MONTHLY#{monthly_window}", "monthly"),
        ]

        try:
            client = self._get_client()
            for sk, name in windows:
                response = client.get_item(
                    TableName=self._table_name,
                    Key={"PK": {"S": pk}, "SK": {"S": sk}},
                )
                item = response.get("Item")
                if item and "count" in item:
                    counts[name] = int(item["count"]["N"])
                else:
                    counts[name] = 0
        except (ClientError, Exception) as e:
            logger.warning("Failed to read counter state: %s", str(e))
            counts = {"hourly": 0, "daily": 0, "monthly": 0}

        return CounterState(
            user_id=user_id,
            hourly_count=counts.get("hourly", 0),
            hourly_window=hourly_window,
            daily_count=counts.get("daily", 0),
            daily_window=daily_window,
            monthly_count=counts.get("monthly", 0),
            monthly_window=monthly_window,
        )
