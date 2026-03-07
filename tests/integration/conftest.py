"""
DynamoDB integration test fixtures using moto.

Replaces testcontainers-python to eliminate Docker dependency on Windows.
Uses moto.mock_aws to provide a complete, fast, in-memory AWS emulation.
"""

import os
import time

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

# Table schemas matching production (from provision.sh)
AGENT_STATE_TABLE_SCHEMA = {
    "TableName": "AletheiaAgentState",
    "KeySchema": [
        {"AttributeName": "thread_id", "KeyType": "HASH"},
        {"AttributeName": "checkpoint_id", "KeyType": "RANGE"},
    ],
    "AttributeDefinitions": [
        {"AttributeName": "thread_id", "AttributeType": "S"},
        {"AttributeName": "checkpoint_id", "AttributeType": "S"},
        {"AttributeName": "user_id", "AttributeType": "S"},
    ],
    "GlobalSecondaryIndexes": [
        {
            "IndexName": "user_id-index",
            "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
            "Projection": {"ProjectionType": "KEYS_ONLY"},
        }
    ],
    "BillingMode": "PAY_PER_REQUEST",
}

USERS_TABLE_SCHEMA = {
    "TableName": "aletheia-users",
    "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
    "AttributeDefinitions": [
        {"AttributeName": "user_id", "AttributeType": "S"},
    ],
    "BillingMode": "PAY_PER_REQUEST",
}

COUPONS_TABLE_SCHEMA = {
    "TableName": "aletheia-coupons",
    "KeySchema": [{"AttributeName": "code", "KeyType": "HASH"}],
    "AttributeDefinitions": [
        {"AttributeName": "code", "AttributeType": "S"},
    ],
    "BillingMode": "PAY_PER_REQUEST",
}

TOKEN_CAP_TABLE_SCHEMA = {
    "TableName": "aletheia-token-cap",
    "KeySchema": [
        {"AttributeName": "PK", "KeyType": "HASH"},
        {"AttributeName": "SK", "KeyType": "RANGE"},
    ],
    "AttributeDefinitions": [
        {"AttributeName": "PK", "AttributeType": "S"},
        {"AttributeName": "SK", "AttributeType": "S"},
    ],
    "BillingMode": "PAY_PER_REQUEST",
}


@pytest.fixture(scope="session")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture(scope="session")
def dynamodb_client(aws_credentials):
    """
    Create boto3 DynamoDB client using moto.

    Sets env vars so Lambda code uses fixture tables.
    """
    with mock_aws():
        # Set table name env vars to match fixture table names
        table_name: str = AGENT_STATE_TABLE_SCHEMA["TableName"]  # type: ignore[assignment]
        os.environ["DYNAMODB_TABLE"] = table_name
        os.environ["AGENT_STATE_TABLE"] = table_name

        token_cap_name: str = TOKEN_CAP_TABLE_SCHEMA["TableName"]  # type: ignore[assignment]
        os.environ["TOKEN_CAP_TABLE"] = token_cap_name

        coupons_name: str = COUPONS_TABLE_SCHEMA["TableName"]  # type: ignore[assignment]
        os.environ["COUPONS_TABLE"] = coupons_name

        # Explicitly remove endpoint override if it exists so boto3 hits moto interceptor
        if "DYNAMODB_ENDPOINT" in os.environ:
            del os.environ["DYNAMODB_ENDPOINT"]

        client = boto3.client("dynamodb", region_name="us-east-1")
        yield client

        # Cleanup
        del os.environ["DYNAMODB_TABLE"]
        del os.environ["AGENT_STATE_TABLE"]
        del os.environ["TOKEN_CAP_TABLE"]
        del os.environ["COUPONS_TABLE"]


@pytest.fixture(scope="session")
def agent_state_table(dynamodb_client) -> str:
    """Create AletheiaAgentState table with GSI."""
    table_name: str = AGENT_STATE_TABLE_SCHEMA["TableName"]  # type: ignore[assignment]
    dynamodb_client.create_table(**AGENT_STATE_TABLE_SCHEMA)
    return table_name


@pytest.fixture(scope="session")
def users_table(dynamodb_client) -> str:
    """Create aletheia-users table."""
    table_name: str = USERS_TABLE_SCHEMA["TableName"]  # type: ignore[assignment]
    dynamodb_client.create_table(**USERS_TABLE_SCHEMA)
    return table_name


@pytest.fixture(scope="session")
def token_cap_table(dynamodb_client) -> str:
    """Create aletheia-token-cap table for rate limiting."""
    table_name: str = TOKEN_CAP_TABLE_SCHEMA["TableName"]  # type: ignore[assignment]
    dynamodb_client.create_table(**TOKEN_CAP_TABLE_SCHEMA)
    return table_name


