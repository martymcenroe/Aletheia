"""Unit tests for token cap service.

Issue: #341 - Add JWT authentication to analysis endpoint with daily token cap.

Tests cover:
- T060: Token cap - under limit (REQ-5)
- T070: Token cap - at limit (REQ-7)
- T080: Token cap - race condition / atomic increment (REQ-7)
- T120: Admin set cap via CLI / DynamoDB (REQ-8)
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from auth.token_cap_service import (
    CAP_CONFIG_PK,
    CAP_CONFIG_SK,
    COUNTER_SK_PREFIX,
    DEFAULT_DAILY_CAP,
    check_and_increment_cap,
    get_current_cap,
    get_today_key,
    set_daily_cap,
)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

TABLE_NAME = "test-token-cap-table"
TEST_ADMIN_ID = "admin-user-001"

# 7 days in seconds (matches _get_ttl_epoch logic)
COUNTER_TTL_SECONDS = 7 * 24 * 3600


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _client_error(code: str, message: str = "test error") -> ClientError:
    """Build a botocore ClientError for testing."""
    return ClientError(
        {"Error": {"Code": code, "Message": message}},
        "TestOperation",
    )


def _build_mock_dynamodb():
    """Build a mock DynamoDB resource + table pair."""
    mock_resource = MagicMock()
    mock_table = MagicMock()
    mock_resource.Table.return_value = mock_table
    return mock_resource, mock_table


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture()
def mock_dynamodb():
    """Provide a mock DynamoDB resource + table injected via _get_dynamodb_resource."""
    mock_resource, mock_table = _build_mock_dynamodb()
    with patch(
        "auth.token_cap_service._get_dynamodb_resource",
        return_value=mock_resource,
    ):
        yield mock_table


@pytest.fixture()
def frozen_today():
    """Freeze get_today_key to a deterministic date."""
    with patch(
        "auth.token_cap_service.get_today_key", return_value="2026-02-16"
    ):
        yield "2026-02-16"


# --------------------------------------------------------------------------- #
# get_today_key
# --------------------------------------------------------------------------- #


class TestGetTodayKey:
    """Utility: get_today_key returns UTC date string."""

    def test_returns_yyyy_mm_dd_format(self):
        """Date key matches YYYY-MM-DD pattern."""
        key = get_today_key()
        # Validate format by parsing back
        parsed = datetime.strptime(key, "%Y-%m-%d")
        assert parsed is not None

    def test_uses_utc_timezone(self):
        """Date key is based on UTC, not local time."""
        fixed_utc = datetime(2026, 2, 16, 23, 59, 59, tzinfo=timezone.utc)
        with patch("auth.token_cap_service.datetime", wraps=datetime) as mock_dt:
            mock_dt.now.return_value = fixed_utc
            key = get_today_key()
            mock_dt.now.assert_called_once_with(timezone.utc)
            assert key == "2026-02-16"

    def test_returns_string(self):
        """Date key is a string."""
        assert isinstance(get_today_key(), str)


# --------------------------------------------------------------------------- #
# T060 - test_check_cap_under_limit (REQ-5)
# --------------------------------------------------------------------------- #


class TestCheckCapUnderLimit:
    """T060: Returns (True, count) when under cap."""

    def test_under_cap_returns_allowed(self, mock_dynamodb, frozen_today):
        """When count < cap, request is allowed."""
        # get_current_cap reads CONFIG record via get_item
        mock_dynamodb.get_item.return_value = {
            "Item": {"PK": CAP_CONFIG_PK, "SK": CAP_CONFIG_SK, "daily_cap": 20}
        }
        # Atomic increment succeeds (count goes from 5 to 6)
        mock_dynamodb.update_item.return_value = {
            "Attributes": {"tokens_issued": 6}
        }

        allowed, count = check_and_increment_cap(TABLE_NAME)

        assert allowed is True
        assert count == 6

    def test_first_token_of_day(self, mock_dynamodb, frozen_today):
        """First token of the day succeeds (attribute_not_exists path)."""
        mock_dynamodb.get_item.return_value = {
            "Item": {"PK": CAP_CONFIG_PK, "SK": CAP_CONFIG_SK, "daily_cap": 20}
        }
        mock_dynamodb.update_item.return_value = {
            "Attributes": {"tokens_issued": 1}
        }

        allowed, count = check_and_increment_cap(TABLE_NAME)

        assert allowed is True
        assert count == 1

    def test_increment_uses_conditional_write(self, mock_dynamodb, frozen_today):
        """Atomic increment uses ConditionExpression to prevent over-cap."""
        mock_dynamodb.get_item.return_value = {
            "Item": {"PK": CAP_CONFIG_PK, "SK": CAP_CONFIG_SK, "daily_cap": 20}
        }
        mock_dynamodb.update_item.return_value = {
            "Attributes": {"tokens_issued": 10}
        }

        check_and_increment_cap(TABLE_NAME)

        call_kwargs = mock_dynamodb.update_item.call_args[1]
        assert "ConditionExpression" in call_kwargs
        assert "attribute_not_exists" in call_kwargs["ConditionExpression"]

    def test_counter_has_ttl(self, mock_dynamodb, frozen_today):
        """Counter records include a TTL for automatic cleanup."""
        mock_dynamodb.get_item.return_value = {
            "Item": {"PK": CAP_CONFIG_PK, "SK": CAP_CONFIG_SK, "daily_cap": 20}
        }
        mock_dynamodb.update_item.return_value = {
            "Attributes": {"tokens_issued": 1}
        }

        before = int(time.time())
        check_and_increment_cap(TABLE_NAME)
        after = int(time.time())

        call_kwargs = mock_dynamodb.update_item.call_args[1]
        expr_values = call_kwargs["ExpressionAttributeValues"]
        ttl_value = int(expr_values[":ttl_val"])
        expected_min = before + COUNTER_TTL_SECONDS
        expected_max = after + COUNTER_TTL_SECONDS
        assert expected_min <= ttl_value <= expected_max

    def test_returns_tuple(self, mock_dynamodb, frozen_today):
        """Return value is a tuple of (bool, int)."""
        mock_dynamodb.get_item.return_value = {
            "Item": {"PK": CAP_CONFIG_PK, "SK": CAP_CONFIG_SK, "daily_cap": 20}
        }
        mock_dynamodb.update_item.return_value = {
            "Attributes": {"tokens_issued": 15}
        }

        result = check_and_increment_cap(TABLE_NAME)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], int)


# --------------------------------------------------------------------------- #
# T070 - test_check_cap_at_limit (REQ-7)
# --------------------------------------------------------------------------- #


class TestCheckCapAtLimit:
    """T070: Returns (False, count) and 503 when at cap."""

    def test_at_cap_returns_denied(self, mock_dynamodb, frozen_today):
        """When count == cap, conditional write fails and request is denied."""
        # First get_item call: get_current_cap reads CONFIG
        # Second get_item call: _get_current_count fallback after ConditionalCheckFailed
        mock_dynamodb.get_item.side_effect = [
            {"Item": {"PK": CAP_CONFIG_PK, "SK": CAP_CONFIG_SK, "daily_cap": 20}},
            {"Item": {"PK": "COUNTER", "SK": f"{COUNTER_SK_PREFIX}2026-02-16", "tokens_issued": 20}},
        ]
        # Conditional write fails (cap reached)
        mock_dynamodb.update_item.side_effect = _client_error(
            "ConditionalCheckFailedException"
        )

        allowed, count = check_and_increment_cap(TABLE_NAME)

        assert allowed is False
        assert count == 20

    def test_21st_token_denied_when_cap_is_20(self, mock_dynamodb, frozen_today):
        """REQ-7: 21st token issuance when cap=20 is denied."""
        mock_dynamodb.get_item.side_effect = [
            {"Item": {"PK": CAP_CONFIG_PK, "SK": CAP_CONFIG_SK, "daily_cap": 20}},
            {"Item": {"PK": "COUNTER", "SK": f"{COUNTER_SK_PREFIX}2026-02-16", "tokens_issued": 20}},
        ]
        mock_dynamodb.update_item.side_effect = _client_error(
            "ConditionalCheckFailedException"
        )

        allowed, count = check_and_increment_cap(TABLE_NAME)

        assert allowed is False
        # Count should reflect the current (at-cap) value
        assert count >= 20

    def test_over_cap_returns_false(self, mock_dynamodb, frozen_today):
        """Count already exceeding cap returns denied."""
        mock_dynamodb.get_item.side_effect = [
            {"Item": {"PK": CAP_CONFIG_PK, "SK": CAP_CONFIG_SK, "daily_cap": 20}},
            {"Item": {"PK": "COUNTER", "SK": f"{COUNTER_SK_PREFIX}2026-02-16", "tokens_issued": 25}},
        ]
        mock_dynamodb.update_item.side_effect = _client_error(
            "ConditionalCheckFailedException"
        )

        allowed, count = check_and_increment_cap(TABLE_NAME)

        assert allowed is False

    def test_cap_of_one_blocks_second_request(self, mock_dynamodb, frozen_today):
        """With cap=1, second request is denied."""
        mock_dynamodb.get_item.side_effect = [
            {"Item": {"PK": CAP_CONFIG_PK, "SK": CAP_CONFIG_SK, "daily_cap": 1}},
            {"Item": {"PK": "COUNTER", "SK": f"{COUNTER_SK_PREFIX}2026-02-16", "tokens_issued": 1}},
        ]
        mock_dynamodb.update_item.side_effect = _client_error(
            "ConditionalCheckFailedException"
        )

        allowed, count = check_and_increment_cap(TABLE_NAME)

        assert allowed is False
        assert count == 1

    def test_unexpected_dynamodb_error_raises(self, mock_dynamodb, frozen_today):
        """Non-conditional-check DynamoDB errors propagate as exceptions."""
        mock_dynamodb.get_item.return_value = {
            "Item": {"PK": CAP_CONFIG_PK, "SK": CAP_CONFIG_SK, "daily_cap": 20}
        }
        mock_dynamodb.update_item.side_effect = _client_error(
            "ProvisionedThroughputExceededException"
        )

        with pytest.raises(ClientError) as exc_info:
            check_and_increment_cap(TABLE_NAME)

        assert (
            exc_info.value.response["Error"]["Code"]
            == "ProvisionedThroughputExceededException"
        )


# --------------------------------------------------------------------------- #
# T080 - test_check_cap_race_condition (REQ-7)
# --------------------------------------------------------------------------- #


class TestCheckCapRaceCondition:
    """T080: Handles concurrent increments atomically."""

    def test_conditional_write_prevents_over_increment(
        self, mock_dynamodb, frozen_today
    ):
        """Two concurrent requests: one succeeds, one gets ConditionalCheckFailed."""
        mock_dynamodb.get_item.return_value = {
            "Item": {"PK": CAP_CONFIG_PK, "SK": CAP_CONFIG_SK, "daily_cap": 20}
        }
        mock_dynamodb.update_item.return_value = {
            "Attributes": {"tokens_issued": 20}
        }

        # First concurrent request succeeds (count goes to 20)
        allowed, count = check_and_increment_cap(TABLE_NAME)
        assert allowed is True
        assert count == 20

    def test_second_concurrent_request_denied(self, mock_dynamodb, frozen_today):
        """Second concurrent request sees ConditionalCheckFailedException."""
        mock_dynamodb.get_item.side_effect = [
            {"Item": {"PK": CAP_CONFIG_PK, "SK": CAP_CONFIG_SK, "daily_cap": 20}},
            {"Item": {"PK": "COUNTER", "SK": f"{COUNTER_SK_PREFIX}2026-02-16", "tokens_issued": 20}},
        ]
        mock_dynamodb.update_item.side_effect = _client_error(
            "ConditionalCheckFailedException"
        )

        allowed, count = check_and_increment_cap(TABLE_NAME)
        assert allowed is False
        assert count == 20

    def test_update_expression_uses_if_not_exists(
        self, mock_dynamodb, frozen_today
    ):
        """UpdateExpression uses if_not_exists for atomic initialize-or-increment."""
        mock_dynamodb.get_item.return_value = {
            "Item": {"PK": CAP_CONFIG_PK, "SK": CAP_CONFIG_SK, "daily_cap": 20}
        }
        mock_dynamodb.update_item.return_value = {
            "Attributes": {"tokens_issued": 1}
        }

        check_and_increment_cap(TABLE_NAME)

        call_kwargs = mock_dynamodb.update_item.call_args[1]
        # if_not_exists ensures atomic increment even for first write
        assert "if_not_exists" in call_kwargs["UpdateExpression"]

    def test_returns_all_new_to_get_post_increment_count(
        self, mock_dynamodb, frozen_today
    ):
        """ReturnValues=ALL_NEW ensures we get the count after increment."""
        mock_dynamodb.get_item.return_value = {
            "Item": {"PK": CAP_CONFIG_PK, "SK": CAP_CONFIG_SK, "daily_cap": 20}
        }
        mock_dynamodb.update_item.return_value = {
            "Attributes": {"tokens_issued": 7}
        }

        check_and_increment_cap(TABLE_NAME)

        call_kwargs = mock_dynamodb.update_item.call_args[1]
        assert call_kwargs["ReturnValues"] == "ALL_NEW"

    def test_condition_checks_tokens_less_than_cap(
        self, mock_dynamodb, frozen_today
    ):
        """ConditionExpression compares tokens < cap, not <=."""
        mock_dynamodb.get_item.return_value = {
            "Item": {"PK": CAP_CONFIG_PK, "SK": CAP_CONFIG_SK, "daily_cap": 20}
        }
        mock_dynamodb.update_item.return_value = {
            "Attributes": {"tokens_issued": 1}
        }

        check_and_increment_cap(TABLE_NAME)

        call_kwargs = mock_dynamodb.update_item.call_args[1]
        condition = call_kwargs["ConditionExpression"]
        # Must use strict less-than to ensure count never exceeds cap
        assert "tokens_issued < :cap" in condition


# --------------------------------------------------------------------------- #
# get_current_cap
# --------------------------------------------------------------------------- #


class TestGetCurrentCap:
    """Reading the current daily cap from DynamoDB."""

    def test_returns_cap_from_config_record(self, mock_dynamodb):
        """Reads cap from CONFIG record."""
        mock_dynamodb.get_item.return_value = {
            "Item": {
                "PK": CAP_CONFIG_PK,
                "SK": CAP_CONFIG_SK,
                "daily_cap": 30,
            }
        }

        cap = get_current_cap(TABLE_NAME)

        assert cap == 30

    def test_returns_default_when_no_config(self, mock_dynamodb):
        """Returns DEFAULT_DAILY_CAP when no CONFIG record exists."""
        mock_dynamodb.get_item.return_value = {}

        cap = get_current_cap(TABLE_NAME)

        assert cap == DEFAULT_DAILY_CAP

    def test_returns_default_when_config_missing_cap_attr(self, mock_dynamodb):
        """Returns default when CONFIG record exists but lacks daily_cap."""
        mock_dynamodb.get_item.return_value = {
            "Item": {"PK": CAP_CONFIG_PK, "SK": CAP_CONFIG_SK}
        }

        cap = get_current_cap(TABLE_NAME)

        assert cap == DEFAULT_DAILY_CAP

    def test_queries_config_key(self, mock_dynamodb):
        """Reads the CONFIG partition key, not a date key."""
        mock_dynamodb.get_item.return_value = {}

        get_current_cap(TABLE_NAME)

        call_kwargs = mock_dynamodb.get_item.call_args[1]
        assert call_kwargs["Key"]["PK"] == CAP_CONFIG_PK
        assert call_kwargs["Key"]["SK"] == CAP_CONFIG_SK

    def test_dynamodb_error_raises(self, mock_dynamodb):
        """DynamoDB ClientError propagates (fail closed)."""
        mock_dynamodb.get_item.side_effect = _client_error("InternalServerError")

        with pytest.raises(ClientError):
            get_current_cap(TABLE_NAME)


# --------------------------------------------------------------------------- #
# T120 - test_admin_set_cap (REQ-8)
# --------------------------------------------------------------------------- #


class TestSetDailyCap:
    """T120: Admin can update daily cap in DynamoDB without redeployment."""

    def test_set_cap_returns_true(self, mock_dynamodb):
        """Successful cap update returns True."""
        result = set_daily_cap(TABLE_NAME, 30, TEST_ADMIN_ID)

        assert result is True

    def test_set_cap_writes_to_dynamodb(self, mock_dynamodb):
        """Cap is written to DynamoDB CONFIG record."""
        set_daily_cap(TABLE_NAME, 50, TEST_ADMIN_ID)

        mock_dynamodb.put_item.assert_called_once()
        call_kwargs = mock_dynamodb.put_item.call_args[1]
        item = call_kwargs["Item"]
        assert item["PK"] == CAP_CONFIG_PK
        assert item["SK"] == CAP_CONFIG_SK
        assert item["daily_cap"] == 50

    def test_set_cap_records_admin_id(self, mock_dynamodb):
        """Admin ID is stored for audit trail."""
        set_daily_cap(TABLE_NAME, 25, TEST_ADMIN_ID)

        call_kwargs = mock_dynamodb.put_item.call_args[1]
        item = call_kwargs["Item"]
        assert item["updated_by"] == TEST_ADMIN_ID

    def test_set_cap_records_timestamp(self, mock_dynamodb):
        """Update timestamp is stored."""
        set_daily_cap(TABLE_NAME, 25, TEST_ADMIN_ID)

        call_kwargs = mock_dynamodb.put_item.call_args[1]
        item = call_kwargs["Item"]
        assert "updated_at" in item
        # Validate ISO format
        assert "T" in item["updated_at"]

    def test_set_cap_rejects_zero(self, mock_dynamodb):
        """Cap of zero is rejected."""
        with pytest.raises(ValueError, match="positive integer"):
            set_daily_cap(TABLE_NAME, 0, TEST_ADMIN_ID)

    def test_set_cap_rejects_negative(self, mock_dynamodb):
        """Negative cap is rejected."""
        with pytest.raises(ValueError, match="positive integer"):
            set_daily_cap(TABLE_NAME, -5, TEST_ADMIN_ID)

    def test_set_cap_rejects_non_integer(self, mock_dynamodb):
        """Non-integer cap is rejected."""
        with pytest.raises((ValueError, TypeError)):
            set_daily_cap(TABLE_NAME, 3.5, TEST_ADMIN_ID)  # type: ignore[arg-type]

    def test_set_cap_dynamodb_error_raises(self, mock_dynamodb):
        """DynamoDB errors propagate as ClientError (fail closed)."""
        mock_dynamodb.put_item.side_effect = _client_error("AccessDeniedException")

        with pytest.raises(ClientError):
            set_daily_cap(TABLE_NAME, 30, TEST_ADMIN_ID)

    def test_cap_can_be_read_after_set(self, mock_dynamodb):
        """After setting cap, get_current_cap returns the new value."""
        # set_daily_cap writes
        set_daily_cap(TABLE_NAME, 42, TEST_ADMIN_ID)

        # Simulate get_current_cap reading back what was written
        mock_dynamodb.get_item.return_value = {
            "Item": {
                "PK": CAP_CONFIG_PK,
                "SK": CAP_CONFIG_SK,
                "daily_cap": 42,
            }
        }

        cap = get_current_cap(TABLE_NAME)
        assert cap == 42

    def test_set_cap_accepts_large_value(self, mock_dynamodb):
        """Large cap values are accepted."""
        result = set_daily_cap(TABLE_NAME, 10000, TEST_ADMIN_ID)

        assert result is True
        call_kwargs = mock_dynamodb.put_item.call_args[1]
        assert call_kwargs["Item"]["daily_cap"] == 10000

    def test_set_cap_accepts_one(self, mock_dynamodb):
        """Minimum valid cap of 1 is accepted."""
        result = set_daily_cap(TABLE_NAME, 1, TEST_ADMIN_ID)

        assert result is True
        call_kwargs = mock_dynamodb.put_item.call_args[1]
        assert call_kwargs["Item"]["daily_cap"] == 1


# --------------------------------------------------------------------------- #
# Module constants
# --------------------------------------------------------------------------- #


class TestModuleConstants:
    """Verify module-level constants match LLD specification."""

    def test_default_daily_cap_is_20(self):
        """LLD specifies default cap of 20."""
        assert DEFAULT_DAILY_CAP == 20

    def test_config_pk_defined(self):
        """CAP_CONFIG_PK is a well-known constant."""
        assert CAP_CONFIG_PK == "CONFIG"

    def test_config_sk_defined(self):
        """CAP_CONFIG_SK is a well-known constant."""
        assert CAP_CONFIG_SK == "daily_cap"

    def test_counter_sk_prefix_defined(self):
        """COUNTER_SK_PREFIX is used for daily counter records."""
        assert COUNTER_SK_PREFIX == "COUNT#"
