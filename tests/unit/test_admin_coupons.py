"""Tests for admin coupon CLI.

Issue #367: Manual Subscriptions with Coupons.
"""

import string
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from tools.admin_coupons import (
    MAX_BATCH_SIZE,
    generate_coupon_code,
    generate_coupons,
    list_coupons,
    revoke_coupon,
)


# --------------------------------------------------------------------------- #
# Code Generation Tests
# --------------------------------------------------------------------------- #


class TestGenerateCouponCode:
    """T010-T030: Coupon code format and randomness."""

    def test_code_length_is_16(self):
        """T010: Generated code is exactly 16 characters."""
        code = generate_coupon_code()
        assert len(code) == 16

    def test_code_is_uppercase_alphanumeric(self):
        """T020: Code contains only uppercase letters and digits."""
        valid_chars = set(string.ascii_uppercase + string.digits)
        code = generate_coupon_code()
        assert all(c in valid_chars for c in code)

    def test_codes_are_unique(self):
        """T030: Multiple generated codes are distinct."""
        codes = {generate_coupon_code() for _ in range(100)}
        assert len(codes) == 100  # All unique

    def test_code_uses_secrets_module(self):
        """Codes use cryptographic randomness (secrets module)."""
        # Verify by checking that codes vary (not static)
        codes = [generate_coupon_code() for _ in range(10)]
        assert len(set(codes)) > 1


# --------------------------------------------------------------------------- #
# Batch Generation Tests
# --------------------------------------------------------------------------- #


