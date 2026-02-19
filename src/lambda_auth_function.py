"""
Lambda Auth Function - LinkedIn OAuth Token Exchange and Validation.

Handles:
- Token exchange (auth code → tokens + JWT issuance)
- Token refresh (refresh token → new tokens)
- Token validation (stateless, via LinkedIn API)
- User creation/lookup in DynamoDB
- OAuth callback for Firefox (Issue #256)
- GDPR data erasure (Issue #147)

See: docs/1116-linkedin-oauth.md

Issue #116: LinkedIn OAuth Authentication
Issue #341: JWT authentication and daily token cap
Issue #364: Tiered rate limiting with multi-window caps
"""

import html
import json
import logging
import os
import time
from typing import Any

import boto3
import requests
from botocore.exceptions import ClientError

try:
    from .auth.jwt_service import create_jwt, get_jwt_secret
    from .auth.token_cap_service import check_and_increment_cap
except ImportError:
    from auth.jwt_service import create_jwt, get_jwt_secret  # type: ignore[no-redef]
    from auth.token_cap_service import check_and_increment_cap  # type: ignore[no-redef]

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuration
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
USERS_TABLE = os.environ.get("USERS_TABLE", "aletheia-users")
AGENT_STATE_TABLE = os.environ.get("AGENT_STATE_TABLE", "AletheiaAgentState")
TOKEN_CAP_TABLE = os.environ.get("TOKEN_CAP_TABLE", "aletheia-token-cap")

# LinkedIn OAuth endpoints
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"

# Lazy-initialized clients
_dynamodb_client = None
_secrets_client = None
_linkedin_credentials = None


def get_dynamodb_client():
    """Lazy-initialize DynamoDB client.

    Supports DYNAMODB_ENDPOINT env var for local testing with DynamoDB Local.
    Issue #264: DynamoDB integration test fixtures.
    """
    global _dynamodb_client
    if _dynamodb_client is None:
        endpoint = os.environ.get("DYNAMODB_ENDPOINT")
        if endpoint:
            _dynamodb_client = boto3.client(
                "dynamodb", endpoint_url=endpoint, region_name=AWS_REGION
            )
        else:
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


def validate_token(event: dict, context: Any) -> dict:
    """Validate a LinkedIn token by calling the LinkedIn API (stateless validation).

    This function is designed for direct Lambda invocation from the CLI client.
    It performs stateless validation by calling LinkedIn's userinfo endpoint
    to verify the token is valid and extract the user profile.

    Issue #116: Backend token validation for CLI OAuth flow.

    Args:
        event: Lambda event containing:
            - access_token (str): The LinkedIn access token to validate.
        context: Lambda context (unused).

    Returns:
        Dict with:
            - statusCode: 200 if valid, 401 if invalid, 502 if LinkedIn error.
            - body: JSON string with validation result and user profile,
              or error details.
    """
    access_token = None

    # Support multiple invocation patterns
    if isinstance(event, dict):
        # Direct invocation: {"access_token": "..."}
        access_token = event.get("access_token")

        # Also support body-wrapped format: {"body": "{\"access_token\": \"...\"}"}
        if not access_token and event.get("body"):
            try:
                body = (
                    json.loads(event["body"])
                    if isinstance(event["body"], str)
                    else event["body"]
                )
                access_token = body.get("access_token")
            except (json.JSONDecodeError, AttributeError):
                pass

        # Also support Authorization header format
        if not access_token:
            headers = event.get("headers", {})
            auth_header = headers.get(
                "Authorization", headers.get("authorization", "")
            )
            if auth_header.startswith("Bearer "):
                access_token = auth_header[7:]

    if not access_token:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Missing access_token"}),
        }

    try:
        profile = fetch_linkedin_profile(access_token)
    except Exception as e:
        logger.error(f"LinkedIn API error during token validation: {e}")
        return {
            "statusCode": 502,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "LinkedIn API error",
                "message": str(e),
            }),
        }

    if profile is None:
        return {
            "statusCode": 401,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Invalid token"}),
        }

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "valid": True,
            "user": {
                "id": profile.get("sub", ""),
                "name": profile.get("name", "Unknown"),
                "email": profile.get("email", ""),
                "picture": profile.get("picture"),
            },
        }),
    }


