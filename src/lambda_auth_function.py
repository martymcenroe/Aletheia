"""
Lambda Auth Function - LinkedIn OAuth Token Exchange and Validation.

Handles:
- Token exchange (auth code → tokens)
- Token refresh (refresh token → new tokens)
- User creation/lookup in DynamoDB

See: docs/1116-linkedin-oauth.md

Issue #116: LinkedIn OAuth Authentication
"""

import json
import logging
import os
import time
from typing import Any

import boto3
import requests
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuration
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
USERS_TABLE = os.environ.get("USERS_TABLE", "aletheia-users")

# LinkedIn OAuth endpoints
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"

# Lazy-initialized clients
_dynamodb_client = None
_secrets_client = None
_linkedin_credentials = None


def get_dynamodb_client():
    """Lazy-initialize DynamoDB client."""
    global _dynamodb_client
    if _dynamodb_client is None:
        _dynamodb_client = boto3.client("dynamodb", region_name=AWS_REGION)
    return _dynamodb_client


def get_secrets_client():
    """Lazy-initialize Secrets Manager client."""
    global _secrets_client
    if _secrets_client is None:
        _secrets_client = boto3.client("secretsmanager", region_name=AWS_REGION)
    return _secrets_client


def get_linkedin_credentials() -> dict:
    """
    Retrieve LinkedIn OAuth credentials from Secrets Manager.

    Cached after first retrieval for warm start optimization.
    """
    global _linkedin_credentials
    if _linkedin_credentials is None:
        client = get_secrets_client()
        secret_name = os.environ.get("LINKEDIN_SECRET_NAME", "aletheia/linkedin-oauth")
        try:
            response = client.get_secret_value(SecretId=secret_name)
            _linkedin_credentials = json.loads(response["SecretString"])
        except ClientError as e:
            logger.error(f"Failed to retrieve LinkedIn credentials: {e}")
            raise
    return _linkedin_credentials


def exchange_code_for_tokens(code: str, redirect_uri: str) -> dict:
    """
    Exchange authorization code for access and refresh tokens.

    Args:
        code: Authorization code from LinkedIn OAuth callback.
        redirect_uri: The redirect URI used in the auth request.

    Returns:
        Dict with access_token, refresh_token, expires_in.

    Raises:
        ValueError: If token exchange fails.
    """
    credentials = get_linkedin_credentials()

    response = requests.post(
        LINKEDIN_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": credentials["client_id"],
            "client_secret": credentials["client_secret"],
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10,
    )

    if response.status_code != 200:
        logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
        raise ValueError(f"Token exchange failed: {response.status_code}")

    return response.json()


def refresh_access_token(refresh_token: str) -> dict:
    """
    Use refresh token to obtain new access token.

    Args:
        refresh_token: The refresh token from previous auth.

    Returns:
        Dict with new access_token and expires_in.

    Raises:
        ValueError: If refresh fails.
    """
    credentials = get_linkedin_credentials()

    response = requests.post(
        LINKEDIN_TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": credentials["client_id"],
            "client_secret": credentials["client_secret"],
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10,
    )

    if response.status_code != 200:
        logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
        raise ValueError(f"Token refresh failed: {response.status_code}")

    return response.json()


def get_linkedin_user_info(access_token: str) -> dict | None:
    """
    Validate token and retrieve user info from LinkedIn.

    This validates the token by calling LinkedIn's userinfo endpoint.
    The response contains the OIDC claims (sub, name, etc.).

    Args:
        access_token: LinkedIn access token.

    Returns:
        User info dict with sub, name, etc., or None if invalid.
    """
    response = requests.get(
        LINKEDIN_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )

    if response.status_code == 200:
        return response.json()
    elif response.status_code == 401:
        logger.warning("LinkedIn token validation failed: 401 Unauthorized")
        return None
    else:
        logger.error(f"LinkedIn userinfo error: {response.status_code}")
        return None


def get_or_create_user(user_info: dict) -> dict:
    """
    Get existing user or create new one in DynamoDB.

    Uses LinkedIn OIDC 'sub' as the primary key (user_id).
    See: docs/1116-linkedin-oauth.md Section 1 (User Identity Decision)

    Args:
        user_info: LinkedIn OIDC userinfo response.

    Returns:
        User record dict.
    """
    client = get_dynamodb_client()
    user_id = user_info["sub"]  # LinkedIn's stable member ID
    display_name = user_info.get("name", "Unknown")
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Try to get existing user
    try:
        response = client.get_item(
            TableName=USERS_TABLE,
            Key={"user_id": {"S": user_id}},
        )
        if "Item" in response:
            # Update last_login
            client.update_item(
                TableName=USERS_TABLE,
                Key={"user_id": {"S": user_id}},
                UpdateExpression="SET last_login = :now",
                ExpressionAttributeValues={":now": {"S": now}},
            )
            return {
                "user_id": user_id,
                "display_name": response["Item"]["display_name"]["S"],
                "created_at": response["Item"]["created_at"]["S"],
                "last_login": now,
            }
    except ClientError as e:
        logger.error(f"DynamoDB get_item error: {e}")
        raise

    # Create new user
    try:
        client.put_item(
            TableName=USERS_TABLE,
            Item={
                "user_id": {"S": user_id},
                "display_name": {"S": display_name},
                "created_at": {"S": now},
                "last_login": {"S": now},
            },
        )
        logger.info(f"Created new user: {user_id}")
        return {
            "user_id": user_id,
            "display_name": display_name,
            "created_at": now,
            "last_login": now,
        }
    except ClientError as e:
        logger.error(f"DynamoDB put_item error: {e}")
        raise


