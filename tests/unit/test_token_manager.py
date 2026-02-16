"""Unit tests for token management.

Tests for secure token storage, retrieval, encryption, expiration checking,
refresh logic, and logout/clear functionality. All file storage tests use
the ``tmp_path`` pytest fixture for isolation (no writes to ~/.config).

Issue: #116
"""

from __future__ import annotations

import json
import platform
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

from auth.token_manager import (
    LINKEDIN_TOKEN_URL,
    REFRESH_BUFFER_SECONDS,
    _decrypt_data,
    _encrypt_data,
    _get_key_path,
    _get_or_create_key,
    _set_file_permissions,
    clear_tokens,
    get_default_storage_path,
    get_stored_tokens,
    is_token_valid,
    refresh_token_if_needed,
    store_tokens,
)
from auth.types import LinkedInTokens


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def valid_tokens() -> LinkedInTokens:
    """Return a valid (non-expired) token set."""
    return LinkedInTokens(
        access_token="valid-access-token-abc123",
        expires_at=int(time.time()) + 86400 * 30,  # 30 days from now
        refresh_token="valid-refresh-token-xyz789",
    )


@pytest.fixture()
def expired_tokens() -> LinkedInTokens:
    """Return an expired token set (expired 1 hour ago)."""
    return LinkedInTokens(
        access_token="expired-access-token",
        expires_at=int(time.time()) - 3600,
        refresh_token="refresh-for-expired",
    )


@pytest.fixture()
def near_expiry_tokens() -> LinkedInTokens:
    """Return tokens that expire within 1 hour (inside 24h refresh buffer)."""
    return LinkedInTokens(
        access_token="near-expiry-token",
        expires_at=int(time.time()) + 3600,  # 1 hour from now
        refresh_token="refresh-for-near-expiry",
    )