def fetch_linkedin_profile(access_token: str) -> dict | None:
    """Call LinkedIn API to fetch user profile (stateless validation).

    Makes a request to LinkedIn's OpenID Connect userinfo endpoint to
    validate the access token and retrieve the user's profile claims.

    Issue #116: Stateless backend token validation.

    Args:
        access_token: LinkedIn OAuth access token.

    Returns:
        Dict with LinkedIn profile claims (sub, name, email, picture, etc.)
        if the token is valid, or None if the token is invalid (401).

    Raises:
        requests.exceptions.RequestException: If there is a network error
            or LinkedIn returns a server error (5xx).
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
        # For server errors, raise so caller can return 502
        logger.error(
            f"LinkedIn API error: {response.status_code} - {response.text}"
        )
        response.raise_for_status()
        return None  # pragma: no cover


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


def get_user_tier(user_id: str) -> tuple[str, int]:
    """Look up user tier and billing anchor day from DynamoDB.

    Issue #364: Embed tier in JWT for per-request rate limiting.

    Args:
        user_id: The user's unique identifier (LinkedIn sub).

    Returns:
        Tuple of (tier, billing_anchor_day). Defaults to ("free", 1)
        if user record doesn't have these fields.
    """
    try:
        client = get_dynamodb_client()
        response = client.get_item(
            TableName=USERS_TABLE,
            Key={"user_id": {"S": user_id}},
            ProjectionExpression="tier, billing_anchor_day",
        )
        item = response.get("Item", {})
        tier = item.get("tier", {}).get("S", "free")
        billing_anchor_day = int(item.get("billing_anchor_day", {}).get("N", "1"))
        return tier, billing_anchor_day
    except (ClientError, KeyError, ValueError) as e:
        logger.warning(f"Failed to get user tier for {user_id}: {e}")
        return "free", 1


def handle_token_exchange(body: dict) -> dict:
    """
    Handle POST /auth/token - Exchange auth code for tokens and issue JWT.

    Issue #341: After LinkedIn validation, check daily token cap and issue
    a signed JWT for subsequent API authentication.

    Expected body: { "code": "...", "redirectUri": "..." }

    Flow (per LLD §2.5 "Auth Lambda - Token Issuance"):
    1. Exchange LinkedIn auth code for tokens
    2. Validate token and get user info
    3. Create or update user in DynamoDB
    4. Check daily token cap (return 503 if exceeded)
    5. Generate JWT with user_id, exp (24h), iat, jti
    6. Return JWT + user info to client
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

        # 4. Check daily token cap (Issue #341)
        try:
            allowed, current_count = check_and_increment_cap(TOKEN_CAP_TABLE)
        except Exception as e:
            # Fail closed: if cap check fails, deny token issuance
            logger.error(
                json.dumps({
                    "action": "token_denied",
                    "reason": "cap_check_failed",
                    "error": str(e),
                    "user_id": user["user_id"],
                })
            )
            return {
                "statusCode": 503,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "error": "Service temporarily unavailable",
                }),
            }

        if not allowed:
            logger.warning(
                json.dumps({
                    "action": "token_denied",
                    "reason": "daily_cap_exceeded",
                    "current_count": current_count,
                    "user_id": user["user_id"],
                })
            )
            return {
                "statusCode": 503,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "error": "Daily token limit exceeded. Please try again tomorrow.",
                }),
            }

        # 5. Generate JWT with tier (Issue #341, #364)
        try:
            jwt_secret = get_jwt_secret()
            tier, billing_anchor_day = get_user_tier(user["user_id"])
            jwt_token = create_jwt(
                user["user_id"], jwt_secret, expiry_hours=24,
                tier=tier, billing_anchor_day=billing_anchor_day,
            )
        except Exception as e:
            logger.error(f"JWT generation failed: {e}")
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Internal server error"}),
            }

        # 6. Return JWT + tokens and user info to extension
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "accessToken": tokens["access_token"],
                "refreshToken": tokens.get("refresh_token"),
                "expiresIn": tokens.get("expires_in", 3600),
                "jwt": jwt_token,
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

    Issue #116: Stateless validation via LinkedIn API.
    """
    auth_header = headers.get("Authorization", headers.get("authorization", ""))

    if not auth_header.startswith("Bearer "):
        return {
            "statusCode": 401,
            "body": json.dumps({"error": "Missing or invalid Authorization header"}),
        }

    token = auth_header.replace("Bearer ", "")

    try:
        profile = fetch_linkedin_profile(token)
    except Exception as e:
        logger.error(f"LinkedIn API error during validation: {e}")
        return {
            "statusCode": 502,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "LinkedIn API error",
                "message": str(e),
            }),
        }

    if profile is None:
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
                "id": profile["sub"],
                "name": profile.get("name", "Unknown"),
                "email": profile.get("email", ""),
                "picture": profile.get("picture"),
            },
        }),
    }


def delete_user_data(user_id: str) -> int:
    """
    Delete all DynamoDB items for a user from AletheiaAgentState table.

    Issue #147: GDPR Article 17 - Right to Erasure implementation.
    Uses GSI on user_id to efficiently query user's items.

    Args:
        user_id: LinkedIn OIDC 'sub' identifier.

    Returns:
        Count of items deleted.
    """
    client = get_dynamodb_client()
    deleted_count = 0

    try:
        # Query all items for this user using GSI
        response = client.query(
            TableName=AGENT_STATE_TABLE,
            IndexName="user_id-index",
            KeyConditionExpression="user_id = :uid",
            ExpressionAttributeValues={":uid": {"S": user_id}},
            ProjectionExpression="thread_id, checkpoint_id",
        )

        items = response.get("Items", [])

        # Handle pagination for users with many items
        while response.get("LastEvaluatedKey"):
            response = client.query(
                TableName=AGENT_STATE_TABLE,
                IndexName="user_id-index",
                KeyConditionExpression="user_id = :uid",
                ExpressionAttributeValues={":uid": {"S": user_id}},
                ProjectionExpression="thread_id, checkpoint_id",
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(response.get("Items", []))

        # Delete each item (DynamoDB requires primary key for deletion)
        for item in items:
            client.delete_item(
                TableName=AGENT_STATE_TABLE,
                Key={
                    "thread_id": item["thread_id"],
                    "checkpoint_id": item["checkpoint_id"],
                },
            )
            deleted_count += 1

        logger.info(f"GDPR erasure: deleted {deleted_count} items for user {user_id}")
        return deleted_count

    except ClientError as e:
        logger.error(f"GDPR erasure failed: {e}")
        raise


def handle_oauth_callback(query_params: dict) -> dict:
    """
    Handle GET /auth/callback - OAuth redirect endpoint for Firefox.

    Firefox doesn't have browser.identity API, so we use a Lambda callback.
    LinkedIn redirects here with ?code=...&state=...
    We return an HTML page that the extension can detect and extract the code from.

    Issue #256: Firefox OAuth tabs-based flow.
    Issue #262: XSS fix - escape all user-provided parameters.
    """
    # XSS prevention: escape all user-provided parameters before HTML insertion
    code = html.escape(query_params.get("code", ""))
    state = html.escape(query_params.get("state", ""))
    error = html.escape(query_params.get("error", ""))
    error_description = html.escape(query_params.get("error_description", ""))

    if error:
        # OAuth error from LinkedIn
        response_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Aletheia - Login Failed</title>
    <style>
        body {{ font-family: system-ui, sans-serif; max-width: 400px; margin: 50px auto; text-align: center; }}
        .error {{ color: #dc3545; }}
    </style>
</head>
<body>
    <h1 class="error">Login Failed</h1>
    <p>{error_description or error}</p>
    <p>You can close this tab.</p>
    <div id="oauth-result" data-error="{error}" data-error-description="{error_description}"></div>
</body>
</html>"""
    else:
        # Success - include code and state in a hidden div for extension to extract
        response_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Aletheia - Login Successful</title>
    <style>
        body {{ font-family: system-ui, sans-serif; max-width: 400px; margin: 50px auto; text-align: center; }}
        .success {{ color: #28a745; }}
        #oauth-result {{ display: none; }}
    </style>
</head>
<body>
    <h1 class="success">Login Successful!</h1>
    <p>You can close this tab and return to the extension.</p>
    <div id="oauth-result" data-code="{code}" data-state="{state}"></div>
</body>
</html>"""

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/html; charset=utf-8",
        },
        "body": response_html,
    }


def handle_delete_my_data(headers: dict) -> dict:
    """
    Handle DELETE /my-data - GDPR Article 17 data erasure endpoint.

    Issue #147: Implements user's right to erasure.
    Requires valid OAuth token to identify user.

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
            "body": json.dumps({"error": "Invalid token - cannot verify identity"}),
        }

    user_id = user_info["sub"]

    try:
        # Delete user's analysis data from agent state table
        deleted_count = delete_user_data(user_id)

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "success": True,
                "message": "Your data has been deleted",
                "itemsDeleted": deleted_count,
            }),
        }

    except ClientError as e:
        logger.error(f"GDPR deletion error for user {user_id}: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Deletion failed - please try again"}),
        }