def handle_token_exchange(body: dict) -> dict:
    """
    Handle POST /auth/token - Exchange auth code for tokens.

    Expected body: { "code": "...", "redirectUri": "..." }
    """
    code = body.get("code")
    redirect_uri = body.get("redirectUri")

    # Debug logging for redirect URI mismatch issues
    logger.info(f"Token exchange request - redirectUri: {redirect_uri}")
    logger.info(f"Token exchange request - code length: {len(code) if code else 0}")

    if not code or not redirect_uri:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing code or redirectUri"}),
        }

    try:
        # 1. Exchange code for tokens
        tokens = exchange_code_for_tokens(code, redirect_uri)

        # 2. Validate token and get user info
        user_info = get_linkedin_user_info(tokens["access_token"])
        if user_info is None:
            return {
                "statusCode": 401,
                "body": json.dumps({"error": "Token validation failed"}),
            }

        # 3. Create or update user in DynamoDB
        user = get_or_create_user(user_info)

        # 4. Return tokens and user info to extension
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "accessToken": tokens["access_token"],
                "refreshToken": tokens.get("refresh_token"),
                "expiresIn": tokens.get("expires_in", 3600),
                "user": {
                    "id": user["user_id"],
                    "name": user["display_name"],
                },
            }),
        }

    except ValueError as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": str(e)}),
        }
    except Exception as e:
        logger.error(f"Token exchange error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"}),
        }


def handle_token_refresh(body: dict) -> dict:
    """
    Handle POST /auth/refresh - Refresh access token.

    Expected body: { "refreshToken": "..." }
    """
    refresh_token = body.get("refreshToken")

    if not refresh_token:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing refreshToken"}),
        }

    try:
        # Refresh tokens
        tokens = refresh_access_token(refresh_token)

        # Validate new token
        user_info = get_linkedin_user_info(tokens["access_token"])
        if user_info is None:
            return {
                "statusCode": 401,
                "body": json.dumps({"error": "Token validation failed"}),
            }

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "accessToken": tokens["access_token"],
                "expiresIn": tokens.get("expires_in", 3600),
            }),
        }

    except ValueError as e:
        return {
            "statusCode": 401,
            "body": json.dumps({"error": str(e)}),
        }
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"}),
        }


def handle_validate_token(headers: dict) -> dict:
    """
    Handle GET /auth/validate - Validate access token.

    Expects Authorization header: Bearer <token>
    """
    auth_header = headers.get("Authorization", headers.get("authorization", ""))

    if not auth_header.startswith("Bearer "):
        return {
            "statusCode": 401,
            "body": json.dumps({"error": "Missing or invalid Authorization header"}),
        }

    token = auth_header.replace("Bearer ", "")
    user_info = get_linkedin_user_info(token)

    if user_info is None:
        return {
            "statusCode": 401,
            "body": json.dumps({"error": "Invalid token"}),
        }

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "valid": True,
            "user": {
                "id": user_info["sub"],
                "name": user_info.get("name", "Unknown"),
            },
        }),
    }


def lambda_handler(event: dict, context: Any) -> dict:
    """
    Main entry point for auth Lambda.

    Routes:
    - POST /auth/token - Exchange code for tokens
    - POST /auth/refresh - Refresh access token
    - GET /auth/validate - Validate access token

    See: docs/1116-linkedin-oauth.md
    """
    try:
        # Parse HTTP method and path
        http_method = event.get("requestContext", {}).get("http", {}).get("method", "")
        path = event.get("requestContext", {}).get("http", {}).get("path", "")

        # Also support direct invocation format
        if not http_method:
            http_method = event.get("httpMethod", "POST")
        if not path:
            path = event.get("path", "/auth/token")

        # Parse body
        body = {}
        if event.get("body"):
            body = (
                json.loads(event["body"])
                if isinstance(event["body"], str)
                else event["body"]
            )

        headers = event.get("headers", {})

        # Route to appropriate handler
        if path == "/auth/token" and http_method == "POST":
            return handle_token_exchange(body)
        elif path == "/auth/refresh" and http_method == "POST":
            return handle_token_refresh(body)
        elif path == "/auth/validate" and http_method == "GET":
            return handle_validate_token(headers)
        else:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Not found"}),
            }

    except Exception as e:
        logger.error(f"Unhandled error: {type(e).__name__}: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"}),
        }