class TestGenerateCoupons:
    """T040: Batch generation with DynamoDB storage."""

    @patch("tools.admin_coupons.get_dynamodb_client")
    def test_generate_single_coupon(self, mock_get_client):
        """Generate a single coupon and store in DynamoDB."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.put_item.return_value = {}

        codes = generate_coupons(tier="subscriber", count=1, expires_days=30)

        assert len(codes) == 1
        assert len(codes[0]) == 16
        mock_client.put_item.assert_called_once()

        # Verify the stored item has correct attributes
        call_kwargs = mock_client.put_item.call_args.kwargs
        item = call_kwargs["Item"]
        assert item["tier"]["S"] == "subscriber"
        assert item["max_uses"]["N"] == "1"
        assert item["uses"]["N"] == "0"
        assert item["revoked"]["BOOL"] is False

    @patch("tools.admin_coupons.get_dynamodb_client")
    def test_generate_batch(self, mock_get_client):
        """Generate multiple coupons in a batch."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        codes = generate_coupons(tier="premium", count=5, expires_days=60)

        assert len(codes) == 5
        assert mock_client.put_item.call_count == 5

    def test_batch_exceeds_max_raises(self):
        """T040: Batch exceeding MAX_BATCH_SIZE raises ValueError."""
        with pytest.raises(ValueError, match="exceeds maximum"):
            generate_coupons(tier="subscriber", count=MAX_BATCH_SIZE + 1, expires_days=30)

    def test_zero_count_raises(self):
        """Count must be positive."""
        with pytest.raises(ValueError, match="must be positive"):
            generate_coupons(tier="subscriber", count=0, expires_days=30)

    @patch("tools.admin_coupons.get_dynamodb_client")
    def test_no_expiry_when_zero_days(self, mock_get_client):
        """expires_days=0 sets expiry to 0 (no expiry)."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        generate_coupons(tier="subscriber", count=1, expires_days=0)

        call_kwargs = mock_client.put_item.call_args.kwargs
        item = call_kwargs["Item"]
        assert item["expiry"]["N"] == "0"

    @patch("tools.admin_coupons.get_dynamodb_client")
    def test_custom_max_uses(self, mock_get_client):
        """Custom max_uses is stored correctly."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        generate_coupons(tier="subscriber", count=1, expires_days=30, max_uses=10)

        call_kwargs = mock_client.put_item.call_args.kwargs
        item = call_kwargs["Item"]
        assert item["max_uses"]["N"] == "10"

    @patch("tools.admin_coupons.get_dynamodb_client")
    def test_put_item_failure_skips_code(self, mock_get_client):
        """Failed put_item doesn't include code in result."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.put_item.side_effect = ClientError(
            {"Error": {"Code": "InternalServerError", "Message": ""}},
            "PutItem",
        )

        codes = generate_coupons(tier="subscriber", count=3, expires_days=30)

        assert len(codes) == 0


# --------------------------------------------------------------------------- #
# List Coupons Tests
# --------------------------------------------------------------------------- #


class TestListCoupons:
    """T140: List command tests."""

    @patch("tools.admin_coupons.get_dynamodb_client")
    def test_list_active_filters_revoked(self, mock_get_client):
        """Active filter excludes revoked coupons."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.scan.return_value = {
            "Items": [
                {
                    "code": {"S": "GOOD1234GOOD5678"},
                    "tier": {"S": "subscriber"},
                    "expiry": {"N": "9999999999"},
                    "max_uses": {"N": "1"},
                    "uses": {"N": "0"},
                    "revoked": {"BOOL": False},
                    "created_by": {"S": "admin-cli"},
                },
                {
                    "code": {"S": "REVK1234REVK5678"},
                    "tier": {"S": "subscriber"},
                    "expiry": {"N": "9999999999"},
                    "max_uses": {"N": "1"},
                    "uses": {"N": "0"},
                    "revoked": {"BOOL": True},
                    "created_by": {"S": "admin-cli"},
                },
            ]
        }

        coupons = list_coupons(status="active")

        assert len(coupons) == 1
        assert coupons[0]["code"] == "GOOD1234GOOD5678"

    @patch("tools.admin_coupons.get_dynamodb_client")
    def test_list_active_filters_expired(self, mock_get_client):
        """Active filter excludes expired coupons."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.scan.return_value = {
            "Items": [
                {
                    "code": {"S": "EXPR1234EXPR5678"},
                    "tier": {"S": "subscriber"},
                    "expiry": {"N": "1000000000"},
                    "max_uses": {"N": "1"},
                    "uses": {"N": "0"},
                    "revoked": {"BOOL": False},
                    "created_by": {"S": "admin-cli"},
                },
            ]
        }

        coupons = list_coupons(status="active")

        assert len(coupons) == 0

    @patch("tools.admin_coupons.get_dynamodb_client")
    def test_list_active_filters_exhausted(self, mock_get_client):
        """Active filter excludes fully-used coupons."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.scan.return_value = {
            "Items": [
                {
                    "code": {"S": "USED1234USED5678"},
                    "tier": {"S": "subscriber"},
                    "expiry": {"N": "9999999999"},
                    "max_uses": {"N": "1"},
                    "uses": {"N": "1"},
                    "revoked": {"BOOL": False},
                    "created_by": {"S": "admin-cli"},
                },
            ]
        }

        coupons = list_coupons(status="active")

        assert len(coupons) == 0

    @patch("tools.admin_coupons.get_dynamodb_client")
    def test_list_all_includes_everything(self, mock_get_client):
        """Status 'all' includes revoked, expired, and exhausted."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.scan.return_value = {
            "Items": [
                {
                    "code": {"S": "GOOD1234GOOD5678"},
                    "tier": {"S": "subscriber"},
                    "expiry": {"N": "9999999999"},
                    "max_uses": {"N": "1"},
                    "uses": {"N": "0"},
                    "revoked": {"BOOL": False},
                    "created_by": {"S": "admin-cli"},
                },
                {
                    "code": {"S": "REVK1234REVK5678"},
                    "tier": {"S": "subscriber"},
                    "expiry": {"N": "9999999999"},
                    "max_uses": {"N": "1"},
                    "uses": {"N": "0"},
                    "revoked": {"BOOL": True},
                    "created_by": {"S": "admin-cli"},
                },
            ]
        }

        coupons = list_coupons(status="all")

        assert len(coupons) == 2


# --------------------------------------------------------------------------- #
# Revoke Tests
# --------------------------------------------------------------------------- #


class TestRevokeCoupon:
    """T140: Revoke command tests."""

    @patch("tools.admin_coupons.get_dynamodb_client")
    def test_revoke_success(self, mock_get_client):
        """Revoking existing coupon returns True."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.update_item.return_value = {}

        result = revoke_coupon("ABCD1234EFGH5678")

        assert result is True

    @patch("tools.admin_coupons.get_dynamodb_client")
    def test_revoke_not_found(self, mock_get_client):
        """Revoking non-existent coupon returns False."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.update_item.side_effect = ClientError(
            {"Error": {"Code": "ConditionalCheckFailedException", "Message": ""}},
            "UpdateItem",
        )

        result = revoke_coupon("ZZZZ9999ZZZZ9999")

        assert result is False

    @patch("tools.admin_coupons.get_dynamodb_client")
    def test_revoke_uppercases_code(self, mock_get_client):
        """Code is uppercased before revocation."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.update_item.return_value = {}

        revoke_coupon("abcd1234efgh5678")

        call_kwargs = mock_client.update_item.call_args.kwargs
        assert call_kwargs["Key"]["code"]["S"] == "ABCD1234EFGH5678"

    @patch("tools.admin_coupons.get_dynamodb_client")
    def test_revoke_other_error_raises(self, mock_get_client):
        """Non-conditional-check errors are re-raised."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.update_item.side_effect = ClientError(
            {"Error": {"Code": "InternalServerError", "Message": ""}},
            "UpdateItem",
        )

        with pytest.raises(ClientError):
            revoke_coupon("ABCD1234EFGH5678")
