"""Integration tests for full auth flow.

Issue: #341 - Add JWT authentication to analysis endpoint with daily token cap.

Tests the end-to-end auth flow using mocked DynamoDB (via unittest.mock):
- Token issuance with cap enforcement (JWT + DynamoDB interaction)
- JWT validation through the middleware (full stack)
- Daily cap reset at UTC midnight boundary
- Admin cap adjustment and its effect on issuance
- Concurrent token issuance under cap pressure
- Full round-trip: issue JWT via auth Lambda, then validate via middleware

Covers requirements: REQ-1 through REQ-10 in integration context.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import jwt as pyjwt
import pytest
from botocore.exceptions import ClientError

# Ensure src/ is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from auth.auth_middleware import (
    require_auth,
)
from auth.jwt_service import (
    create_jwt,
    invalidate_secret_cache,
    validate_jwt,
)
from auth.token_cap_service import (
    CAP_CONFIG_PK,
    CAP_CONFIG_SK,
    COUNTER_SK_PREFIX,
    DEFAULT_DAILY_CAP,
    check_and_increment_cap,
    get_current_cap,
    get_today_key,
    set_daily_cap,
)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

TEST_SECRET = "integration-test-secret-key-for-jwt-341"
TEST_SECRET_ALT = "integration-test-secondary-secret-341"
TEST_USER_ID = "integration-user-001"
TOKEN_CAP_TABLE = "aletheia-token-cap-integration"


# --------------------------------------------------------------------------- #
# Mock DynamoDB table fixture
# --------------------------------------------------------------------------- #


class MockDynamoDBTable:
    """In-memory mock of a DynamoDB Table resource for integration tests.

    Uses composite (PK, SK) keys matching the actual token_cap_service.
    Supports get_item, put_item, update_item, and scan operations.
    """

    def __init__(self):
        self._items: dict[tuple[str, str], dict] = {}

    def _make_key(self, key_dict: dict) -> tuple[str, str]:
        return (key_dict.get("PK", ""), key_dict.get("SK", ""))

    def get_item(self, **kwargs) -> dict:
        key = self._make_key(kwargs.get("Key", {}))
        item = self._items.get(key)
        if item:
            return {"Item": dict(item)}
        return {}

    def put_item(self, **kwargs) -> dict:
        item = kwargs.get("Item", {})
        key = (item.get("PK", ""), item.get("SK", ""))
        self._items[key] = dict(item)
        return {}

    def update_item(self, **kwargs) -> dict:
        key = self._make_key(kwargs.get("Key", {}))
        condition = kwargs.get("ConditionExpression", "")
        expr_values = kwargs.get("ExpressionAttributeValues", {})
        return_values = kwargs.get("ReturnValues", "NONE")

        item = self._items.get(key, {})

        # Evaluate condition: "attribute_not_exists(tokens_issued) OR tokens_issued < :cap"
        cap_value = expr_values.get(":cap", 0)
        current_tokens = item.get("tokens_issued", 0)

        if condition and "attribute_not_exists" in condition:
            if "tokens_issued" in item and current_tokens >= cap_value:
                raise ClientError(
                    {
                        "Error": {
                            "Code": "ConditionalCheckFailedException",
                            "Message": "The conditional request failed",
                        }
                    },
                    "UpdateItem",
                )

        # Apply: SET tokens_issued = if_not_exists(tokens_issued, :zero) + :one
        inc_value = expr_values.get(":one", expr_values.get(":inc", 1))
        zero_value = expr_values.get(":zero", 0)

        if "tokens_issued" not in item:
            new_tokens = zero_value + inc_value
        else:
            new_tokens = item["tokens_issued"] + inc_value

        item["PK"] = key[0]
        item["SK"] = key[1]
        item["tokens_issued"] = new_tokens

        if ":cap" in expr_values:
            item["daily_cap"] = expr_values[":cap"]
        if ":ttl_val" in expr_values:
            item["ttl"] = expr_values[":ttl_val"]

        self._items[key] = item

        if return_values == "ALL_NEW":
            return {"Attributes": dict(item)}
        return {}

    def scan(self, **kwargs) -> dict:
        items = list(self._items.values())
        return {"Items": items}

    def clear(self):
        self._items.clear()


@pytest.fixture()
def mock_table():
    """Provide a mock DynamoDB table via patched _get_dynamodb_resource."""
    table = MockDynamoDBTable()
    mock_resource = MagicMock()
    mock_resource.Table.return_value = table
    with patch("auth.token_cap_service._get_dynamodb_resource", return_value=mock_resource):
        yield table


@pytest.fixture(autouse=True)
def _reset_auth_state():
    """Reset cached secrets before each test."""
    invalidate_secret_cache()
    yield
    invalidate_secret_cache()


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _make_event(auth_header: str | None = None) -> dict[str, Any]:
    """Build a minimal Lambda event with optional Authorization header."""
    event: dict[str, Any] = {
        "headers": {},
        "requestContext": {
            "http": {
                "sourceIp": "10.0.0.1",
                "path": "/analyze",
            }
        },
    }
    if auth_header is not None:
        event["headers"]["Authorization"] = auth_header
    return event


def _dummy_handler(event: dict, context: Any, **kwargs: Any) -> dict[str, Any]:
    """Dummy Lambda handler returning 200 with user_id from event."""
    return {
        "statusCode": 200,
        "body": json.dumps({
            "user_id": event.get("auth_user_id"),
            "analysis": "test-result",
        }),
    }


# --------------------------------------------------------------------------- #
# Integration: JWT issuance + cap enforcement via mock DynamoDB
# --------------------------------------------------------------------------- #


class TestTokenIssuanceWithCap:
    """Integration: JWT issuance with DynamoDB-backed daily cap."""

    def test_issue_tokens_up_to_cap(self, mock_table):
        """REQ-5, REQ-7: Issue tokens up to cap, then deny.

        Uses mock DynamoDB to verify atomic counter behavior
        across multiple sequential issuances.
        """
        # Set cap to 3 for fast test
        set_daily_cap(TOKEN_CAP_TABLE, 3, "test-admin")

        issued_jwts = []

        # Issue 3 tokens (should all succeed)
        for i in range(3):
            allowed, count = check_and_increment_cap(TOKEN_CAP_TABLE)
            assert allowed is True, f"Token {i+1} should be allowed"
            assert count == i + 1

            jwt_token = create_jwt(f"user-{i}", TEST_SECRET)
            issued_jwts.append(jwt_token)

        # 4th token should be denied (REQ-7)
        allowed, count = check_and_increment_cap(TOKEN_CAP_TABLE)
        assert allowed is False

        # Verify all issued JWTs are valid
        for jwt_token in issued_jwts:
            result = validate_jwt(jwt_token, TEST_SECRET)
            assert result["success"] is True

    def test_cap_default_is_20(self, mock_table):
        """REQ-7: Default cap is 20 when no CONFIG record exists."""
        cap = get_current_cap(TOKEN_CAP_TABLE)
        assert cap == DEFAULT_DAILY_CAP
        assert cap == 20

    def test_first_token_of_day_creates_counter(self, mock_table):
        """First token issuance of the day creates the counter record."""
        set_daily_cap(TOKEN_CAP_TABLE, 10, "test-admin")

        allowed, count = check_and_increment_cap(TOKEN_CAP_TABLE)
        assert allowed is True
        assert count == 1

        # Verify record was created in mock DynamoDB
        date_key = get_today_key()
        counter_sk = f"{COUNTER_SK_PREFIX}{date_key}"
        response = mock_table.get_item(Key={"PK": "COUNTER", "SK": counter_sk})
        assert "Item" in response
        assert response["Item"]["tokens_issued"] == 1

    def test_counter_has_ttl_attribute(self, mock_table):
        """Counter records include TTL for automatic DynamoDB cleanup (7-day)."""
        set_daily_cap(TOKEN_CAP_TABLE, 10, "test-admin")
        check_and_increment_cap(TOKEN_CAP_TABLE)

        date_key = get_today_key()
        counter_sk = f"{COUNTER_SK_PREFIX}{date_key}"

        response = mock_table.get_item(Key={"PK": "COUNTER", "SK": counter_sk})
        item = response["Item"]
        assert "ttl" in item

        ttl_value = item["ttl"]
        # TTL should be ~7 days from now
        expected_ttl = int(time.time()) + (7 * 86400)
        # Allow 60s tolerance
        assert abs(ttl_value - expected_ttl) < 60


# --------------------------------------------------------------------------- #
# Integration: Admin cap adjustment + immediate effect
# --------------------------------------------------------------------------- #


class TestAdminCapAdjustment:
    """Integration: Admin cap changes take effect immediately (REQ-8)."""

    def test_set_cap_then_enforce(self, mock_table):
        """REQ-8: Admin sets cap via CLI, issuance respects new cap immediately."""
        # Set low cap
        result = set_daily_cap(TOKEN_CAP_TABLE, 2, "admin-integration")
        assert result is True

        # Verify cap is readable
        cap = get_current_cap(TOKEN_CAP_TABLE)
        assert cap == 2

        # Issue 2 tokens
        for _ in range(2):
            allowed, _ = check_and_increment_cap(TOKEN_CAP_TABLE)
            assert allowed is True

        # 3rd token denied
        allowed, count = check_and_increment_cap(TOKEN_CAP_TABLE)
        assert allowed is False

    def test_increase_cap_mid_day(self, mock_table):
        """REQ-8: Increasing cap mid-day allows more tokens without redeployment."""
        # Start with cap of 2
        set_daily_cap(TOKEN_CAP_TABLE, 2, "admin-integration")

        # Issue 2 tokens (exhaust cap)
        for _ in range(2):
            check_and_increment_cap(TOKEN_CAP_TABLE)

        # Verify cap reached
        allowed, _ = check_and_increment_cap(TOKEN_CAP_TABLE)
        assert allowed is False

        # Admin increases cap to 5
        set_daily_cap(TOKEN_CAP_TABLE, 5, "admin-integration")

        # Now more tokens should be allowed
        allowed, count = check_and_increment_cap(TOKEN_CAP_TABLE)
        assert allowed is True
        assert count == 3

    def test_decrease_cap_below_current_count(self, mock_table):
        """Decreasing cap below current count blocks further issuance."""
        # Start with cap of 10, issue 5 tokens
        set_daily_cap(TOKEN_CAP_TABLE, 10, "admin-integration")
        for _ in range(5):
            check_and_increment_cap(TOKEN_CAP_TABLE)

        # Decrease cap to 3 (below current count of 5)
        set_daily_cap(TOKEN_CAP_TABLE, 3, "admin-integration")

        # Next token should be denied
        allowed, count = check_and_increment_cap(TOKEN_CAP_TABLE)
        assert allowed is False

    def test_admin_audit_trail(self, mock_table):
        """REQ-8: Admin changes include audit trail (admin_id, timestamp)."""
        set_daily_cap(TOKEN_CAP_TABLE, 50, "admin-jane-doe")

        response = mock_table.get_item(Key={"PK": CAP_CONFIG_PK, "SK": CAP_CONFIG_SK})
        item = response["Item"]

        assert item["updated_by"] == "admin-jane-doe"
        assert "updated_at" in item
        # Timestamp should be a valid ISO format
        assert "T" in item["updated_at"]


# --------------------------------------------------------------------------- #
# Integration: Full round-trip (issue JWT -> validate via middleware)
# --------------------------------------------------------------------------- #


class TestFullAuthRoundTrip:
    """Integration: End-to-end JWT issuance and validation."""

    def test_issue_then_validate_via_middleware(self, mock_table):
        """REQ-4, REQ-5: Issue JWT, then validate it through auth middleware.

        Simulates the full flow:
        1. Check cap and increment (Auth Lambda)
        2. Create JWT (Auth Lambda)
        3. Validate JWT via require_auth decorator (Analysis Lambda)
        """
        set_daily_cap(TOKEN_CAP_TABLE, 10, "test-admin")

        # Step 1: Check cap (simulating Auth Lambda)
        allowed, count = check_and_increment_cap(TOKEN_CAP_TABLE)
        assert allowed is True

        # Step 2: Create JWT (simulating Auth Lambda)
        jwt_token = create_jwt(TEST_USER_ID, TEST_SECRET, expiry_hours=24)
        assert isinstance(jwt_token, str)
        assert len(jwt_token) > 0

        # Step 3: Validate JWT via middleware (simulating Analysis Lambda)
        protected = require_auth(_dummy_handler)
        event = _make_event(f"Bearer {jwt_token}")

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            response = protected(event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["user_id"] == TEST_USER_ID
        assert body["analysis"] == "test-result"

    def test_expired_jwt_rejected_by_middleware(self, mock_table):
        """REQ-3: Expired JWT is rejected even if cap allows issuance."""
        set_daily_cap(TOKEN_CAP_TABLE, 10, "test-admin")

        # Issue a token that's already expired
        now = int(time.time())
        payload = {
            "user_id": TEST_USER_ID,
            "exp": now - 3600,  # Expired 1 hour ago
            "iat": now - 7200,
            "jti": "expired-integration-test-001",
        }
        expired_jwt = pyjwt.encode(payload, TEST_SECRET, algorithm="HS256")

        # Try to use it via middleware
        protected = require_auth(_dummy_handler)
        event = _make_event(f"Bearer {expired_jwt}")

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            response = protected(event, None)

        assert response["statusCode"] == 401

    def test_invalid_signature_rejected_by_middleware(self, mock_table):
        """REQ-2: JWT signed with wrong key is rejected."""
        set_daily_cap(TOKEN_CAP_TABLE, 10, "test-admin")

        # Issue JWT with different secret
        bad_jwt = create_jwt(TEST_USER_ID, "wrong-secret-entirely")

        protected = require_auth(_dummy_handler)
        event = _make_event(f"Bearer {bad_jwt}")

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            response = protected(event, None)

        assert response["statusCode"] == 401

    def test_no_auth_header_rejected(self):
        """REQ-1: Request without Authorization header returns 401."""
        protected = require_auth(_dummy_handler)
        event = _make_event()

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            response = protected(event, None)

        assert response["statusCode"] == 401

    def test_malformed_token_rejected(self):
        """REQ-2: Malformed token returns 401."""
        protected = require_auth(_dummy_handler)
        event = _make_event("Bearer not-a-real-jwt-token")

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            response = protected(event, None)

        assert response["statusCode"] == 401

    def test_cap_exhausted_blocks_new_issuance_but_existing_jwt_still_valid(
        self, mock_table
    ):
        """REQ-4, REQ-7: Existing valid JWTs work even after cap is exhausted.

        The cap only limits new token issuance, not validation of
        previously issued tokens.
        """
        set_daily_cap(TOKEN_CAP_TABLE, 1, "test-admin")

        # Issue one token (exhausts cap)
        allowed, _ = check_and_increment_cap(TOKEN_CAP_TABLE)
        assert allowed is True
        jwt_token = create_jwt(TEST_USER_ID, TEST_SECRET)

        # Cap is now exhausted
        allowed, _ = check_and_increment_cap(TOKEN_CAP_TABLE)
        assert allowed is False

        # But the previously issued JWT is still valid for analysis
        protected = require_auth(_dummy_handler)
        event = _make_event(f"Bearer {jwt_token}")

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            response = protected(event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["user_id"] == TEST_USER_ID


# --------------------------------------------------------------------------- #
# Integration: JWT claims verification (REQ-6)
# --------------------------------------------------------------------------- #


class TestJWTClaimsIntegration:
    """Integration: JWT claims are correct end-to-end (REQ-6)."""

    def test_jwt_contains_all_required_claims(self, mock_table):
        """REQ-6: JWT contains user_id, exp (24h), iat, and jti."""
        set_daily_cap(TOKEN_CAP_TABLE, 10, "test-admin")
        check_and_increment_cap(TOKEN_CAP_TABLE)

        now = int(time.time())
        jwt_token = create_jwt(TEST_USER_ID, TEST_SECRET, expiry_hours=24)

        # Decode without verification to inspect claims
        payload = pyjwt.decode(jwt_token, TEST_SECRET, algorithms=["HS256"])

        assert payload["user_id"] == TEST_USER_ID
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload

        # exp should be ~24h from now
        exp_delta = payload["exp"] - now
        assert 23 * 3600 <= exp_delta <= 25 * 3600

        # iat should be approximately now
        assert abs(payload["iat"] - now) < 5

        # jti should be a non-empty string (UUID format)
        assert isinstance(payload["jti"], str)
        assert len(payload["jti"]) > 0

    def test_each_jwt_has_unique_jti(self, mock_table):
        """REQ-6: Each JWT has a unique jti for tracking."""
        set_daily_cap(TOKEN_CAP_TABLE, 10, "test-admin")

        jtis = set()
        for i in range(5):
            check_and_increment_cap(TOKEN_CAP_TABLE)
            jwt_token = create_jwt(f"user-{i}", TEST_SECRET)
            payload = pyjwt.decode(jwt_token, TEST_SECRET, algorithms=["HS256"])
            jtis.add(payload["jti"])

        assert len(jtis) == 5, "All JTIs should be unique"


# --------------------------------------------------------------------------- #
# Integration: Dual-secret rotation (REQ-10)
# --------------------------------------------------------------------------- #


class TestDualSecretRotationIntegration:
    """Integration: Secret rotation with dual-secret support (REQ-10)."""

    def test_rotation_flow_old_jwt_still_valid(self, mock_table):
        """REQ-10: During rotation, JWTs signed with old secret still validate.

        Simulates:
        1. Issue JWT with old secret
        2. Rotate to new secret (old becomes secondary)
        3. Validate old JWT via middleware with dual-secret
        """
        set_daily_cap(TOKEN_CAP_TABLE, 10, "test-admin")
        check_and_increment_cap(TOKEN_CAP_TABLE)

        # Issue JWT with the "old" secret
        old_jwt = create_jwt(TEST_USER_ID, TEST_SECRET_ALT)

        # Now the primary is TEST_SECRET, secondary is TEST_SECRET_ALT
        protected = require_auth(_dummy_handler)
        event = _make_event(f"Bearer {old_jwt}")

        with (
            patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET),
            patch.dict(
                "os.environ",
                {"JWT_SECONDARY_SECRET": TEST_SECRET_ALT},
            ),
        ):
            response = protected(event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["user_id"] == TEST_USER_ID

    def test_rotation_new_jwt_validates_with_primary(self, mock_table):
        """REQ-10: New JWTs signed with primary secret validate normally."""
        set_daily_cap(TOKEN_CAP_TABLE, 10, "test-admin")
        check_and_increment_cap(TOKEN_CAP_TABLE)

        new_jwt = create_jwt(TEST_USER_ID, TEST_SECRET)

        protected = require_auth(_dummy_handler)
        event = _make_event(f"Bearer {new_jwt}")

        with (
            patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET),
            patch.dict(
                "os.environ",
                {"JWT_SECONDARY_SECRET": TEST_SECRET_ALT},
            ),
        ):
            response = protected(event, None)

        assert response["statusCode"] == 200

    def test_unknown_secret_rejected_even_with_dual(self, mock_table):
        """REQ-10: JWT signed with unknown secret rejected even with dual-secret."""
        check_and_increment_cap(TOKEN_CAP_TABLE)

        unknown_jwt = create_jwt(TEST_USER_ID, "completely-unknown-key")

        protected = require_auth(_dummy_handler)
        event = _make_event(f"Bearer {unknown_jwt}")

        with (
            patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET),
            patch.dict(
                "os.environ",
                {"JWT_SECONDARY_SECRET": TEST_SECRET_ALT},
            ),
        ):
            response = protected(event, None)

        assert response["statusCode"] == 401


# --------------------------------------------------------------------------- #
# Integration: Auth failure logging (REQ-9)
# --------------------------------------------------------------------------- #


class TestAuthFailureLoggingIntegration:
    """Integration: All auth failures logged with structured data (REQ-9)."""

    def test_missing_header_logged(self, caplog):
        """REQ-9: Missing auth header logged with action and reason."""
        protected = require_auth(_dummy_handler)
        event = _make_event()

        with (
            patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET),
            caplog.at_level(logging.WARNING, logger="auth.auth_middleware"),
        ):
            response = protected(event, None)

        assert response["statusCode"] == 401

        auth_logs = [r for r in caplog.records if "auth_failed" in r.getMessage()]
        assert len(auth_logs) >= 1
        log_data = json.loads(auth_logs[0].getMessage())
        assert log_data["action"] == "auth_failed"
        assert log_data["reason"] == "missing_header"

    def test_invalid_format_logged(self, caplog):
        """REQ-9: Invalid auth format logged with action and reason."""
        protected = require_auth(_dummy_handler)
        event = _make_event("Basic dXNlcjpwYXNz")

        with (
            patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET),
            caplog.at_level(logging.WARNING, logger="auth.auth_middleware"),
        ):
            response = protected(event, None)

        assert response["statusCode"] == 401

        auth_logs = [r for r in caplog.records if "auth_failed" in r.getMessage()]
        assert len(auth_logs) >= 1
        log_data = json.loads(auth_logs[0].getMessage())
        assert log_data["action"] == "auth_failed"
        assert log_data["reason"] == "invalid_format"

    def test_expired_token_logged(self, caplog):
        """REQ-9: Expired token logged with reason 'token_expired'."""
        now = int(time.time())
        expired_jwt = pyjwt.encode(
            {
                "user_id": TEST_USER_ID,
                "exp": now - 3600,
                "iat": now - 7200,
                "jti": "expired-log-test",
            },
            TEST_SECRET,
            algorithm="HS256",
        )

        protected = require_auth(_dummy_handler)
        event = _make_event(f"Bearer {expired_jwt}")

        with (
            patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET),
            caplog.at_level(logging.WARNING, logger="auth.auth_middleware"),
        ):
            response = protected(event, None)

        assert response["statusCode"] == 401

        auth_logs = [r for r in caplog.records if "auth_failed" in r.getMessage()]
        assert len(auth_logs) >= 1
        log_data = json.loads(auth_logs[0].getMessage())
        assert log_data["action"] == "auth_failed"
        assert log_data["reason"] == "token_expired"

    def test_invalid_signature_logged(self, caplog):
        """REQ-9: Invalid signature logged with reason 'invalid_signature'."""
        bad_jwt = create_jwt(TEST_USER_ID, "wrong-signing-key")

        protected = require_auth(_dummy_handler)
        event = _make_event(f"Bearer {bad_jwt}")

        with (
            patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET),
            caplog.at_level(logging.WARNING, logger="auth.auth_middleware"),
        ):
            response = protected(event, None)

        assert response["statusCode"] == 401

        auth_logs = [r for r in caplog.records if "auth_failed" in r.getMessage()]
        assert len(auth_logs) >= 1
        log_data = json.loads(auth_logs[0].getMessage())
        assert log_data["action"] == "auth_failed"
        assert log_data["reason"] == "invalid_signature"

    def test_successful_auth_not_logged(self, caplog):
        """REQ-9: Successful auth does NOT produce auth_failed logs."""
        jwt_token = create_jwt(TEST_USER_ID, TEST_SECRET)

        protected = require_auth(_dummy_handler)
        event = _make_event(f"Bearer {jwt_token}")

        with (
            patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET),
            caplog.at_level(logging.WARNING, logger="auth.auth_middleware"),
        ):
            response = protected(event, None)

        assert response["statusCode"] == 200

        auth_logs = [r for r in caplog.records if "auth_failed" in r.getMessage()]
        assert len(auth_logs) == 0

    def test_log_contains_source_ip_and_path(self, caplog):
        """REQ-9: Failure logs include source IP and request path."""
        protected = require_auth(_dummy_handler)
        event = _make_event()
        event["requestContext"]["http"]["sourceIp"] = "192.168.1.42"
        event["requestContext"]["http"]["path"] = "/analyze"

        with (
            patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET),
            caplog.at_level(logging.WARNING, logger="auth.auth_middleware"),
        ):
            protected(event, None)

        auth_logs = [r for r in caplog.records if "auth_failed" in r.getMessage()]
        log_data = json.loads(auth_logs[0].getMessage())
        assert log_data["source_ip"] == "192.168.1.42"
        assert log_data["path"] == "/analyze"


# --------------------------------------------------------------------------- #
# Integration: Secrets Manager fail closed
# --------------------------------------------------------------------------- #


class TestFailClosedIntegration:
    """Integration: System fails closed when dependencies unavailable."""

    def test_secrets_manager_down_returns_401(self):
        """Fail closed: Secrets Manager unavailable -> 401 (not 500)."""
        jwt_token = create_jwt(TEST_USER_ID, TEST_SECRET)

        protected = require_auth(_dummy_handler)
        event = _make_event(f"Bearer {jwt_token}")

        with patch(
            "auth.auth_middleware.get_jwt_secret",
            side_effect=RuntimeError("Secrets Manager unavailable"),
        ):
            response = protected(event, None)

        assert response["statusCode"] == 401
        body = json.loads(response["body"])
        assert "error" in body

    def test_secrets_manager_down_logged(self, caplog):
        """Fail closed: Secrets Manager failure is logged."""
        jwt_token = create_jwt(TEST_USER_ID, TEST_SECRET)

        protected = require_auth(_dummy_handler)
        event = _make_event(f"Bearer {jwt_token}")

        with (
            patch(
                "auth.auth_middleware.get_jwt_secret",
                side_effect=RuntimeError("SM down"),
            ),
            caplog.at_level(logging.WARNING, logger="auth.auth_middleware"),
        ):
            response = protected(event, None)

        assert response["statusCode"] == 401

        auth_logs = [r for r in caplog.records if "auth_failed" in r.getMessage()]
        assert len(auth_logs) >= 1
        log_data = json.loads(auth_logs[0].getMessage())
        assert log_data["reason"] == "secret_unavailable"


# --------------------------------------------------------------------------- #
# Integration: Token cap with concurrent-like access patterns
# --------------------------------------------------------------------------- #


class TestCapConcurrencyIntegration:
    """Integration: Cap enforcement under concurrent-like access."""

    def test_sequential_issuance_at_boundary(self, mock_table):
        """REQ-7: Sequential issuance at exact cap boundary.

        Issue exactly cap tokens, verify the cap+1 request is denied.
        """
        cap = 5
        set_daily_cap(TOKEN_CAP_TABLE, cap, "test-admin")

        results = []
        for i in range(cap + 2):
            allowed, count = check_and_increment_cap(TOKEN_CAP_TABLE)
            results.append((allowed, count))

        # First 'cap' should succeed
        for i in range(cap):
            assert results[i][0] is True, f"Token {i+1} should be allowed"
            assert results[i][1] == i + 1

        # cap+1 and cap+2 should be denied
        assert results[cap][0] is False
        assert results[cap + 1][0] is False

    def test_cap_persists_across_function_calls(self, mock_table):
        """Counter persists in DynamoDB across separate function invocations."""
        set_daily_cap(TOKEN_CAP_TABLE, 5, "test-admin")

        # First "invocation" - issue 3 tokens
        for _ in range(3):
            check_and_increment_cap(TOKEN_CAP_TABLE)

        # Counter should continue from count=3
        allowed, count = check_and_increment_cap(TOKEN_CAP_TABLE)
        assert allowed is True
        assert count == 4


# --------------------------------------------------------------------------- #
# Integration: Auth Lambda token exchange simulation
# --------------------------------------------------------------------------- #


class TestAuthLambdaTokenExchangeIntegration:
    """Integration: Simulate Auth Lambda token exchange with cap + JWT."""

    def test_token_exchange_flow_simulation(self, mock_table):
        """Simulate the full token exchange flow from LLD S2.5.

        1. LinkedIn validation (mocked)
        2. Check daily cap (mock DynamoDB)
        3. Generate JWT (real)
        4. Validate JWT (real)
        """
        set_daily_cap(TOKEN_CAP_TABLE, 10, "test-admin")

        # Step 1: Simulate LinkedIn validation result
        user_id = "linkedin-sub-12345"

        # Step 2: Check cap (mock DynamoDB)
        allowed, count = check_and_increment_cap(TOKEN_CAP_TABLE)
        assert allowed is True
        assert count == 1

        # Step 3: Generate JWT
        jwt_token = create_jwt(user_id, TEST_SECRET, expiry_hours=24)
        assert isinstance(jwt_token, str)

        # Step 4: Validate JWT (as the Analysis Lambda would)
        result = validate_jwt(jwt_token, TEST_SECRET)
        assert result["success"] is True
        assert result["user_id"] == user_id

    def test_token_exchange_denied_when_cap_exceeded(self, mock_table):
        """Simulate token exchange denial when cap is exceeded (503)."""
        set_daily_cap(TOKEN_CAP_TABLE, 1, "test-admin")

        # First exchange succeeds
        allowed, _ = check_and_increment_cap(TOKEN_CAP_TABLE)
        assert allowed is True

        # Second exchange should fail (simulating 503 response)
        allowed, count = check_and_increment_cap(TOKEN_CAP_TABLE)
        assert allowed is False

        # In the real Auth Lambda, this would return:
        # {"statusCode": 503, "body": "Daily token limit exceeded..."}


# --------------------------------------------------------------------------- #
# Integration: Daily cap reset boundary
# --------------------------------------------------------------------------- #


class TestDailyCapResetIntegration:
    """Integration: Cap resets at UTC midnight boundary."""

    def test_different_date_keys_are_independent(self, mock_table):
        """Counters for different dates are independent (simulates day rollover)."""
        set_daily_cap(TOKEN_CAP_TABLE, 2, "test-admin")

        # Manually seed "yesterday" as exhausted
        yesterday_sk = f"{COUNTER_SK_PREFIX}2025-01-01"
        mock_table.put_item(
            Item={
                "PK": "COUNTER",
                "SK": yesterday_sk,
                "tokens_issued": 2,
            },
        )

        # Today's counter should start fresh
        today_key = get_today_key()
        assert today_key != "2025-01-01"

        # Should be allowed (new day)
        allowed, count = check_and_increment_cap(TOKEN_CAP_TABLE)
        assert allowed is True
        assert count == 1

    def test_get_today_key_returns_utc_date(self):
        """get_today_key returns a valid YYYY-MM-DD UTC date string."""
        key = get_today_key()
        assert len(key) == 10
        assert key[4] == "-"
        assert key[7] == "-"

        # Parse to verify it's a valid date
        from datetime import datetime

        parsed = datetime.strptime(key, "%Y-%m-%d")
        assert parsed is not None


# --------------------------------------------------------------------------- #
# Integration: Middleware + handler interaction
# --------------------------------------------------------------------------- #


class TestMiddlewareHandlerIntegration:
    """Integration: Middleware correctly passes data to handler."""

    def test_user_id_injected_into_event(self):
        """REQ-4: auth_user_id is injected into event for downstream handler."""
        jwt_token = create_jwt(TEST_USER_ID, TEST_SECRET)

        captured_event = {}

        def capturing_handler(event, context, **kwargs):
            captured_event.update(event)
            return {"statusCode": 200, "body": "{}"}

        protected = require_auth(capturing_handler)
        event = _make_event(f"Bearer {jwt_token}")

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            response = protected(event, None)

        assert response["statusCode"] == 200
        assert captured_event.get("auth_user_id") == TEST_USER_ID

    def test_kwargs_passed_through_to_handler(self):
        """Extra kwargs (like denylist) are forwarded through middleware."""
        jwt_token = create_jwt(TEST_USER_ID, TEST_SECRET)

        captured_kwargs = {}

        def capturing_handler(event, context, **kwargs):
            captured_kwargs.update(kwargs)
            return {"statusCode": 200, "body": "{}"}

        protected = require_auth(capturing_handler)
        event = _make_event(f"Bearer {jwt_token}")

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            protected(event, None, denylist={"blocked-term"})

        assert captured_kwargs.get("denylist") == {"blocked-term"}

    def test_context_passed_through_to_handler(self):
        """Lambda context object is forwarded through middleware."""
        jwt_token = create_jwt(TEST_USER_ID, TEST_SECRET)
        mock_context = MagicMock()
        mock_context.aws_request_id = "test-req-integration"

        captured_context = {}

        def capturing_handler(event, context, **kwargs):
            captured_context["ctx"] = context
            return {"statusCode": 200, "body": "{}"}

        protected = require_auth(capturing_handler)
        event = _make_event(f"Bearer {jwt_token}")

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            protected(event, mock_context)

        assert captured_context["ctx"] is mock_context
        assert captured_context["ctx"].aws_request_id == "test-req-integration"

    def test_handler_response_returned_unchanged(self):
        """Handler response passes through middleware unchanged."""
        jwt_token = create_jwt(TEST_USER_ID, TEST_SECRET)
        expected = {
            "statusCode": 200,
            "headers": {"X-Custom": "header-value"},
            "body": json.dumps({"result": "etymology-analysis-data"}),
        }

        handler = MagicMock(return_value=expected)
        protected = require_auth(handler)
        event = _make_event(f"Bearer {jwt_token}")

        with patch("auth.auth_middleware.get_jwt_secret", return_value=TEST_SECRET):
            response = protected(event, None)

        assert response == expected
