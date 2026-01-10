"""
DynamoDB integration tests for Lambda data operations.

Issue #264: DynamoDB integration test infrastructure.
LLD: docs/lld/active/1264-dynamodb-integration-fixtures.md Section 11.1

Test Scenarios:
- 010: delete_user_data happy path (10 items)
- 020: delete_user_data pagination (2000 items)
- 030: delete_user_data no items
- 040: save_state with TTL
- 050: GSI query returns correct user
- 060: Table creation with GSI
"""

import sys
import time
from pathlib import Path


# Add src to path for Lambda imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Import Lambda functions after setting up environment in fixtures
# These imports must be delayed until DYNAMODB_ENDPOINT is set


class TestDeleteUserData:
    """Tests for delete_user_data() GDPR function."""

    def test_010_delete_user_data_happy_path(
        self, dynamodb_client, agent_state_table, sample_user_data
    ):
        """
        Scenario 010: delete_user_data removes all 10 items for a user.

        Verifies:
        - All items are deleted
        - GSI query returns empty after deletion
        """
        # Import here after DYNAMODB_ENDPOINT is set
        # Reset module state to pick up new endpoint
        import src.lambda_auth_function as auth_module

        auth_module._dynamodb_client = None

        user_id = "test-user-1"

        # Verify items exist before deletion
        response = dynamodb_client.query(
            TableName=agent_state_table,
            IndexName="user_id-index",
            KeyConditionExpression="user_id = :uid",
            ExpressionAttributeValues={":uid": {"S": user_id}},
        )
        assert len(response["Items"]) == 10

        # Call delete_user_data
        deleted_count = auth_module.delete_user_data(user_id)

        # Verify all items deleted
        assert deleted_count == 10

        # Verify GSI query returns empty
        response = dynamodb_client.query(
            TableName=agent_state_table,
            IndexName="user_id-index",
            KeyConditionExpression="user_id = :uid",
            ExpressionAttributeValues={":uid": {"S": user_id}},
        )
        assert len(response["Items"]) == 0

    def test_020_delete_user_data_pagination(
        self, dynamodb_client, agent_state_table, large_user_data
    ):
        """
        Scenario 020: delete_user_data handles >1MB response (pagination).

        DynamoDB Query returns max 1MB per request.
        2000 items with ~500 bytes each = ~1MB, triggering pagination.
        """
        import src.lambda_auth_function as auth_module

        auth_module._dynamodb_client = None

        user_id = "large-user"

        # Verify items exist
        response = dynamodb_client.query(
            TableName=agent_state_table,
            IndexName="user_id-index",
            KeyConditionExpression="user_id = :uid",
            ExpressionAttributeValues={":uid": {"S": user_id}},
            Select="COUNT",
        )
        initial_count = response["Count"]
        # Handle pagination in count
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

        # Call delete_user_data
        deleted_count = auth_module.delete_user_data(user_id)

        # Verify all 2000 items deleted
        assert deleted_count == 2000

        # Verify no items remain
        response = dynamodb_client.query(
            TableName=agent_state_table,
            IndexName="user_id-index",
            KeyConditionExpression="user_id = :uid",
            ExpressionAttributeValues={":uid": {"S": user_id}},
            Select="COUNT",
        )
        assert response["Count"] == 0

    def test_030_delete_user_data_no_items(self, dynamodb_client, agent_state_table):
        """
        Scenario 030: delete_user_data handles user with no items gracefully.

        Should return 0 without error.
        """
        import src.lambda_auth_function as auth_module

        auth_module._dynamodb_client = None

        user_id = "nonexistent-user"

        # Verify no items exist
        response = dynamodb_client.query(
            TableName=agent_state_table,
            IndexName="user_id-index",
            KeyConditionExpression="user_id = :uid",
            ExpressionAttributeValues={":uid": {"S": user_id}},
        )
        assert len(response["Items"]) == 0

        # Call delete_user_data - should not raise
        deleted_count = auth_module.delete_user_data(user_id)

        # Verify 0 deleted
        assert deleted_count == 0


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
