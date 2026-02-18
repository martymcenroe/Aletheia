"""Rate limiting data models.

Issue: #364 - Tiered rate limiting with multi-window caps.
"""

from __future__ import annotations

from enum import Enum
from typing import TypedDict


class UserTier(str, Enum):
    """User subscription tier for rate limiting."""

    FREE = "free"
    SUBSCRIBER = "subscriber"
    ADMIN = "admin"


class WindowType(str, Enum):
    """Rate limit time window."""

    HOURLY = "hourly"
    DAILY = "daily"
    MONTHLY = "monthly"


class TierConfig(TypedDict):
    """Rate limit configuration for a user tier."""

    tier: str
    hourly_cap: int
    daily_cap: int
    monthly_cap: int


class CounterState(TypedDict):
    """Current counter state for a user across all windows."""

    user_id: str
    hourly_count: int
    hourly_window: str
    daily_count: int
    daily_window: str
    monthly_count: int
    monthly_window: str


class RateLimitResult(TypedDict):
    """Result of a rate limit check."""

    allowed: bool
    exceeded_window: str | None
    resets_at: str | None
    resets_in_seconds: int | None
    current_counts: dict[str, int]


class RateLimitErrorResponse(TypedDict):
    """Error response body for 429 Too Many Requests."""

    error: str
    window: str
    resets_at: str
    resets_in_seconds: int
    upgrade_url: str
