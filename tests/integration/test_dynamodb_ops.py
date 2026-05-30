"""
DynamoDB integration tests for Lambda data operations.

Issue #264: DynamoDB integration test infrastructure.
LLD: docs/lld/active/1264-dynamodb-integration-fixtures.md Section 11.1

Test Scenarios:
- 010: delete_user_data happy path (profile + 10 analysis records)
- 011: profile-only (OAuth'd but never used the analyzer)
- 020: delete_user_data pagination (profile + 2000 records, >1MB)
- 030: delete_user_data nonexistent user (nothing anywhere)
- 031: records-only orphan (records exist, no profile)
- 032: Stripe subscriber, cancel succeeds
- 033: Stripe subscriber, cancel raises (rest of deletion must still complete)
- 034: coupon single redemption (user_id stripped from one redeemed_by set)
- 035: coupon many redemptions (exercise the scan/pagination loop)
- 036: token-cap rows (rate-limit windows for a user wiped)
- 037: full-spectrum (every column of the state space active simultaneously)
- 040: save_state with TTL
- 050: GSI query returns correct user
- 060: Table creation with GSI
"""

import sys
import time
from pathlib import Path
from unittest.mock import patch


# Add src to path for Lambda imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Import Lambda functions after setting up environment in fixtures
# These imports must be delayed until DYNAMODB_ENDPOINT is set


# ---------------------------------------------------------------------------
# GDPR deletion test helpers
# ---------------------------------------------------------------------------
# Each helper seeds one or more rows into a named table. Helpers are plain
# functions (not pytest fixtures) because they take per-test parameters
# (user_id, sub_id, counts) — fixtures with that surface area would either
# need parametrize-per-test or factory closures, both noisier than just
# calling a helper.


def _seed_user_profile(
    dynamodb_client,
    users_table_name: str,
    user_id: str,
    stripe_subscription_id: str | None = None,
) -> dict:
    """Seed a row in the users table for the given user_id.

    Returns the item written so callers can assert on shape after deletion.
    Pass stripe_subscription_id to put a user on the paying-subscriber path
    that _cancel_stripe_subscription exercises.
    """
    item = {
        "user_id": {"S": user_id},
        "email": {"S": f"{user_id}@example.test"},
        "created_at": {"N": str(int(time.time()))},
    }
    if stripe_subscription_id is not None:
        item["stripe_subscription_id"] = {"S": stripe_subscription_id}
    dynamodb_client.put_item(TableName=users_table_name, Item=item)
    return item


def _seed_coupon_redemption(
    dynamodb_client,
    coupons_table_name: str,
    code: str,
    redeemed_by_user_ids: list,
) -> dict:
    """Seed one coupon with a redeemed_by string-set membership.

    The redeemed_by attribute MUST be SS (String Set), because the production
    code's _remove_from_coupon_redeemed_by uses both `contains(redeemed_by,
    :uid)` (works on SS) and `DELETE redeemed_by :user_set` (set-element
    removal, also SS-specific). A list-typed attribute would not exercise
    the same code path.
    """
    item = {
        "code": {"S": code},
        "tier": {"S": "subscriber"},
        "redeemed_by": {"SS": list(redeemed_by_user_ids)},
    }
    dynamodb_client.put_item(TableName=coupons_table_name, Item=item)
    return item


def _seed_token_cap_rows(
    dynamodb_client,
    token_cap_table_name: str,
    user_id: str,
    count: int,
) -> int:
    """Seed `count` rate-limit window rows under PK=USER#{user_id}.

    Each row uses a distinct SK so the composite key is unique. Returns
    the count actually seeded, for symmetric verification in the caller.
    """
    pk = f"USER#{user_id}"
    for i in range(count):
        dynamodb_client.put_item(
            TableName=token_cap_table_name,
            Item={
                "PK": {"S": pk},
                "SK": {"S": f"WINDOW#{i:04d}"},
                "tokens_used": {"N": str(100 * (i + 1))},
            },
        )
    return count


