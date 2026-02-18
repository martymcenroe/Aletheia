"""Unit tests for JWT service.

Issue: #341 - Add JWT authentication to analysis endpoint with daily token cap.
Issue: #364 - Tiered rate limiting with multi-window caps.

Tests cover:
- T010: JWT creation with valid inputs (REQ-5, REQ-6)
- T020: JWT validation success (REQ-4)
- T030: JWT validation - expired token (REQ-3)
- T040: JWT validation - invalid signature (REQ-2)
- T050: JWT validation - malformed token (REQ-2)
- T140: Secret retrieval from Secrets Manager (REQ-10)
- T150: Dual-secret validation during rotation (REQ-10)
- T220: Tier and billing_anchor_day embedded in JWT (#364)
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import jwt as pyjwt
import pytest

from auth.jwt_service import (
    create_jwt,
    get_jwt_secret,
    invalidate_secret_cache,
    validate_jwt,
    validate_jwt_dual_secret,
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
        "jti": "expired-jti-001",
    }
    return pyjwt.encode(payload, TEST_SECRET, algorithm="HS256")


@pytest.fixture()
def wrong_signature_token() -> str:
    """Create a JWT signed with a different secret."""
    return create_jwt(TEST_USER_ID, "wrong-secret-key")


# --------------------------------------------------------------------------- #
# T010 - test_create_jwt_valid (REQ-5, REQ-6)
# --------------------------------------------------------------------------- #


class TestCreateJwt:
    """T010: JWT creation with valid inputs."""

    def test_create_jwt_returns_string(self):
        """create_jwt returns a non-empty string."""
        token = create_jwt(TEST_USER_ID, TEST_SECRET)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_jwt_contains_user_id(self):
        """REQ-6: JWT contains user_id claim."""
        token = create_jwt(TEST_USER_ID, TEST_SECRET)
        payload = pyjwt.decode(token, TEST_SECRET, algorithms=["HS256"])
        assert payload["user_id"] == TEST_USER_ID

    def test_create_jwt_contains_exp(self):
        """REQ-6: JWT contains exp claim set to 24h from issuance."""
        before = int(time.time())
        token = create_jwt(TEST_USER_ID, TEST_SECRET, expiry_hours=24)
        after = int(time.time())

        payload = pyjwt.decode(token, TEST_SECRET, algorithms=["HS256"])
        assert "exp" in payload
        # exp should be ~24h from now (within the before/after window)
        expected_min = before + (24 * 3600)
        expected_max = after + (24 * 3600)
        assert expected_min <= payload["exp"] <= expected_max

    def test_create_jwt_contains_iat(self):
        """REQ-6: JWT contains iat (issued-at) claim."""
        before = int(time.time())
        token = create_jwt(TEST_USER_ID, TEST_SECRET)
        after = int(time.time())

        payload = pyjwt.decode(token, TEST_SECRET, algorithms=["HS256"])
        assert "iat" in payload
        assert before <= payload["iat"] <= after

    def test_create_jwt_contains_jti(self):
        """REQ-6: JWT contains jti (JWT ID) claim."""
        token = create_jwt(TEST_USER_ID, TEST_SECRET)
        payload = pyjwt.decode(token, TEST_SECRET, algorithms=["HS256"])
        assert "jti" in payload
        assert len(payload["jti"]) > 0

    def test_create_jwt_jti_unique(self):
        """Each JWT should have a unique jti."""
        token1 = create_jwt(TEST_USER_ID, TEST_SECRET)
        token2 = create_jwt(TEST_USER_ID, TEST_SECRET)

        payload1 = pyjwt.decode(token1, TEST_SECRET, algorithms=["HS256"])
        payload2 = pyjwt.decode(token2, TEST_SECRET, algorithms=["HS256"])
        assert payload1["jti"] != payload2["jti"]

    def test_create_jwt_custom_expiry(self):
        """Custom expiry_hours is respected."""
        before = int(time.time())
        token = create_jwt(TEST_USER_ID, TEST_SECRET, expiry_hours=1)
        after = int(time.time())

        payload = pyjwt.decode(token, TEST_SECRET, algorithms=["HS256"])
        expected_min = before + 3600
        expected_max = after + 3600
        assert expected_min <= payload["exp"] <= expected_max

    def test_create_jwt_signed_with_hs256(self):
        """JWT uses HS256 algorithm."""
        token = create_jwt(TEST_USER_ID, TEST_SECRET)
        header = pyjwt.get_unverified_header(token)
        assert header["alg"] == "HS256"


# --------------------------------------------------------------------------- #
# T020 - test_validate_jwt_success (REQ-4)
# --------------------------------------------------------------------------- #


class TestValidateJwtSuccess:
    """T020: Valid JWT returns user_id."""

    def test_validate_valid_jwt(self, valid_token: str):
        """Valid JWT returns success=True with correct user_id."""
        result = validate_jwt(valid_token, TEST_SECRET)
        assert result["success"] is True
        assert result["user_id"] == TEST_USER_ID
        assert result["error"] is None
        assert result["reason"] is None

    def test_validate_returns_auth_result_shape(self, valid_token: str):
        """Result has all AuthResult fields."""
        result = validate_jwt(valid_token, TEST_SECRET)
        assert "success" in result
        assert "user_id" in result
        assert "error" in result
        assert "reason" in result


# --------------------------------------------------------------------------- #
# T030 - test_validate_jwt_expired (REQ-3)
# --------------------------------------------------------------------------- #


class TestValidateJwtExpired:
    """T030: Expired JWT returns error with reason 'token_expired'."""

    def test_expired_jwt_returns_failure(self, expired_token: str):
        """Expired JWT returns success=False."""
        result = validate_jwt(expired_token, TEST_SECRET, leeway_seconds=0)
        assert result["success"] is False

    def test_expired_jwt_reason(self, expired_token: str):
        """Expired JWT has reason='token_expired'."""
        result = validate_jwt(expired_token, TEST_SECRET, leeway_seconds=0)
        assert result["reason"] == "token_expired"

    def test_expired_jwt_user_id_none(self, expired_token: str):
        """Expired JWT does not expose user_id."""
        result = validate_jwt(expired_token, TEST_SECRET, leeway_seconds=0)
        assert result["user_id"] is None

    def test_expired_jwt_has_error_message(self, expired_token: str):
        """Expired JWT has a human-readable error message."""
        result = validate_jwt(expired_token, TEST_SECRET, leeway_seconds=0)
        assert result["error"] is not None
        assert len(result["error"]) > 0

    def test_expired_jwt_within_leeway_succeeds(self):
        """JWT expired within leeway window still validates."""
        now = int(time.time())
        payload = {
            "user_id": TEST_USER_ID,
            "exp": now - 60,  # Expired 60 seconds ago
            "iat": now - 3600,
            "jti": "leeway-test-jti",
        }
        token = pyjwt.encode(payload, TEST_SECRET, algorithm="HS256")
        # Default leeway is 300 seconds, so 60 seconds expired should pass
        result = validate_jwt(token, TEST_SECRET, leeway_seconds=300)
        assert result["success"] is True
        assert result["user_id"] == TEST_USER_ID

    def test_expired_jwt_beyond_leeway_fails(self):
        """JWT expired beyond leeway window fails."""
        now = int(time.time())
        payload = {
            "user_id": TEST_USER_ID,
            "exp": now - 600,  # Expired 10 minutes ago
            "iat": now - 7200,
            "jti": "beyond-leeway-jti",
        }
        token = pyjwt.encode(payload, TEST_SECRET, algorithm="HS256")
        # Leeway of 300s (5 min) won't cover 10 min expiry
        result = validate_jwt(token, TEST_SECRET, leeway_seconds=300)
        assert result["success"] is False
        assert result["reason"] == "token_expired"


# --------------------------------------------------------------------------- #
# T040 - test_validate_jwt_invalid_signature (REQ-2)
# --------------------------------------------------------------------------- #


class TestValidateJwtInvalidSignature:
    """T040: Bad signature returns error with reason 'invalid_signature'."""

    def test_wrong_secret_returns_failure(self, wrong_signature_token: str):
        """JWT signed with wrong key returns success=False."""
        result = validate_jwt(wrong_signature_token, TEST_SECRET)
        assert result["success"] is False

    def test_wrong_secret_reason(self, wrong_signature_token: str):
        """JWT signed with wrong key has reason='invalid_signature'."""
        result = validate_jwt(wrong_signature_token, TEST_SECRET)
        assert result["reason"] == "invalid_signature"

    def test_wrong_secret_user_id_none(self, wrong_signature_token: str):
        """JWT signed with wrong key does not expose user_id."""
        result = validate_jwt(wrong_signature_token, TEST_SECRET)
        assert result["user_id"] is None

    def test_tampered_payload_returns_invalid_signature(self):
        """JWT with tampered payload (modified after signing) is rejected."""
        token = create_jwt(TEST_USER_ID, TEST_SECRET)
        # Tamper with the payload section (middle part)
        parts = token.split(".")
        # Flip a character in the payload
        tampered_payload = parts[1][:-1] + ("A" if parts[1][-1] != "A" else "B")
        tampered_token = f"{parts[0]}.{tampered_payload}.{parts[2]}"
        result = validate_jwt(tampered_token, TEST_SECRET)
        assert result["success"] is False
        # Could be invalid_signature or malformed depending on base64 decode
        assert result["reason"] in ("invalid_signature", "malformed", "invalid_token")


# --------------------------------------------------------------------------- #
# T050 - test_validate_jwt_malformed (REQ-2)
# --------------------------------------------------------------------------- #


class TestValidateJwtMalformed:
    """T050: Malformed token returns error."""

    def test_completely_invalid_string(self):
        """Random string fails validation."""
        result = validate_jwt("not-a-jwt-at-all", TEST_SECRET)
        assert result["success"] is False
        assert result["reason"] == "malformed"

    def test_incomplete_segments(self):
        """Token with only two segments fails."""
        result = validate_jwt("header.payload", TEST_SECRET)
        assert result["success"] is False

    def test_empty_string(self):
        """Empty string fails validation."""
        result = validate_jwt("", TEST_SECRET)
        assert result["success"] is False

    def test_not_a_jwt_three_dots(self):
        """'not.a.jwt' format fails validation."""
        result = validate_jwt("not.a.jwt", TEST_SECRET)
        assert result["success"] is False
        assert result["user_id"] is None

    def test_malformed_has_error_message(self):
        """Malformed token has a human-readable error."""
        result = validate_jwt("garbage", TEST_SECRET)
        assert result["error"] is not None

    def test_missing_required_claims(self):
        """JWT missing required claims (no user_id) is rejected."""
        payload = {
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
            "jti": "test-jti",
            # Intentionally missing user_id
        }
        token = pyjwt.encode(payload, TEST_SECRET, algorithm="HS256")
        result = validate_jwt(token, TEST_SECRET)
        assert result["success"] is False


# --------------------------------------------------------------------------- #
# T140 - test_get_jwt_secret_from_secrets_manager (REQ-10)
# --------------------------------------------------------------------------- #


class TestGetJwtSecret:
    """T140: JWT secret retrieved from Secrets Manager."""

    def test_retrieves_secret_from_secrets_manager(self):
        """get_jwt_secret calls Secrets Manager and returns the secret string."""
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {
            "SecretString": "my-super-secret-key"
        }

        with patch("auth.jwt_service.boto3") as mock_boto3:
            mock_boto3.client.return_value = mock_client
            # Reset the module-level client to force re-creation
            import auth.jwt_service as jwt_mod
            jwt_mod._secrets_client = None

            secret = get_jwt_secret()

        assert secret == "my-super-secret-key"
        mock_client.get_secret_value.assert_called_once()

    def test_uses_correct_secret_name_from_env(self):
        """Reads JWT_SECRET_NAME from environment."""
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {
            "SecretString": "env-secret"
        }

        with (
            patch("auth.jwt_service.boto3") as mock_boto3,
            patch.dict(
                "os.environ",
                {"JWT_SECRET_NAME": "custom/secret-name"},
            ),
        ):
            mock_boto3.client.return_value = mock_client
            import auth.jwt_service as jwt_mod
            jwt_mod._secrets_client = None

            get_jwt_secret()

        mock_client.get_secret_value.assert_called_once_with(
            SecretId="custom/secret-name"
        )

    def test_caches_secret_within_ttl(self):
        """Secret is cached and not re-fetched within TTL window."""
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {
            "SecretString": "cached-secret"
        }

        with patch("auth.jwt_service.boto3") as mock_boto3:
            mock_boto3.client.return_value = mock_client
            import auth.jwt_service as jwt_mod
            jwt_mod._secrets_client = None

            # First call: fetches from Secrets Manager
            secret1 = get_jwt_secret()
            # Second call: should use cache
            secret2 = get_jwt_secret()

        assert secret1 == "cached-secret"
        assert secret2 == "cached-secret"
        # Only one actual API call
        assert mock_client.get_secret_value.call_count == 1

    def test_raises_runtime_error_on_failure(self):
        """get_jwt_secret raises RuntimeError if Secrets Manager fails."""
        mock_client = MagicMock()
        mock_client.get_secret_value.side_effect = Exception("Access denied")

        with patch("auth.jwt_service.boto3") as mock_boto3:
            mock_boto3.client.return_value = mock_client
            import auth.jwt_service as jwt_mod
            jwt_mod._secrets_client = None

            with pytest.raises(RuntimeError, match="Failed to retrieve JWT secret"):
                get_jwt_secret()

    def test_invalidate_cache_forces_refresh(self):
        """invalidate_secret_cache causes next call to re-fetch."""
        mock_client = MagicMock()
        mock_client.get_secret_value.side_effect = [
            {"SecretString": "secret-v1"},
            {"SecretString": "secret-v2"},
        ]

        with patch("auth.jwt_service.boto3") as mock_boto3:
            mock_boto3.client.return_value = mock_client
            import auth.jwt_service as jwt_mod
            jwt_mod._secrets_client = None

            secret1 = get_jwt_secret()
            invalidate_secret_cache()
            secret2 = get_jwt_secret()

        assert secret1 == "secret-v1"
        assert secret2 == "secret-v2"
        assert mock_client.get_secret_value.call_count == 2


# --------------------------------------------------------------------------- #
# T150 - test_validate_jwt_dual_secret (REQ-10)
# --------------------------------------------------------------------------- #


class TestValidateJwtDualSecret:
    """T150: Falls back to secondary secret during rotation."""

    def test_primary_secret_succeeds(self, valid_token: str):
        """JWT signed with primary secret validates on first try."""
        result = validate_jwt_dual_secret(
            valid_token, TEST_SECRET, TEST_SECRET_ALT
        )
        assert result["success"] is True
        assert result["user_id"] == TEST_USER_ID

    def test_fallback_to_secondary_secret(self):
        """JWT signed with old (secondary) secret validates via fallback."""
        # Token signed with secondary (old) secret
        token = create_jwt(TEST_USER_ID, TEST_SECRET_ALT)

        # Primary is different; secondary matches
        result = validate_jwt_dual_secret(
            token, TEST_SECRET, TEST_SECRET_ALT
        )
        assert result["success"] is True
        assert result["user_id"] == TEST_USER_ID

    def test_no_secondary_secret_fails_on_bad_signature(self):
        """Without secondary secret, bad signature fails immediately."""
        token = create_jwt(TEST_USER_ID, TEST_SECRET_ALT)

        result = validate_jwt_dual_secret(token, TEST_SECRET, None)
        assert result["success"] is False
        assert result["reason"] == "invalid_signature"

    def test_both_secrets_wrong_fails(self):
        """Token signed with unknown key fails even with dual-secret."""
        token = create_jwt(TEST_USER_ID, "completely-unknown-key")

        result = validate_jwt_dual_secret(
            token, TEST_SECRET, TEST_SECRET_ALT
        )
        assert result["success"] is False
        assert result["reason"] == "invalid_signature"

    def test_expired_token_not_rescued_by_secondary(self):
        """Expired token fails even if secondary secret matches signature."""
        now = int(time.time())
        payload = {
            "user_id": TEST_USER_ID,
            "exp": now - 3600,  # Expired
            "iat": now - 7200,
            "jti": "dual-expired-jti",
        }
        token = pyjwt.encode(payload, TEST_SECRET, algorithm="HS256")

        # Primary matches but token is expired; secondary shouldn't help
        result = validate_jwt_dual_secret(token, TEST_SECRET, TEST_SECRET_ALT)
        assert result["success"] is False
        assert result["reason"] == "token_expired"

    def test_malformed_token_not_rescued_by_secondary(self):
        """Malformed token fails regardless of dual-secret."""
        result = validate_jwt_dual_secret(
            "not.a.jwt", TEST_SECRET, TEST_SECRET_ALT
        )
        assert result["success"] is False

    def test_secondary_only_tried_on_signature_failure(self):
        """Secondary is NOT tried for non-signature failures (e.g., expired)."""
        now = int(time.time())
        payload = {
            "user_id": TEST_USER_ID,
            "exp": now - 7200,  # Expired well beyond leeway
            "iat": now - 14400,
            "jti": "selective-fallback-jti",
        }
        # Sign with primary — signature is fine, but token is expired
        token = pyjwt.encode(payload, TEST_SECRET, algorithm="HS256")

        result = validate_jwt_dual_secret(token, TEST_SECRET, TEST_SECRET_ALT)
        # Should get token_expired, not try secondary
        assert result["success"] is False
        assert result["reason"] == "token_expired"


# --------------------------------------------------------------------------- #
# T220 - Tier and billing_anchor_day in JWT (#364)
# --------------------------------------------------------------------------- #


class TestJwtTierClaims:
    """T220: Tier and billing_anchor_day are embedded in JWT."""

    def test_create_jwt_contains_tier(self):
        """JWT contains tier claim."""
        token = create_jwt(TEST_USER_ID, TEST_SECRET, tier="subscriber")
        payload = pyjwt.decode(token, TEST_SECRET, algorithms=["HS256"])
        assert payload["tier"] == "subscriber"

    def test_create_jwt_contains_billing_anchor_day(self):
        """JWT contains billing_anchor_day claim."""
        token = create_jwt(
            TEST_USER_ID, TEST_SECRET, billing_anchor_day=15
        )
        payload = pyjwt.decode(token, TEST_SECRET, algorithms=["HS256"])
        assert payload["billing_anchor_day"] == 15

    def test_default_tier_is_free(self):
        """Default tier claim is 'free'."""
        token = create_jwt(TEST_USER_ID, TEST_SECRET)
        payload = pyjwt.decode(token, TEST_SECRET, algorithms=["HS256"])
        assert payload["tier"] == "free"

    def test_default_billing_anchor_day_is_1(self):
        """Default billing_anchor_day is 1."""
        token = create_jwt(TEST_USER_ID, TEST_SECRET)
        payload = pyjwt.decode(token, TEST_SECRET, algorithms=["HS256"])
        assert payload["billing_anchor_day"] == 1

    def test_tier_roundtrip_through_validate(self):
        """Tier survives create → validate roundtrip in claims."""
        token = create_jwt(
            TEST_USER_ID, TEST_SECRET, tier="admin", billing_anchor_day=20
        )
        result = validate_jwt(token, TEST_SECRET)
        assert result["success"] is True
        assert result["claims"]["tier"] == "admin"
        assert result["claims"]["billing_anchor_day"] == 20

    def test_validate_returns_claims_on_success(self, valid_token: str):
        """Successful validation includes claims dict."""
        result = validate_jwt(valid_token, TEST_SECRET)
        assert result["claims"] is not None
        assert "user_id" in result["claims"]
        assert "exp" in result["claims"]

    def test_validate_returns_none_claims_on_failure(self):
        """Failed validation has claims=None."""
        result = validate_jwt("invalid.token.here", TEST_SECRET)
        assert result["success"] is False
        assert result["claims"] is None

    def test_admin_tier_in_jwt(self):
        """Admin tier value embeds correctly."""
        token = create_jwt(TEST_USER_ID, TEST_SECRET, tier="admin")
        payload = pyjwt.decode(token, TEST_SECRET, algorithms=["HS256"])
        assert payload["tier"] == "admin"