@pytest.fixture()
def oauth_env(monkeypatch):
    """Set required LinkedIn OAuth environment variables."""
    monkeypatch.setenv("LINKEDIN_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("LINKEDIN_CLIENT_SECRET", "test-client-secret")


# ---------------------------------------------------------------------------
# T055 / Scenario 055 — Default storage path is outside worktree
# ---------------------------------------------------------------------------


class TestDefaultStoragePath:
    """Tests for get_default_storage_path()."""

    def test_t055_default_storage_path_outside_worktree(self):
        """T055: Default path is ~/.config/assemblyzero/tokens.json."""
        path = get_default_storage_path()

        assert path.name == "tokens.json"
        assert "assemblyzero" in str(path)
        assert ".config" in str(path)
        # Must be outside current working directory
        cwd = Path.cwd()
        assert not str(path).startswith(str(cwd))

    def test_055_path_is_absolute(self):
        """Scenario 055: Default storage path is absolute."""
        path = get_default_storage_path()
        assert path.is_absolute()

    def test_default_path_uses_home_directory(self):
        """Default path is rooted at the user's home directory."""
        path = get_default_storage_path()
        home = Path.home()
        assert str(path).startswith(str(home))

    def test_default_path_structure(self):
        """Default path follows ~/.config/assemblyzero/tokens.json layout."""
        path = get_default_storage_path()
        parts = path.parts
        # Should contain .config and assemblyzero as components
        assert ".config" in parts
        assert "assemblyzero" in parts
        assert parts[-1] == "tokens.json"


# ---------------------------------------------------------------------------
# T050 / Scenario 050 — store_tokens / get_stored_tokens (uses tmp_path)
# ---------------------------------------------------------------------------


class TestStoreAndRetrieveTokens:
    """Tests for store_tokens() and get_stored_tokens() with file isolation."""

    def test_t050_store_tokens_persists(self, tmp_path, valid_tokens):
        """T050: Tokens retrievable after storage (uses tmp_path)."""
        storage = tmp_path / "tokens.json"
        store_tokens(valid_tokens, storage_path=storage)

        retrieved = get_stored_tokens(storage_path=storage)

        assert retrieved is not None
        assert retrieved["access_token"] == valid_tokens["access_token"]
        assert retrieved["expires_at"] == valid_tokens["expires_at"]
        assert retrieved["refresh_token"] == valid_tokens["refresh_token"]

    def test_store_creates_parent_directories(self, tmp_path, valid_tokens):
        """store_tokens creates parent directories if they don't exist."""
        storage = tmp_path / "nested" / "deep" / "tokens.json"
        store_tokens(valid_tokens, storage_path=storage)

        assert storage.exists()
        retrieved = get_stored_tokens(storage_path=storage)
        assert retrieved is not None
        assert retrieved["access_token"] == valid_tokens["access_token"]

    def test_store_tokens_uses_default_path_when_none(self, valid_tokens):
        """store_tokens uses get_default_storage_path() when storage_path is None."""
        with patch("auth.token_manager.get_default_storage_path") as mock_path:
            mock_storage = MagicMock()
            mock_storage.parent.mkdir = MagicMock()
            mock_storage.write_bytes = MagicMock()
            mock_path.return_value = mock_storage

            with patch("auth.token_manager._encrypt_data", return_value=b"encrypted"):
                store_tokens(valid_tokens, storage_path=None)

            mock_path.assert_called_once()

    def test_get_stored_tokens_returns_none_when_missing(self, tmp_path):
        """Returns None when no token file exists."""
        storage = tmp_path / "nonexistent.json"
        assert get_stored_tokens(storage_path=storage) is None

    def test_store_overwrites_existing_tokens(self, tmp_path, valid_tokens):
        """Storing tokens replaces previously stored tokens."""
        storage = tmp_path / "tokens.json"
        store_tokens(valid_tokens, storage_path=storage)

        new_tokens = LinkedInTokens(
            access_token="updated-access-token",
            expires_at=int(time.time()) + 86400 * 60,
            refresh_token="updated-refresh-token",
        )
        store_tokens(new_tokens, storage_path=storage)

        retrieved = get_stored_tokens(storage_path=storage)
        assert retrieved is not None
        assert retrieved["access_token"] == "updated-access-token"
        assert retrieved["refresh_token"] == "updated-refresh-token"

    def test_store_tokens_without_refresh_token(self, tmp_path):
        """Tokens without a refresh token can be stored and retrieved."""
        tokens = LinkedInTokens(
            access_token="no-refresh-token",
            expires_at=int(time.time()) + 86400,
            refresh_token=None,
        )
        storage = tmp_path / "tokens.json"
        store_tokens(tokens, storage_path=storage)

        retrieved = get_stored_tokens(storage_path=storage)
        assert retrieved is not None
        assert retrieved["access_token"] == "no-refresh-token"
        assert retrieved["refresh_token"] is None

    def test_roundtrip_preserves_all_fields(self, tmp_path):
        """Full round-trip preserves access_token, expires_at, and refresh_token."""
        tokens = LinkedInTokens(
            access_token="roundtrip-token-abc",
            expires_at=1700000000,
            refresh_token="roundtrip-refresh-xyz",
        )
        storage = tmp_path / "tokens.json"
        store_tokens(tokens, storage_path=storage)

        retrieved = get_stored_tokens(storage_path=storage)
        assert retrieved is not None
        assert retrieved["access_token"] == "roundtrip-token-abc"
        assert retrieved["expires_at"] == 1700000000
        assert retrieved["refresh_token"] == "roundtrip-refresh-xyz"


# ---------------------------------------------------------------------------
# Encryption — stored file is ciphertext
# ---------------------------------------------------------------------------


class TestTokenEncryption:
    """Tests for token encryption (reviewer suggestion: verify ciphertext)."""

    def test_stored_file_is_encrypted(self, tmp_path, valid_tokens):
        """Reviewer suggestion: stored file contains ciphertext, not plaintext."""
        storage = tmp_path / "tokens.json"
        store_tokens(valid_tokens, storage_path=storage)

        raw_bytes = storage.read_bytes()
        # Plaintext access token should NOT appear in the file
        assert valid_tokens["access_token"].encode() not in raw_bytes

    def test_stored_file_not_valid_json(self, tmp_path, valid_tokens):
        """Encrypted file should not be parseable as plain JSON."""
        storage = tmp_path / "tokens.json"
        store_tokens(valid_tokens, storage_path=storage)

        raw = storage.read_text(errors="replace")
        with pytest.raises(json.JSONDecodeError):
            json.loads(raw)

    def test_encrypt_decrypt_roundtrip(self, tmp_path):
        """_encrypt_data and _decrypt_data round-trip correctly."""
        storage = tmp_path / "tokens.json"
        data = {"access_token": "test", "expires_at": 123}

        encrypted = _encrypt_data(data, storage)
        decrypted = _decrypt_data(encrypted, storage)

        assert decrypted == data

    def test_key_file_created_alongside_tokens(self, tmp_path, valid_tokens):
        """Encryption key seed file is created alongside the token file."""
        storage = tmp_path / "tokens.json"
        store_tokens(valid_tokens, storage_path=storage)

        key_path = _get_key_path(storage)
        assert key_path.exists()

    def test_key_is_reused_across_calls(self, tmp_path):
        """Same key is returned for subsequent calls (key file is reused)."""
        storage = tmp_path / "tokens.json"

        key1 = _get_or_create_key(storage)
        key2 = _get_or_create_key(storage)

        assert key1 == key2

    def test_different_storage_paths_get_different_keys(self, tmp_path):
        """Different storage paths produce different encryption keys."""
        storage1 = tmp_path / "tokens1.json"
        storage2 = tmp_path / "tokens2.json"

        key1 = _get_or_create_key(storage1)
        key2 = _get_or_create_key(storage2)

        assert key1 != key2

    def test_wrong_key_cannot_decrypt(self, tmp_path, valid_tokens):
        """Tokens encrypted with one key cannot be decrypted with another."""
        storage1 = tmp_path / "tokens1.json"
        storage2 = tmp_path / "tokens2.json"

        # Create keys for both
        _get_or_create_key(storage1)
        _get_or_create_key(storage2)

        encrypted = _encrypt_data(dict(valid_tokens), storage1)

        # Attempting to decrypt with storage2's key should fail
        from cryptography.fernet import InvalidToken

        with pytest.raises(InvalidToken):
            _decrypt_data(encrypted, storage2)


# ---------------------------------------------------------------------------
# Scenario 110 — Corrupted storage recovery
# ---------------------------------------------------------------------------


class TestCorruptedStorageRecovery:
    """Tests for corrupted token storage recovery (graceful fallback)."""

    def test_110_corrupted_storage_recovery(self, tmp_path):
        """Scenario 110: Corrupted storage falls back to None (no crash)."""
        storage = tmp_path / "tokens.json"
        storage.write_text("this is not valid encrypted data at all")

        result = get_stored_tokens(storage_path=storage)
        assert result is None

    def test_110_corrupted_json_recovery(self, tmp_path, valid_tokens):
        """Corrupted JSON inside valid encryption returns None."""
        storage = tmp_path / "tokens.json"
        # Write valid tokens first to create the key file
        store_tokens(valid_tokens, storage_path=storage)
        # Overwrite with garbage
        storage.write_bytes(b"garbled-nonsense")

        result = get_stored_tokens(storage_path=storage)
        assert result is None

    def test_empty_file_returns_none(self, tmp_path):
        """Empty token file returns None without crashing."""
        storage = tmp_path / "tokens.json"
        storage.write_bytes(b"")

        result = get_stored_tokens(storage_path=storage)
        assert result is None

    def test_missing_required_fields_returns_none(self, tmp_path):
        """Token file missing access_token or expires_at returns None."""
        storage = tmp_path / "tokens.json"

        # Encrypt data that's missing required fields
        incomplete_data = {"some_field": "value"}
        encrypted = _encrypt_data(incomplete_data, storage)
        storage.write_bytes(encrypted)

        result = get_stored_tokens(storage_path=storage)
        assert result is None

    def test_truncated_encrypted_data_returns_none(self, tmp_path, valid_tokens):
        """Truncated encrypted data returns None (no crash)."""
        storage = tmp_path / "tokens.json"
        store_tokens(valid_tokens, storage_path=storage)

        # Truncate the encrypted file
        raw = storage.read_bytes()
        storage.write_bytes(raw[:10])

        result = get_stored_tokens(storage_path=storage)
        assert result is None


# ---------------------------------------------------------------------------
# T060 / Scenario 040 — Token expiration check
# ---------------------------------------------------------------------------


class TestTokenExpiration:
    """Tests for is_token_valid()."""

    def test_t060_token_expiration_check(self, expired_tokens):
        """T060: Correctly identifies expired tokens."""
        assert is_token_valid(expired_tokens) is False

    def test_040_expired_1_hour_ago(self):
        """Scenario 040: Token expired 1 hour ago is invalid."""
        tokens = LinkedInTokens(
            access_token="expired",
            expires_at=int(time.time()) - 3600,
            refresh_token=None,
        )
        assert is_token_valid(tokens) is False

    def test_valid_token_returns_true(self, valid_tokens):
        """Non-expired token returns True."""
        assert is_token_valid(valid_tokens) is True

    def test_token_expiring_right_now_is_invalid(self):
        """Token with expires_at == now is invalid (boundary)."""
        tokens = LinkedInTokens(
            access_token="edge",
            expires_at=int(time.time()),
            refresh_token=None,
        )
        # expires_at == now means NOT > now, so invalid
        assert is_token_valid(tokens) is False

    def test_token_expiring_in_1_second(self):
        """Token expiring in 1 second is still valid."""
        tokens = LinkedInTokens(
            access_token="almost",
            expires_at=int(time.time()) + 1,
            refresh_token=None,
        )
        assert is_token_valid(tokens) is True

    def test_token_far_future_is_valid(self):
        """Token with far-future expiration is valid."""
        tokens = LinkedInTokens(
            access_token="future",
            expires_at=int(time.time()) + 86400 * 365,
            refresh_token=None,
        )
        assert is_token_valid(tokens) is True

    def test_token_expired_long_ago_is_invalid(self):
        """Token expired a year ago is invalid."""
        tokens = LinkedInTokens(
            access_token="ancient",
            expires_at=int(time.time()) - 86400 * 365,
            refresh_token=None,
        )
        assert is_token_valid(tokens) is False


# ---------------------------------------------------------------------------
# T070 / Scenario 060 — Logout clears all data
# ---------------------------------------------------------------------------


class TestLogout:
    """Tests for clear_tokens() and logout flow."""

    def test_t070_logout_clears_all_data(self, tmp_path, valid_tokens):
        """T070: No tokens or profile after logout (uses tmp_path)."""
        storage = tmp_path / "tokens.json"
        store_tokens(valid_tokens, storage_path=storage)

        # Verify tokens exist
        assert get_stored_tokens(storage_path=storage) is not None

        # Logout
        clear_tokens(storage_path=storage)

        # Verify tokens are gone
        assert get_stored_tokens(storage_path=storage) is None
        assert not storage.exists()

    def test_060_logout_clears_state(self, tmp_path, valid_tokens):
        """Scenario 060: Logout clears all data, auth state resets."""
        from auth.auth_state import get_auth_state

        storage = tmp_path / "tokens.json"
        store_tokens(valid_tokens, storage_path=storage)

        clear_tokens(storage_path=storage)

        state = get_auth_state(storage_path=storage)
        assert state["is_authenticated"] is False
        assert state["tokens"] is None

    def test_clear_tokens_removes_key_file(self, tmp_path, valid_tokens):
        """Clearing tokens also removes the encryption key file."""
        storage = tmp_path / "tokens.json"
        store_tokens(valid_tokens, storage_path=storage)

        key_path = _get_key_path(storage)
        assert key_path.exists()

        clear_tokens(storage_path=storage)

        assert not key_path.exists()

    def test_clear_tokens_no_file_is_noop(self, tmp_path):
        """Clearing tokens when no file exists does not raise."""
        storage = tmp_path / "nonexistent.json"
        clear_tokens(storage_path=storage)  # Should not raise

    def test_clear_tokens_idempotent(self, tmp_path, valid_tokens):
        """Clearing tokens twice does not raise on the second call."""
        storage = tmp_path / "tokens.json"
        store_tokens(valid_tokens, storage_path=storage)

        clear_tokens(storage_path=storage)
        clear_tokens(storage_path=storage)  # Second call is a no-op

        assert get_stored_tokens(storage_path=storage) is None


# ---------------------------------------------------------------------------
# Token refresh — Scenario 050
# ---------------------------------------------------------------------------


class TestTokenRefresh:
    """Tests for refresh_token_if_needed()."""

    def test_050_near_expiration_triggers_refresh(
        self, oauth_env, near_expiry_tokens
    ):
        """Scenario 050: Token near expiration triggers refresh, new token stored."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "refreshed-access-token",
            "expires_in": 5184000,
            "refresh_token": "new-refresh-token",
        }

        with patch("auth.token_manager.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            refreshed = refresh_token_if_needed(near_expiry_tokens)

        assert refreshed["access_token"] == "refreshed-access-token"
        assert refreshed["expires_at"] > near_expiry_tokens["expires_at"]

    def test_no_refresh_needed_when_far_from_expiry(self, valid_tokens):
        """Token far from expiration is returned unchanged."""
        result = refresh_token_if_needed(valid_tokens)

        assert result is valid_tokens  # Exact same object (no refresh)

    def test_expired_token_no_refresh_token_raises(self):
        """Expired token without refresh token raises TOKEN_EXPIRED."""
        tokens = LinkedInTokens(
            access_token="expired",
            expires_at=int(time.time()) - 3600,
            refresh_token=None,
        )

        with pytest.raises(TypeError):
            # AuthError is a TypedDict — raising it causes TypeError
            refresh_token_if_needed(tokens)

    def test_refresh_failure_returns_original(
        self, oauth_env, near_expiry_tokens
    ):
        """Failed refresh returns original tokens (graceful degradation)."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "invalid_grant"

        with patch("auth.token_manager.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            result = refresh_token_if_needed(near_expiry_tokens)

        assert result["access_token"] == near_expiry_tokens["access_token"]

    def test_refresh_sends_correct_payload(self, oauth_env, near_expiry_tokens):
        """Refresh request sends grant_type=refresh_token with correct data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "refreshed-token",
            "expires_in": 5184000,
            "refresh_token": "new-refresh",
        }

        with patch("auth.token_manager.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            refresh_token_if_needed(near_expiry_tokens)

            call_kwargs = mock_client.post.call_args
            assert call_kwargs[0][0] == LINKEDIN_TOKEN_URL
            data = call_kwargs[1]["data"]
            assert data["grant_type"] == "refresh_token"
            assert data["refresh_token"] == near_expiry_tokens["refresh_token"]
            assert data["client_id"] == "test-client-id"
            assert data["client_secret"] == "test-client-secret"

    def test_network_error_during_refresh_returns_original(
        self, oauth_env, near_expiry_tokens
    ):
        """Network error during refresh returns original tokens."""
        with patch("auth.token_manager.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.side_effect = httpx.ConnectError("Connection refused")
            mock_client_cls.return_value = mock_client

            result = refresh_token_if_needed(near_expiry_tokens)

        assert result["access_token"] == near_expiry_tokens["access_token"]

    def test_near_expiry_no_refresh_token_returns_original(self):
        """Near-expiry token without refresh_token returns original (with warning)."""
        tokens = LinkedInTokens(
            access_token="near-expiry-no-refresh",
            expires_at=int(time.time()) + 3600,  # Within 24h buffer
            refresh_token=None,
        )

        result = refresh_token_if_needed(tokens)

        assert result["access_token"] == "near-expiry-no-refresh"

    def test_missing_credentials_returns_original(
        self, monkeypatch, near_expiry_tokens
    ):
        """Missing client credentials returns original tokens (can't refresh)."""
        monkeypatch.delenv("LINKEDIN_CLIENT_ID", raising=False)
        monkeypatch.delenv("LINKEDIN_CLIENT_SECRET", raising=False)

        result = refresh_token_if_needed(near_expiry_tokens)

        assert result["access_token"] == near_expiry_tokens["access_token"]

    def test_refresh_preserves_old_refresh_token_if_not_returned(
        self, oauth_env, near_expiry_tokens
    ):
        """If LinkedIn doesn't return a new refresh_token, the old one is kept."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new-access",
            "expires_in": 5184000,
            # No refresh_token in response
        }

        with patch("auth.token_manager.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            refreshed = refresh_token_if_needed(near_expiry_tokens)

        assert refreshed["access_token"] == "new-access"
        assert refreshed["refresh_token"] == near_expiry_tokens["refresh_token"]

    def test_refresh_buffer_boundary_exact(self, valid_tokens):
        """Token expiring exactly at REFRESH_BUFFER_SECONDS + 1 is not refreshed."""
        tokens = LinkedInTokens(
            access_token="boundary",
            expires_at=int(time.time()) + REFRESH_BUFFER_SECONDS + 1,
            refresh_token="some-refresh",
        )
        result = refresh_token_if_needed(tokens)
        assert result is tokens  # Same object — no refresh

    def test_refresh_buffer_boundary_inside(self, oauth_env):
        """Token expiring exactly at REFRESH_BUFFER_SECONDS triggers refresh."""
        tokens = LinkedInTokens(
            access_token="inside-buffer",
            expires_at=int(time.time()) + REFRESH_BUFFER_SECONDS,
            refresh_token="some-refresh",
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "refreshed-boundary",
            "expires_in": 5184000,
        }

        with patch("auth.token_manager.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            refreshed = refresh_token_if_needed(tokens)

        assert refreshed["access_token"] == "refreshed-boundary"


# ---------------------------------------------------------------------------
# File permissions
# ---------------------------------------------------------------------------


class TestFilePermissions:
    """Tests for _set_file_permissions()."""

    @pytest.mark.skipif(
        platform.system() == "Windows",
        reason="Unix file permissions not applicable on Windows",
    )
    def test_file_permissions_set_to_0600(self, tmp_path, valid_tokens):
        """On Unix, token file is created with 0600 permissions."""

        storage = tmp_path / "tokens.json"
        store_tokens(valid_tokens, storage_path=storage)

        mode = storage.stat().st_mode
        # Owner read/write only
        assert mode & 0o777 == 0o600

    def test_set_file_permissions_no_crash_on_windows(self, tmp_path):
        """_set_file_permissions does not crash on Windows."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        # Should not raise regardless of platform
        _set_file_permissions(test_file)


# ---------------------------------------------------------------------------
# Key path helper
# ---------------------------------------------------------------------------


class TestKeyPath:
    """Tests for _get_key_path() helper."""

    def test_key_path_has_key_suffix(self):
        """Key path replaces .json with .key."""
        storage = Path("/tmp/tokens.json")
        key_path = _get_key_path(storage)
        assert key_path == Path("/tmp/tokens.key")

    def test_key_path_same_directory(self):
        """Key file is in the same directory as the token file."""
        storage = Path("/home/user/.config/assemblyzero/tokens.json")
        key_path = _get_key_path(storage)
        assert key_path.parent == storage.parent


# ---------------------------------------------------------------------------
# Integration: store + retrieve + validate cycle
# ---------------------------------------------------------------------------


class TestTokenLifecycle:
    """Integration tests for the token management lifecycle."""

    def test_store_retrieve_validate_cycle(self, tmp_path, valid_tokens):
        """Full lifecycle: store -> retrieve -> validate."""
        storage = tmp_path / "tokens.json"

        store_tokens(valid_tokens, storage_path=storage)
        retrieved = get_stored_tokens(storage_path=storage)

        assert retrieved is not None
        assert is_token_valid(retrieved) is True

    def test_store_retrieve_expired_token(self, tmp_path, expired_tokens):
        """Expired tokens can be stored and retrieved, but fail validation."""
        storage = tmp_path / "tokens.json"

        store_tokens(expired_tokens, storage_path=storage)
        retrieved = get_stored_tokens(storage_path=storage)

        assert retrieved is not None
        assert is_token_valid(retrieved) is False

    def test_store_clear_retrieve_returns_none(self, tmp_path, valid_tokens):
        """After clear, retrieval returns None."""
        storage = tmp_path / "tokens.json"

        store_tokens(valid_tokens, storage_path=storage)
        clear_tokens(storage_path=storage)
        retrieved = get_stored_tokens(storage_path=storage)

        assert retrieved is None

    def test_store_new_tokens_after_clear(self, tmp_path, valid_tokens):
        """New tokens can be stored after clearing (new key is generated)."""
        storage = tmp_path / "tokens.json"

        store_tokens(valid_tokens, storage_path=storage)
        clear_tokens(storage_path=storage)

        new_tokens = LinkedInTokens(
            access_token="brand-new-token",
            expires_at=int(time.time()) + 86400,
            refresh_token="brand-new-refresh",
        )
        store_tokens(new_tokens, storage_path=storage)
        retrieved = get_stored_tokens(storage_path=storage)

        assert retrieved is not None
        assert retrieved["access_token"] == "brand-new-token"
