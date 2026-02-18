"""Secure token storage and refresh logic for LinkedIn OAuth.

Provides functions to store, retrieve, validate, refresh, and clear
LinkedIn OAuth tokens. Tokens are persisted to an encrypted JSON file
at ``~/.config/assemblyzero/tokens.json`` (outside the worktree) with
restrictive file permissions (0600).

Encryption uses Fernet symmetric encryption from the ``cryptography``
library. The encryption key is derived from a machine-specific seed
stored alongside the token file.

Issue: #116
"""

from __future__ import annotations

import json
import logging
import os
import platform
import stat
import time
from pathlib import Path
from typing import Optional

import httpx
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

import base64

from .types import AuthError, LinkedInTokens

logger = logging.getLogger(__name__)

# LinkedIn OAuth 2.0 token refresh endpoint
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

# Refresh buffer: refresh if token expires within this many seconds (24 hours)
REFRESH_BUFFER_SECONDS = 24 * 60 * 60

# HTTP timeout for refresh requests (seconds)
HTTP_TIMEOUT = 10

# Salt for key derivation (fixed per installation; not secret, just uniqueness)
_KDF_SALT = b"assemblyzero-token-storage-v1"

# PBKDF2 iterations for key derivation
_KDF_ITERATIONS = 480_000


def get_default_storage_path() -> Path:
    """Return the default token storage path outside the worktree.

    The path is ``~/.config/assemblyzero/tokens.json`` on Unix-like
    systems and ``%USERPROFILE%/.config/assemblyzero/tokens.json`` on
    Windows. This ensures tokens are never accidentally committed to git.

    Returns:
        A :class:`Path` pointing to the default token file location.
    """
    home = Path.home()
    return home / ".config" / "assemblyzero" / "tokens.json"


def _get_key_path(storage_path: Path) -> Path:
    """Return the path to the encryption key seed file.

    The key seed file lives alongside the token file with a ``.key`` suffix.

    Args:
        storage_path: Path to the token storage file.

    Returns:
        Path to the key seed file.
    """
    return storage_path.with_suffix(".key")


def _get_or_create_key(storage_path: Path) -> bytes:
    """Get or create the Fernet encryption key for token storage.

    If a key seed file exists alongside the storage path, it is read and
    used to derive the encryption key. Otherwise, a new random seed is
    generated and persisted.

    The seed is run through PBKDF2-HMAC-SHA256 to produce a
    URL-safe base64-encoded Fernet key.

    Args:
        storage_path: Path to the token storage file (key file is derived
            from this path).

    Returns:
        A Fernet-compatible encryption key (URL-safe base64, 32 bytes).
    """
    key_path = _get_key_path(storage_path)

    if key_path.exists():
        seed = key_path.read_bytes()
    else:
        # Generate a new random seed
        seed = os.urandom(32)
        key_path.parent.mkdir(parents=True, exist_ok=True)
        key_path.write_bytes(seed)
        # Set restrictive permissions on key file (owner-only)
        _set_file_permissions(key_path)

    # Derive Fernet key from seed using PBKDF2
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_KDF_SALT,
        iterations=_KDF_ITERATIONS,
    )
    derived_key = kdf.derive(seed)
    return base64.urlsafe_b64encode(derived_key)


def _set_file_permissions(file_path: Path) -> None:
    """Set restrictive file permissions (owner read/write only).

    On Unix-like systems, sets permissions to 0600. On Windows, this is
    a best-effort operation that relies on default user-only ACLs.

    Args:
        file_path: Path to the file whose permissions should be restricted.
    """
    if platform.system() != "Windows":
        try:
            file_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
        except OSError as e:
            logger.warning("Could not set file permissions on %s: %s", file_path, e)


def _encrypt_data(data: dict, storage_path: Path) -> bytes:
    """Encrypt a dictionary as JSON using Fernet symmetric encryption.

    Args:
        data: The dictionary to encrypt.
        storage_path: Path to the token file (used to locate the key).

    Returns:
        Encrypted bytes (Fernet token).
    """
    key = _get_or_create_key(storage_path)
    fernet = Fernet(key)
    json_bytes = json.dumps(data).encode("utf-8")
    return fernet.encrypt(json_bytes)


def _decrypt_data(encrypted: bytes, storage_path: Path) -> dict:
    """Decrypt Fernet-encrypted bytes back to a dictionary.

    Args:
        encrypted: The encrypted bytes (Fernet token).
        storage_path: Path to the token file (used to locate the key).

    Returns:
        The decrypted dictionary.

    Raises:
        InvalidToken: If decryption fails (wrong key, corrupted data).
        json.JSONDecodeError: If decrypted content is not valid JSON.
    """
    key = _get_or_create_key(storage_path)
    fernet = Fernet(key)
    decrypted_bytes = fernet.decrypt(encrypted)
    return json.loads(decrypted_bytes.decode("utf-8"))


def store_tokens(tokens: LinkedInTokens, storage_path: Optional[Path] = None) -> None:
    """Securely store LinkedIn OAuth tokens to an encrypted file.

    Creates the parent directories if they don't exist and sets
    restrictive file permissions (0600) on the token file.

    Args:
        tokens: The :class:`LinkedInTokens` dict to persist, containing
            ``access_token``, ``expires_at``, and optionally ``refresh_token``.
        storage_path: Path to the storage file. Defaults to
            :func:`get_default_storage_path` if not specified.

    Raises:
        OSError: If the file cannot be written (permissions, disk full, etc.).
    """
    if storage_path is None:
        storage_path = get_default_storage_path()

    # Ensure parent directory exists
    storage_path.parent.mkdir(parents=True, exist_ok=True)

    # Encrypt and write
    encrypted = _encrypt_data(dict(tokens), storage_path)
    storage_path.write_bytes(encrypted)

    # Set restrictive permissions
    _set_file_permissions(storage_path)

    logger.info("Tokens stored securely at %s", storage_path)


