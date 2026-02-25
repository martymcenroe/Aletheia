"""Unit tests for MultiWindowCounter.

Issue: #364 - Tiered rate limiting with multi-window caps.

Tests cover:
- T010: Request under all limits → allowed
- T020: Hourly limit exceeded → 429 with hourly window
- T030: Daily limit exceeded → 429 with daily window
- T040: Monthly limit exceeded → 429 with monthly window
- T050: Free tier boundary (5th hourly OK, 6th fails)
- T060: Subscriber tier boundary (20th hourly OK, 21st fails)
- T080a: DynamoDB timeout + free tier → fail-closed
- T080b: DynamoDB timeout + subscriber tier → fail-open
- T090: Atomic transaction failure → no partial increments
- T100: Monthly anniversary reset with billing_anchor_day
- T110: TTL verification (2h/2d/35d)
- T160: Multiple windows exceeded → returns first (hourly priority)
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from auth.models.rate_limit import TierConfig, WindowType
from auth.token_cap_service import (
    MultiWindowCounter,
    _DAILY_TTL_SECONDS,
    _HOURLY_TTL_SECONDS,
    _MONTHLY_TTL_SECONDS,
)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

TABLE_NAME = "test-token-cap-table"
TEST_USER_ID = "test-user-001"

FREE_CONFIG = TierConfig(tier="free", hourly_cap=5, daily_cap=15, monthly_cap=100)
SUBSCRIBER_CONFIG = TierConfig(tier="subscriber", hourly_cap=20, daily_cap=200, monthly_cap=2000)
ADMIN_CONFIG = TierConfig(tier="admin", hourly_cap=50, daily_cap=500, monthly_cap=10000)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _client_error(code: str, message: str = "test error") -> ClientError:
    """Build a botocore ClientError for testing."""
    return ClientError(
        {"Error": {"Code": code, "Message": message}},
        "TestOperation",
    )


def _transaction_canceled(
    hourly_failed: bool = False,
    daily_failed: bool = False,
    monthly_failed: bool = False,
) -> ClientError:
    """Build a TransactionCanceledException with specific cancellation reasons."""
    reasons = []
    for failed in [hourly_failed, daily_failed, monthly_failed]:
        if failed:
            reasons.append({"Code": "ConditionalCheckFailed", "Message": "cap exceeded"})
        else:
            reasons.append({"Code": "None", "Message": ""})

    error = _client_error("TransactionCanceledException", "Transaction cancelled")
    error.response["CancellationReasons"] = reasons
    return error


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture()
def mock_client():
    """Provide a mock DynamoDB client."""
    return MagicMock()


@pytest.fixture()
def counter(mock_client):
    """Provide a MultiWindowCounter with mock client."""
    return MultiWindowCounter(
        table_name=TABLE_NAME,
        dynamodb_client=mock_client,
        timeout_seconds=2.0,
    )


@pytest.fixture()
def frozen_now():
    """Freeze time to a deterministic datetime."""
    now = datetime(2026, 2, 16, 14, 30, 0, tzinfo=timezone.utc)
    with patch("auth.token_cap_service.datetime") as mock_dt:
        mock_dt.now.return_value = now
        mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
        yield now


# --------------------------------------------------------------------------- #
# T010: Request under all limits → allowed
# --------------------------------------------------------------------------- #


class TestUnderAllLimits:
    """T010: Request under all rate limits returns allowed."""

    def test_allowed_when_under_caps(self, counter, mock_client):
        """All counters under cap → allowed=True."""
        mock_client.transact_write_items.return_value = {}

        result = counter.check_and_increment(TEST_USER_ID, FREE_CONFIG)

        assert result["allowed"] is True
        assert result["exceeded_window"] is None
        mock_client.transact_write_items.assert_called_once()

    def test_transaction_has_three_updates(self, counter, mock_client):
        """Transaction includes 3 Update items (hourly, daily, monthly)."""
        mock_client.transact_write_items.return_value = {}

        counter.check_and_increment(TEST_USER_ID, FREE_CONFIG)

        call_kwargs = mock_client.transact_write_items.call_args[1]
        assert len(call_kwargs["TransactItems"]) == 3

    def test_all_updates_use_conditional_write(self, counter, mock_client):
        """Each update has ConditionExpression for cap enforcement."""
        mock_client.transact_write_items.return_value = {}

        counter.check_and_increment(TEST_USER_ID, FREE_CONFIG)

        call_kwargs = mock_client.transact_write_items.call_args[1]
        for item in call_kwargs["TransactItems"]:
            assert "ConditionExpression" in item["Update"]

    def test_pk_format(self, counter, mock_client):
        """PK uses USER#{user_id} format."""
        mock_client.transact_write_items.return_value = {}

        counter.check_and_increment(TEST_USER_ID, FREE_CONFIG)

        call_kwargs = mock_client.transact_write_items.call_args[1]
        for item in call_kwargs["TransactItems"]:
            pk = item["Update"]["Key"]["PK"]["S"]
            assert pk == f"USER#{TEST_USER_ID}"

    def test_sk_format_hourly(self, counter, mock_client):
        """SK for hourly counter uses RATE#HOURLY#{window} format."""
        mock_client.transact_write_items.return_value = {}

        counter.check_and_increment(TEST_USER_ID, FREE_CONFIG)

        call_kwargs = mock_client.transact_write_items.call_args[1]
        hourly_sk = call_kwargs["TransactItems"][0]["Update"]["Key"]["SK"]["S"]
        assert hourly_sk.startswith("RATE#HOURLY#")


