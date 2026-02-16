"""Daily token cap tracking and enforcement.

Issue: #341 - Add JWT authentication to analysis endpoint with daily token cap.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import TypedDict

import boto3
from botocore.exceptions import ClientError

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
