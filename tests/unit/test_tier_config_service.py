"""Unit tests for TierConfigService.

Issue: #364 - Tiered rate limiting with multi-window caps.

Tests cover:
- T130: Cache hit (second call within 5 min → no DynamoDB call)
- T150: Config loaded from DynamoDB
- T170: Tier config values match stored values
- T180: Admin tier uses 50/500/10000 caps
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from auth.models.rate_limit import UserTier
from auth.tier_config_service import TierConfigService, _CACHE_TTL, _DEFAULT_CONFIGS

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

TABLE_NAME = "test-token-cap-table"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _client_error(code: str, message: str = "test error") -> ClientError:
    """Build a botocore ClientError for testing."""
    return ClientError(
        {"Error": {"Code": code, "Message": message}},
        "TestOperation",
    )


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture()
def mock_client():
    """Provide a mock DynamoDB client."""
    return MagicMock()


@pytest.fixture()
def service(mock_client):
    """Provide a TierConfigService with mock client."""
    return TierConfigService(table_name=TABLE_NAME, dynamodb_client=mock_client)


# --------------------------------------------------------------------------- #
# Default configs
# --------------------------------------------------------------------------- #


class TestDefaultConfigs:
    """Verify hardcoded default tier configurations."""

    def test_free_defaults(self, service, mock_client):
        """Free tier defaults: 5/15/100."""
        mock_client.get_item.return_value = {}

        config = service.get_tier_config(UserTier.FREE)

        assert config["hourly_cap"] == 5
        assert config["daily_cap"] == 15
        assert config["monthly_cap"] == 100

    def test_subscriber_defaults(self, service, mock_client):
        """Subscriber tier defaults: 20/200/2000."""
        mock_client.get_item.return_value = {}

        config = service.get_tier_config(UserTier.SUBSCRIBER)

        assert config["hourly_cap"] == 20
        assert config["daily_cap"] == 200
        assert config["monthly_cap"] == 2000

    def test_admin_defaults(self, service, mock_client):
        """T180: Admin tier defaults: 50/500/10000."""
        mock_client.get_item.return_value = {}

        config = service.get_tier_config(UserTier.ADMIN)

        assert config["hourly_cap"] == 50
        assert config["daily_cap"] == 500
        assert config["monthly_cap"] == 10000

    def test_unknown_tier_defaults_to_free(self, service, mock_client):
        """Unknown tier string defaults to free tier limits."""
        mock_client.get_item.return_value = {}

        config = service.get_tier_config("enterprise")

        assert config["hourly_cap"] == 5
        assert config["daily_cap"] == 15
        assert config["monthly_cap"] == 100


# --------------------------------------------------------------------------- #
# T130: Cache hit
# --------------------------------------------------------------------------- #


class TestCacheHit:
    """T130: Second call within 5 min uses cache, no DynamoDB call."""

    def test_cache_hit_no_second_dynamo_call(self, service, mock_client):
        """Second get_tier_config call within TTL doesn't call DynamoDB."""
        mock_client.get_item.return_value = {}

        service.get_tier_config(UserTier.FREE)
        service.get_tier_config(UserTier.FREE)

        # Only one DynamoDB call (first cache miss)
        assert mock_client.get_item.call_count == 1

    def test_cache_returns_same_config(self, service, mock_client):
        """Cached result returns identical config."""
        mock_client.get_item.return_value = {}

        config1 = service.get_tier_config(UserTier.FREE)
        config2 = service.get_tier_config(UserTier.FREE)

        assert config1 == config2

    def test_cache_ttl_is_5_minutes(self):
        """Cache TTL constant is 300 seconds (5 minutes)."""
        assert _CACHE_TTL == 300

    def test_different_tiers_cached_separately(self, service, mock_client):
        """Different tier lookups each hit DynamoDB once."""
        mock_client.get_item.return_value = {}

        service.get_tier_config(UserTier.FREE)
        service.get_tier_config(UserTier.SUBSCRIBER)

        assert mock_client.get_item.call_count == 2

    def test_cache_expired_refetches(self, service, mock_client):
        """After cache TTL expires, DynamoDB is called again."""
        mock_client.get_item.return_value = {}

        service.get_tier_config(UserTier.FREE)

        # Expire the cache by manipulating the cached timestamp
        for tier_str in service._cache:
            config, _ = service._cache[tier_str]
            service._cache[tier_str] = (config, time.time() - _CACHE_TTL - 1)

        service.get_tier_config(UserTier.FREE)

        assert mock_client.get_item.call_count == 2

    def test_invalidate_cache_clears_specific_tier(self, service, mock_client):
        """invalidate_cache(tier) clears only that tier."""
        mock_client.get_item.return_value = {}

        service.get_tier_config(UserTier.FREE)
        service.get_tier_config(UserTier.SUBSCRIBER)

        service.invalidate_cache(UserTier.FREE)

        service.get_tier_config(UserTier.FREE)
        service.get_tier_config(UserTier.SUBSCRIBER)

        # FREE re-fetched (2 calls), SUBSCRIBER cached (1 call) = 3 total
        assert mock_client.get_item.call_count == 3

    def test_invalidate_cache_all(self, service, mock_client):
        """invalidate_cache() clears all tiers."""
        mock_client.get_item.return_value = {}

        service.get_tier_config(UserTier.FREE)
        service.get_tier_config(UserTier.SUBSCRIBER)
        service.invalidate_cache()
        service.get_tier_config(UserTier.FREE)
        service.get_tier_config(UserTier.SUBSCRIBER)

        assert mock_client.get_item.call_count == 4