# --------------------------------------------------------------------------- #
# T020: Hourly limit exceeded → 429 with hourly window
# --------------------------------------------------------------------------- #


class TestHourlyLimitExceeded:
    """T020: Hourly rate limit exceeded returns correct response."""

    def test_hourly_exceeded_returns_denied(self, counter, mock_client):
        """Hourly cap exceeded → allowed=False."""
        mock_client.transact_write_items.side_effect = _transaction_canceled(
            hourly_failed=True
        )

        result = counter.check_and_increment(TEST_USER_ID, FREE_CONFIG)

        assert result["allowed"] is False
        assert result["exceeded_window"] == "hourly"

    def test_hourly_exceeded_has_reset_time(self, counter, mock_client):
        """Hourly exceeded response includes resets_at."""
        mock_client.transact_write_items.side_effect = _transaction_canceled(
            hourly_failed=True
        )

        result = counter.check_and_increment(TEST_USER_ID, FREE_CONFIG)

        assert result["resets_at"] is not None
        assert "T" in result["resets_at"]  # ISO format

    def test_hourly_exceeded_has_resets_in_seconds(self, counter, mock_client):
        """Hourly exceeded response includes resets_in_seconds."""
        mock_client.transact_write_items.side_effect = _transaction_canceled(
            hourly_failed=True
        )

        result = counter.check_and_increment(TEST_USER_ID, FREE_CONFIG)

        assert result["resets_in_seconds"] is not None
        assert result["resets_in_seconds"] >= 0


# --------------------------------------------------------------------------- #
# T030: Daily limit exceeded → 429 with daily window
# --------------------------------------------------------------------------- #


class TestDailyLimitExceeded:
    """T030: Daily rate limit exceeded returns correct response."""

    def test_daily_exceeded_returns_denied(self, counter, mock_client):
        """Daily cap exceeded → allowed=False with daily window."""
        mock_client.transact_write_items.side_effect = _transaction_canceled(
            daily_failed=True
        )

        result = counter.check_and_increment(TEST_USER_ID, FREE_CONFIG)

        assert result["allowed"] is False
        assert result["exceeded_window"] == "daily"


# --------------------------------------------------------------------------- #
# T040: Monthly limit exceeded → 429 with monthly window
# --------------------------------------------------------------------------- #


class TestMonthlyLimitExceeded:
    """T040: Monthly rate limit exceeded returns correct response."""

    def test_monthly_exceeded_returns_denied(self, counter, mock_client):
        """Monthly cap exceeded → allowed=False with monthly window."""
        mock_client.transact_write_items.side_effect = _transaction_canceled(
            monthly_failed=True
        )

        result = counter.check_and_increment(TEST_USER_ID, FREE_CONFIG)

        assert result["allowed"] is False
        assert result["exceeded_window"] == "monthly"