def get_stored_tokens(storage_path: Optional[Path] = None) -> Optional[LinkedInTokens]:
    """Retrieve stored LinkedIn OAuth tokens from the encrypted file.

    If the file doesn't exist, or if decryption/parsing fails (corrupted
    data), returns ``None`` and logs a warning. This implements the
    fail-closed recovery strategy: corrupted storage results in an
    unauthenticated state rather than a crash.

    Args:
        storage_path: Path to the storage file. Defaults to
            :func:`get_default_storage_path` if not specified.

    Returns:
        A :class:`LinkedInTokens` dict if tokens are found and valid,
        or ``None`` if no tokens exist or the file is corrupted.
    """
    if storage_path is None:
        storage_path = get_default_storage_path()

    if not storage_path.exists():
        logger.debug("No token file found at %s", storage_path)
        return None

    try:
        encrypted = storage_path.read_bytes()
        data = _decrypt_data(encrypted, storage_path)
    except (InvalidToken, json.JSONDecodeError, ValueError, OSError) as e:
        logger.warning(
            "Failed to read/decrypt token file at %s: %s. Treating as logged out.",
            storage_path,
            e,
        )
        return None

    # Validate required fields
    if "access_token" not in data or "expires_at" not in data:
        logger.warning("Token file missing required fields. Treating as logged out.")
        return None

    tokens: LinkedInTokens = {
        "access_token": data["access_token"],
        "expires_at": int(data["expires_at"]),
        "refresh_token": data.get("refresh_token"),
    }

    return tokens


def clear_tokens(storage_path: Optional[Path] = None) -> None:
    """Remove all stored tokens (logout).

    Deletes both the encrypted token file and its associated encryption
    key seed file. If either file doesn't exist, the operation is a no-op
    for that file.

    Args:
        storage_path: Path to the storage file. Defaults to
            :func:`get_default_storage_path` if not specified.
    """
    if storage_path is None:
        storage_path = get_default_storage_path()

    # Remove token file
    if storage_path.exists():
        storage_path.unlink()
        logger.info("Token file removed: %s", storage_path)

    # Remove key file
    key_path = _get_key_path(storage_path)
    if key_path.exists():
        key_path.unlink()
        logger.info("Key file removed: %s", key_path)


def is_token_valid(tokens: LinkedInTokens) -> bool:
    """Check whether a LinkedIn token has not yet expired.

    Args:
        tokens: The :class:`LinkedInTokens` dict to check.

    Returns:
        ``True`` if the token's ``expires_at`` timestamp is in the future,
        ``False`` otherwise.
    """
    return tokens["expires_at"] > int(time.time())


def refresh_token_if_needed(tokens: LinkedInTokens) -> LinkedInTokens:
    """Refresh LinkedIn tokens if they are near expiration.

    If the token expires within 24 hours (``REFRESH_BUFFER_SECONDS``),
    attempts to refresh it using the stored refresh token. If no refresh
    token is available or the refresh fails, returns the original tokens
    unchanged (the caller should handle re-authentication).

    LinkedIn's refresh token flow sends a POST to the token endpoint with
    ``grant_type=refresh_token``.

    Args:
        tokens: The current :class:`LinkedInTokens` dict.

    Returns:
        Refreshed :class:`LinkedInTokens` if refresh was needed and
        successful, or the original tokens if refresh was not needed
        or failed.

    Raises:
        AuthError: With code ``TOKEN_EXPIRED`` if the token is already
            expired and no refresh token is available.
    """
    now = int(time.time())
    expires_at = tokens["expires_at"]

    # Token is not near expiration — no refresh needed
    if expires_at - now > REFRESH_BUFFER_SECONDS:
        return tokens

    # Token is expired and no refresh token available
    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        if expires_at <= now:
            raise AuthError(
                code="TOKEN_EXPIRED",
                message="Access token has expired and no refresh token is available. Please log in again.",
                recoverable=True,
            )
        # Near expiration but no refresh token; return as-is
        logger.warning(
            "Token expires within 24 hours but no refresh token available. "
            "User will need to re-authenticate when token expires."
        )
        return tokens

    # Attempt to refresh the token
    client_id = os.environ.get("LINKEDIN_CLIENT_ID", "")
    client_secret = os.environ.get("LINKEDIN_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        logger.warning(
            "Cannot refresh token: LinkedIn OAuth credentials not configured. "
            "User will need to re-authenticate."
        )
        return tokens

    try:
        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            response = client.post(
                LINKEDIN_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
    except httpx.HTTPError as e:
        logger.error("Network error during token refresh: %s", e)
        # Return original tokens; caller can decide on re-auth
        return tokens

    if response.status_code != 200:
        logger.error(
            "Token refresh failed: %d - %s",
            response.status_code,
            response.text,
        )
        # Return original tokens; caller can decide on re-auth
        return tokens

    data = response.json()

    new_expires_in = data.get("expires_in", 5184000)  # Default 60 days
    new_expires_at = now + new_expires_in

    refreshed_tokens: LinkedInTokens = {
        "access_token": data["access_token"],
        "expires_at": new_expires_at,
        "refresh_token": data.get("refresh_token", refresh_token),
    }

    logger.info("Token refreshed successfully. New expiry: %d", new_expires_at)
    return refreshed_tokens
