"""Tests for coupon redemption handler.

Issue #367: Manual Subscriptions with Coupons.
"""

import json
import time
import uuid
from unittest.mock import MagicMock, patch

import jwt
from botocore.exceptions import ClientError

from src.auth.coupon_handler import (
    handle_redeem_coupon,
    redeem_coupon,
    validate_coupon_code,
    validate_email,
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

JWT_SECRET = "test-secret-key-for-coupon-handler-testing-only-32chars!"


def _make_jwt(tier: str = "free", user_id: str = "user-123") -> str:
    """Create a test JWT with all required fields."""
    payload = {
        "user_id": user_id,
        "tier": tier,
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def _make_event(token: str | None = None, body: dict | None = None) -> dict:
    """Create a Lambda event for POST /redeem-coupon."""
    headers: dict[str, str] = {}
    if token:
        headers["authorization"] = f"Bearer {token}"
    event: dict = {
        "requestContext": {"http": {"method": "POST", "path": "/redeem-coupon"}},
        "headers": headers,
    }
    if body is not None:
        event["body"] = json.dumps(body)
    return event


def _make_coupon_item(
    code: str = "ABCD1234EFGH5678",
    tier: str = "subscriber",
    expiry: int = 9999999999,
    max_uses: int = 1,
    uses: int = 0,
    revoked: bool = False,
) -> dict:
    """Create a DynamoDB coupon item."""
    return {
        "code": {"S": code},
        "tier": {"S": tier},
        "expiry": {"N": str(expiry)},
        "max_uses": {"N": str(max_uses)},
        "uses": {"N": str(uses)},
        "revoked": {"BOOL": revoked},
        "created_by": {"S": "admin-cli"},
        "created_at": {"N": "1700000000"},
    }


# --------------------------------------------------------------------------- #
# Validation Tests
# --------------------------------------------------------------------------- #


class TestValidateCouponCode:
    """T010-T020: Coupon code format validation."""

    def test_valid_16_char_uppercase_alphanumeric(self):
        """T010: Valid 16-char uppercase alphanumeric code."""
        assert validate_coupon_code("ABCD1234EFGH5678") is True

    def test_valid_all_letters(self):
        assert validate_coupon_code("ABCDEFGHIJKLMNOP") is True

    def test_valid_all_digits(self):
        assert validate_coupon_code("1234567890123456") is True

    def test_invalid_too_short(self):
        assert validate_coupon_code("ABCD1234") is False

    def test_invalid_too_long(self):
        assert validate_coupon_code("ABCD1234EFGH56789") is False

    def test_invalid_lowercase(self):
        assert validate_coupon_code("abcd1234efgh5678") is False

    def test_invalid_special_chars(self):
        assert validate_coupon_code("ABCD-1234-EFGH-5") is False

    def test_invalid_empty(self):
        assert validate_coupon_code("") is False


class TestValidateEmail:
    """T100-T110: Email format validation."""

    def test_valid_email(self):
        """T100: Valid email accepted."""
        assert validate_email("user@example.com") is True

    def test_valid_email_with_dots(self):
        assert validate_email("first.last@example.co.uk") is True

    def test_valid_email_with_plus(self):
        assert validate_email("user+tag@example.com") is True

    def test_invalid_no_at(self):
        """T110: Invalid email rejected."""
        assert validate_email("userexample.com") is False

    def test_invalid_no_domain(self):
        assert validate_email("user@") is False

    def test_invalid_empty(self):
        assert validate_email("") is False

    def test_invalid_too_long(self):
        assert validate_email("a" * 250 + "@b.com") is False


# --------------------------------------------------------------------------- #
# Redemption Tests
# --------------------------------------------------------------------------- #


class TestRedeemCoupon:
    """T050-T090: Coupon redemption logic."""

    def test_valid_redemption(self):
        """T050: Valid coupon redeems successfully."""
        client = MagicMock()
        client.get_item.return_value = {"Item": _make_coupon_item()}
        client.update_item.return_value = {}

        result = redeem_coupon(client, "ABCD1234EFGH5678", "user-123")

        assert result["success"] is True
        assert result["tier"] == "subscriber"
        # Verify atomic update was called (coupon table)
        assert client.update_item.call_count == 2  # coupon + user tier

    def test_invalid_code_not_found(self):
        """T050b: Non-existent code returns invalid_code."""
        client = MagicMock()
        client.get_item.return_value = {}

        result = redeem_coupon(client, "ZZZZ9999ZZZZ9999", "user-123")

        assert result["success"] is False
        assert result["error"] == "invalid_code"

    def test_expired_coupon(self):
        """T060: Expired coupon returns code_expired."""
        client = MagicMock()
        client.get_item.return_value = {
            "Item": _make_coupon_item(expiry=1000000000)  # Long past
        }

        result = redeem_coupon(client, "EXPR1234EXPR5678", "user-123")

        assert result["success"] is False
        assert result["error"] == "code_expired"

    def test_exhausted_coupon(self):
        """T070: Exhausted coupon returns code_exhausted."""
        client = MagicMock()
        client.get_item.return_value = {
            "Item": _make_coupon_item(max_uses=1, uses=1)
        }

        result = redeem_coupon(client, "USED1234USED5678", "user-123")

        assert result["success"] is False
        assert result["error"] == "code_exhausted"

    def test_revoked_coupon(self):
        """T080: Revoked coupon returns invalid_code (same as not found)."""
        client = MagicMock()
        client.get_item.return_value = {
            "Item": _make_coupon_item(revoked=True)
        }

        result = redeem_coupon(client, "REVK1234REVK5678", "user-123")

        assert result["success"] is False
        assert result["error"] == "invalid_code"

    def test_race_condition_conditional_check_fails(self):
        """T090: Race condition caught by DynamoDB conditional write."""
        client = MagicMock()
        client.get_item.return_value = {"Item": _make_coupon_item()}
        client.update_item.side_effect = ClientError(
            {"Error": {"Code": "ConditionalCheckFailedException", "Message": ""}},
            "UpdateItem",
        )

        result = redeem_coupon(client, "ABCD1234EFGH5678", "user-123")

        assert result["success"] is False
        assert result["error"] == "code_exhausted"

    def test_tier_upgrade_on_success(self):
        """T120: User tier is updated in users table after redemption."""
        client = MagicMock()
        client.get_item.return_value = {
            "Item": _make_coupon_item(tier="premium")
        }
        client.update_item.return_value = {}

        result = redeem_coupon(client, "ABCD1234EFGH5678", "user-123")

        assert result["success"] is True
        assert result["tier"] == "premium"

        # Check the user table update call
        user_update_call = client.update_item.call_args_list[1]
        assert user_update_call.kwargs["TableName"] == "aletheia-users"
        assert ":tier" in user_update_call.kwargs["ExpressionAttributeValues"]

    def test_email_saved_on_redemption(self):
        """T120b: Email is saved in users table when provided."""
        client = MagicMock()
        client.get_item.return_value = {"Item": _make_coupon_item()}
        client.update_item.return_value = {}

        result = redeem_coupon(
            client, "ABCD1234EFGH5678", "user-123", email="test@example.com"
        )

        assert result["success"] is True
        user_update_call = client.update_item.call_args_list[1]
        expr_values = user_update_call.kwargs["ExpressionAttributeValues"]
        assert ":email" in expr_values
        assert expr_values[":email"]["S"] == "test@example.com"

    def test_audit_trail_redeemed_by(self):
        """T130: redeemed_by set is updated with user ID."""
        client = MagicMock()
        client.get_item.return_value = {"Item": _make_coupon_item()}
        client.update_item.return_value = {}

        redeem_coupon(client, "ABCD1234EFGH5678", "user-123")

        # Check the coupon update call (first update_item)
        coupon_update_call = client.update_item.call_args_list[0]
        expr_values = coupon_update_call.kwargs["ExpressionAttributeValues"]
        assert ":user_set" in expr_values
        assert "user-123" in expr_values[":user_set"]["SS"]

    def test_no_expiry_coupon_valid(self):
        """Coupon with expiry=0 (no expiry) is always valid."""
        client = MagicMock()
        client.get_item.return_value = {
            "Item": _make_coupon_item(expiry=0)
        }
        client.update_item.return_value = {}

        result = redeem_coupon(client, "ABCD1234EFGH5678", "user-123")

        assert result["success"] is True

    def test_dynamodb_get_error_returns_internal(self):
        """DynamoDB get_item error returns internal_error."""
        client = MagicMock()
        client.get_item.side_effect = ClientError(
            {"Error": {"Code": "InternalServerError", "Message": ""}},
            "GetItem",
        )

        result = redeem_coupon(client, "ABCD1234EFGH5678", "user-123")

        assert result["success"] is False
        assert result["error"] == "internal_error"

    def test_tier_upgrade_failure_returns_internal(self):
        """Failed tier upgrade returns internal_error (coupon consumed)."""
        client = MagicMock()
        client.get_item.return_value = {"Item": _make_coupon_item()}

        # First update (coupon) succeeds, second (user tier) fails
        client.update_item.side_effect = [
            {},  # coupon update OK
            ClientError(
                {"Error": {"Code": "InternalServerError", "Message": ""}},
                "UpdateItem",
            ),
        ]

        result = redeem_coupon(client, "ABCD1234EFGH5678", "user-123")

        assert result["success"] is False
        assert result["error"] == "internal_error"


# --------------------------------------------------------------------------- #
# Handler Tests
# --------------------------------------------------------------------------- #


class TestHandleRedeemCoupon:
    """Handler integration tests with JWT auth."""

    @patch("src.auth.coupon_handler.get_jwt_secret", return_value=JWT_SECRET)
    def test_401_no_auth(self, _mock_secret):
        """Returns 401 when no Authorization header."""
        event = _make_event(token=None, body={"code": "ABCD1234EFGH5678"})
        result = handle_redeem_coupon(event)
        assert result["statusCode"] == 401

    @patch("src.auth.coupon_handler.get_jwt_secret", return_value=JWT_SECRET)
    def test_401_invalid_jwt(self, _mock_secret):
        """Returns 401 when JWT is invalid."""
        bad_token = jwt.encode(
            {"user_id": "u", "exp": time.time() + 3600},
            "wrong-secret",
            algorithm="HS256",
        )
        event = _make_event(token=bad_token, body={"code": "ABCD1234EFGH5678"})
        result = handle_redeem_coupon(event)
        assert result["statusCode"] == 401

    @patch("src.auth.coupon_handler._get_dynamodb_client")
    @patch("src.auth.coupon_handler.get_jwt_secret", return_value=JWT_SECRET)
    def test_400_invalid_code_format(self, _mock_secret, mock_client):
        """Returns 400 for invalid coupon code format."""
        token = _make_jwt()
        event = _make_event(token=token, body={"code": "short"})
        result = handle_redeem_coupon(event)
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "Invalid coupon code format" in body["error"]

    @patch("src.auth.coupon_handler._get_dynamodb_client")
    @patch("src.auth.coupon_handler.get_jwt_secret", return_value=JWT_SECRET)
    def test_400_invalid_email(self, _mock_secret, mock_client):
        """Returns 400 for invalid email format."""
        token = _make_jwt()
        event = _make_event(
            token=token, body={"code": "ABCD1234EFGH5678", "email": "not-an-email"}
        )
        result = handle_redeem_coupon(event)
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "Invalid email format" in body["error"]

    @patch("src.auth.coupon_handler._get_dynamodb_client")
    @patch("src.auth.coupon_handler.get_jwt_secret", return_value=JWT_SECRET)
    def test_200_successful_redemption(self, _mock_secret, mock_get_client):
        """Returns 200 with tier on successful redemption."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_item.return_value = {"Item": _make_coupon_item()}
        mock_client.update_item.return_value = {}

        token = _make_jwt()
        event = _make_event(token=token, body={"code": "ABCD1234EFGH5678"})
        result = handle_redeem_coupon(event)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["status"] == "success"
        assert body["tier"] == "subscriber"

    @patch("src.auth.coupon_handler._get_dynamodb_client")
    @patch("src.auth.coupon_handler.get_jwt_secret", return_value=JWT_SECRET)
    def test_case_insensitive_code(self, _mock_secret, mock_get_client):
        """Code is uppercased before lookup."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_item.return_value = {"Item": _make_coupon_item()}
        mock_client.update_item.return_value = {}

        token = _make_jwt()
        event = _make_event(token=token, body={"code": "abcd1234efgh5678"})
        result = handle_redeem_coupon(event)

        assert result["statusCode"] == 200
        # Verify the get_item used uppercase code
        get_call = mock_client.get_item.call_args
        assert get_call.kwargs["Key"]["code"]["S"] == "ABCD1234EFGH5678"

    @patch("src.auth.coupon_handler._get_dynamodb_client")
    @patch("src.auth.coupon_handler.get_jwt_secret", return_value=JWT_SECRET)
    def test_code_prefix_logged_not_full(self, _mock_secret, mock_get_client):
        """Only code prefix is logged, not full code."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_item.return_value = {"Item": _make_coupon_item()}
        mock_client.update_item.return_value = {}

        token = _make_jwt()
        event = _make_event(token=token, body={"code": "ABCD1234EFGH5678"})

        with patch("src.auth.coupon_handler.logger") as mock_logger:
            handle_redeem_coupon(event)
            # Check info calls contain masked code
            logged_messages = [str(c) for c in mock_logger.info.call_args_list]
            for msg in logged_messages:
                assert "ABCD1234EFGH5678" not in msg
                if "ABCD" in msg:
                    assert "****" in msg
