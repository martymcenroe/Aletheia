"""Aletheia-issued refresh tokens for silent, indefinite session renewal.

Issue: #811 - LinkedIn's 'openid profile' scopes never return a refresh token,
and /auth/refresh could not mint a JWT, so a signed-in user was locked out
24 hours after login with a full re-login as the only recovery.

Design notes:

- The refresh token is opaque and high-entropy. Only its SHA-256 hash is
  persisted, so a read of the table yields nothing usable.
- Unlike a JWT, this credential is stateful and therefore revocable: the
  ``revoked`` flag is authoritative and checked on every use.
- DynamoDB TTL deletion is best-effort and can lag by up to 48 hours, so
  expiry is ALSO enforced in code. The ``ttl`` attribute is a storage
  cleanup mechanism, never the security boundary.
"""

from __future__ import annotations

import hashlib
import logging
import os
import secrets
import time
from typing import Any

import boto3

logger = logging.getLogger(__name__)

REFRESH_TOKENS_TABLE = os.environ.get(
    "REFRESH_TOKENS_TABLE", "aletheia-refresh-tokens"
)
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# One year. Long-lived by design: the operator should never be asked to
# re-authenticate during normal use. Revocation, not expiry, is the control.
REFRESH_TOKEN_TTL_DAYS = int(os.environ.get("REFRESH_TOKEN_TTL_DAYS", "365"))

# 32 bytes of entropy, urlsafe-encoded (~43 chars).
_TOKEN_BYTES = 32

_dynamodb_client = None


def _get_dynamodb_client() -> Any:
    global _dynamodb_client
    if _dynamodb_client is None:
        endpoint = os.environ.get("DYNAMODB_ENDPOINT")
        if endpoint:
            _dynamodb_client = boto3.client(
                "dynamodb", endpoint_url=endpoint, region_name=AWS_REGION
            )
        else:
            _dynamodb_client = boto3.client("dynamodb", region_name=AWS_REGION)
    return _dynamodb_client


def generate_refresh_token() -> str:
    """Generate a new opaque refresh token.

    Returns:
        A urlsafe token string. This is the only time the plaintext exists
        server-side; only its hash is stored.
    """
    return secrets.token_urlsafe(_TOKEN_BYTES)


def hash_token(token: str) -> str:
    """Hash a refresh token for storage and lookup.

    SHA-256 is appropriate here (unlike for passwords): the token already
    carries 256 bits of entropy, so there is nothing to brute-force and no
    need for a slow KDF.

    Args:
        token: The plaintext refresh token.

    Returns:
        Lowercase hex SHA-256 digest.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def store_refresh_token(
    user_id: str,
    token: str,
    client: Any = None,
    ttl_days: int = REFRESH_TOKEN_TTL_DAYS,
) -> None:
    """Persist the hash of a newly issued refresh token.

    Args:
        user_id: The user this token authenticates.
        token: The plaintext refresh token (hashed before storage).
        client: Optional DynamoDB client (injected for tests).
        ttl_days: Token lifetime in days.
    """
    client = client or _get_dynamodb_client()
    now = int(time.time())
    expires_at = now + (ttl_days * 86400)

    client.put_item(
        TableName=REFRESH_TOKENS_TABLE,
        Item={
            "token_hash": {"S": hash_token(token)},
            "user_id": {"S": user_id},
            "created_at": {"N": str(now)},
            "last_used_at": {"N": str(now)},
            "revoked": {"BOOL": False},
            "ttl": {"N": str(expires_at)},
        },
    )


def validate_refresh_token(token: str, client: Any = None) -> str | None:
    """Validate a refresh token and return the user it belongs to.

    The stored ``user_id`` is authoritative and is the value returned. A
    client-supplied user identifier is never trusted or consulted, which is
    what prevents a valid token from minting a JWT for a different user.

    Args:
        token: The plaintext refresh token presented by the client.
        client: Optional DynamoDB client (injected for tests).

    Returns:
        The owning ``user_id``, or None if the token is unknown, revoked,
        or expired.
    """
    if not token or not isinstance(token, str):
        return None

    client = client or _get_dynamodb_client()

    try:
        response = client.get_item(
            TableName=REFRESH_TOKENS_TABLE,
            Key={"token_hash": {"S": hash_token(token)}},
        )
    except Exception as e:
        # Never log token material or exception text (project rule).
        logger.error("REFRESH_TOKEN_LOOKUP_ERROR: %s", e.__class__.__name__)
        return None

    item = response.get("Item")
    if not item:
        return None

    if item.get("revoked", {}).get("BOOL", False):
        logger.warning('{"action": "refresh_token_rejected", "reason": "revoked"}')
        return None

    # Enforced in code: DynamoDB TTL deletion lags and must not be the gate.
    expires_at = int(item.get("ttl", {}).get("N", "0"))
    if expires_at and time.time() >= expires_at:
        logger.warning('{"action": "refresh_token_rejected", "reason": "expired"}')
        return None

    user_id = item.get("user_id", {}).get("S")
    if not user_id:
        return None

    _touch_last_used(client, hash_token(token))
    return user_id


def _touch_last_used(client: Any, token_hash: str) -> None:
    """Record last use. Best-effort: a failure here must not deny a valid refresh."""
    try:
        client.update_item(
            TableName=REFRESH_TOKENS_TABLE,
            Key={"token_hash": {"S": token_hash}},
            UpdateExpression="SET last_used_at = :now",
            ExpressionAttributeValues={":now": {"N": str(int(time.time()))}},
        )
    except Exception as e:
        logger.warning("REFRESH_TOKEN_TOUCH_FAILED: %s", e.__class__.__name__)


def revoke_refresh_token(token: str, client: Any = None) -> bool:
    """Revoke a refresh token, ending the session it backs.

    Args:
        token: The plaintext refresh token to revoke.
        client: Optional DynamoDB client (injected for tests).

    Returns:
        True if the revocation was recorded.
    """
    client = client or _get_dynamodb_client()
    try:
        client.update_item(
            TableName=REFRESH_TOKENS_TABLE,
            Key={"token_hash": {"S": hash_token(token)}},
            UpdateExpression="SET revoked = :true",
            ExpressionAttributeValues={":true": {"BOOL": True}},
        )
        return True
    except Exception as e:
        logger.error("REFRESH_TOKEN_REVOKE_ERROR: %s", e.__class__.__name__)
        return False