# --------------------------------------------------------------------------- #
# T050: Free tier boundary (5th hourly OK, 6th fails)
# --------------------------------------------------------------------------- #


class TestFreeTierBoundary:
    """T050: Free tier boundary behavior at cap limit."""

    def test_5th_request_allowed(self, counter, mock_client):
        """5th request under free hourly cap of 5 is allowed."""
        mock_client.transact_write_items.return_value = {}

        result = counter.check_and_increment(TEST_USER_ID, FREE_CONFIG)

        assert result["allowed"] is True

    def test_6th_request_denied(self, counter, mock_client):
        """6th request exceeding free hourly cap of 5 is denied."""
        mock_client.transact_write_items.side_effect = _transaction_canceled(
            hourly_failed=True
        )

        result = counter.check_and_increment(TEST_USER_ID, FREE_CONFIG)

        assert result["allowed"] is False
        assert result["exceeded_window"] == "hourly"

    def test_free_hourly_cap_in_condition(self, counter, mock_client):
        """Free tier cap of 5 is used in condition expression."""
        mock_client.transact_write_items.return_value = {}

        counter.check_and_increment(TEST_USER_ID, FREE_CONFIG)

        call_kwargs = mock_client.transact_write_items.call_args[1]
        hourly_item = call_kwargs["TransactItems"][0]["Update"]
        cap_value = hourly_item["ExpressionAttributeValues"][":cap_limit"]["N"]
        assert cap_value == "4"


# --------------------------------------------------------------------------- #
# T060: Subscriber tier boundary
# --------------------------------------------------------------------------- #


class TestSubscriberTierBoundary:
    """T060: Subscriber tier boundary at 20 hourly cap."""

    def test_20th_request_allowed(self, counter, mock_client):
        """20th request under subscriber hourly cap of 20 is allowed."""
        mock_client.transact_write_items.return_value = {}

        result = counter.check_and_increment(TEST_USER_ID, SUBSCRIBER_CONFIG)

        assert result["allowed"] is True

    def test_21st_request_denied(self, counter, mock_client):
        """21st request exceeding subscriber hourly cap is denied."""
        mock_client.transact_write_items.side_effect = _transaction_canceled(
            hourly_failed=True
        )

        result = counter.check_and_increment(TEST_USER_ID, SUBSCRIBER_CONFIG)

        assert result["allowed"] is False

    def test_subscriber_hourly_cap_in_condition(self, counter, mock_client):
        """Subscriber tier cap of 20 is used in condition expression."""
        mock_client.transact_write_items.return_value = {}

        counter.check_and_increment(TEST_USER_ID, SUBSCRIBER_CONFIG)

        call_kwargs = mock_client.transact_write_items.call_args[1]
        hourly_item = call_kwargs["TransactItems"][0]["Update"]
        cap_value = hourly_item["ExpressionAttributeValues"][":cap_limit"]["N"]
        assert cap_value == "19"


# --------------------------------------------------------------------------- #
# T080a: DynamoDB timeout + free tier → fail-closed
# --------------------------------------------------------------------------- #


class TestFailClosedFree:
    """T080a: DynamoDB errors with free tier → fail-closed."""

    def test_timeout_free_tier_denied(self, counter, mock_client):
        """DynamoDB timeout for free user → denied."""
        mock_client.transact_write_items.side_effect = _client_error(
            "ProvisionedThroughputExceededException"
        )

        result = counter.check_and_increment(TEST_USER_ID, FREE_CONFIG)

        assert result["allowed"] is False

    def test_timeout_free_tier_service_unavailable(self, counter, mock_client):
        """DynamoDB error for free user → SERVICE_UNAVAILABLE window."""
        mock_client.transact_write_items.side_effect = _client_error(
            "InternalServerError"
        )

        result = counter.check_and_increment(TEST_USER_ID, FREE_CONFIG)

        assert result["exceeded_window"] == "SERVICE_UNAVAILABLE"

    def test_connection_error_free_tier_denied(self, counter, mock_client):
        """Connection error for free user → denied."""
        mock_client.transact_write_items.side_effect = ConnectionError("timeout")

        result = counter.check_and_increment(TEST_USER_ID, FREE_CONFIG)

        assert result["allowed"] is False


