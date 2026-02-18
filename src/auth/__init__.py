"""Auth package for JWT authentication, daily token cap, and rate limiting.

Issue #341: Add JWT authentication to analysis endpoint with daily token cap.
Issue #364: Tiered rate limiting with multi-window caps.
"""

from .jwt_service import (
    create_jwt,
    validate_jwt,
    get_jwt_secret,
    validate_jwt_dual_secret,
)
from .token_cap_service import (
    check_and_increment_cap,
    get_current_cap,
    set_daily_cap,
    get_today_key,
    MultiWindowCounter,
)
from .auth_middleware import (
    require_auth,
    extract_token,
    log_auth_failure,
    extract_tier_from_jwt,
    check_rate_limit,
    build_rate_limit_error_response,
)
from .tier_config_service import TierConfigService
from .models import (
    UserTier,
    WindowType,
    TierConfig,
    CounterState,
    RateLimitResult,
    RateLimitErrorResponse,
    UserRecord,
)

__all__ = [
    "create_jwt",
    "validate_jwt",
    "get_jwt_secret",
    "validate_jwt_dual_secret",
    "check_and_increment_cap",
    "get_current_cap",
    "set_daily_cap",
    "get_today_key",
    "MultiWindowCounter",
    "require_auth",
    "extract_token",
    "log_auth_failure",
    "extract_tier_from_jwt",
    "check_rate_limit",
    "build_rate_limit_error_response",
    "TierConfigService",
    "UserTier",
    "WindowType",
    "TierConfig",
    "CounterState",
    "RateLimitResult",
    "RateLimitErrorResponse",
    "UserRecord",
]
