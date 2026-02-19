"""JWT creation and validation service.

Issue: #341 - Add JWT authentication to analysis endpoint with daily token cap.
Issue: #364 - Tiered rate limiting with multi-window caps.
"""

from __future__ import annotations

import logging
import os
import time
import uuid
from typing import TypedDict

import boto3
import jwt

logger = logging.getLogger(__name__)

# Cache for Secrets Manager client and secret value
_secrets_client = None
_cached_secret: str | None = None
_cached_secret_time: float = 0.0
_SECRET_CACHE_TTL = 300  # 5 minutes


class AuthResult(TypedDict):
    """Result of JWT validation."""

    success: bool
    user_id: str | None
    error: str | None
    reason: str | None
    claims: dict | None


def create_jwt(
    user_id: str,
    secret: str,
    expiry_hours: int = 24,
    tier: str = "free",
    billing_anchor_day: int = 1,
) -> str:
    """Create a signed JWT token for the given user.

    Args:
        user_id: The LinkedIn user ID to embed in the token.
        secret: The signing secret.
        expiry_hours: Token lifetime in hours (default 24).
        tier: User subscription tier (default "free").
        billing_anchor_day: Day of month for billing cycle (default 1).

    Returns:
        Encoded JWT string.
    """
    now = int(time.time())
    payload = {
        "user_id": user_id,
        "exp": now + (expiry_hours * 3600),
        "iat": now,
        "jti": str(uuid.uuid4()),
        "tier": tier,
        "billing_anchor_day": billing_anchor_day,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def validate_jwt(token: str, secret: str, leeway_seconds: int = 300) -> AuthResult:
    """Validate a JWT token and extract user_id.

    Supports leeway for clock skew on expiration checks.

    Args:
        token: The JWT string to validate.
        secret: The signing secret to verify against.
        leeway_seconds: Seconds of leeway for expiration (default 300).

    Returns:
        AuthResult with success status, user_id, and error details.
    """
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"require": ["exp", "iat", "jti", "user_id"]},
            leeway=leeway_seconds,
        )
        return AuthResult(
            success=True,
            user_id=payload["user_id"],
            error=None,
            reason=None,
            claims=payload,
        )
    except jwt.ExpiredSignatureError:
        return AuthResult(
            success=False,
            user_id=None,
            error="Token has expired",
            reason="token_expired",
            claims=None,
        )
    except jwt.InvalidSignatureError:
        return AuthResult(
            success=False,
            user_id=None,
            error="Invalid token signature",
            reason="invalid_signature",
            claims=None,
        )
    except jwt.DecodeError:
        return AuthResult(
            success=False,
            user_id=None,
            error="Malformed token",
            reason="malformed",
            claims=None,
        )
    except jwt.InvalidTokenError as e:
        return AuthResult(
            success=False,
            user_id=None,
            error=str(e),
            reason="invalid_token",
            claims=None,
        )


def get_jwt_secret() -> str:
    """Retrieve JWT signing secret from AWS Secrets Manager.

    Uses in-memory caching with a 5-minute TTL to minimize API calls.

    Returns:
        The JWT signing secret string.

    Raises:
        RuntimeError: If the secret cannot be retrieved.
    """
    global _secrets_client, _cached_secret, _cached_secret_time

    now = time.time()
    if _cached_secret is not None and (now - _cached_secret_time) < _SECRET_CACHE_TTL:
        return _cached_secret

    secret_name = os.environ.get("JWT_SECRET_NAME", "aletheia/jwt-signing-key")
    region = os.environ.get("AWS_REGION", "us-east-1")

    try:
        if _secrets_client is None:
            _secrets_client = boto3.client("secretsmanager", region_name=region)

        response = _secrets_client.get_secret_value(SecretId=secret_name)
        secret: str = response["SecretString"]
        _cached_secret = secret
        _cached_secret_time = now
        return secret
    except Exception as e:
        logger.error("Failed to retrieve JWT secret from Secrets Manager: %s", str(e))
        raise RuntimeError(f"Failed to retrieve JWT secret: {e}") from e


def validate_jwt_dual_secret(
    token: str,
    primary_secret: str,
    secondary_secret: str | None,
) -> AuthResult:
    """Validate JWT against primary secret, fall back to secondary during rotation.

    This supports zero-downtime secret rotation by trying the current secret
    first, then falling back to the previous secret if validation fails due
    to an invalid signature.

    Args:
        token: The JWT string to validate.
        primary_secret: The current signing secret.
        secondary_secret: The previous signing secret (None if not rotating).

    Returns:
        AuthResult with success status, user_id, and error details.
    """
    result = validate_jwt(token, primary_secret)

    if result["success"]:
        return result

    # Only fall back to secondary if the failure was a signature issue
    # and a secondary secret is available
    if secondary_secret is not None and result["reason"] == "invalid_signature":
        secondary_result = validate_jwt(token, secondary_secret)
        if secondary_result["success"]:
            logger.info(
                "JWT validated with secondary secret (rotation in progress)"
            )
            return secondary_result

    return result


def invalidate_secret_cache() -> None:
    """Invalidate the cached secret. Useful for testing and forced refresh."""
    global _cached_secret, _cached_secret_time
    _cached_secret = None
    _cached_secret_time = 0.0