# --------------------------------------------------------------------------- #
# T080b: DynamoDB timeout + subscriber tier → fail-closed
# --------------------------------------------------------------------------- #


class TestFailClosedSubscriber:
    """T080b: DynamoDB errors with subscriber tier → fail-closed."""

    def test_timeout_subscriber_denied(self, counter, mock_client):
        """DynamoDB timeout for subscriber → denied (fail-closed)."""
        mock_client.transact_write_items.side_effect = _client_error(
            "ProvisionedThroughputExceededException"
        )

        result = counter.check_and_increment(TEST_USER_ID, SUBSCRIBER_CONFIG)

        assert result["allowed"] is False

    def test_timeout_admin_denied(self, counter, mock_client):
        """DynamoDB timeout for admin → denied (fail-closed)."""
        mock_client.transact_write_items.side_effect = _client_error(
            "InternalServerError"
        )

        result = counter.check_and_increment(TEST_USER_ID, ADMIN_CONFIG)

        assert result["allowed"] is False

    def test_connection_error_subscriber_denied(self, counter, mock_client):
        """Connection error for subscriber → denied (fail-closed)."""
        mock_client.transact_write_items.side_effect = ConnectionError("timeout")

        result = counter.check_and_increment(TEST_USER_ID, SUBSCRIBER_CONFIG)

        assert result["allowed"] is False


# --------------------------------------------------------------------------- #
# T090: Atomic transaction failure → no partial increments
# --------------------------------------------------------------------------- #


class TestAtomicTransaction:
    """T090: Transaction ensures no partial increments."""

    def test_single_transact_write_call(self, counter, mock_client):
        """All three counters updated in a single transact_write_items call."""
        mock_client.transact_write_items.return_value = {}

        counter.check_and_increment(TEST_USER_ID, FREE_CONFIG)

        assert mock_client.transact_write_items.call_count == 1

    def test_all_counters_in_one_transaction(self, counter, mock_client):
        """Transaction contains exactly 3 items for hourly/daily/monthly."""
        mock_client.transact_write_items.return_value = {}

        counter.check_and_increment(TEST_USER_ID, FREE_CONFIG)

        call_kwargs = mock_client.transact_write_items.call_args[1]
        items = call_kwargs["TransactItems"]
        assert len(items) == 3

        # Verify the SK prefixes
        sks = [item["Update"]["Key"]["SK"]["S"] for item in items]
        assert any("RATE#HOURLY#" in sk for sk in sks)
        assert any("RATE#DAILY#" in sk for sk in sks)
        assert any("RATE#MONTHLY#" in sk for sk in sks)


# --------------------------------------------------------------------------- #
# T100: Monthly anniversary reset with billing_anchor_day
# --------------------------------------------------------------------------- #


class TestMonthlyAnchor:
    """T100: Monthly window respects billing_anchor_day."""

    def test_before_anchor_uses_previous_month(self):
        """Day 5 with anchor=15 → previous month window."""
        now = datetime(2026, 2, 5, 10, 0, 0, tzinfo=timezone.utc)
        h, d, m = MultiWindowCounter._get_current_windows(15, now)
        assert m == "2026-01"

    def test_on_anchor_uses_current_month(self):
        """Day 15 with anchor=15 → current month window."""
        now = datetime(2026, 2, 15, 10, 0, 0, tzinfo=timezone.utc)
        h, d, m = MultiWindowCounter._get_current_windows(15, now)
        assert m == "2026-02"

    def test_after_anchor_uses_current_month(self):
        """Day 20 with anchor=15 → current month window."""
        now = datetime(2026, 2, 20, 10, 0, 0, tzinfo=timezone.utc)
        h, d, m = MultiWindowCounter._get_current_windows(15, now)
        assert m == "2026-02"

    def test_anchor_clamped_to_short_month(self):
        """Anchor day 31 in February clamped to 28/29."""
        now = datetime(2026, 2, 28, 10, 0, 0, tzinfo=timezone.utc)
        h, d, m = MultiWindowCounter._get_current_windows(31, now)
        # Feb 28 >= min(31, 28) = 28, so current month
        assert m == "2026-02"

    def test_default_anchor_day_1(self):
        """Default billing_anchor_day=1 uses calendar month."""
        now = datetime(2026, 2, 1, 0, 0, 0, tzinfo=timezone.utc)
        h, d, m = MultiWindowCounter._get_current_windows(1, now)
        assert m == "2026-02"

    def test_hourly_window_format(self):
        """Hourly window is YYYY-MM-DDTHH."""
        now = datetime(2026, 2, 16, 14, 30, 0, tzinfo=timezone.utc)
        h, d, m = MultiWindowCounter._get_current_windows(1, now)
        assert h == "2026-02-16T14"

    def test_daily_window_format(self):
        """Daily window is YYYY-MM-DD."""
        now = datetime(2026, 2, 16, 14, 30, 0, tzinfo=timezone.utc)
        h, d, m = MultiWindowCounter._get_current_windows(1, now)
        assert d == "2026-02-16"


