"""Auth data models.

Issue: #364 - Tiered rate limiting with multi-window caps.
"""

from .rate_limit import (
    CounterState,
    RateLimitErrorResponse,
    RateLimitResult,
    TierConfig,
    UserTier,
    WindowType,
)
from .user import UserRecord

__all__ = [
    "CounterState",
    "RateLimitErrorResponse",
    "RateLimitResult",
    "TierConfig",
    "UserRecord",
    "UserTier",
    "WindowType",
]
