"""Tier configuration service for rate limiting.

Issue: #364 - Tiered rate limiting with multi-window caps.

Manages per-tier rate limit caps (hourly/daily/monthly) with
in-memory caching and DynamoDB persistence.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import boto3
from botocore.exceptions import ClientError

from .models.rate_limit import TierConfig, UserTier

logger = logging.getLogger(__name__)

# Cache TTL in seconds
_CACHE_TTL = 300  # 5 minutes

# Default tier configurations (hardcoded fallbacks)
_DEFAULT_CONFIGS: dict[str, TierConfig] = {
    UserTier.FREE: TierConfig(tier="free", hourly_cap=5, daily_cap=15, monthly_cap=100),
    UserTier.SUBSCRIBER: TierConfig(tier="subscriber", hourly_cap=20, daily_cap=200, monthly_cap=2000),
    UserTier.ADMIN: TierConfig(tier="admin", hourly_cap=50, daily_cap=500, monthly_cap=10000),
}


class TierConfigService:
    """Service for managing tier rate limit configurations.

    Uses an in-memory cache with 5-minute TTL. Falls back to
    hardcoded defaults if DynamoDB is unavailable.
    """

    def __init__(
        self,
        table_name: str | None = None,
        dynamodb_client: Any = None,
    ) -> None:
        self._table_name = table_name or os.environ.get(
            "TOKEN_CAP_TABLE", "aletheia-token-cap"
        )
        self._client = dynamodb_client
        self._cache: dict[str, tuple[TierConfig, float]] = {}

    def _get_client(self) -> Any:
        """Lazy-initialize DynamoDB client."""
        if self._client is None:
            region = os.environ.get("AWS_REGION", "us-east-1")
            endpoint_url = os.environ.get("DYNAMODB_ENDPOINT")
            kwargs: dict[str, Any] = {"region_name": region}
            if endpoint_url:
                kwargs["endpoint_url"] = endpoint_url
            self._client = boto3.client("dynamodb", **kwargs)
        return self._client

    def get_tier_config(self, tier: UserTier | str) -> TierConfig:
        """Get rate limit configuration for a tier.

        Checks in-memory cache first (5-min TTL), then DynamoDB,
        then falls back to hardcoded defaults.

        Args:
            tier: The user tier to look up.

        Returns:
            TierConfig with hourly/daily/monthly caps.
        """
        tier_str = tier.value if isinstance(tier, UserTier) else tier

        # Check cache
        cached = self._cache.get(tier_str)
        if cached is not None:
            config, cached_at = cached
            if time.time() - cached_at < _CACHE_TTL:
                return config

        # Try DynamoDB
        db_config = self._load_from_dynamodb(tier_str)
        if db_config is not None:
            self._cache[tier_str] = (db_config, time.time())
            return db_config

        # Fall back to hardcoded defaults
        default = self._get_default_config(tier_str)
        self._cache[tier_str] = (default, time.time())
        return default

    def _get_default_config(self, tier: str) -> TierConfig:
        """Get hardcoded default configuration for a tier.

        Args:
            tier: The tier string value.

        Returns:
            Default TierConfig for the tier.
        """
        return _DEFAULT_CONFIGS.get(tier, _DEFAULT_CONFIGS[UserTier.FREE])

    def _load_from_dynamodb(self, tier: str) -> TierConfig | None:
        """Load tier configuration from DynamoDB.

        Args:
            tier: The tier string value.

        Returns:
            TierConfig if found in DynamoDB, None otherwise.
        """
        try:
            client = self._get_client()
            response = client.get_item(
                TableName=self._table_name,
                Key={
                    "PK": {"S": "CONFIG"},
                    "SK": {"S": f"TIER#{tier}"},
                },
            )

            item = response.get("Item")
            if not item:
                return None

            return TierConfig(
                tier=tier,
                hourly_cap=int(item["hourly_cap"]["N"]),
                daily_cap=int(item["daily_cap"]["N"]),
                monthly_cap=int(item["monthly_cap"]["N"]),
            )

        except (ClientError, KeyError, ValueError) as e:
            logger.warning("Failed to load tier config from DynamoDB: %s", str(e))
            return None

    def set_tier_config(
        self,
        tier: UserTier | str,
        hourly_cap: int,
        daily_cap: int,
        monthly_cap: int,
    ) -> bool:
        """Write tier configuration to DynamoDB.

        Args:
            tier: The user tier.
            hourly_cap: Hourly request cap.
            daily_cap: Daily request cap.
            monthly_cap: Monthly request cap.

        Returns:
            True if the config was saved successfully.
        """
        tier_str = tier.value if isinstance(tier, UserTier) else tier

        try:
            client = self._get_client()
            client.put_item(
                TableName=self._table_name,
                Item={
                    "PK": {"S": "CONFIG"},
                    "SK": {"S": f"TIER#{tier_str}"},
                    "tier": {"S": tier_str},
                    "hourly_cap": {"N": str(hourly_cap)},
                    "daily_cap": {"N": str(daily_cap)},
                    "monthly_cap": {"N": str(monthly_cap)},
                },
            )

            # Invalidate cache for this tier
            self._cache.pop(tier_str, None)

            logger.info(
                "Tier config updated: tier=%s, hourly=%d, daily=%d, monthly=%d",
                tier_str, hourly_cap, daily_cap, monthly_cap,
            )
            return True

        except ClientError as e:
            logger.error("Failed to save tier config: %s", str(e))
            raise

    def invalidate_cache(self, tier: UserTier | str | None = None) -> None:
        """Clear cached tier configurations.

        Args:
            tier: Specific tier to invalidate, or None for all.
        """
        if tier is None:
            self._cache.clear()
        else:
            tier_str = tier.value if isinstance(tier, UserTier) else tier
            self._cache.pop(tier_str, None)