# --------------------------------------------------------------------------- #
# T110: TTL verification
# --------------------------------------------------------------------------- #


class TestTTLValues:
    """T110: Counter TTLs match spec (2h/2d/35d)."""

    def test_hourly_ttl_is_2_hours(self):
        """Hourly TTL is 2 hours (7200 seconds)."""
        assert _HOURLY_TTL_SECONDS == 2 * 3600

    def test_daily_ttl_is_2_days(self):
        """Daily TTL is 2 days (172800 seconds)."""
        assert _DAILY_TTL_SECONDS == 2 * 86400

    def test_monthly_ttl_is_35_days(self):
        """Monthly TTL is 35 days (3024000 seconds)."""
        assert _MONTHLY_TTL_SECONDS == 35 * 86400

    def test_ttl_set_in_hourly_update(self, counter, mock_client):
        """Hourly counter update includes TTL attribute."""
        mock_client.transact_write_items.return_value = {}

        counter.check_and_increment(TEST_USER_ID, FREE_CONFIG)

        call_kwargs = mock_client.transact_write_items.call_args[1]
        hourly_item = call_kwargs["TransactItems"][0]["Update"]
        assert ":ttl_val" in hourly_item["ExpressionAttributeValues"]
        ttl = int(hourly_item["ExpressionAttributeValues"][":ttl_val"]["N"])
        assert ttl > 0

    def test_ttl_set_in_daily_update(self, counter, mock_client):
        """Daily counter update includes TTL attribute."""
        mock_client.transact_write_items.return_value = {}

        counter.check_and_increment(TEST_USER_ID, FREE_CONFIG)

        call_kwargs = mock_client.transact_write_items.call_args[1]
        daily_item = call_kwargs["TransactItems"][1]["Update"]
        assert ":ttl_val" in daily_item["ExpressionAttributeValues"]

    def test_ttl_set_in_monthly_update(self, counter, mock_client):
        """Monthly counter update includes TTL attribute."""
        mock_client.transact_write_items.return_value = {}

        counter.check_and_increment(TEST_USER_ID, FREE_CONFIG)

        call_kwargs = mock_client.transact_write_items.call_args[1]
        monthly_item = call_kwargs["TransactItems"][2]["Update"]
        assert ":ttl_val" in monthly_item["ExpressionAttributeValues"]


# --------------------------------------------------------------------------- #
# T160: Multiple windows exceeded → returns first (hourly priority)
# --------------------------------------------------------------------------- #


