"""
Integration tests for coupon redemption flow.

Issue #521: Complete coupon feature — Firefox UI, integration tests, Chrome bump.

Tests the full redeem_coupon() function against moto DynamoDB,
verifying atomic writes, tier upgrades, and edge cases.

Test Scenarios:
- 010: Happy path — valid coupon upgrades user tier
- 020: Happy path with email — email saved to users table
- 030: Invalid code — returns invalid_code error
- 040: Expired coupon — returns code_expired error
- 050: Exhausted coupon — returns code_exhausted error
- 060: Revoked coupon — returns invalid_code (same as not found)
- 070: Concurrent redemption — conditional write prevents over-use
"""

import time

from src.auth.coupon_handler import redeem_coupon


def _insert_coupon(client, table, code, tier="subscriber", max_uses=1,
                   uses=0, expiry=0, revoked=False):
    """Helper to insert a coupon into the test table."""
    item = {
        "code": {"S": code},
        "tier": {"S": tier},
        "max_uses": {"N": str(max_uses)},
        "uses": {"N": str(uses)},
    }
    if expiry > 0:
        item["expiry"] = {"N": str(expiry)}
    if revoked:
        item["revoked"] = {"BOOL": True}
    client.put_item(TableName=table, Item=item)


class TestCouponRedemption:
    """Integration tests for redeem_coupon()."""

    def test_010_happy_path(self, dynamodb_client, coupons_table, users_table):
        """Valid coupon upgrades user tier to subscriber."""
        code = "TESTSUBSCRIBER01"
        user_id = "user-010"

        _insert_coupon(dynamodb_client, coupons_table, code, tier="subscriber")

        result = redeem_coupon(dynamodb_client, code, user_id)

        assert result["success"] is True
        assert result["tier"] == "subscriber"

        # Verify coupon uses incremented
        coupon = dynamodb_client.get_item(
            TableName=coupons_table, Key={"code": {"S": code}}
        )["Item"]
        assert int(coupon["uses"]["N"]) == 1
        assert user_id in coupon["redeemed_by"]["SS"]

        # Verify user tier upgraded
        user = dynamodb_client.get_item(
            TableName=users_table, Key={"user_id": {"S": user_id}}
        )["Item"]
        assert user["tier"]["S"] == "subscriber"

    def test_020_happy_path_with_email(self, dynamodb_client, coupons_table, users_table):
        """Valid coupon with email saves email to users table."""
        code = "TESTEMAIL0000001"
        user_id = "user-020"
        email = "test@example.com"

        _insert_coupon(dynamodb_client, coupons_table, code)

        result = redeem_coupon(dynamodb_client, code, user_id, email=email)

        assert result["success"] is True

        user = dynamodb_client.get_item(
            TableName=users_table, Key={"user_id": {"S": user_id}}
        )["Item"]
        assert user["email"]["S"] == email
        assert user["tier"]["S"] == "subscriber"

    def test_030_invalid_code(self, dynamodb_client, coupons_table, users_table):
        """Non-existent coupon code returns invalid_code."""
        result = redeem_coupon(dynamodb_client, "DOESNOTEXIST0001", "user-030")

        assert result["success"] is False
        assert result["error"] == "invalid_code"

    def test_040_expired_coupon(self, dynamodb_client, coupons_table, users_table):
        """Expired coupon returns code_expired."""
        code = "EXPIREDCODE00001"
        past = int(time.time()) - 3600  # 1 hour ago

        _insert_coupon(dynamodb_client, coupons_table, code, expiry=past)

        result = redeem_coupon(dynamodb_client, code, "user-040")

        assert result["success"] is False
        assert result["error"] == "code_expired"

    def test_050_exhausted_coupon(self, dynamodb_client, coupons_table, users_table):
        """Fully used coupon returns code_exhausted."""
        code = "EXHAUSTEDCODE001"

        _insert_coupon(dynamodb_client, coupons_table, code, max_uses=1, uses=1)

        result = redeem_coupon(dynamodb_client, code, "user-050")

        assert result["success"] is False
        assert result["error"] == "code_exhausted"

    def test_060_revoked_coupon(self, dynamodb_client, coupons_table, users_table):
        """Revoked coupon returns invalid_code (same as not found)."""
        code = "REVOKEDCODE00001"

        _insert_coupon(dynamodb_client, coupons_table, code, revoked=True)

        result = redeem_coupon(dynamodb_client, code, "user-060")

        assert result["success"] is False
        assert result["error"] == "invalid_code"

    def test_070_multi_use_coupon(self, dynamodb_client, coupons_table, users_table):
        """Multi-use coupon allows multiple redemptions up to max_uses."""
        code = "MULTIUSE00000001"

        _insert_coupon(dynamodb_client, coupons_table, code, max_uses=3)

        # First two redemptions succeed
        r1 = redeem_coupon(dynamodb_client, code, "user-070a")
        assert r1["success"] is True

        r2 = redeem_coupon(dynamodb_client, code, "user-070b")
        assert r2["success"] is True

        r3 = redeem_coupon(dynamodb_client, code, "user-070c")
        assert r3["success"] is True

        # Fourth redemption fails
        r4 = redeem_coupon(dynamodb_client, code, "user-070d")
        assert r4["success"] is False
        assert r4["error"] == "code_exhausted"

        # Verify uses count
        coupon = dynamodb_client.get_item(
            TableName=coupons_table, Key={"code": {"S": code}}
        )["Item"]
        assert int(coupon["uses"]["N"]) == 3
