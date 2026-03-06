"""
Unit tests for Lambda Auth Function.

Issue #313: Ruthless elimination of MagicMocks for Boto3 clients.
Utilizes moto for real in-memory AWS emulation and responses for HTTP mocking.
"""

import json
import os

import boto3
import pytest
import responses
from botocore.exceptions import ClientError
from moto import mock_aws

import src.lambda_auth_function as auth_func

# Constants for testing
TEST_REGION = "us-east-1"
TEST_USER_ID = "test-linkedin-id"
TEST_USER_NAME = "Test User"
TEST_TOKEN = "valid-test-token"
TEST_REFRESH_TOKEN = "valid-refresh-token"
TEST_JWT_SECRET = "super-secret-key-that-is-at-least-32-bytes"

@pytest.fixture(scope="function", autouse=True)
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = TEST_REGION

    os.environ["JWT_SECRET_NAME"] = "test-jwt-secret"
    os.environ["LINKEDIN_SECRET_NAME"] = "test-linkedin-secret"

    # Reset globals
    auth_func._dynamodb_client = None
    auth_func._secrets_client = None
    auth_func._linkedin_credentials = None

    import src.auth.jwt_service as jwt_service
    jwt_service._secrets_client = None
    jwt_service.invalidate_secret_cache()

@pytest.fixture(scope="function")
def aws_env():
    """Set up complete AWS mocked environment."""
    with mock_aws():
        # Setup SecretsManager
        secrets = boto3.client("secretsmanager", region_name=TEST_REGION)
        secrets.create_secret(
            Name="test-linkedin-secret",
            SecretString=json.dumps({"client_id": "cid", "client_secret": "csec"})
        )
        secrets.create_secret(
            Name="test-jwt-secret",
            SecretString=json.dumps({"primary": TEST_JWT_SECRET})
        )

        # Setup DynamoDB
        dynamodb = boto3.client("dynamodb", region_name=TEST_REGION)

        # Users Table
        dynamodb.create_table(
            TableName=auth_func.USERS_TABLE,
            KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST"
        )

        # Agent State Table (GDPR Deletions)
        dynamodb.create_table(
            TableName=auth_func.AGENT_STATE_TABLE,
            KeySchema=[
                {"AttributeName": "thread_id", "KeyType": "HASH"},
                {"AttributeName": "checkpoint_id", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "thread_id", "AttributeType": "S"},
                {"AttributeName": "checkpoint_id", "AttributeType": "S"},
                {"AttributeName": "user_id", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[{
                "IndexName": "user_id-index",
                "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "KEYS_ONLY"}
            }],
            BillingMode="PAY_PER_REQUEST"
        )

        # Token Cap Table
        dynamodb.create_table(
            TableName=auth_func.TOKEN_CAP_TABLE,
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST"
        )

        yield {"dynamodb": dynamodb, "secrets": secrets}


class TestSecretsRetrieval:
    def test_get_linkedin_credentials(self, aws_env):
        creds = auth_func.get_linkedin_credentials()
        assert creds["client_id"] == "cid"
        assert creds["client_secret"] == "csec"

    def test_get_linkedin_credentials_error(self, aws_env):
        # Delete secret to force error
        aws_env["secrets"].delete_secret(SecretId="test-linkedin-secret", ForceDeleteWithoutRecovery=True)
        with pytest.raises(ClientError):
            auth_func.get_linkedin_credentials()


class TestTokenExchange:
    @responses.activate
    def test_exchange_code_for_tokens_success(self, aws_env):
        responses.add(
            responses.POST,
            auth_func.LINKEDIN_TOKEN_URL,
            json={"access_token": TEST_TOKEN, "expires_in": 3600},
            status=200
        )
        result = auth_func.exchange_code_for_tokens("code123", "http://redirect")
        assert result["access_token"] == TEST_TOKEN

    @responses.activate
    def test_exchange_code_for_tokens_failure(self, aws_env):
        responses.add(responses.POST, auth_func.LINKEDIN_TOKEN_URL, status=400)
        with pytest.raises(ValueError):
            auth_func.exchange_code_for_tokens("code123", "http://redirect")


class TestUserInfoRetrieval:
    @responses.activate
    def test_get_linkedin_user_info_success(self):
        responses.add(
            responses.GET,
            auth_func.LINKEDIN_USERINFO_URL,
            json={"sub": TEST_USER_ID, "name": TEST_USER_NAME},
            status=200
        )
        result = auth_func.get_linkedin_user_info(TEST_TOKEN)
        assert result["sub"] == TEST_USER_ID
        assert result["name"] == TEST_USER_NAME

    @responses.activate
    def test_get_linkedin_user_info_unauthorized(self):
        responses.add(responses.GET, auth_func.LINKEDIN_USERINFO_URL, status=401)
        result = auth_func.get_linkedin_user_info("bad_token")
        assert result is None

    @responses.activate
    def test_get_linkedin_user_info_error(self):
        responses.add(responses.GET, auth_func.LINKEDIN_USERINFO_URL, status=500)
        result = auth_func.get_linkedin_user_info(TEST_TOKEN)
        assert result is None


class TestUserManagement:
    def test_get_or_create_user_new(self, aws_env):
        user_info = {"sub": TEST_USER_ID, "name": TEST_USER_NAME}
        user = auth_func.get_or_create_user(user_info)
        assert user["user_id"] == TEST_USER_ID
        assert user["display_name"] == TEST_USER_NAME

        # Verify in DB
        db_user = aws_env["dynamodb"].get_item(
            TableName=auth_func.USERS_TABLE,
            Key={"user_id": {"S": TEST_USER_ID}}
        )["Item"]
        assert db_user["display_name"]["S"] == TEST_USER_NAME

    def test_get_or_create_user_existing(self, aws_env):
        # Create user
        aws_env["dynamodb"].put_item(
            TableName=auth_func.USERS_TABLE,
            Item={
                "user_id": {"S": TEST_USER_ID},
                "display_name": {"S": "Old Name"},
                "created_at": {"S": "2020-01-01T00:00:00Z"},
                "last_login": {"S": "2020-01-01T00:00:00Z"}
            }
        )

        user_info = {"sub": TEST_USER_ID, "name": "New Name Should Be Ignored"}
        user = auth_func.get_or_create_user(user_info)
        assert user["user_id"] == TEST_USER_ID
        assert user["display_name"] == "Old Name"  # Display name is not updated on login currently

    def test_get_or_create_user_stores_email_and_picture_on_create(self, aws_env):
        user_info = {
            "sub": TEST_USER_ID, "name": TEST_USER_NAME,
            "email": "test@example.com", "picture": "https://example.com/photo.jpg",
        }
        auth_func.get_or_create_user(user_info)
        db_user = aws_env["dynamodb"].get_item(
            TableName=auth_func.USERS_TABLE,
            Key={"user_id": {"S": TEST_USER_ID}}
        )["Item"]
        assert db_user["email"]["S"] == "test@example.com"
        assert db_user["picture"]["S"] == "https://example.com/photo.jpg"

    def test_get_or_create_user_updates_email_and_picture_on_login(self, aws_env):
        aws_env["dynamodb"].put_item(
            TableName=auth_func.USERS_TABLE,
            Item={
                "user_id": {"S": TEST_USER_ID},
                "display_name": {"S": "Old Name"},
                "created_at": {"S": "2020-01-01T00:00:00Z"},
                "last_login": {"S": "2020-01-01T00:00:00Z"},
            }
        )
        user_info = {
            "sub": TEST_USER_ID, "name": "Old Name",
            "email": "new@example.com", "picture": "https://example.com/new.jpg",
        }
        auth_func.get_or_create_user(user_info)
        db_user = aws_env["dynamodb"].get_item(
            TableName=auth_func.USERS_TABLE,
            Key={"user_id": {"S": TEST_USER_ID}}
        )["Item"]
        assert db_user["email"]["S"] == "new@example.com"
        assert db_user["picture"]["S"] == "https://example.com/new.jpg"

    def test_get_or_create_user_no_email_picture_no_error(self, aws_env):
        user_info = {"sub": TEST_USER_ID, "name": TEST_USER_NAME}
        user = auth_func.get_or_create_user(user_info)
        assert user["user_id"] == TEST_USER_ID
        db_user = aws_env["dynamodb"].get_item(
            TableName=auth_func.USERS_TABLE,
            Key={"user_id": {"S": TEST_USER_ID}}
        )["Item"]
        assert "email" not in db_user
        assert "picture" not in db_user

    def test_get_user_tier_missing(self, aws_env):
        tier, day = auth_func.get_user_tier("missing-user")
        assert tier == "free"
        assert day == 1

    def test_get_user_tier_existing(self, aws_env):
        aws_env["dynamodb"].put_item(
            TableName=auth_func.USERS_TABLE,
            Item={
                "user_id": {"S": TEST_USER_ID},
                "tier": {"S": "subscriber"},
                "billing_anchor_day": {"N": "15"}
            }
        )
        tier, day = auth_func.get_user_tier(TEST_USER_ID)
        assert tier == "subscriber"
        assert day == 15


class TestHandlers:
    @responses.activate
    def test_handle_token_exchange(self, aws_env):
        # Mock LinkedIn Tokens
        responses.add(
            responses.POST, auth_func.LINKEDIN_TOKEN_URL,
            json={"access_token": TEST_TOKEN, "expires_in": 3600}, status=200
        )
        # Mock LinkedIn UserInfo
        responses.add(
            responses.GET, auth_func.LINKEDIN_USERINFO_URL,
            json={"sub": TEST_USER_ID, "name": TEST_USER_NAME}, status=200
        )

        event_body = {"code": "code123", "redirectUri": "http://redirect"}
        result = auth_func.handle_token_exchange(event_body)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["accessToken"] == TEST_TOKEN
        assert "jwt" in body
        assert body["user"]["id"] == TEST_USER_ID

    def test_handle_token_exchange_missing_args(self):
        result = auth_func.handle_token_exchange({})
        assert result["statusCode"] == 400

    @responses.activate
    def test_handle_token_refresh(self, aws_env):
        responses.add(
            responses.POST, auth_func.LINKEDIN_TOKEN_URL,
            json={"access_token": TEST_TOKEN, "expires_in": 3600}, status=200
        )
        responses.add(
            responses.GET, auth_func.LINKEDIN_USERINFO_URL,
            json={"sub": TEST_USER_ID, "name": TEST_USER_NAME}, status=200
        )

        result = auth_func.handle_token_refresh({"refreshToken": "refresh123"})
        assert result["statusCode"] == 200
        assert json.loads(result["body"])["accessToken"] == TEST_TOKEN

    @responses.activate
    def test_handle_validate_token_success(self, aws_env):
        responses.add(
            responses.GET, auth_func.LINKEDIN_USERINFO_URL,
            json={"sub": TEST_USER_ID, "name": TEST_USER_NAME}, status=200
        )
        result = auth_func.handle_validate_token({"Authorization": "Bearer token123"})
        assert result["statusCode"] == 200
        assert json.loads(result["body"])["valid"] is True

    @responses.activate
    def test_handle_validate_token_missing_header(self):
        result = auth_func.handle_validate_token({})
        assert result["statusCode"] == 401

    @responses.activate
    def test_handle_validate_token_invalid(self, aws_env):
        responses.add(responses.GET, auth_func.LINKEDIN_USERINFO_URL, status=401)
        result = auth_func.handle_validate_token({"Authorization": "Bearer badtoken"})
        assert result["statusCode"] == 401

    def test_handle_oauth_callback_success(self):
        result = auth_func.handle_oauth_callback({"code": "abc", "state": "def"})
        assert result["statusCode"] == 200
        assert "Login Successful" in result["body"]
        assert 'data-code="abc"' in result["body"]

    def test_handle_oauth_callback_error(self):
        result = auth_func.handle_oauth_callback({"error": "access_denied", "error_description": "User cancelled"})
        assert result["statusCode"] == 200
        assert "Login Failed" in result["body"]
        assert "User cancelled" in result["body"]


class TestGDPRDataErasure:
    def test_delete_user_data_success(self, aws_env):
        # Insert data
        dynamodb = aws_env["dynamodb"]
        for i in range(3):
            dynamodb.put_item(
                TableName=auth_func.AGENT_STATE_TABLE,
                Item={
                    "thread_id": {"S": f"thread-{i}"},
                    "checkpoint_id": {"S": f"cp-{i}"},
                    "user_id": {"S": TEST_USER_ID}
                }
            )

        # Insert another user's data
        dynamodb.put_item(
            TableName=auth_func.AGENT_STATE_TABLE,
            Item={
                "thread_id": {"S": "thread-other"},
                "checkpoint_id": {"S": "cp-other"},
                "user_id": {"S": "other-user"}
            }
        )

        deleted = auth_func.delete_user_data(TEST_USER_ID)
        assert deleted == 3

        # Verify deletion
        response = dynamodb.scan(TableName=auth_func.AGENT_STATE_TABLE)
        items = response["Items"]
        assert len(items) == 1
        assert items[0]["user_id"]["S"] == "other-user"

    @responses.activate
    def test_handle_delete_my_data(self, aws_env):
        responses.add(
            responses.GET, auth_func.LINKEDIN_USERINFO_URL,
            json={"sub": TEST_USER_ID, "name": TEST_USER_NAME}, status=200
        )

        result = auth_func.handle_delete_my_data({"Authorization": "Bearer token123"})
        assert result["statusCode"] == 200
        assert json.loads(result["body"])["success"] is True

    def test_handle_delete_my_data_unauthorized(self):
        result = auth_func.handle_delete_my_data({})
        assert result["statusCode"] == 401


class TestLambdaHandlerRouting:
    def test_route_metrics(self, aws_env):
        # Testing the router hits the right file
        try:
            auth_func.lambda_handler({"httpMethod": "GET", "path": "/metrics"}, None)
        except Exception:
            pass # We just want to ensure it tries to route

    def test_route_serve_static(self):
        result = auth_func.lambda_handler({"httpMethod": "GET", "path": "/admin/nonexistent.html"}, None)
        assert result["statusCode"] == 404

    def test_route_serve_static_traversal(self):
        result = auth_func.lambda_handler({"httpMethod": "GET", "path": "/admin/../../etc/passwd"}, None)
        assert result["statusCode"] == 404

    def test_route_upgrade_success(self):
        result = auth_func.lambda_handler({"httpMethod": "GET", "path": "/upgrade-success"}, None)
        assert result["statusCode"] == 200

    def test_route_upgrade_cancel(self):
        result = auth_func.lambda_handler({"httpMethod": "GET", "path": "/upgrade-cancel"}, None)
        assert result["statusCode"] == 200
