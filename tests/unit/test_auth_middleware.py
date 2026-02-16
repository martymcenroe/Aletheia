"""Unit tests for auth middleware.

Issue: #341 - Add JWT authentication to analysis endpoint with daily token cap.

Tests cover:
- T090: Auth middleware - missing header (REQ-1, REQ-9)
- T100: Auth middleware - invalid format (REQ-1, REQ-9)
- T110: Auth middleware - valid token (REQ-4)
- T130: Auth failure logging format (REQ-9)
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any
from unittest.mock import MagicMock, patch

import jwt as pyjwt
import pytest

from auth.auth_middleware import (
    _build_401_response,
    extract_token,
    log_auth_failure,
    require_auth,
)
from auth.jwt_service import (
    create_jwt,
    invalidate_secret_cache,
)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

TEST_SECRET = "test-secret-key-for-jwt-signing-341"
TEST_SECRET_ALT = "alternate-secret-key-for-rotation-341"
TEST_USER_ID = "u123"


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture(autouse=True)
def _clear_secret_cache():
    """Ensure secret cache is clean before each test."""
    invalidate_secret_cache()
    yield
    invalidate_secret_cache()


@pytest.fixture()
def valid_token() -> str:
    """Create a valid JWT for testing."""
    return create_jwt(TEST_USER_ID, TEST_SECRET, expiry_hours=24)


@pytest.fixture()
def expired_token() -> str:
    """Create an expired JWT for testing."""
    now = int(time.time())
    payload = {
        "user_id": TEST_USER_ID,
        "exp": now - 3600,  # Expired 1 hour ago
        "iat": now - 7200,  # Issued 2 hours ago
        "jti": "expired-jti-middleware-001",
    }
    return pyjwt.encode(payload, TEST_SECRET, algorithm="HS256")


@pytest.fixture()
def wrong_signature_token() -> str:
    """Create a JWT signed with a different secret."""
    return create_jwt(TEST_USER_ID, "wrong-secret-key")


def _make_event(auth_header: str | None = None) -> dict:
    """Build a minimal Lambda event with optional Authorization header."""
    event: dict[str, Any] = {
        "headers": {},
        "requestContext": {
            "http": {
                "sourceIp": "127.0.0.1",
                "path": "/analyze",
            }
        },
    }
    if auth_header is not None:
        event["headers"]["Authorization"] = auth_header
    return event


def _dummy_handler(event: dict, context: Any, **kwargs: Any) -> dict[str, Any]:
    """Dummy Lambda handler that returns 200 with user_id from event."""
    return {
        "statusCode": 200,
        "body": json.dumps({"user_id": event.get("auth_user_id")}),
    }


# --------------------------------------------------------------------------- #
# extract_token
# --------------------------------------------------------------------------- #


class TestExtractToken:
    """Unit tests for extract_token utility."""

    def test_extracts_bearer_token(self):
        """Standard 'Bearer <token>' format extracts the token."""
        event = _make_event("Bearer my-jwt-token")
        assert extract_token(event) == "my-jwt-token"

    def test_returns_none_for_missing_headers(self):
        """Event with no headers returns None."""
        event: dict[str, Any] = {"requestContext": {}}
        assert extract_token(event) is None

    def test_returns_none_for_empty_headers(self):
        """Event with empty headers dict returns None."""
        event = _make_event()
        assert extract_token(event) is None

    def test_returns_none_for_non_bearer_scheme(self):
        """Non-Bearer scheme (e.g. Basic) returns None."""
        event = _make_event("Basic dXNlcjpwYXNz")
        assert extract_token(event) is None

    def test_returns_none_for_missing_token_after_bearer(self):
        """'Bearer ' with no token returns None."""
        event = _make_event("Bearer ")
        assert extract_token(event) is None

    def test_returns_none_when_headers_not_dict(self):
        """Non-dict headers returns None."""
        event: dict[str, Any] = {"headers": "not-a-dict"}
        assert extract_token(event) is None

    def test_handles_lowercase_authorization_header(self):
        """API Gateway normalizes headers to lowercase."""
        event: dict[str, Any] = {
            "headers": {"authorization": "Bearer lowercase-token"},
            "requestContext": {},
        }
        assert extract_token(event) == "lowercase-token"

    def test_handles_mixed_case_authorization(self):
        """Supports both 'Authorization' and 'authorization' keys."""
        event: dict[str, Any] = {
            "headers": {"Authorization": "Bearer mixed-case-token"},
            "requestContext": {},
        }
        assert extract_token(event) == "mixed-case-token"

    def test_bearer_case_sensitive(self):
        """'bearer' (lowercase) does not match — must be 'Bearer'."""
        event = _make_event("bearer my-token")
        assert extract_token(event) is None

    def test_extra_whitespace_after_bearer(self):
        """Multiple spaces between Bearer and token are handled."""
        event = _make_event("Bearer   spaced-token")
        # The regex \s+ matches one or more spaces
        assert extract_token(event) == "spaced-token"


# --------------------------------------------------------------------------- #
# T090 - test_middleware_missing_header (REQ-1, REQ-9)
# --------------------------------------------------------------------------- #


class TestMiddlewareMissingHeader:
    """T090: Request without Authorization header returns 401 with logging."""

    def test_missing_header_returns_401(self):
        """REQ-1: No Authorization header → 401 Unauthorized."""
        protected = require_auth(_dummy_handler)
        event = _make_event()  # No auth header

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            response = protected(event, None)

        assert response["statusCode"] == 401

    def test_missing_header_response_body(self):
        """401 response body contains error message."""
        protected = require_auth(_dummy_handler)
        event = _make_event()

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            response = protected(event, None)

        body = json.loads(response["body"])
        assert "error" in body

    def test_missing_header_response_content_type(self):
        """401 response has JSON content type."""
        protected = require_auth(_dummy_handler)
        event = _make_event()

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            response = protected(event, None)

        assert response["headers"]["Content-Type"] == "application/json"

    def test_missing_header_logs_auth_failed(self, caplog):
        """REQ-9: Missing header logs action: 'auth_failed'."""
        protected = require_auth(_dummy_handler)
        event = _make_event()

        with (
            patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET),
            caplog.at_level(logging.WARNING, logger="auth.auth_middleware"),
        ):
            protected(event, None)

        # Find the auth_failed log entry
        auth_logs = [r for r in caplog.records if "auth_failed" in r.getMessage()]
        assert len(auth_logs) >= 1
        log_data = json.loads(auth_logs[0].getMessage())
        assert log_data["action"] == "auth_failed"
        assert log_data["reason"] == "missing_header"

    def test_missing_header_handler_not_called(self):
        """Handler is NOT invoked when header is missing."""
        handler = MagicMock(return_value={"statusCode": 200})
        protected = require_auth(handler)
        event = _make_event()

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            protected(event, None)

        handler.assert_not_called()

    def test_no_headers_key_in_event(self):
        """Event completely missing 'headers' key returns 401."""
        protected = require_auth(_dummy_handler)
        event: dict[str, Any] = {"requestContext": {"http": {}}}

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            response = protected(event, None)

        assert response["statusCode"] == 401

    def test_empty_event_returns_401(self):
        """Completely empty event dict returns 401."""
        protected = require_auth(_dummy_handler)
        event: dict[str, Any] = {}

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            response = protected(event, None)

        assert response["statusCode"] == 401


# --------------------------------------------------------------------------- #
# T100 - test_middleware_invalid_format (REQ-1, REQ-9)
# --------------------------------------------------------------------------- #


class TestMiddlewareInvalidFormat:
    """T100: Request with wrong auth format returns 401 with logging."""

    def test_basic_auth_returns_401(self):
        """REQ-1: 'Basic xyz' format → 401 Unauthorized."""
        protected = require_auth(_dummy_handler)
        event = _make_event("Basic dXNlcjpwYXNz")

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            response = protected(event, None)

        assert response["statusCode"] == 401

    def test_token_only_returns_401(self):
        """REQ-1: Token without 'Bearer' prefix → 401."""
        protected = require_auth(_dummy_handler)
        event = _make_event("just-a-token")

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            response = protected(event, None)

        assert response["statusCode"] == 401

    def test_empty_authorization_header(self):
        """Empty Authorization header → 401."""
        protected = require_auth(_dummy_handler)
        event = _make_event("")

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            response = protected(event, None)

        assert response["statusCode"] == 401

    def test_invalid_format_logs_reason(self, caplog):
        """REQ-9: Invalid format logs action: 'auth_failed' with reason."""
        protected = require_auth(_dummy_handler)
        event = _make_event("Basic xyz")

        with (
            patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET),
            caplog.at_level(logging.WARNING, logger="auth.auth_middleware"),
        ):
            protected(event, None)

        auth_logs = [r for r in caplog.records if "auth_failed" in r.getMessage()]
        assert len(auth_logs) >= 1
        log_data = json.loads(auth_logs[0].getMessage())
        assert log_data["action"] == "auth_failed"
        assert log_data["reason"] == "invalid_format"

    def test_invalid_format_handler_not_called(self):
        """Handler is NOT invoked when format is invalid."""
        handler = MagicMock(return_value={"statusCode": 200})
        protected = require_auth(handler)
        event = _make_event("Basic abc123")

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            protected(event, None)

        handler.assert_not_called()

    def test_bearer_lowercase_returns_401(self):
        """'bearer' (lowercase b) is not a valid Bearer scheme."""
        protected = require_auth(_dummy_handler)
        event = _make_event("bearer some-token")

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            response = protected(event, None)

        assert response["statusCode"] == 401


# --------------------------------------------------------------------------- #
# T110 - test_middleware_valid_token (REQ-4)
# --------------------------------------------------------------------------- #


class TestMiddlewareValidToken:
    """T110: Request with valid JWT proceeds to handler with user_id."""

    def test_valid_token_calls_handler(self, valid_token: str):
        """REQ-4: Valid JWT → handler is invoked."""
        handler = MagicMock(return_value={"statusCode": 200, "body": "{}"})
        protected = require_auth(handler)
        event = _make_event(f"Bearer {valid_token}")

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            protected(event, None)

        handler.assert_called_once()

    def test_valid_token_injects_user_id(self, valid_token: str):
        """REQ-4: user_id is injected into event['auth_user_id']."""
        protected = require_auth(_dummy_handler)
        event = _make_event(f"Bearer {valid_token}")

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            response = protected(event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["user_id"] == TEST_USER_ID

    def test_valid_token_passes_context(self, valid_token: str):
        """Context object is passed through to the handler."""
        mock_context = MagicMock()
        handler = MagicMock(return_value={"statusCode": 200})
        protected = require_auth(handler)
        event = _make_event(f"Bearer {valid_token}")

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            protected(event, mock_context)

        call_args = handler.call_args
        assert call_args[0][1] is mock_context

    def test_valid_token_returns_handler_response(self, valid_token: str):
        """Response from the handler is returned unchanged."""
        expected_response = {
            "statusCode": 200,
            "body": json.dumps({"result": "analysis-data"}),
        }
        handler = MagicMock(return_value=expected_response)
        protected = require_auth(handler)
        event = _make_event(f"Bearer {valid_token}")

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            response = protected(event, None)

        assert response == expected_response

    def test_valid_token_no_auth_failure_logged(self, valid_token: str, caplog):
        """No auth_failed log on successful authentication."""
        protected = require_auth(_dummy_handler)
        event = _make_event(f"Bearer {valid_token}")

        with (
            patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET),
            caplog.at_level(logging.WARNING, logger="auth.auth_middleware"),
        ):
            protected(event, None)

        auth_logs = [r for r in caplog.records if "auth_failed" in r.getMessage()]
        assert len(auth_logs) == 0

    def test_valid_token_with_lowercase_header(self, valid_token: str):
        """Lowercase 'authorization' header is supported (API Gateway normalization)."""
        protected = require_auth(_dummy_handler)
        event: dict[str, Any] = {
            "headers": {"authorization": f"Bearer {valid_token}"},
            "requestContext": {"http": {"sourceIp": "127.0.0.1", "path": "/analyze"}},
        }

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            response = protected(event, None)

        assert response["statusCode"] == 200

    def test_handler_kwargs_passed_through(self, valid_token: str):
        """Extra kwargs are forwarded to the handler."""
        handler = MagicMock(return_value={"statusCode": 200})
        protected = require_auth(handler)
        event = _make_event(f"Bearer {valid_token}")

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            protected(event, None, denylist={"bad-word"})

        call_kwargs = handler.call_args[1]
        assert call_kwargs["denylist"] == {"bad-word"}


# --------------------------------------------------------------------------- #
# Middleware - expired token
# --------------------------------------------------------------------------- #


class TestMiddlewareExpiredToken:
    """Expired JWT returns 401 and logs failure."""

    def test_expired_token_returns_401(self, expired_token: str):
        """REQ-3: Expired JWT → 401 Unauthorized."""
        protected = require_auth(_dummy_handler)
        event = _make_event(f"Bearer {expired_token}")

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            response = protected(event, None)

        assert response["statusCode"] == 401

    def test_expired_token_logs_reason(self, expired_token: str, caplog):
        """Expired JWT logs reason='token_expired'."""
        protected = require_auth(_dummy_handler)
        event = _make_event(f"Bearer {expired_token}")

        with (
            patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET),
            caplog.at_level(logging.WARNING, logger="auth.auth_middleware"),
        ):
            protected(event, None)

        auth_logs = [r for r in caplog.records if "auth_failed" in r.getMessage()]
        assert len(auth_logs) >= 1
        log_data = json.loads(auth_logs[0].getMessage())
        assert log_data["reason"] == "token_expired"

    def test_expired_token_handler_not_called(self, expired_token: str):
        """Handler is NOT invoked when token is expired."""
        handler = MagicMock(return_value={"statusCode": 200})
        protected = require_auth(handler)
        event = _make_event(f"Bearer {expired_token}")

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            protected(event, None)

        handler.assert_not_called()


# --------------------------------------------------------------------------- #
# Middleware - invalid signature
# --------------------------------------------------------------------------- #


class TestMiddlewareInvalidSignature:
    """Invalid signature returns 401 and logs failure."""

    def test_bad_signature_returns_401(self, wrong_signature_token: str):
        """REQ-2: Bad signature → 401 Unauthorized."""
        protected = require_auth(_dummy_handler)
        event = _make_event(f"Bearer {wrong_signature_token}")

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            response = protected(event, None)

        assert response["statusCode"] == 401

    def test_bad_signature_logs_reason(self, wrong_signature_token: str, caplog):
        """Bad signature logs reason='invalid_signature'."""
        protected = require_auth(_dummy_handler)
        event = _make_event(f"Bearer {wrong_signature_token}")

        with (
            patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET),
            caplog.at_level(logging.WARNING, logger="auth.auth_middleware"),
        ):
            protected(event, None)

        auth_logs = [r for r in caplog.records if "auth_failed" in r.getMessage()]
        assert len(auth_logs) >= 1
        log_data = json.loads(auth_logs[0].getMessage())
        assert log_data["reason"] == "invalid_signature"

    def test_bad_signature_handler_not_called(self, wrong_signature_token: str):
        """Handler is NOT invoked when signature is invalid."""
        handler = MagicMock(return_value={"statusCode": 200})
        protected = require_auth(handler)
        event = _make_event(f"Bearer {wrong_signature_token}")

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            protected(event, None)

        handler.assert_not_called()


# --------------------------------------------------------------------------- #
# Middleware - malformed token
# --------------------------------------------------------------------------- #


class TestMiddlewareMalformedToken:
    """Malformed token returns 401."""

    def test_malformed_token_returns_401(self):
        """REQ-2: Malformed token → 401 Unauthorized."""
        protected = require_auth(_dummy_handler)
        event = _make_event("Bearer not.a.jwt")

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            response = protected(event, None)

        assert response["statusCode"] == 401

    def test_malformed_token_handler_not_called(self):
        """Handler is NOT invoked with malformed token."""
        handler = MagicMock(return_value={"statusCode": 200})
        protected = require_auth(handler)
        event = _make_event("Bearer garbage-token")

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            protected(event, None)

        handler.assert_not_called()


# --------------------------------------------------------------------------- #
# Middleware - secret unavailable (Fail Closed)
# --------------------------------------------------------------------------- #


class TestMiddlewareSecretUnavailable:
    """Fail Closed: if Secrets Manager is unavailable, deny auth."""

    def test_secret_unavailable_returns_401(self, valid_token: str):
        """Secrets Manager failure → 401 (fail closed)."""
        protected = require_auth(_dummy_handler)
        event = _make_event(f"Bearer {valid_token}")

        with patch(
            "auth.auth_middleware.get_jwt_secret",
            side_effect=RuntimeError("Secrets Manager down"),
        ):
            response = protected(event, None)

        assert response["statusCode"] == 401

    def test_secret_unavailable_logs_reason(self, valid_token: str, caplog):
        """Secret unavailability logs reason='secret_unavailable'."""
        protected = require_auth(_dummy_handler)
        event = _make_event(f"Bearer {valid_token}")

        with (
            patch(
                "auth.auth_middleware.get_jwt_secret",
                side_effect=RuntimeError("Secrets Manager down"),
            ),
            caplog.at_level(logging.WARNING, logger="auth.auth_middleware"),
        ):
            protected(event, None)

        auth_logs = [r for r in caplog.records if "auth_failed" in r.getMessage()]
        assert len(auth_logs) >= 1
        log_data = json.loads(auth_logs[0].getMessage())
        assert log_data["reason"] == "secret_unavailable"

    def test_secret_unavailable_handler_not_called(self, valid_token: str):
        """Handler is NOT invoked when secret is unavailable."""
        handler = MagicMock(return_value={"statusCode": 200})
        protected = require_auth(handler)
        event = _make_event(f"Bearer {valid_token}")

        with patch(
            "auth.auth_middleware.get_jwt_secret",
            side_effect=RuntimeError("down"),
        ):
            protected(event, None)

        handler.assert_not_called()


# --------------------------------------------------------------------------- #
# Middleware - dual-secret rotation support
# --------------------------------------------------------------------------- #


class TestMiddlewareDualSecret:
    """Dual-secret rotation support in middleware."""

    def test_secondary_secret_validates_old_token(self):
        """Token signed with old (secondary) secret validates during rotation."""
        old_token = create_jwt(TEST_USER_ID, TEST_SECRET_ALT)
        protected = require_auth(_dummy_handler)
        event = _make_event(f"Bearer {old_token}")

        with (
            patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET),
            patch.dict(
                "os.environ",
                {"JWT_SECONDARY_SECRET": TEST_SECRET_ALT},
            ),
        ):
            response = protected(event, None)

        assert response["statusCode"] == 200

    def test_no_secondary_env_skips_dual_validation(self, valid_token: str):
        """Without JWT_SECONDARY_SECRET env var, only primary is tried."""
        protected = require_auth(_dummy_handler)
        event = _make_event(f"Bearer {valid_token}")

        with (
            patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET),
            patch.dict("os.environ", {}, clear=False),
        ):
            # Ensure JWT_SECONDARY_SECRET is not set
            import os

            os.environ.pop("JWT_SECONDARY_SECRET", None)
            response = protected(event, None)

        assert response["statusCode"] == 200


# --------------------------------------------------------------------------- #
# T130 - test_log_auth_failure_format (REQ-9)
# --------------------------------------------------------------------------- #


class TestLogAuthFailureFormat:
    """T130: Logs contain action: 'auth_failed' and reason field."""

    def test_log_contains_action_field(self, caplog):
        """Log entry has action: 'auth_failed'."""
        event = _make_event()

        with caplog.at_level(logging.WARNING, logger="auth.auth_middleware"):
            log_auth_failure(None, "test_reason", event)

        assert len(caplog.records) >= 1
        log_data = json.loads(caplog.records[-1].getMessage())
        assert log_data["action"] == "auth_failed"

    def test_log_contains_reason_field(self, caplog):
        """Log entry has the specified reason."""
        event = _make_event()

        with caplog.at_level(logging.WARNING, logger="auth.auth_middleware"):
            log_auth_failure(None, "missing_header", event)

        log_data = json.loads(caplog.records[-1].getMessage())
        assert log_data["reason"] == "missing_header"

    def test_log_contains_user_id(self, caplog):
        """Log entry includes user_id when provided."""
        event = _make_event()

        with caplog.at_level(logging.WARNING, logger="auth.auth_middleware"):
            log_auth_failure("user-456", "token_expired", event)

        log_data = json.loads(caplog.records[-1].getMessage())
        assert log_data["user_id"] == "user-456"

    def test_log_user_id_none_when_unknown(self, caplog):
        """Log entry has user_id: null when user is unknown."""
        event = _make_event()

        with caplog.at_level(logging.WARNING, logger="auth.auth_middleware"):
            log_auth_failure(None, "missing_header", event)

        log_data = json.loads(caplog.records[-1].getMessage())
        assert log_data["user_id"] is None

    def test_log_contains_source_ip(self, caplog):
        """Log entry includes source IP from request context."""
        event = _make_event()
        event["requestContext"]["http"]["sourceIp"] = "192.168.1.100"

        with caplog.at_level(logging.WARNING, logger="auth.auth_middleware"):
            log_auth_failure(None, "invalid_format", event)

        log_data = json.loads(caplog.records[-1].getMessage())
        assert log_data["source_ip"] == "192.168.1.100"

    def test_log_contains_path(self, caplog):
        """Log entry includes request path."""
        event = _make_event()
        event["requestContext"]["http"]["path"] = "/analyze"

        with caplog.at_level(logging.WARNING, logger="auth.auth_middleware"):
            log_auth_failure(None, "token_expired", event)

        log_data = json.loads(caplog.records[-1].getMessage())
        assert log_data["path"] == "/analyze"

    def test_log_is_valid_json(self, caplog):
        """Log message is valid JSON."""
        event = _make_event()

        with caplog.at_level(logging.WARNING, logger="auth.auth_middleware"):
            log_auth_failure("u789", "invalid_signature", event)

        raw_message = caplog.records[-1].getMessage()
        parsed = json.loads(raw_message)
        assert isinstance(parsed, dict)

    def test_log_sanitizes_user_id(self, caplog):
        """User ID with control characters is sanitized (log injection prevention)."""
        event = _make_event()
        malicious_user_id = "user\x00injected\nnewline"

        with caplog.at_level(logging.WARNING, logger="auth.auth_middleware"):
            log_auth_failure(malicious_user_id, "invalid_signature", event)

        log_data = json.loads(caplog.records[-1].getMessage())
        # Control characters should be stripped
        assert "\x00" not in log_data["user_id"]
        assert "\n" not in log_data["user_id"]

    def test_log_truncates_long_user_id(self, caplog):
        """Long user IDs are truncated to prevent log bloat."""
        event = _make_event()
        long_user_id = "x" * 500

        with caplog.at_level(logging.WARNING, logger="auth.auth_middleware"):
            log_auth_failure(long_user_id, "invalid_signature", event)

        log_data = json.loads(caplog.records[-1].getMessage())
        assert len(log_data["user_id"]) <= 128

    def test_log_handles_missing_request_context(self, caplog):
        """Gracefully handles event without requestContext."""
        event: dict[str, Any] = {"headers": {}}

        with caplog.at_level(logging.WARNING, logger="auth.auth_middleware"):
            log_auth_failure(None, "missing_header", event)

        log_data = json.loads(caplog.records[-1].getMessage())
        assert log_data["source_ip"] == "unknown"
        assert log_data["path"] == "unknown"

    def test_log_level_is_warning(self, caplog):
        """Auth failures are logged at WARNING level."""
        event = _make_event()

        with caplog.at_level(logging.WARNING, logger="auth.auth_middleware"):
            log_auth_failure(None, "missing_header", event)

        assert caplog.records[-1].levelno == logging.WARNING


# --------------------------------------------------------------------------- #
# _build_401_response
# --------------------------------------------------------------------------- #


class TestBuild401Response:
    """Unit tests for _build_401_response helper."""

    def test_status_code_is_401(self):
        """Response status code is 401."""
        response = _build_401_response("Unauthorized")
        assert response["statusCode"] == 401

    def test_content_type_is_json(self):
        """Response Content-Type is application/json."""
        response = _build_401_response("Unauthorized")
        assert response["headers"]["Content-Type"] == "application/json"

    def test_body_contains_error(self):
        """Response body contains the error message."""
        response = _build_401_response("Token expired")
        body = json.loads(response["body"])
        assert body["error"] == "Token expired"

    def test_body_is_valid_json(self):
        """Response body is valid JSON."""
        response = _build_401_response("test")
        parsed = json.loads(response["body"])
        assert isinstance(parsed, dict)


# --------------------------------------------------------------------------- #
# require_auth decorator properties
# --------------------------------------------------------------------------- #


class TestRequireAuthDecorator:
    """Decorator-level properties of require_auth."""

    def test_preserves_function_name(self):
        """@require_auth preserves the wrapped function's __name__."""
        protected = require_auth(_dummy_handler)
        assert protected.__name__ == "_dummy_handler"

    def test_preserves_function_docstring(self):
        """@require_auth preserves the wrapped function's docstring."""

        def handler_with_docs(event, context):
            """My handler docstring."""
            return {"statusCode": 200}

        protected = require_auth(handler_with_docs)
        assert protected.__doc__ == "My handler docstring."

    def test_is_callable(self):
        """Decorated handler is callable."""
        protected = require_auth(_dummy_handler)
        assert callable(protected)