class TestMultipleWindowsExceeded:
    """T160: When multiple windows exceeded, report hourly first."""

    def test_hourly_and_daily_exceeded_returns_hourly(self, counter, mock_client):
        """Both hourly and daily exceeded → reports hourly."""
        mock_client.transact_write_items.side_effect = _transaction_canceled(
            hourly_failed=True, daily_failed=True
        )

        result = counter.check_and_increment(TEST_USER_ID, FREE_CONFIG)

        assert result["allowed"] is False
        assert result["exceeded_window"] == "hourly"

    def test_all_three_exceeded_returns_hourly(self, counter, mock_client):
        """All three windows exceeded → reports hourly."""
        mock_client.transact_write_items.side_effect = _transaction_canceled(
            hourly_failed=True, daily_failed=True, monthly_failed=True
        )

        result = counter.check_and_increment(TEST_USER_ID, FREE_CONFIG)

        assert result["allowed"] is False
        assert result["exceeded_window"] == "hourly"

    def test_daily_and_monthly_exceeded_returns_daily(self, counter, mock_client):
        """Daily and monthly exceeded (not hourly) → reports daily."""
        mock_client.transact_write_items.side_effect = _transaction_canceled(
            daily_failed=True, monthly_failed=True
        )

        result = counter.check_and_increment(TEST_USER_ID, FREE_CONFIG)

        assert result["allowed"] is False
        assert result["exceeded_window"] == "daily"


# --------------------------------------------------------------------------- #
# Reset time calculation
# --------------------------------------------------------------------------- #


class TestResetTimeCalculation:
    """Test _calculate_reset_time produces correct reset times."""

    def test_hourly_resets_at_next_hour(self):
        """Hourly window resets at start of next hour."""
        now = datetime(2026, 2, 16, 14, 30, 0, tzinfo=timezone.utc)
        reset = MultiWindowCounter._calculate_reset_time(
            WindowType.HOURLY, "2026-02-16T14", 1, now
        )
        assert reset.hour == 15
        assert reset.minute == 0
        assert reset.second == 0

    def test_daily_resets_at_midnight(self):
        """Daily window resets at midnight UTC tomorrow."""
        now = datetime(2026, 2, 16, 14, 30, 0, tzinfo=timezone.utc)
        reset = MultiWindowCounter._calculate_reset_time(
            WindowType.DAILY, "2026-02-16", 1, now
        )
        assert reset.day == 17
        assert reset.hour == 0

    def test_monthly_resets_at_next_anchor(self):
        """Monthly window resets at next billing anchor day."""
        now = datetime(2026, 2, 16, 14, 30, 0, tzinfo=timezone.utc)
        reset = MultiWindowCounter._calculate_reset_time(
            WindowType.MONTHLY, "2026-02", 1, now
        )
        # Anchor day=1, current day=16, so resets March 1
        assert reset.month == 3
        assert reset.day == 1

    def test_monthly_resets_this_month_if_before_anchor(self):
        """Monthly resets later this month if before anchor day."""
        now = datetime(2026, 2, 5, 14, 30, 0, tzinfo=timezone.utc)
        reset = MultiWindowCounter._calculate_reset_time(
            WindowType.MONTHLY, "2026-01", 15, now
        )
        # Before anchor 15, so resets Feb 15
        assert reset.month == 2
        assert reset.day == 15


# --------------------------------------------------------------------------- #
# get_counter_state
# --------------------------------------------------------------------------- #


class TestGetCounterState:
    """Test read-only counter state retrieval."""

    def test_returns_counter_state(self, counter, mock_client):
        """get_counter_state returns CounterState with all fields."""
        mock_client.get_item.return_value = {
            "Item": {"count": {"N": "3"}}
        }

        state = counter.get_counter_state(TEST_USER_ID)

        assert state["user_id"] == TEST_USER_ID
        assert "hourly_count" in state
        assert "daily_count" in state
        assert "monthly_count" in state

    def test_returns_zero_when_no_counters(self, counter, mock_client):
        """Counter state returns 0 when no items exist."""
        mock_client.get_item.return_value = {}

        state = counter.get_counter_state(TEST_USER_ID)

        assert state["hourly_count"] == 0
        assert state["daily_count"] == 0
        assert state["monthly_count"] == 0

    def test_handles_dynamodb_error(self, counter, mock_client):
        """Counter state returns 0s on DynamoDB error."""
        mock_client.get_item.side_effect = _client_error("InternalServerError")

        state = counter.get_counter_state(TEST_USER_ID)

        assert state["hourly_count"] == 0
        assert state["daily_count"] == 0
        assert state["monthly_count"] == 0