# --------------------------------------------------------------------------- #
# T150: Config loaded from DynamoDB
# --------------------------------------------------------------------------- #


class TestLoadFromDynamoDB:
    """T150: Config loaded from DynamoDB overrides defaults."""

    def test_dynamo_config_overrides_defaults(self, service, mock_client):
        """Config from DynamoDB takes precedence over hardcoded defaults."""
        mock_client.get_item.return_value = {
            "Item": {
                "PK": {"S": "CONFIG"},
                "SK": {"S": "TIER#free"},
                "hourly_cap": {"N": "10"},
                "daily_cap": {"N": "50"},
                "monthly_cap": {"N": "500"},
            }
        }

        config = service.get_tier_config(UserTier.FREE)

        assert config["hourly_cap"] == 10
        assert config["daily_cap"] == 50
        assert config["monthly_cap"] == 500

    def test_dynamo_queries_correct_key(self, service, mock_client):
        """DynamoDB query uses PK=CONFIG, SK=TIER#{tier}."""
        mock_client.get_item.return_value = {}

        service.get_tier_config(UserTier.FREE)

        call_kwargs = mock_client.get_item.call_args[1]
        assert call_kwargs["Key"]["PK"]["S"] == "CONFIG"
        assert call_kwargs["Key"]["SK"]["S"] == "TIER#free"

    def test_dynamo_error_falls_back_to_defaults(self, service, mock_client):
        """DynamoDB error → falls back to hardcoded defaults."""
        mock_client.get_item.side_effect = _client_error("InternalServerError")

        config = service.get_tier_config(UserTier.FREE)

        # Should still return valid config (defaults)
        assert config["hourly_cap"] == 5
        assert config["daily_cap"] == 15
        assert config["monthly_cap"] == 100


# --------------------------------------------------------------------------- #
# T170: Tier config values match stored values
# --------------------------------------------------------------------------- #


class TestTierConfigValues:
    """T170: Stored config values are returned accurately."""

    def test_subscriber_config_from_dynamo(self, service, mock_client):
        """Subscriber config read from DynamoDB matches stored values."""
        mock_client.get_item.return_value = {
            "Item": {
                "PK": {"S": "CONFIG"},
                "SK": {"S": "TIER#subscriber"},
                "hourly_cap": {"N": "25"},
                "daily_cap": {"N": "250"},
                "monthly_cap": {"N": "2500"},
            }
        }

        config = service.get_tier_config(UserTier.SUBSCRIBER)

        assert config["tier"] == "subscriber"
        assert config["hourly_cap"] == 25
        assert config["daily_cap"] == 250
        assert config["monthly_cap"] == 2500


# --------------------------------------------------------------------------- #
# set_tier_config
# --------------------------------------------------------------------------- #


class TestSetTierConfig:
    """Writing tier config to DynamoDB."""

    def test_set_config_writes_to_dynamo(self, service, mock_client):
        """set_tier_config calls put_item on DynamoDB."""
        result = service.set_tier_config(UserTier.FREE, 10, 50, 500)

        assert result is True
        mock_client.put_item.assert_called_once()

    def test_set_config_writes_correct_values(self, service, mock_client):
        """Written values match the provided caps."""
        service.set_tier_config(UserTier.FREE, 10, 50, 500)

        call_kwargs = mock_client.put_item.call_args[1]
        item = call_kwargs["Item"]
        assert item["PK"]["S"] == "CONFIG"
        assert item["SK"]["S"] == "TIER#free"
        assert item["hourly_cap"]["N"] == "10"
        assert item["daily_cap"]["N"] == "50"
        assert item["monthly_cap"]["N"] == "500"

    def test_set_config_invalidates_cache(self, service, mock_client):
        """After set_tier_config, cache for that tier is cleared."""
        mock_client.get_item.return_value = {}

        service.get_tier_config(UserTier.FREE)
        service.set_tier_config(UserTier.FREE, 10, 50, 500)

        assert "free" not in service._cache

    def test_set_config_dynamo_error_raises(self, service, mock_client):
        """DynamoDB error propagates from set_tier_config."""
        mock_client.put_item.side_effect = _client_error("AccessDeniedException")

        with pytest.raises(ClientError):
            service.set_tier_config(UserTier.FREE, 10, 50, 500)

    def test_accepts_string_tier(self, service, mock_client):
        """set_tier_config accepts plain string tier."""
        result = service.set_tier_config("subscriber", 20, 200, 2000)

        assert result is True
        call_kwargs = mock_client.put_item.call_args[1]
        assert call_kwargs["Item"]["SK"]["S"] == "TIER#subscriber"


# --------------------------------------------------------------------------- #
# T180: Admin tier
# --------------------------------------------------------------------------- #


class TestAdminTier:
    """T180: Admin tier has correct default caps."""

    def test_admin_defaults_in_module(self):
        """Module-level default for admin is 50/500/10000."""
        admin_config = _DEFAULT_CONFIGS[UserTier.ADMIN]
        assert admin_config["hourly_cap"] == 50
        assert admin_config["daily_cap"] == 500
        assert admin_config["monthly_cap"] == 10000