class TestDeleteUserData:
    """Tests for delete_user_data() — GDPR Article 17 erasure procedure.

    Covers the full state space of (profile present, analysis records,
    Stripe subscription, coupon redemptions, token-cap rows) both
    individually and in interaction. The procedure returns a 5-key summary
    dict; tests verify the counts in the dict AND the actual state of each
    DynamoDB table after the call.
    """

    def test_010_delete_user_data_happy_path(
        self, dynamodb_client, agent_state_table, users_table, sample_user_data
    ):
        """Profile + 10 analysis records, no Stripe → analysis_records=10, profile_deleted=True."""
        import src.lambda_auth_function as auth_module

        auth_module._dynamodb_client = None

        user_id = "test-user-1"
        _seed_user_profile(dynamodb_client, users_table, user_id)

        # Preconditions
        records_before = dynamodb_client.query(
            TableName=agent_state_table,
            IndexName="user_id-index",
            KeyConditionExpression="user_id = :uid",
            ExpressionAttributeValues={":uid": {"S": user_id}},
        )
        assert len(records_before["Items"]) == 10
        profile_before = dynamodb_client.get_item(
            TableName=users_table, Key={"user_id": {"S": user_id}}
        )
        assert "Item" in profile_before

        result = auth_module.delete_user_data(user_id)

        # Summary dict
        assert result["analysis_records"] == 10
        assert result["profile_deleted"] is True
        assert result["stripe_cancelled"] is False  # no subscription on this profile
        assert result["coupons_updated"] == 0
        assert result["rate_limits_deleted"] == 0

        # Actual table state
        records_after = dynamodb_client.query(
            TableName=agent_state_table,
            IndexName="user_id-index",
            KeyConditionExpression="user_id = :uid",
            ExpressionAttributeValues={":uid": {"S": user_id}},
        )
        assert len(records_after["Items"]) == 0
        profile_after = dynamodb_client.get_item(
            TableName=users_table, Key={"user_id": {"S": user_id}}
        )
        assert "Item" not in profile_after

    def test_011_profile_only(
        self, dynamodb_client, agent_state_table, users_table
    ):
        """Profile exists, no analysis records → profile deleted, analysis_records=0.

        Covers the case where a user OAuth'd but never used the analyzer
        (so `get_or_create_user` created a profile row but `save_state` was
        never called). Before this test was added, only test_010 covered
        the `profile_deleted is True` path, and it required sample_user_data
        too — so the standalone-profile case was uncovered.
        """
        import src.lambda_auth_function as auth_module

        auth_module._dynamodb_client = None

        user_id = "profile-only-user"
        _seed_user_profile(dynamodb_client, users_table, user_id)

        result = auth_module.delete_user_data(user_id)

        assert result["analysis_records"] == 0
        assert result["profile_deleted"] is True
        assert result["stripe_cancelled"] is False
        assert result["coupons_updated"] == 0
        assert result["rate_limits_deleted"] == 0

        profile_after = dynamodb_client.get_item(
            TableName=users_table, Key={"user_id": {"S": user_id}}
        )
        assert "Item" not in profile_after

    def test_020_delete_user_data_pagination(
        self, dynamodb_client, agent_state_table, users_table, large_user_data
    ):
        """Profile + 2000 analysis records (triggers >1MB pagination) → all wiped."""
        import src.lambda_auth_function as auth_module

        auth_module._dynamodb_client = None

        user_id = "large-user"
        _seed_user_profile(dynamodb_client, users_table, user_id)

        # Verify item count before (with pagination)
        response = dynamodb_client.query(
            TableName=agent_state_table,
            IndexName="user_id-index",
            KeyConditionExpression="user_id = :uid",
            ExpressionAttributeValues={":uid": {"S": user_id}},
            Select="COUNT",
        )
        initial_count = response["Count"]
        while response.get("LastEvaluatedKey"):
            response = dynamodb_client.query(
                TableName=agent_state_table,
                IndexName="user_id-index",
                KeyConditionExpression="user_id = :uid",
                ExpressionAttributeValues={":uid": {"S": user_id}},
                Select="COUNT",
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            initial_count += response["Count"]
        assert initial_count == 2000

        result = auth_module.delete_user_data(user_id)

        assert result["analysis_records"] == 2000
        assert result["profile_deleted"] is True

        # No records remain
        response = dynamodb_client.query(
            TableName=agent_state_table,
            IndexName="user_id-index",
            KeyConditionExpression="user_id = :uid",
            ExpressionAttributeValues={":uid": {"S": user_id}},
            Select="COUNT",
        )
        assert response["Count"] == 0

    def test_030_delete_user_data_no_items(
        self, dynamodb_client, agent_state_table
    ):
        """Nonexistent user (no data anywhere) → all counts zero, profile_deleted=False.

        Pre-#680 this test asserted `profile_deleted is True` for a
        nonexistent user. That was logically backwards: `_delete_user_profile`
        correctly returns False when no row existed to delete (it uses
        ReturnValues=ALL_OLD and checks Attributes is not None). Production
        code is right; the assertion was wrong.
        """
        import src.lambda_auth_function as auth_module

        auth_module._dynamodb_client = None

        user_id = "nonexistent-user"

        result = auth_module.delete_user_data(user_id)

        assert result["analysis_records"] == 0
        assert result["profile_deleted"] is False  # correctly False — no profile existed
        assert result["stripe_cancelled"] is False  # no profile → early-return path
        assert result["coupons_updated"] == 0
        assert result["rate_limits_deleted"] == 0

    def test_031_records_only_orphan(
        self, dynamodb_client, agent_state_table, sample_user_data
    ):
        """Records exist, no profile → records wiped, profile_deleted=False.

        Models a partial-erasure-mid-flight or data-integrity scenario.
        The procedure should still wipe what's there (the analysis records)
        and report profile_deleted=False truthfully (no profile was present
        to delete). Note this test does NOT use the users_table fixture's
        seeded profile — the autouse cleanup_tables fixture guarantees the
        users table is empty.
        """
        import src.lambda_auth_function as auth_module

        auth_module._dynamodb_client = None

        user_id = "test-user-1"  # sample_user_data seeds records for this user

        result = auth_module.delete_user_data(user_id)

        assert result["analysis_records"] == 10
        assert result["profile_deleted"] is False

        # Records still got wiped
        response = dynamodb_client.query(
            TableName=agent_state_table,
            IndexName="user_id-index",
            KeyConditionExpression="user_id = :uid",
            ExpressionAttributeValues={":uid": {"S": user_id}},
        )
        assert len(response["Items"]) == 0

    def test_032_stripe_subscriber_cancel_succeeds(
        self, dynamodb_client, agent_state_table, users_table
    ):
        """Profile with stripe_subscription_id, cancel mock returns OK → stripe_cancelled=True.

        Patches `stripe.Subscription.cancel` and `auth.stripe_handler.get_stripe_api_key`
        at the import sites, since `_cancel_stripe_subscription` imports them
        lazily inside its try block.
        """
        import src.lambda_auth_function as auth_module

        auth_module._dynamodb_client = None

        user_id = "stripe-subscriber"
        sub_id = "sub_test_123"
        _seed_user_profile(
            dynamodb_client,
            users_table,
            user_id,
            stripe_subscription_id=sub_id,
        )

        with patch("stripe.Subscription.cancel") as mock_cancel, patch(
            "auth.stripe_handler.get_stripe_api_key", return_value="sk_test_fake"
        ):
            result = auth_module.delete_user_data(user_id)
            mock_cancel.assert_called_once_with(sub_id)

        assert result["stripe_cancelled"] is True
        assert result["profile_deleted"] is True

    def test_033_stripe_cancel_fails_but_rest_completes(
        self,
        dynamodb_client,
        agent_state_table,
        users_table,
        sample_user_data,
    ):
        """Stripe.cancel raises → stripe_cancelled=False, but profile+records still wiped.

        Verifies _cancel_stripe_subscription's broad except is genuinely
        non-cascading: a Stripe-side failure must not abort the rest of
        delete_user_data, because the user has the right to erasure on the
        surfaces we DO control even when an external API is unavailable.
        """
        import src.lambda_auth_function as auth_module

        auth_module._dynamodb_client = None

        user_id = "test-user-1"
        sub_id = "sub_test_456"
        _seed_user_profile(
            dynamodb_client,
            users_table,
            user_id,
            stripe_subscription_id=sub_id,
        )

        with patch(
            "stripe.Subscription.cancel", side_effect=Exception("Stripe API down")
        ), patch(
            "auth.stripe_handler.get_stripe_api_key", return_value="sk_test_fake"
        ):
            result = auth_module.delete_user_data(user_id)

        assert result["stripe_cancelled"] is False
        assert result["profile_deleted"] is True  # rest completed
        assert result["analysis_records"] == 10

        # Profile actually gone from the table
        profile_after = dynamodb_client.get_item(
            TableName=users_table, Key={"user_id": {"S": user_id}}
        )
        assert "Item" not in profile_after

    def test_034_coupon_single_redemption(
        self, dynamodb_client, agent_state_table, users_table, coupons_table
    ):
        """Profile + 1 coupon redemption → coupons_updated=1, user_id removed from set."""
        import src.lambda_auth_function as auth_module

        auth_module._dynamodb_client = None

        user_id = "coupon-user"
        _seed_user_profile(dynamodb_client, users_table, user_id)
        _seed_coupon_redemption(
            dynamodb_client,
            coupons_table,
            "TESTCODE001",
            redeemed_by_user_ids=[user_id, "other-user"],
        )

        result = auth_module.delete_user_data(user_id)

        assert result["coupons_updated"] == 1

        # Coupon row still exists, but user_id is no longer in redeemed_by
        coupon = dynamodb_client.get_item(
            TableName=coupons_table, Key={"code": {"S": "TESTCODE001"}}
        )
        assert "Item" in coupon
        remaining = coupon["Item"]["redeemed_by"]["SS"]
        assert user_id not in remaining
        assert "other-user" in remaining

    def test_035_coupon_many_redemptions_pagination(
        self, dynamodb_client, agent_state_table, users_table, coupons_table
    ):
        """Profile + many coupon redemptions → all updated, exercises the scan loop.

        moto does not enforce DynamoDB's 1MB scan boundary identically to
        AWS, so this test exercises the production loop structure rather
        than the boundary itself. 100 coupons keeps the test fast (~1s) while
        still walking the pagination code path.
        """
        import src.lambda_auth_function as auth_module

        auth_module._dynamodb_client = None

        user_id = "popular-user"
        _seed_user_profile(dynamodb_client, users_table, user_id)

        coupon_count = 100
        for i in range(coupon_count):
            _seed_coupon_redemption(
                dynamodb_client,
                coupons_table,
                f"BULK{i:04d}",
                redeemed_by_user_ids=[user_id],
            )

        result = auth_module.delete_user_data(user_id)

        assert result["coupons_updated"] == coupon_count

        # Spot-check three coupons across the range: user_id must be absent.
        # When the only element of a DynamoDB SS is deleted, the attribute
        # itself is removed from the row entirely — accept either "no
        # redeemed_by attribute" or "redeemed_by present but missing user_id".
        for code in ("BULK0000", "BULK0050", "BULK0099"):
            coupon = dynamodb_client.get_item(
                TableName=coupons_table, Key={"code": {"S": code}}
            )
            redeemed_by_attr = coupon["Item"].get("redeemed_by")
            if redeemed_by_attr is not None:
                assert user_id not in redeemed_by_attr["SS"]

    def test_036_token_cap_rows(
        self,
        dynamodb_client,
        agent_state_table,
        users_table,
        token_cap_table,
    ):
        """Profile + N token-cap rows under PK=USER#{user_id} → all wiped."""
        import src.lambda_auth_function as auth_module

        auth_module._dynamodb_client = None

        user_id = "rate-limited-user"
        _seed_user_profile(dynamodb_client, users_table, user_id)
        seeded = _seed_token_cap_rows(
            dynamodb_client, token_cap_table, user_id, count=5
        )
        assert seeded == 5

        result = auth_module.delete_user_data(user_id)

        assert result["rate_limits_deleted"] == 5

        rows = dynamodb_client.query(
            TableName=token_cap_table,
            KeyConditionExpression="PK = :pk",
            ExpressionAttributeValues={":pk": {"S": f"USER#{user_id}"}},
        )
        assert len(rows["Items"]) == 0

    def test_037_full_spectrum(
        self,
        dynamodb_client,
        agent_state_table,
        users_table,
        coupons_table,
        token_cap_table,
        sample_user_data,
    ):
        """Every column of the state space active → every surface wiped.

        The integration validator. If a future refactor of delete_user_data
        forgets one of the five surfaces, this test catches it: not only the
        summary dict's counts but also the actual DynamoDB rows.
        """
        import src.lambda_auth_function as auth_module

        auth_module._dynamodb_client = None

        user_id = "test-user-1"  # sample_user_data already seeded 10 records
        sub_id = "sub_full_spectrum"

        _seed_user_profile(
            dynamodb_client,
            users_table,
            user_id,
            stripe_subscription_id=sub_id,
        )
        _seed_coupon_redemption(
            dynamodb_client,
            coupons_table,
            "FULLSPEC1",
            redeemed_by_user_ids=[user_id],
        )
        _seed_token_cap_rows(dynamodb_client, token_cap_table, user_id, count=3)

        with patch("stripe.Subscription.cancel") as mock_cancel, patch(
            "auth.stripe_handler.get_stripe_api_key", return_value="sk_test_fake"
        ):
            result = auth_module.delete_user_data(user_id)
            mock_cancel.assert_called_once_with(sub_id)

        # Summary dict — all five counts
        assert result["analysis_records"] == 10
        assert result["profile_deleted"] is True
        assert result["stripe_cancelled"] is True
        assert result["coupons_updated"] == 1
        assert result["rate_limits_deleted"] == 3

        # Actual table state — every surface
        records = dynamodb_client.query(
            TableName=agent_state_table,
            IndexName="user_id-index",
            KeyConditionExpression="user_id = :uid",
            ExpressionAttributeValues={":uid": {"S": user_id}},
        )
        assert len(records["Items"]) == 0

        profile = dynamodb_client.get_item(
            TableName=users_table, Key={"user_id": {"S": user_id}}
        )
        assert "Item" not in profile

        coupon = dynamodb_client.get_item(
            TableName=coupons_table, Key={"code": {"S": "FULLSPEC1"}}
        )
        redeemed_by_attr = coupon["Item"].get("redeemed_by")
        if redeemed_by_attr is not None:
            assert user_id not in redeemed_by_attr["SS"]

        rate_limits = dynamodb_client.query(
            TableName=token_cap_table,
            KeyConditionExpression="PK = :pk",
            ExpressionAttributeValues={":pk": {"S": f"USER#{user_id}"}},
        )
        assert len(rate_limits["Items"]) == 0


class TestSaveState:
    """Tests for save_state() with TTL verification."""

    def test_040_save_state_with_ttl(self, dynamodb_client, agent_state_table):
        """
        Scenario 040: save_state() sets ttl attribute correctly.

        TTL should be now + 30 days (2592000 seconds).
        """
        import src.lambda_function as main_module

        main_module._dynamodb_client = None

        thread_id = "ttl-test-thread"
        now = int(time.time())

        # Call save_state
        main_module.save_state(
            thread_id,
            {
                "text": "Test input for TTL",
                "url": "https://example.com",
                "safety_score": {"score": 0.9},
            },
        )

        # Query the item
        response = dynamodb_client.scan(
            TableName=agent_state_table,
            FilterExpression="thread_id = :tid",
            ExpressionAttributeValues={":tid": {"S": thread_id}},
        )

        assert len(response["Items"]) == 1
        item = response["Items"][0]

        # Verify TTL is set to approximately now + 30 days
        ttl_value = int(item["ttl"]["N"])
        expected_ttl = now + (30 * 24 * 60 * 60)  # 30 days in seconds

        # Allow 60 second tolerance for test execution time
        assert abs(ttl_value - expected_ttl) < 60, (
            f"TTL {ttl_value} not within 60s of expected {expected_ttl}"
        )

        # Verify other fields
        assert item["input"]["S"] == "Test input for TTL"
        assert item["url"]["S"] == "https://example.com"


class TestGSIQuery:
    """Tests for GSI (Global Secondary Index) query functionality."""

    def test_050_gsi_query_returns_correct_user(
        self, dynamodb_client, agent_state_table, multiple_users_data
    ):
        """
        Scenario 050: GSI query returns only items for target user.

        With items for 3 users, querying for user-bob should only return
        user-bob's items, not items from user-alice or user-charlie.
        """
        # Query for user-bob
        response = dynamodb_client.query(
            TableName=agent_state_table,
            IndexName="user_id-index",
            KeyConditionExpression="user_id = :uid",
            ExpressionAttributeValues={":uid": {"S": "user-bob"}},
        )

        # Should return exactly 5 items (all for user-bob)
        assert len(response["Items"]) == 5

        # Verify all items belong to user-bob (check via primary key pattern)
        for item in response["Items"]:
            assert item["thread_id"]["S"].startswith("user-bob-thread-")

        # Verify user-alice items are NOT included
        for item in response["Items"]:
            assert "alice" not in item["thread_id"]["S"]
            assert "charlie" not in item["thread_id"]["S"]


class TestTableCreation:
    """Tests for table creation with GSI."""

    def test_060_table_creation_with_gsi(self, dynamodb_client, agent_state_table):
        """
        Scenario 060: Table created with GSI is queryable.

        Verifies:
        - Table exists and is ACTIVE
        - GSI exists and is ACTIVE
        - GSI is queryable
        """
        # Describe table
        response = dynamodb_client.describe_table(TableName=agent_state_table)
        table = response["Table"]

        # Verify table is ACTIVE
        assert table["TableStatus"] == "ACTIVE"

        # Verify GSI exists
        gsi_list = table.get("GlobalSecondaryIndexes", [])
        assert len(gsi_list) == 1
        gsi = gsi_list[0]

        # Verify GSI configuration
        assert gsi["IndexName"] == "user_id-index"
        assert gsi["IndexStatus"] == "ACTIVE"

        # Verify GSI key schema
        key_schema = gsi["KeySchema"]
        assert len(key_schema) == 1
        assert key_schema[0]["AttributeName"] == "user_id"
        assert key_schema[0]["KeyType"] == "HASH"

        # Verify GSI is queryable (empty query should work)
        response = dynamodb_client.query(
            TableName=agent_state_table,
            IndexName="user_id-index",
            KeyConditionExpression="user_id = :uid",
            ExpressionAttributeValues={":uid": {"S": "test-query"}},
        )
        assert "Items" in response  # Query succeeded