@pytest.fixture(scope="session")
def coupons_table(dynamodb_client) -> str:
    """Create aletheia-coupons table."""
    table_name: str = COUPONS_TABLE_SCHEMA["TableName"]  # type: ignore[assignment]
    dynamodb_client.create_table(**COUPONS_TABLE_SCHEMA)
    return table_name


@pytest.fixture(autouse=True)
def cleanup_tables(dynamodb_client, agent_state_table, users_table, token_cap_table, coupons_table):
    """Delete all items after each test."""
    yield  # Test runs here

    # Cleanup agent_state_table
    try:
        response = dynamodb_client.scan(
            TableName=agent_state_table,
            ProjectionExpression="thread_id, checkpoint_id",
        )
        for item in response.get("Items", []):
            dynamodb_client.delete_item(
                TableName=agent_state_table,
                Key={
                    "thread_id": item["thread_id"],
                    "checkpoint_id": item["checkpoint_id"],
                },
            )
    except ClientError:
        pass

    # Cleanup users_table
    try:
        response = dynamodb_client.scan(
            TableName=users_table,
            ProjectionExpression="user_id",
        )
        for item in response.get("Items", []):
            dynamodb_client.delete_item(
                TableName=users_table,
                Key={"user_id": item["user_id"]},
            )
    except ClientError:
        pass

    # Cleanup token_cap_table
    try:
        response = dynamodb_client.scan(
            TableName=token_cap_table,
            ProjectionExpression="PK, SK",
        )
        for item in response.get("Items", []):
            dynamodb_client.delete_item(
                TableName=token_cap_table,
                Key={"PK": item["PK"], "SK": item["SK"]},
            )
    except ClientError:
        pass

    # Cleanup coupons_table
    try:
        response = dynamodb_client.scan(
            TableName=coupons_table,
            ProjectionExpression="code",
        )
        for item in response.get("Items", []):
            dynamodb_client.delete_item(
                TableName=coupons_table,
                Key={"code": item["code"]},
            )
    except ClientError:
        pass

    # Reset rate limiter singletons
    import src.auth.auth_middleware as _mw
    _mw._tier_config_service = None
    _mw._multi_window_counter = None


@pytest.fixture
def sample_user_data(dynamodb_client, agent_state_table) -> list[dict]:
    """Insert 10 items for test-user-1."""
    user_id = "test-user-1"
    items = []
    now = int(time.time())

    for i in range(10):
        item = {
            "thread_id": {"S": f"thread-{i}"},
            "checkpoint_id": {"S": str(now * 1000 + i)},
            "user_id": {"S": user_id},
            "input": {"S": f"Test input {i}"},
            "ttl": {"N": str(now + 86400 * 30)},
        }
        dynamodb_client.put_item(TableName=agent_state_table, Item=item)
        items.append(item)

    return items


@pytest.fixture
def large_user_data(dynamodb_client, agent_state_table) -> list[dict]:
    """Insert 2000 items to trigger pagination."""
    user_id = "large-user"
    items = []
    now = int(time.time())

    for batch_start in range(0, 2000, 25):
        batch_items = []
        for i in range(batch_start, min(batch_start + 25, 2000)):
            item = {
                "thread_id": {"S": f"thread-{i}"},
                "checkpoint_id": {"S": str(now * 1000 + i)},
                "user_id": {"S": user_id},
                "input": {"S": f"Test input {i} " + "x" * 500},
                "ttl": {"N": str(now + 86400 * 30)},
            }
            batch_items.append({"PutRequest": {"Item": item}})
            items.append(item)

        dynamodb_client.batch_write_item(
            RequestItems={agent_state_table: batch_items}
        )

    return items


@pytest.fixture
def multiple_users_data(dynamodb_client, agent_state_table) -> dict[str, list[dict]]:
    """Insert items for 3 different users for GSI query testing."""
    now = int(time.time())
    users_data: dict[str, list[dict]] = {
        "user-alice": [],
        "user-bob": [],
        "user-charlie": [],
    }

    for user_id, user_items in users_data.items():
        for i in range(5):
            item = {
                "thread_id": {"S": f"{user_id}-thread-{i}"},
                "checkpoint_id": {"S": str(now * 1000 + i)},
                "user_id": {"S": user_id},
                "input": {"S": f"Input from {user_id}"},
                "ttl": {"N": str(now + 86400 * 30)},
            }
            dynamodb_client.put_item(TableName=agent_state_table, Item=item)
            user_items.append(item)

    return users_data
