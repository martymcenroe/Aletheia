"""
Unit tests for GitHub OAuth handler.

Issue #433: GitHub OAuth for admin dashboard.
"""

import hashlib
import hmac
import json
import time
from unittest.mock import MagicMock, patch


from src.auth.github_oauth import (
    _generate_state,
    _validate_state,
    handle_github_authorize,
    handle_github_callback,
    get_github_credentials,
    invalidate_credentials_cache,
)

# Test constants
FAKE_JWT_SECRET = "test-jwt-secret-for-hmac"
FAKE_CLIENT_ID = "gh-client-id-123"
FAKE_CLIENT_SECRET = "gh-client-secret-456"
FAKE_GITHUB_CREDENTIALS = {
    "client_id": FAKE_CLIENT_ID,
    "client_secret": FAKE_CLIENT_SECRET,
}


def _make_valid_state(jwt_secret=FAKE_JWT_SECRET, timestamp=None):
    """Generate a valid HMAC state token for testing."""
    ts = str(timestamp or int(time.time()))
    sig = hmac.new(jwt_secret.encode(), ts.encode(), hashlib.sha256).hexdigest()
    return f"{ts}.{sig}"


class TestGenerateState:
    """Tests for _generate_state()."""

    def test_format(self):
        """State is timestamp.hmac format."""
        state = _generate_state(FAKE_JWT_SECRET)
        parts = state.split(".")
        assert len(parts) == 2
        # Timestamp is numeric
        int(parts[0])
        # HMAC is hex
        assert len(parts[1]) == 64  # SHA-256 hex digest

    def test_deterministic_with_same_timestamp(self):
        """Same secret + timestamp produces same HMAC."""
        t = str(int(time.time()))
        sig1 = hmac.new(FAKE_JWT_SECRET.encode(), t.encode(), hashlib.sha256).hexdigest()
        sig2 = hmac.new(FAKE_JWT_SECRET.encode(), t.encode(), hashlib.sha256).hexdigest()
        assert sig1 == sig2

    def test_different_secrets_produce_different_state(self):
        """Different secrets produce different HMACs."""
        state1 = _generate_state("secret-a")
        state2 = _generate_state("secret-b")
        # Timestamps may differ slightly but HMACs definitely differ
        assert state1.split(".")[1] != state2.split(".")[1]


class TestValidateState:
    """Tests for _validate_state()."""

    def test_valid_state(self):
        """Valid, fresh state passes validation."""
        state = _make_valid_state()
        assert _validate_state(state, FAKE_JWT_SECRET) is True

    def test_expired_state(self):
        """State older than 5 minutes is rejected."""
        old_timestamp = int(time.time()) - 400  # 6+ minutes ago
        state = _make_valid_state(timestamp=old_timestamp)
        assert _validate_state(state, FAKE_JWT_SECRET) is False

    def test_tampered_signature(self):
        """Modified HMAC is rejected."""
        state = _make_valid_state()
        timestamp = state.split(".")[0]
        tampered = f"{timestamp}.{'a' * 64}"
        assert _validate_state(tampered, FAKE_JWT_SECRET) is False

    def test_wrong_secret(self):
        """State signed with different secret is rejected."""
        state = _make_valid_state(jwt_secret="correct-secret")
        assert _validate_state(state, "wrong-secret") is False

    def test_empty_state(self):
        """Empty state string is rejected."""
        assert _validate_state("", FAKE_JWT_SECRET) is False

    def test_no_dot_separator(self):
        """State without dot separator is rejected."""
        assert _validate_state("nodot", FAKE_JWT_SECRET) is False

    def test_non_numeric_timestamp(self):
        """Non-numeric timestamp is rejected."""
        assert _validate_state("abc.def", FAKE_JWT_SECRET) is False


class TestHandleGitHubAuthorize:
    """Tests for handle_github_authorize()."""

    @patch("src.auth.github_oauth.get_jwt_secret", return_value=FAKE_JWT_SECRET)
    @patch("src.auth.github_oauth.get_github_credentials", return_value=FAKE_GITHUB_CREDENTIALS)
    def test_returns_302_with_state(self, mock_creds, mock_secret):
        """Authorize endpoint returns 302 redirect to GitHub."""
        response = handle_github_authorize({})

        assert response["statusCode"] == 302
        location = response["headers"]["Location"]
        assert "github.com/login/oauth/authorize" in location
        assert f"client_id={FAKE_CLIENT_ID}" in location
        assert "state=" in location
        assert "redirect_uri=" in location

    @patch("src.auth.github_oauth.get_jwt_secret", return_value=FAKE_JWT_SECRET)
    @patch("src.auth.github_oauth.get_github_credentials", return_value=FAKE_GITHUB_CREDENTIALS)
    def test_no_cache_header(self, mock_creds, mock_secret):
        """Authorize response has no-store cache control."""
        response = handle_github_authorize({})
        assert response["headers"]["Cache-Control"] == "no-store"

    @patch("src.auth.github_oauth.get_jwt_secret", side_effect=RuntimeError("Secret unavailable"))
    @patch("src.auth.github_oauth.get_github_credentials", return_value=FAKE_GITHUB_CREDENTIALS)
    def test_error_returns_500(self, mock_creds, mock_secret):
        """Returns 500 if JWT secret retrieval fails."""
        response = handle_github_authorize({})
        assert response["statusCode"] == 500


