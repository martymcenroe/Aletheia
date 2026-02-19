"""JWT validation middleware for analysis endpoint.

Issue: #341 - Add JWT authentication to analysis endpoint with daily token cap.
Issue: #364 - Tiered rate limiting with multi-window caps.

Provides a decorator-based middleware for clean separation of auth concerns.
Fail mode: Fail Closed for auth, hybrid for rate limiting.
"""

from __future__ import annotations

import functools
import json
import logging
import os
import re
from typing import Any, Callable

from .jwt_service import (
    AuthResult,
    get_jwt_secret,
    validate_jwt,
    validate_jwt_dual_secret,
)
from .models.rate_limit import RateLimitResult, UserTier
from .tier_config_service import TierConfigService
from .token_cap_service import MultiWindowCounter

logger = logging.getLogger(__name__)

# Bearer token regex: "Bearer " followed by a non-empty token
_BEARER_RE = re.compile(r"^Bearer\s+(\S+)$")

# Environment variable for optional secondary secret (rotation support)
_SECONDARY_SECRET_ENV = "JWT_SECONDARY_SECRET"


def extract_token(event: dict) -> str | None:
    """Extract Bearer token from Authorization header.

    Supports both direct Lambda invocation (headers in event root)
    and API Gateway / Function URL format (headers in event["headers"]).

    Args:
        event: Lambda event dict.

    Returns:
        The JWT token string, or None if not found or invalid format.
    """
    headers = event.get("headers", {})
    if not isinstance(headers, dict):
        return None

    # API Gateway and Function URL normalize headers to lowercase
    auth_header = headers.get("authorization") or headers.get("Authorization")
    if not auth_header:
        return None

    match = _BEARER_RE.match(auth_header)
    if not match:
        return None

    return match.group(1)


def log_auth_failure(user_id: str | None, reason: str, event: dict) -> None:
    """Log authentication failure with structured data.

    Logs contain action: "auth_failed" and reason field per REQ-9.
    User IDs are sanitized before logging to prevent log injection.

    Args:
        user_id: The user ID if available (may be None).
        reason: Detailed reason code for the failure.
        event: The original Lambda event (for request metadata).
    """
    # Sanitize user_id to prevent log injection (REQ-9 / Security §7.1)
    safe_user_id: str | None = None
    if user_id is not None:
        # Strip control characters and limit length
        safe_user_id = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", str(user_id))[:128]

    # Extract request metadata for debugging (no PII)
    request_context = event.get("requestContext", {})
    source_ip = request_context.get("http", {}).get("sourceIp", "unknown")

    log_entry = {
        "action": "auth_failed",
        "reason": reason,
        "user_id": safe_user_id,
        "source_ip": source_ip,
        "path": request_context.get("http", {}).get("path", "unknown"),
    }

    logger.warning(json.dumps(log_entry))


def _build_401_response(error_message: str) -> dict[str, Any]:
    """Build a 401 Unauthorized response.

    Args:
        error_message: Human-readable error message.

    Returns:
        Lambda response dict with 401 status.
    """
    return {
        "statusCode": 401,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": error_message}),
    }


# --------------------------------------------------------------------------- #
# Rate limiting (Issue #364)
# --------------------------------------------------------------------------- #

# Module-level singletons for rate limiting services
_tier_config_service: TierConfigService | None = None
_multi_window_counter: MultiWindowCounter | None = None

# Upgrade URL for rate limit error responses
_UPGRADE_URL = "https://aletheia.study/upgrade"


def _get_tier_config_service() -> TierConfigService:
    """Get or create the TierConfigService singleton."""
    global _tier_config_service
    if _tier_config_service is None:
        _tier_config_service = TierConfigService()
    return _tier_config_service


def _get_multi_window_counter() -> MultiWindowCounter:
    """Get or create the MultiWindowCounter singleton."""
    global _multi_window_counter
    if _multi_window_counter is None:
        _multi_window_counter = MultiWindowCounter()
    return _multi_window_counter


def extract_tier_from_jwt(claims: dict) -> UserTier:
    """Extract and validate user tier from JWT claims.

    Args:
        claims: Decoded JWT payload.

    Returns:
        UserTier enum value, defaults to FREE if missing or invalid.
    """
    tier_str = claims.get("tier", "free")
    try:
        return UserTier(tier_str)
    except ValueError:
        return UserTier.FREE