def lambda_handler(event: dict, context: Any) -> dict:
    """
    Main entry point for auth Lambda.

    Routes:
    - POST /auth/token - Exchange code for tokens + issue JWT (Issue #341)
    - POST /auth/refresh - Refresh access token
    - GET /auth/validate - Validate access token
    - GET /auth/callback - OAuth callback for Firefox (Issue #256)
    - POST /auth/validate-token - Stateless token validation for CLI (Issue #116)
    - DELETE /my-data - GDPR erasure (Issue #147)

    See: docs/1116-linkedin-oauth.md, docs/1147-gdpr-data-erasure.md
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

        # Parse query string parameters (for callback)
        query_params = event.get("queryStringParameters", {}) or {}

        # Route to appropriate handler
        if path == "/auth/token" and http_method == "POST":
            return handle_token_exchange(body)
        elif path == "/auth/refresh" and http_method == "POST":
            return handle_token_refresh(body)
        elif path == "/auth/validate" and http_method == "GET":
            return handle_validate_token(headers)
        elif path == "/auth/validate-token" and http_method == "POST":
            return validate_token(event, context)
        elif path == "/auth/callback" and http_method == "GET":
            return handle_oauth_callback(query_params)
        elif path == "/my-data" and http_method == "DELETE":
            return handle_delete_my_data(headers)
        elif path == "/metrics" and http_method == "GET":
            # Issue #368: Admin-only business metrics dashboard
            from .auth.metrics_handler import handle_metrics_request
            return handle_metrics_request(event, context)
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