class TestHandleGitHubCallback:
    """Tests for handle_github_callback()."""

    def _mock_token_response(self, access_token="gh-token-123"):  # noqa: S107
        """Create a mock successful token exchange response."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"access_token": access_token}
        return mock_resp

    def _mock_user_response(self, github_id=12345, login="testuser"):
        """Create a mock successful user info response."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": github_id, "login": login}
        return mock_resp

    def _mock_repo_response(self, push=True):
        """Create a mock repo response with permissions."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"permissions": {"push": push, "pull": True}}
        return mock_resp

    def _mock_repo_not_found(self):
        """Create a mock 404 repo response (non-collaborator)."""
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.json.return_value = {"message": "Not Found"}
        return mock_resp

    @patch("src.auth.github_oauth.get_jwt_secret", return_value=FAKE_JWT_SECRET)
    def test_rejects_invalid_state(self, mock_secret):
        """Callback rejects invalid/tampered state token."""
        response = handle_github_callback({
            "code": "test-code",
            "state": "invalid.state",
        })

        assert response["statusCode"] == 200
        assert "Session Expired" in response["body"]

    @patch("src.auth.github_oauth.get_jwt_secret", return_value=FAKE_JWT_SECRET)
    def test_rejects_expired_state(self, mock_secret):
        """Callback rejects state token older than 5 minutes."""
        old_state = _make_valid_state(timestamp=int(time.time()) - 400)
        response = handle_github_callback({
            "code": "test-code",
            "state": old_state,
        })

        assert response["statusCode"] == 200
        assert "Session Expired" in response["body"]

    @patch("src.auth.github_oauth.get_jwt_secret", return_value=FAKE_JWT_SECRET)
    def test_rejects_missing_code(self, mock_secret):
        """Callback rejects request without authorization code."""
        state = _make_valid_state()
        response = handle_github_callback({"state": state})

        assert response["statusCode"] == 200
        assert "Invalid Request" in response["body"]

    @patch("src.auth.github_oauth.requests.get")
    @patch("src.auth.github_oauth.requests.post")
    @patch("src.auth.github_oauth.get_github_credentials", return_value=FAKE_GITHUB_CREDENTIALS)
    @patch("src.auth.github_oauth.get_jwt_secret", return_value=FAKE_JWT_SECRET)
    def test_rejects_non_collaborator(self, mock_secret, mock_creds, mock_post, mock_get):
        """Callback rejects users who are not repo collaborators."""
        state = _make_valid_state()
        mock_post.return_value = self._mock_token_response()

        # First get call = user info, second = repo check (404 = not collaborator)
        mock_get.side_effect = [
            self._mock_user_response(),
            self._mock_repo_not_found(),
        ]

        response = handle_github_callback({"code": "test-code", "state": state})

        assert response["statusCode"] == 200
        assert "Access Denied" in response["body"]

    @patch("src.auth.github_oauth.requests.get")
    @patch("src.auth.github_oauth.requests.post")
    @patch("src.auth.github_oauth.get_github_credentials", return_value=FAKE_GITHUB_CREDENTIALS)
    @patch("src.auth.github_oauth.get_jwt_secret", return_value=FAKE_JWT_SECRET)
    def test_rejects_collaborator_without_push(self, mock_secret, mock_creds, mock_post, mock_get):
        """Callback rejects collaborators without push access."""
        state = _make_valid_state()
        mock_post.return_value = self._mock_token_response()

        mock_get.side_effect = [
            self._mock_user_response(),
            self._mock_repo_response(push=False),
        ]

        response = handle_github_callback({"code": "test-code", "state": state})

        assert response["statusCode"] == 200
        assert "Access Denied" in response["body"]

    @patch("src.auth.github_oauth.requests.get")
    @patch("src.auth.github_oauth.requests.post")
    @patch("src.auth.github_oauth.get_github_credentials", return_value=FAKE_GITHUB_CREDENTIALS)
    @patch("src.auth.github_oauth.get_jwt_secret", return_value=FAKE_JWT_SECRET)
    def test_issues_admin_jwt_for_collaborator(self, mock_secret, mock_creds, mock_post, mock_get):
        """Callback issues admin JWT for valid collaborator with push access."""
        state = _make_valid_state()
        mock_post.return_value = self._mock_token_response()

        mock_get.side_effect = [
            self._mock_user_response(github_id=99999, login="admin-user"),
            self._mock_repo_response(push=True),
        ]

        response = handle_github_callback({"code": "test-code", "state": state})

        assert response["statusCode"] == 302
        location = response["headers"]["Location"]
        assert "metrics.html" in location
        assert "jwt=" in location

    @patch("src.auth.github_oauth.requests.get")
    @patch("src.auth.github_oauth.requests.post")
    @patch("src.auth.github_oauth.get_github_credentials", return_value=FAKE_GITHUB_CREDENTIALS)
    @patch("src.auth.github_oauth.get_jwt_secret", return_value=FAKE_JWT_SECRET)
    def test_redirects_to_dashboard(self, mock_secret, mock_creds, mock_post, mock_get):
        """Callback redirects to the dashboard URL."""
        state = _make_valid_state()
        mock_post.return_value = self._mock_token_response()

        mock_get.side_effect = [
            self._mock_user_response(),
            self._mock_repo_response(push=True),
        ]

        response = handle_github_callback({"code": "test-code", "state": state})

        assert response["statusCode"] == 302
        assert "api.aletheia.study/admin/metrics.html" in response["headers"]["Location"]
        assert response["headers"]["Cache-Control"] == "no-store"

    @patch("src.auth.github_oauth.requests.get")
    @patch("src.auth.github_oauth.requests.post")
    @patch("src.auth.github_oauth.get_github_credentials", return_value=FAKE_GITHUB_CREDENTIALS)
    @patch("src.auth.github_oauth.get_jwt_secret", return_value=FAKE_JWT_SECRET)
    def test_jwt_contains_admin_tier(self, mock_secret, mock_creds, mock_post, mock_get):
        """Issued JWT contains tier=admin and gh: prefixed user_id."""
        import jwt as pyjwt

        state = _make_valid_state()
        mock_post.return_value = self._mock_token_response()

        mock_get.side_effect = [
            self._mock_user_response(github_id=42, login="admin"),
            self._mock_repo_response(push=True),
        ]

        response = handle_github_callback({"code": "test-code", "state": state})

        location = response["headers"]["Location"]
        token = location.split("jwt=")[1]
        claims = pyjwt.decode(token, FAKE_JWT_SECRET, algorithms=["HS256"])
        assert claims["user_id"] == "gh:42"
        assert claims["tier"] == "admin"

    def test_github_error_response(self):
        """Callback handles GitHub-reported errors gracefully."""
        response = handle_github_callback({
            "error": "access_denied",
            "error_description": "User denied access",
        })

        assert response["statusCode"] == 200
        assert "Authorization Failed" in response["body"]

    @patch("src.auth.github_oauth.requests.post")
    @patch("src.auth.github_oauth.get_github_credentials", return_value=FAKE_GITHUB_CREDENTIALS)
    @patch("src.auth.github_oauth.get_jwt_secret", return_value=FAKE_JWT_SECRET)
    def test_token_exchange_failure(self, mock_secret, mock_creds, mock_post):
        """Callback handles failed token exchange."""
        state = _make_valid_state()

        error_resp = MagicMock()
        error_resp.status_code = 400
        error_resp.text = "Bad request"
        mock_post.return_value = error_resp

        response = handle_github_callback({"code": "bad-code", "state": state})

        assert response["statusCode"] == 200
        assert "Authentication Failed" in response["body"]


class TestGetGitHubCredentials:
    """Tests for get_github_credentials() caching."""

    def setup_method(self):
        """Reset cache before each test."""
        invalidate_credentials_cache()

    @patch("src.auth.github_oauth._get_secrets_client")
    def test_credentials_fetched_from_secrets_manager(self, mock_client_fn):
        """Credentials are fetched from Secrets Manager."""
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps(FAKE_GITHUB_CREDENTIALS),
        }
        mock_client_fn.return_value = mock_client

        creds = get_github_credentials()
        assert creds["client_id"] == FAKE_CLIENT_ID
        assert creds["client_secret"] == FAKE_CLIENT_SECRET

    @patch("src.auth.github_oauth._get_secrets_client")
    def test_credentials_cached(self, mock_client_fn):
        """Second call uses cached credentials, not Secrets Manager."""
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps(FAKE_GITHUB_CREDENTIALS),
        }
        mock_client_fn.return_value = mock_client

        get_github_credentials()
        get_github_credentials()

        # Should only call Secrets Manager once
        assert mock_client.get_secret_value.call_count == 1