def check_rate_limit(
    user_id: str, tier: UserTier, billing_anchor_day: int = 1
) -> tuple[bool, dict | None]:
    """Check rate limits for a user request.

    Args:
        user_id: The user's unique identifier.
        tier: The user's subscription tier.
        billing_anchor_day: Day of month for billing cycle.

    Returns:
        Tuple of (allowed, error_response_dict_or_None).
    """
    config_service = _get_tier_config_service()
    counter = _get_multi_window_counter()

    tier_config = config_service.get_tier_config(tier)
    result = counter.check_and_increment(user_id, tier_config, billing_anchor_day)

    if result["allowed"]:
        return True, None

    error_body = build_rate_limit_error_response(result)
    return False, error_body


def build_rate_limit_error_response(result: RateLimitResult) -> dict:
    """Build error response body for a rate limit violation.

    Args:
        result: The RateLimitResult from the counter check.

    Returns:
        Dict suitable for JSON serialization in a 429 response body.
    """
    if result.get("exceeded_window") == "SERVICE_UNAVAILABLE":
        return {
            "error": "Service temporarily unavailable, please retry",
        }

    return {
        "error": "rate_limit_exceeded",
        "window": result.get("exceeded_window", "unknown"),
        "resets_at": result.get("resets_at", ""),
        "resets_in_seconds": result.get("resets_in_seconds", 0),
        "upgrade_url": _UPGRADE_URL,
    }


def _build_429_response(error_body: dict) -> dict[str, Any]:
    """Build a 429 Too Many Requests response.

    Args:
        error_body: Error details dict.

    Returns:
        Lambda response dict with 429 status.
    """
    status = 503 if error_body.get("error") == "Service temporarily unavailable, please retry" else 429
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(error_body),
    }


def require_auth(handler: Callable) -> Callable:
    """Decorator to require valid JWT authentication.

    Wraps a Lambda handler to validate the JWT in the Authorization
    header before calling the handler. On success, injects ``user_id``
    into the event dict so downstream logic can use it.

    The validation flow (per LLD §2.5 "Analysis Lambda - JWT Validation"):
    1. Extract Authorization header
    2. Verify Bearer format
    3. Validate JWT signature (with dual-secret rotation support)
    4. Check expiration (with 5-minute leeway)
    5. Extract user_id and inject into event
    6. Call the wrapped handler

    Fail mode: Fail Closed. If Secrets Manager is unavailable, auth
    is denied to prevent unauthorized access.

    Args:
        handler: The Lambda handler function to wrap.
            Expected signature: handler(event, context, **kwargs) -> dict

    Returns:
        Wrapped handler that validates JWT before execution.
    """

    @functools.wraps(handler)
    def wrapper(event: dict, context: Any, **kwargs: Any) -> dict[str, Any]:
        # Step 1: Extract token from Authorization header
        token = extract_token(event)

        if token is None:
            # Determine specific reason for logging
            headers = event.get("headers", {})
            if not isinstance(headers, dict):
                reason = "missing_header"
            else:
                auth_header = headers.get("authorization") or headers.get(
                    "Authorization"
                )
                if not auth_header:
                    reason = "missing_header"
                else:
                    reason = "invalid_format"

            log_auth_failure(None, reason, event)
            return _build_401_response("Unauthorized")

        # Step 2: Retrieve JWT secret (fail closed if unavailable)
        try:
            primary_secret = get_jwt_secret()
        except RuntimeError:
            log_auth_failure(None, "secret_unavailable", event)
            return _build_401_response("Unauthorized")

        # Step 3: Validate JWT (with optional dual-secret rotation)
        secondary_secret = os.environ.get(_SECONDARY_SECRET_ENV)

        if secondary_secret:
            auth_result: AuthResult = validate_jwt_dual_secret(
                token, primary_secret, secondary_secret
            )
        else:
            auth_result = validate_jwt(token, primary_secret)

        # Step 4: Handle validation failure
        if not auth_result["success"]:
            reason = auth_result["reason"] or "unknown"
            log_auth_failure(auth_result.get("user_id"), reason, event)
            return _build_401_response("Unauthorized")

        # Step 5: Check rate limits (Issue #364)
        claims = auth_result.get("claims") or {}
        tier = extract_tier_from_jwt(claims)
        billing_anchor_day = claims.get("billing_anchor_day", 1)

        user_id = str(auth_result["user_id"])  # guaranteed non-None after auth success
        allowed, error_response = check_rate_limit(
            user_id, tier, billing_anchor_day
        )
        if not allowed and error_response is not None:
            return _build_429_response(error_response)

        # Step 6: Inject user_id into event for downstream use
        event["auth_user_id"] = auth_result["user_id"]

        # Step 7: Proceed to the wrapped handler
        return handler(event, context, **kwargs)

    return wrapper
