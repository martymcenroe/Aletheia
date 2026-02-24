"""GitHub OAuth handler for admin dashboard access.

Implements the GitHub OAuth Web Application flow to authenticate
admin dashboard users. Only repo collaborators with push access
are granted admin JWTs.

Issue #433: GitHub OAuth for admin dashboard.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import time

import boto3
import requests
from botocore.exceptions import ClientError

try:
    from .jwt_service import create_jwt, get_jwt_secret
except ImportError:
    from jwt_service import create_jwt, get_jwt_secret  # type: ignore[no-redef]

logger = logging.getLogger(__name__)

# GitHub OAuth endpoints
GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"  # noqa: S105
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_REPO_URL = "https://api.github.com/repos/martymcenroe/Aletheia"

# CSRF state token lifetime
STATE_TTL_SECONDS = 300  # 5 minutes

# Dashboard redirect target
DASHBOARD_URL = "https://api.aletheia.study/admin/metrics.html"

# Callback URL for GitHub OAuth
CALLBACK_URL = "https://api.aletheia.study/auth/github/callback"

# Credentials cache
_github_credentials: dict | None = None
_github_credentials_time: float = 0.0
_CREDENTIALS_CACHE_TTL = 300  # 5 minutes
_secrets_client = None


def _get_secrets_client():
    """Lazy-initialize Secrets Manager client."""
    global _secrets_client
    if _secrets_client is None:
        region = os.environ.get("AWS_REGION", "us-east-1")
        _secrets_client = boto3.client("secretsmanager", region_name=region)
    return _secrets_client


def get_github_credentials() -> dict:
    """Retrieve GitHub OAuth credentials from Secrets Manager.

    Cached for 5 minutes to minimize API calls. Same pattern as
    LinkedIn credentials in lambda_auth_function.py.

    Returns:
        Dict with client_id and client_secret.

    Raises:
        ClientError: If secret retrieval fails.
    """
    global _github_credentials, _github_credentials_time

    now = time.time()
    if _github_credentials is not None and (now - _github_credentials_time) < _CREDENTIALS_CACHE_TTL:
        return _github_credentials

    client = _get_secrets_client()
    secret_name = os.environ.get("GITHUB_SECRET_NAME", "aletheia/github-oauth")
    try:
        response = client.get_secret_value(SecretId=secret_name)
        result: dict = json.loads(response["SecretString"])
        _github_credentials = result
        _github_credentials_time = now
        return result
    except ClientError as e:
        logger.error("Failed to retrieve GitHub credentials: %s", e)
        raise


def _generate_state(jwt_secret: str) -> str:
    """Generate HMAC-signed CSRF state token.

    Format: {timestamp}.{hmac_hex}
    The HMAC is computed over the timestamp using the JWT signing secret,
    making it stateless (no database needed).

    Args:
        jwt_secret: The JWT signing secret to use as HMAC key.

    Returns:
        State string in format "timestamp.hmac".
    """
    timestamp = str(int(time.time()))
    signature = hmac.new(
        jwt_secret.encode(), timestamp.encode(), hashlib.sha256
    ).hexdigest()
    return f"{timestamp}.{signature}"


def _validate_state(state: str, jwt_secret: str) -> bool:
    """Validate HMAC-signed CSRF state token.

    Checks both the HMAC signature and the timestamp freshness
    (must be within STATE_TTL_SECONDS).

    Args:
        state: The state string to validate.
        jwt_secret: The JWT signing secret used as HMAC key.

    Returns:
        True if state is valid and fresh, False otherwise.
    """
    if not state or "." not in state:
        return False

    parts = state.split(".", 1)
    if len(parts) != 2:
        return False

    timestamp_str, provided_sig = parts

    try:
        timestamp = int(timestamp_str)
    except ValueError:
        return False

    # Check freshness
    if abs(time.time() - timestamp) > STATE_TTL_SECONDS:
        return False

    # Verify HMAC
    expected_sig = hmac.new(
        jwt_secret.encode(), timestamp_str.encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(provided_sig, expected_sig)


def handle_github_authorize(query_params: dict) -> dict:
    """Handle GET /auth/github/authorize — redirect to GitHub OAuth.

    Generates a CSRF state token and redirects the user to GitHub's
    OAuth authorization page.

    Args:
        query_params: Query string parameters (unused, included for consistency).

    Returns:
        302 redirect response to GitHub OAuth.
    """
    try:
        credentials = get_github_credentials()
        jwt_secret = get_jwt_secret()
        state = _generate_state(jwt_secret)

        authorize_url = (
            f"{GITHUB_AUTHORIZE_URL}"
            f"?client_id={credentials['client_id']}"
            f"&redirect_uri={CALLBACK_URL}"
            f"&state={state}"
            f"&scope=read:org"
        )

        return {
            "statusCode": 302,
            "headers": {
                "Location": authorize_url,
                "Cache-Control": "no-store",
            },
            "body": "",
        }
    except Exception as e:
        logger.error("GitHub authorize error: %s", e)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Internal server error"}),
        }


def handle_github_callback(query_params: dict) -> dict:
    """Handle GET /auth/github/callback — exchange code and issue admin JWT.

    Flow:
    1. Validate CSRF state token
    2. Exchange authorization code for GitHub access token
    3. Fetch GitHub user info
    4. Check collaborator status on martymcenroe/Aletheia
    5. Issue admin JWT with tier="admin" and user_id="gh:{github_id}"
    6. Redirect to dashboard with JWT in query param

    Args:
        query_params: Query string parameters with code and state.

    Returns:
        302 redirect to dashboard on success, or error HTML page.
    """
    code = query_params.get("code", "")
    state = query_params.get("state", "")
    error = query_params.get("error", "")

    if error:
        error_description = query_params.get("error_description", error)
        logger.warning("GitHub OAuth error: %s - %s", error, error_description)
        return _error_page("Authorization Failed", error_description)

    if not code or not state:
        return _error_page("Invalid Request", "Missing authorization code or state parameter.")

    try:
        jwt_secret = get_jwt_secret()
    except Exception as e:
        logger.error("Failed to get JWT secret: %s", e)
        return _error_page("Internal Error", "Unable to process authentication.")

    # 1. Validate CSRF state
    if not _validate_state(state, jwt_secret):
        logger.warning("Invalid or expired state token in GitHub callback")
        return _error_page("Session Expired", "Your login session has expired. Please try again.")

    # 2. Exchange code for GitHub access token
    try:
        credentials = get_github_credentials()
        token_response = requests.post(
            GITHUB_TOKEN_URL,
            data={
                "client_id": credentials["client_id"],
                "client_secret": credentials["client_secret"],
                "code": code,
                "redirect_uri": CALLBACK_URL,
            },
            headers={"Accept": "application/json"},
            timeout=10,
        )

        if token_response.status_code != 200:
            logger.error("GitHub token exchange failed: HTTP %s", token_response.status_code)
            return _error_page("Authentication Failed", "Unable to verify your GitHub account.")

        token_data = token_response.json()
        if "error" in token_data:
            logger.error("GitHub token error: %s", token_data.get("error_description", token_data["error"]))
            return _error_page("Authentication Failed", "Unable to verify your GitHub account.")

        access_token = token_data["access_token"]
    except requests.RequestException as e:
        logger.error("GitHub token exchange network error: %s", e)
        return _error_page("Authentication Failed", "Unable to connect to GitHub.")

    # 3. Fetch GitHub user info
    try:
        user_response = requests.get(
            GITHUB_USER_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
            timeout=10,
        )
        if user_response.status_code != 200:
            logger.error("GitHub user info failed: %s", user_response.status_code)
            return _error_page("Authentication Failed", "Unable to retrieve your GitHub profile.")

        user_data = user_response.json()
        github_id = str(user_data["id"])
        github_login = user_data.get("login", "unknown")
    except requests.RequestException as e:
        logger.error("GitHub user info network error: %s", e)
        return _error_page("Authentication Failed", "Unable to connect to GitHub.")

    # 4. Check collaborator status
    try:
        repo_response = requests.get(
            GITHUB_REPO_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
            timeout=10,
        )
        if repo_response.status_code != 200:
            logger.warning("Non-collaborator login attempt: %s (gh:%s)", github_login, github_id)
            return _error_page("Access Denied", "You must be a collaborator on the Aletheia repository.")

        repo_data = repo_response.json()
        permissions = repo_data.get("permissions", {})
        if not permissions.get("push", False):
            logger.warning("Collaborator without push access: %s (gh:%s)", github_login, github_id)
            return _error_page("Access Denied", "You need push access to the Aletheia repository.")
    except requests.RequestException as e:
        logger.error("GitHub repo check network error: %s", e)
        return _error_page("Authentication Failed", "Unable to verify repository access.")

    # 5. Issue admin JWT
    user_id = f"gh:{github_id}"
    try:
        admin_jwt = create_jwt(
            user_id, jwt_secret, expiry_hours=24,
            tier="admin", billing_anchor_day=1,
        )
    except Exception as e:
        logger.error("Failed to create admin JWT: %s", e)
        return _error_page("Internal Error", "Unable to create authentication token.")

    logger.info("Admin login successful: %s (gh:%s)", github_login, github_id)

    # 6. Redirect to dashboard with JWT
    return {
        "statusCode": 302,
        "headers": {
            "Location": f"{DASHBOARD_URL}?jwt={admin_jwt}",
            "Cache-Control": "no-store",
        },
        "body": "",
    }


def _error_page(title: str, message: str) -> dict:
    """Generate an HTML error page for OAuth failures.

    Args:
        title: Error page heading.
        message: Error description to display.

    Returns:
        HTTP response dict with error HTML.
    """
    # Escape for safe HTML insertion
    import html
    safe_title = html.escape(title)
    safe_message = html.escape(message)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/html; charset=utf-8",
            "Cache-Control": "no-store",
        },
        "body": f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Aletheia - {safe_title}</title>
    <style>
        body {{ font-family: system-ui, sans-serif; max-width: 420px; margin: 80px auto; text-align: center; color: #333; }}
        h1 {{ color: #dc3545; font-size: 1.5rem; }}
        p {{ margin: 1rem 0; line-height: 1.5; }}
        a {{ color: #4ecdc4; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>{safe_title}</h1>
    <p>{safe_message}</p>
    <p><a href="{DASHBOARD_URL}">Back to Dashboard</a></p>
</body>
</html>""",
    }


def invalidate_credentials_cache() -> None:
    """Invalidate cached GitHub credentials. Useful for testing."""
    global _github_credentials, _github_credentials_time
    _github_credentials = None
    _github_credentials_time = 0.0
