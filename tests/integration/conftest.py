"""
DynamoDB Local integration test fixtures.

Issue #264: DynamoDB integration test infrastructure.
LLD: docs/lld/active/1264-dynamodb-integration-fixtures.md

Uses testcontainers-python to manage DynamoDB Local container.
Sets DYNAMODB_ENDPOINT env var for Lambda code to connect to local instance.
"""

import os
import time
from typing import Generator

import boto3
import pytest
from botocore.exceptions import ClientError
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

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


@pytest.fixture(scope="session")
def dynamodb_endpoint() -> Generator[str, None, None]:
    """
    Get DynamoDB endpoint - uses existing if set (CI), otherwise starts container (local).

    Dual-mode behavior (per Gemini implementation review):
    - CI mode: DYNAMODB_ENDPOINT already set by GitHub Actions service container
    - Local mode: Start container via testcontainers-python

    This avoids running two DynamoDB instances in CI (wasteful).
    """
    existing_endpoint = os.environ.get("DYNAMODB_ENDPOINT")
    if existing_endpoint:
        # CI mode: use existing service container, no cleanup needed
        yield existing_endpoint
        return

    # Local mode: start container via testcontainers
    container = DockerContainer("amazon/dynamodb-local:latest")
    container.with_exposed_ports(8000)
    container.start()

    # Wait for DynamoDB Local to be ready
    wait_for_logs(container, "Initializing DynamoDB Local", timeout=30)
    # Give it a moment to fully initialize
    time.sleep(1)

    host = container.get_container_host_ip()
    port = container.get_exposed_port(8000)
    endpoint = f"http://{host}:{port}"

    yield endpoint

    container.stop()


@pytest.fixture(scope="session")
def dynamodb_client(dynamodb_endpoint: str):
    """
    Create boto3 DynamoDB client pointing to local instance.

    Sets env vars so Lambda code uses local instance.
    Also sets table name env vars so Lambda code uses fixture tables:
    - DYNAMODB_TABLE: used by lambda_function.py save_state()
    - AGENT_STATE_TABLE: used by lambda_auth_function.py delete_user_data()
    """
    # Only set DYNAMODB_ENDPOINT if not already set (local mode)
    endpoint_was_set = "DYNAMODB_ENDPOINT" in os.environ
    if not endpoint_was_set:
        os.environ["DYNAMODB_ENDPOINT"] = dynamodb_endpoint

    os.environ["AWS_ACCESS_KEY_ID"] = "testing"  # noqa: S105
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"  # noqa: S105
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

    # Set table name env vars to match fixture table names
    # lambda_function.py uses DYNAMODB_TABLE (default: aletheia-state)
    # lambda_auth_function.py uses AGENT_STATE_TABLE (default: AletheiaAgentState)
    table_name: str = AGENT_STATE_TABLE_SCHEMA["TableName"]  # type: ignore[assignment]
    os.environ["DYNAMODB_TABLE"] = table_name
    os.environ["AGENT_STATE_TABLE"] = table_name

    client = boto3.client(
        "dynamodb",
        endpoint_url=dynamodb_endpoint,
        region_name="us-east-1",
        aws_access_key_id="testing",  # noqa: S106
        aws_secret_access_key="testing",  # noqa: S106
    )

    yield client

    # Cleanup env vars only if we set them
    if not endpoint_was_set:
        del os.environ["DYNAMODB_ENDPOINT"]
    del os.environ["DYNAMODB_TABLE"]
    del os.environ["AGENT_STATE_TABLE"]


@pytest.fixture(scope="session")
def agent_state_table(dynamodb_client) -> str:
    """
    Create AletheiaAgentState table with GSI.

    Session-scoped - table persists for all tests, data is cleaned per-test.
    """
    table_name: str = AGENT_STATE_TABLE_SCHEMA["TableName"]  # type: ignore[assignment]

    try:
        dynamodb_client.create_table(**AGENT_STATE_TABLE_SCHEMA)
        # Wait for table to be active
        waiter = dynamodb_client.get_waiter("table_exists")
        waiter.wait(TableName=table_name, WaiterConfig={"Delay": 1, "MaxAttempts": 30})
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceInUseException":
            raise

    return table_name


@pytest.fixture(scope="session")
def users_table(dynamodb_client) -> str:
    """Create aletheia-users table."""
    table_name: str = USERS_TABLE_SCHEMA["TableName"]  # type: ignore[assignment]

    try:
        dynamodb_client.create_table(**USERS_TABLE_SCHEMA)
        waiter = dynamodb_client.get_waiter("table_exists")
        waiter.wait(TableName=table_name, WaiterConfig={"Delay": 1, "MaxAttempts": 30})
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceInUseException":
            raise

    return table_name


@pytest.fixture(autouse=True)
def cleanup_tables(dynamodb_client, agent_state_table, users_table):
    """
    Delete all items after each test.

    Autouse ensures isolation between tests without table recreation overhead.
    Per LLD Section 6.2.
    """
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
        # Handle pagination
        while response.get("LastEvaluatedKey"):
            response = dynamodb_client.scan(
                TableName=agent_state_table,
                ProjectionExpression="thread_id, checkpoint_id",
                ExclusiveStartKey=response["LastEvaluatedKey"],
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
        pass  # Table might not exist yet

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


@pytest.fixture
def sample_user_data(dynamodb_client, agent_state_table) -> list[dict]:
    """
    Insert 10 items for test-user-1.

    Returns list of inserted items for verification.
    """
    user_id = "test-user-1"
    items = []
    now = int(time.time())

    for i in range(10):
        item = {
            "thread_id": {"S": f"thread-{i}"},
            "checkpoint_id": {"S": str(now * 1000 + i)},
            "user_id": {"S": user_id},
            "input": {"S": f"Test input {i}"},
            "ttl": {"N": str(now + 86400 * 30)},  # 30 days TTL
        }
        dynamodb_client.put_item(TableName=agent_state_table, Item=item)
        items.append(item)

    return items


@pytest.fixture
def large_user_data(dynamodb_client, agent_state_table) -> list[dict]:
    """
    Insert 2000 items to trigger pagination.

    DynamoDB Query returns max 1MB per request, requiring pagination.
    Per LLD Section 4.3.
    """
    user_id = "large-user"
    items = []
    now = int(time.time())

    # Use batch_write_item for efficiency (25 items per batch)
    for batch_start in range(0, 2000, 25):
        batch_items = []
        for i in range(batch_start, min(batch_start + 25, 2000)):
            item = {
                "thread_id": {"S": f"thread-{i}"},
                "checkpoint_id": {"S": str(now * 1000 + i)},
                "user_id": {"S": user_id},
                "input": {"S": f"Test input {i} " + "x" * 500},  # ~500 bytes per item
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
    """
    Insert items for 3 different users for GSI query testing.

    Returns dict mapping user_id to list of their items.
    """
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
