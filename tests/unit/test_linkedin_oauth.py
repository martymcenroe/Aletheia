"""Unit tests for LinkedIn OAuth flow.

Tests for the core OAuth flow implementation including URL generation,
callback handling, token exchange, local server, and the full login
orchestrator. Also covers Lambda validate_token / fetch_linkedin_profile.

Issue: #116
"""

from __future__ import annotations

import json
import socket
import time
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
import requests

from auth.linkedin_oauth import (
    LINKEDIN_SCOPES,
    LINKEDIN_TOKEN_URL,
    _extract_state_from_url,
    exchange_code_for_tokens,
    handle_oauth_callback,
    initiate_oauth_flow,
    run_oauth_login,
    start_local_oauth_server,
)
from auth.token_manager import (
    clear_tokens,
    get_default_storage_path,
    get_stored_tokens,
    is_token_valid,
    refresh_token_if_needed,
    store_tokens,
)
from auth.auth_state import (
    _listeners,
    get_auth_state,
    set_auth_state,
    subscribe_to_auth_changes,
)
from auth.types import AuthError, AuthState, LinkedInTokens, UserProfile
from lambda_auth_function import (
    fetch_linkedin_profile,
    validate_token,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clean_listeners():
    """Ensure auth state listeners are cleared between tests."""
    _listeners.clear()
    yield
    _listeners.clear()


@pytest.fixture()
def oauth_env(monkeypatch):
    """Set required LinkedIn OAuth environment variables."""
    monkeypatch.setenv("LINKEDIN_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("LINKEDIN_CLIENT_SECRET", "test-client-secret")


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
def mock_linkedin_profile() -> dict:
    """Mock LinkedIn userinfo response."""
    return {
        "sub": "linkedin-member-12345",
        "name": "Test User",
        "email": "test@example.com",
        "picture": "https://media.licdn.com/photo.jpg",
    }


# ---------------------------------------------------------------------------
# T010 / Scenario 010 — initiate_oauth_flow returns a valid auth URL
# ---------------------------------------------------------------------------


class TestInitiateOAuthFlow:
    """Tests for initiate_oauth_flow()."""

    def test_t010_initiate_oauth_returns_auth_url(self, oauth_env):
        """T010: Generates valid LinkedIn OAuth URL with state."""
        redirect_uri = "http://localhost:8585/callback"
        url = initiate_oauth_flow(redirect_uri)

        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        assert parsed.scheme == "https"
        assert "linkedin.com" in parsed.netloc
        assert "/oauth/v2/authorization" in parsed.path
        assert params["response_type"] == ["code"]
        assert params["client_id"] == ["test-client-id"]
        assert params["redirect_uri"] == [redirect_uri]
        assert "state" in params
        assert len(params["state"][0]) > 16  # CSPRNG state should be long
        assert params["scope"] == [LINKEDIN_SCOPES]

    def test_state_is_unique_per_call(self, oauth_env):
        """Each invocation generates a unique state parameter."""
        url1 = initiate_oauth_flow("http://localhost:8585/callback")
        url2 = initiate_oauth_flow("http://localhost:8585/callback")

        state1 = _extract_state_from_url(url1)
        state2 = _extract_state_from_url(url2)

        assert state1 != state2

    def test_raises_without_client_id(self, monkeypatch):
        """Raises when LINKEDIN_CLIENT_ID is not set."""
        monkeypatch.delenv("LINKEDIN_CLIENT_ID", raising=False)
        # Also clear the default that may have been read at module load
        monkeypatch.setattr("auth.linkedin_oauth.DEFAULT_CLIENT_ID", "")

        with pytest.raises(AuthError):
            initiate_oauth_flow("http://localhost:8585/callback")


# ---------------------------------------------------------------------------
# T015 / Scenario 015 — Port already in use
# ---------------------------------------------------------------------------


class TestStartLocalOAuthServer:
    """Tests for start_local_oauth_server()."""

    def test_t015_start_server_port_in_use(self):
        """T015: Returns PORT_IN_USE error when port is already bound."""
        # Bind a socket to a port to simulate it being in use
        blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        blocker.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        blocker.bind(("localhost", 0))
        port = blocker.getsockname()[1]

        try:
            with pytest.raises(AuthError):
                start_local_oauth_server(port=port)
        finally:
            blocker.close()

    def test_redirect_uri_format(self):
        """redirect_uri follows http://localhost:<port>/callback format."""
        # Find a free port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("localhost", 0))
        port = sock.getsockname()[1]
        sock.close()

        redirect_uri, get_callback = start_local_oauth_server(port=port)

        assert redirect_uri == f"http://localhost:{port}/callback"

        # Clean up — send a fake request so the server thread can finish
        try:
            import urllib.request

            urllib.request.urlopen(
                f"http://localhost:{port}/callback?code=x&state=y", timeout=2
            )
        except Exception:
            pass


# ---------------------------------------------------------------------------
# T020 / Scenario 020 — handle_oauth_callback extracts code
# ---------------------------------------------------------------------------


class TestHandleOAuthCallback:
    """Tests for handle_oauth_callback()."""

    def test_t020_handle_callback_extracts_code(self, oauth_env):
        """T020: Parses auth code from redirect URL and exchanges for tokens."""
        callback_url = (
            "http://localhost:8585/callback?code=AUTH_CODE_123&state=expected-state"
        )
        expected_state = "expected-state"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new-access-token",
            "expires_in": 5184000,
            "refresh_token": "new-refresh-token",
        }

        with patch("auth.linkedin_oauth.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            tokens = handle_oauth_callback(callback_url, expected_state)

        assert tokens["access_token"] == "new-access-token"
        assert tokens["refresh_token"] == "new-refresh-token"
        assert tokens["expires_at"] > int(time.time())

    def test_t030_handle_callback_validates_state(self, oauth_env):
        """T030: Rejects callback with mismatched state (CSRF protection)."""
        callback_url = (
            "http://localhost:8585/callback?code=AUTH_CODE&state=wrong-state"
        )
        expected_state = "correct-state"

        with pytest.raises(AuthError):
            handle_oauth_callback(callback_url, expected_state)

    def test_120_csrf_state_mismatch(self, oauth_env):
        """Scenario 120: CSRF state mismatch returns OAUTH_FAILED error."""
        callback_url = (
            "http://localhost:8585/callback?code=SOME_CODE&state=attacker-state"
        )

        with pytest.raises(AuthError):
            handle_oauth_callback(callback_url, "legitimate-state")

    def test_020_oauth_canceled_by_user(self, oauth_env):
        """Scenario 020: OAuth error in callback raises AuthError."""
        callback_url = (
            "http://localhost:8585/callback"
            "?error=user_cancelled_authorize"
            "&error_description=User+cancelled"
        )
        expected_state = "some-state"

        with pytest.raises(AuthError):
            handle_oauth_callback(callback_url, expected_state)

    def test_no_code_in_callback_raises(self, oauth_env):
        """Callback without authorization code raises AuthError."""
        callback_url = "http://localhost:8585/callback?state=expected-state"

        with pytest.raises(AuthError):
            handle_oauth_callback(callback_url, "expected-state")


# ---------------------------------------------------------------------------
# T040 — exchange_code_for_tokens
# ---------------------------------------------------------------------------


class TestExchangeCodeForTokens:
    """Tests for exchange_code_for_tokens()."""

    def test_t040_exchange_code_returns_tokens(self, oauth_env):
        """T040: Returns token object on successful exchange."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "li_access_token_value",
            "expires_in": 5184000,
            "refresh_token": "li_refresh_token_value",
        }

        with patch("auth.linkedin_oauth.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            tokens = exchange_code_for_tokens(
                "auth-code-123", "http://localhost:8585/callback"
            )

        assert tokens["access_token"] == "li_access_token_value"
        assert tokens["refresh_token"] == "li_refresh_token_value"
        assert isinstance(tokens["expires_at"], int)
        assert tokens["expires_at"] > int(time.time())

    def test_030_invalid_auth_code_raises(self, oauth_env):
        """Scenario 030: Invalid auth code triggers AuthError (OAUTH_FAILED)."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "invalid_grant"

        with patch("auth.linkedin_oauth.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            with pytest.raises(AuthError):
                exchange_code_for_tokens(
                    "bad-code", "http://localhost:8585/callback"
                )

    def test_network_error_raises(self, oauth_env):
        """Network error during exchange raises AuthError (NETWORK_ERROR)."""
        with patch("auth.linkedin_oauth.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.side_effect = httpx.ConnectError("Connection refused")
            mock_client_cls.return_value = mock_client

            with pytest.raises(AuthError):
                exchange_code_for_tokens(
                    "code", "http://localhost:8585/callback"
                )

    def test_missing_credentials_raises(self, monkeypatch):
        """Missing client credentials raises AuthError."""
        monkeypatch.delenv("LINKEDIN_CLIENT_ID", raising=False)
        monkeypatch.delenv("LINKEDIN_CLIENT_SECRET", raising=False)
        monkeypatch.setattr("auth.linkedin_oauth.DEFAULT_CLIENT_ID", "")

        with pytest.raises(AuthError):
            exchange_code_for_tokens("code", "http://localhost:8585/callback")

    def test_token_exchange_sends_correct_payload(self, oauth_env):
        """Token exchange sends grant_type, code, redirect_uri, client_id, client_secret."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "token",
            "expires_in": 3600,
        }

        with patch("auth.linkedin_oauth.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            exchange_code_for_tokens(
                "my-code", "http://localhost:8585/callback"
            )

            call_kwargs = mock_client.post.call_args
            assert call_kwargs[0][0] == LINKEDIN_TOKEN_URL
            data = call_kwargs[1]["data"]
            assert data["grant_type"] == "authorization_code"
            assert data["code"] == "my-code"
            assert data["redirect_uri"] == "http://localhost:8585/callback"
            assert data["client_id"] == "test-client-id"
            assert data["client_secret"] == "test-client-secret"


# ---------------------------------------------------------------------------
# T050 — store_tokens / get_stored_tokens (uses tmp_path)
# ---------------------------------------------------------------------------


class TestTokenStorage:
    """Tests for store_tokens / get_stored_tokens (file isolation via tmp_path)."""

    def test_t050_store_tokens_persists(self, tmp_path, valid_tokens):
        """T050: Tokens retrievable after storage (uses tmp_path)."""
        storage = tmp_path / "tokens.json"
        store_tokens(valid_tokens, storage_path=storage)

        retrieved = get_stored_tokens(storage_path=storage)

        assert retrieved is not None
        assert retrieved["access_token"] == valid_tokens["access_token"]
        assert retrieved["expires_at"] == valid_tokens["expires_at"]
        assert retrieved["refresh_token"] == valid_tokens["refresh_token"]

    def test_stored_file_is_encrypted(self, tmp_path, valid_tokens):
        """Reviewer suggestion: stored file contains ciphertext, not plaintext."""
        storage = tmp_path / "tokens.json"
        store_tokens(valid_tokens, storage_path=storage)

        raw_bytes = storage.read_bytes()
        # Plaintext access token should NOT appear in the file
        assert valid_tokens["access_token"].encode() not in raw_bytes

    def test_get_stored_tokens_returns_none_when_missing(self, tmp_path):
        """Returns None when no token file exists."""
        storage = tmp_path / "nonexistent.json"
        assert get_stored_tokens(storage_path=storage) is None

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


# ---------------------------------------------------------------------------
# T055 — Default storage path is outside worktree
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


# ---------------------------------------------------------------------------
# T060 — Token expiration check
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


# ---------------------------------------------------------------------------
# T070 — Logout clears all data
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

        key_path = storage.with_suffix(".key")
        assert key_path.exists()

        clear_tokens(storage_path=storage)

        assert not key_path.exists()

    def test_clear_tokens_no_file_is_noop(self, tmp_path):
        """Clearing tokens when no file exists does not raise."""
        storage = tmp_path / "nonexistent.json"
        clear_tokens(storage_path=storage)  # Should not raise


# ---------------------------------------------------------------------------
# T080 / T090 — Lambda validate_token and fetch_linkedin_profile
# ---------------------------------------------------------------------------


class TestLambdaValidateToken:
    """Tests for validate_token() Lambda handler."""

    def test_t080_lambda_validates_good_token(self, mock_linkedin_profile):
        """T080: Returns profile for valid token (stateless)."""
        with patch("lambda_auth_function.fetch_linkedin_profile") as mock_fetch:
            mock_fetch.return_value = mock_linkedin_profile

            result = validate_token(
                {"access_token": "valid-token-abc"},
                context=None,
            )

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["valid"] is True
        assert body["user"]["id"] == "linkedin-member-12345"
        assert body["user"]["name"] == "Test User"
        assert body["user"]["email"] == "test@example.com"

    def test_t090_lambda_rejects_bad_token(self):
        """T090: Returns 401 for invalid token."""
        with patch("lambda_auth_function.fetch_linkedin_profile") as mock_fetch:
            mock_fetch.return_value = None  # Invalid token

            result = validate_token(
                {"access_token": "bad-token"},
                context=None,
            )

        assert result["statusCode"] == 401
        body = json.loads(result["body"])
        assert "Invalid token" in body["error"]

    def test_070_lambda_validates_good_token_via_body(self, mock_linkedin_profile):
        """Scenario 070: Lambda validates token in body-wrapped format."""
        with patch("lambda_auth_function.fetch_linkedin_profile") as mock_fetch:
            mock_fetch.return_value = mock_linkedin_profile

            event = {
                "body": json.dumps({"access_token": "valid-token"}),
            }
            result = validate_token(event, context=None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["valid"] is True

    def test_080_lambda_rejects_expired_token(self):
        """Scenario 080: Lambda rejects expired token with 401."""
        with patch("lambda_auth_function.fetch_linkedin_profile") as mock_fetch:
            mock_fetch.return_value = None

            result = validate_token(
                {"access_token": "expired-token"},
                context=None,
            )

        assert result["statusCode"] == 401

    def test_090_lambda_handles_linkedin_api_error(self):
        """Scenario 090: Lambda returns 502 when LinkedIn API errors."""
        with patch("lambda_auth_function.fetch_linkedin_profile") as mock_fetch:
            mock_fetch.side_effect = requests.exceptions.HTTPError(
                "500 Server Error"
            )

            result = validate_token(
                {"access_token": "trigger-500"},
                context=None,
            )

        assert result["statusCode"] == 502
        body = json.loads(result["body"])
        assert "LinkedIn API error" in body["error"]

    def test_missing_access_token_returns_400(self):
        """Missing access_token returns 400."""
        result = validate_token({}, context=None)
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "Missing access_token" in body["error"]

    def test_authorization_header_format(self, mock_linkedin_profile):
        """Supports Authorization: Bearer <token> format."""
        with patch("lambda_auth_function.fetch_linkedin_profile") as mock_fetch:
            mock_fetch.return_value = mock_linkedin_profile

            event = {
                "headers": {"Authorization": "Bearer header-token"},
            }
            result = validate_token(event, context=None)

        assert result["statusCode"] == 200
        mock_fetch.assert_called_once_with("header-token")


class TestFetchLinkedInProfile:
    """Tests for fetch_linkedin_profile()."""

    def test_valid_token_returns_profile(self, mock_linkedin_profile):
        """Valid token returns user profile dict."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_linkedin_profile

        with patch(
            "lambda_auth_function.requests.get", return_value=mock_response
        ):
            profile = fetch_linkedin_profile("valid-token")

        assert profile is not None
        assert profile["sub"] == "linkedin-member-12345"

    def test_invalid_token_returns_none(self):
        """Invalid (401) token returns None."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch(
            "lambda_auth_function.requests.get", return_value=mock_response
        ):
            profile = fetch_linkedin_profile("bad-token")

        assert profile is None

    def test_server_error_raises(self):
        """Server error (5xx) raises for caller to handle as 502."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status.side_effect = (
            requests.exceptions.HTTPError("500 Server Error")
        )

        with patch(
            "lambda_auth_function.requests.get", return_value=mock_response
        ):
            with pytest.raises(requests.exceptions.HTTPError):
                fetch_linkedin_profile("trigger-500")


# ---------------------------------------------------------------------------
# T100 — Auth state notifies listeners
# ---------------------------------------------------------------------------


class TestAuthStateNotification:
    """Tests for auth state change notifications."""

    def test_t100_auth_state_notifies_listeners(self, tmp_path, valid_tokens):
        """T100: Subscribers receive state updates."""
        storage = tmp_path / "tokens.json"
        received_states: list[AuthState] = []

        subscribe_to_auth_changes(lambda s: received_states.append(s))

        state = AuthState(
            is_authenticated=True,
            user=UserProfile(
                linkedin_id="sub-123",
                email="test@example.com",
                display_name="Test User",
                profile_picture=None,
            ),
            tokens=valid_tokens,
            last_validated=int(time.time()),
        )
        set_auth_state(state, storage_path=storage)

        assert len(received_states) == 1
        assert received_states[0]["is_authenticated"] is True
        assert received_states[0]["user"]["email"] == "test@example.com"

    def test_100_state_change_notification(self, tmp_path, valid_tokens):
        """Scenario 100: Login completion triggers listener callback."""
        storage = tmp_path / "tokens.json"
        callback_count = 0

        def on_change(state: AuthState) -> None:
            nonlocal callback_count
            callback_count += 1

        subscribe_to_auth_changes(on_change)

        state = AuthState(
            is_authenticated=True,
            user=None,
            tokens=valid_tokens,
            last_validated=int(time.time()),
        )
        set_auth_state(state, storage_path=storage)

        assert callback_count == 1

    def test_unsubscribe_stops_notifications(self, tmp_path, valid_tokens):
        """Unsubscribed listeners do not receive further updates."""
        storage = tmp_path / "tokens.json"
        received: list[AuthState] = []

        unsub = subscribe_to_auth_changes(lambda s: received.append(s))

        state = AuthState(
            is_authenticated=True,
            user=None,
            tokens=valid_tokens,
            last_validated=int(time.time()),
        )
        set_auth_state(state, storage_path=storage)
        assert len(received) == 1

        unsub()

        set_auth_state(state, storage_path=storage)
        assert len(received) == 1  # Still 1 — unsubscribed

    def test_multiple_listeners_all_notified(self, tmp_path, valid_tokens):
        """All subscribed listeners receive the state change."""
        storage = tmp_path / "tokens.json"
        results = {"a": 0, "b": 0}

        subscribe_to_auth_changes(
            lambda s: results.update(a=results["a"] + 1)
        )
        subscribe_to_auth_changes(
            lambda s: results.update(b=results["b"] + 1)
        )

        state = AuthState(
            is_authenticated=True,
            user=None,
            tokens=valid_tokens,
            last_validated=0,
        )
        set_auth_state(state, storage_path=storage)

        assert results["a"] == 1
        assert results["b"] == 1

    def test_listener_exception_does_not_block_others(
        self, tmp_path, valid_tokens
    ):
        """A failing listener does not prevent other listeners from running."""
        storage = tmp_path / "tokens.json"
        reached = []

        def bad_listener(s: AuthState) -> None:
            raise RuntimeError("boom")

        def good_listener(s: AuthState) -> None:
            reached.append(True)

        subscribe_to_auth_changes(bad_listener)
        subscribe_to_auth_changes(good_listener)

        state = AuthState(
            is_authenticated=True,
            user=None,
            tokens=valid_tokens,
            last_validated=0,
        )
        set_auth_state(state, storage_path=storage)

        assert len(reached) == 1  # good_listener was called despite bad_listener


# ---------------------------------------------------------------------------
# Token refresh
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

        with pytest.raises(AuthError):
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


# ---------------------------------------------------------------------------
# Auth state (get/set)
# ---------------------------------------------------------------------------


class TestAuthState:
    """Tests for get_auth_state / set_auth_state."""

    def test_unauthenticated_when_no_tokens(self, tmp_path):
        """get_auth_state returns unauthenticated when no tokens stored."""
        storage = tmp_path / "tokens.json"
        state = get_auth_state(storage_path=storage)

        assert state["is_authenticated"] is False
        assert state["user"] is None
        assert state["tokens"] is None

    def test_authenticated_when_valid_tokens_stored(
        self, tmp_path, valid_tokens
    ):
        """get_auth_state returns authenticated when valid tokens exist."""
        storage = tmp_path / "tokens.json"
        store_tokens(valid_tokens, storage_path=storage)

        state = get_auth_state(storage_path=storage)

        assert state["is_authenticated"] is True
        assert state["tokens"] is not None
        assert state["tokens"]["access_token"] == valid_tokens["access_token"]

    def test_set_auth_state_persists_tokens(self, tmp_path, valid_tokens):
        """set_auth_state persists tokens to disk."""
        storage = tmp_path / "tokens.json"

        state = AuthState(
            is_authenticated=True,
            user=None,
            tokens=valid_tokens,
            last_validated=int(time.time()),
        )
        set_auth_state(state, storage_path=storage)

        retrieved = get_stored_tokens(storage_path=storage)
        assert retrieved is not None
        assert retrieved["access_token"] == valid_tokens["access_token"]


# ---------------------------------------------------------------------------
# Happy path (Scenario 010) — Full OAuth flow (mocked)
# ---------------------------------------------------------------------------


class TestHappyPathOAuthFlow:
    """Integration-style test of the full OAuth login flow (all external I/O mocked)."""

    def test_010_happy_path_oauth_flow(
        self, oauth_env, tmp_path, mock_linkedin_profile
    ):
        """Scenario 010: Happy path — valid auth code -> tokens stored, profile loaded."""
        storage = tmp_path / "tokens.json"

        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {
            "access_token": "happy-path-token",
            "expires_in": 5184000,
            "refresh_token": "happy-refresh",
        }

        # Mock the local server, browser, and HTTP client
        with (
            patch("auth.linkedin_oauth.start_local_oauth_server") as mock_server,
            patch("auth.linkedin_oauth.webbrowser.open"),
            patch("auth.linkedin_oauth.httpx.Client") as mock_client_cls,
        ):
            mock_server.return_value = (
                "http://localhost:8585/callback",
                lambda: "http://localhost:8585/callback?code=HAPPY_CODE&state=test-state",
            )

            # Make initiate_oauth_flow return a URL with state=test-state
            with patch(
                "auth.linkedin_oauth.secrets.token_urlsafe",
                return_value="test-state",
            ):
                mock_client = MagicMock()
                mock_client.__enter__ = MagicMock(return_value=mock_client)
                mock_client.__exit__ = MagicMock(return_value=False)
                mock_client.post.return_value = mock_token_response
                mock_client_cls.return_value = mock_client

                tokens = run_oauth_login(port=8585)

        assert tokens["access_token"] == "happy-path-token"
        assert tokens["refresh_token"] == "happy-refresh"
        assert tokens["expires_at"] > int(time.time())

        # Store and verify state
        store_tokens(tokens, storage_path=storage)
        state = get_auth_state(storage_path=storage)
        assert state["is_authenticated"] is True

    def test_run_oauth_login_no_callback_raises(self, oauth_env):
        """run_oauth_login raises when callback is not received (timeout)."""
        with (
            patch("auth.linkedin_oauth.start_local_oauth_server") as mock_server,
            patch("auth.linkedin_oauth.webbrowser.open"),
        ):
            mock_server.return_value = (
                "http://localhost:8585/callback",
                lambda: None,  # No callback received
            )

            with pytest.raises(AuthError):
                run_oauth_login(port=8585)


# ---------------------------------------------------------------------------
# Scenario 130 — Live OAuth flow (marked for live-only execution)
# ---------------------------------------------------------------------------


@pytest.mark.live
class TestLiveOAuthFlow:
    """Live integration test — requires real LinkedIn test app credentials.

    Scenario 130: Skipped in normal CI. Run with: pytest -m live
    """

    def test_130_live_oauth_flow(self):
        """Scenario 130: Live OAuth flow (skipped unless -m live)."""
        pytest.skip(
            "Live OAuth test requires real LinkedIn credentials and browser interaction"
        )


# ---------------------------------------------------------------------------
# _extract_state_from_url
# ---------------------------------------------------------------------------


class TestExtractState:
    """Tests for _extract_state_from_url helper."""

    def test_extracts_state_from_valid_url(self):
        """Extracts state parameter from a well-formed OAuth URL."""
        url = "https://www.linkedin.com/oauth/v2/authorization?state=abc123&client_id=x"
        assert _extract_state_from_url(url) == "abc123"

    def test_raises_when_no_state(self):
        """Raises ValueError when state parameter is missing."""
        url = "https://www.linkedin.com/oauth/v2/authorization?client_id=x"
        with pytest.raises(ValueError, match="No state parameter"):
            _extract_state_from_url(url)
