"""Auth package for JWT authentication and daily token cap.

Issue #341: Add JWT authentication to analysis endpoint with daily token cap.
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
)
from .auth_middleware import (
    require_auth,
    extract_token,
    log_auth_failure,
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
    "require_auth",
    "extract_token",
    "log_auth_failure",
]
