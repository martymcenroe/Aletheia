"""JWT validation middleware for analysis endpoint.

Issue: #341 - Add JWT authentication to analysis endpoint with daily token cap.

Provides a decorator-based middleware for clean separation of auth concerns.
Fail mode: Fail Closed - deny authentication if any component is unavailable.
"""

from __future__ import annotations

import functools
import json
import logging
import os
import re
from typing import Any, Callable

from auth.jwt_service import (
    AuthResult,
    get_jwt_secret,
    validate_jwt,
    validate_jwt_dual_secret,
)

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

        # Step 5: Inject user_id into event for downstream use
        event["auth_user_id"] = auth_result["user_id"]

        # Step 6: Proceed to the wrapped handler
        return handler(event, context, **kwargs)

    return wrapper
