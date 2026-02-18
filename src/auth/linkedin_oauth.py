"""Core OAuth flow implementation for LinkedIn authentication.

Provides functions to initiate the OAuth 2.0 authorization code flow,
handle the OAuth callback, exchange authorization codes for tokens, and
run a local HTTP server to receive the OAuth redirect.

The flow:
1. ``start_local_oauth_server`` binds a local HTTP server for the redirect.
2. ``initiate_oauth_flow`` builds the LinkedIn authorization URL with a CSPRNG
   state parameter and returns it.
3. The user authenticates in the browser; LinkedIn redirects to the local server.
4. ``handle_oauth_callback`` validates the state and extracts the auth code.
5. ``exchange_code_for_tokens`` exchanges the code for LinkedIn tokens.
6. ``run_oauth_login`` orchestrates the above into a single call.

Issue: #116
"""

from __future__ import annotations

import logging
import os
import secrets
import socket
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable, Optional
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

from .types import AuthError, LinkedInTokens

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LinkedIn OAuth 2.0 constants
# ---------------------------------------------------------------------------

LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_SCOPES = "openid profile email"

# Default local server port for the OAuth redirect
DEFAULT_PORT = 8585

# HTTP timeout for token exchange requests (seconds)
HTTP_TIMEOUT = 10

# Default client ID (read from environment; can be overridden in tests)
DEFAULT_CLIENT_ID = os.environ.get("LINKEDIN_CLIENT_ID", "")


# ---------------------------------------------------------------------------
# Helper: extract state from URL
# ---------------------------------------------------------------------------


def _extract_state_from_url(url: str) -> str:
    """Extract the ``state`` query parameter from an OAuth URL.

    Args:
        url: A fully-qualified URL containing a ``state`` query parameter.

    Returns:
        The value of the ``state`` parameter.

    Raises:
        ValueError: If the URL does not contain a ``state`` parameter.
    """
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    if "state" not in params:
        raise ValueError(f"No state parameter found in URL: {url}")
    return params["state"][0]


# ---------------------------------------------------------------------------
# Core OAuth functions
# ---------------------------------------------------------------------------


def initiate_oauth_flow(redirect_uri: str) -> str:
    """Generate a LinkedIn OAuth authorization URL with a CSPRNG state parameter.

    Reads the LinkedIn client ID from the ``LINKEDIN_CLIENT_ID`` environment
    variable (or the module-level ``DEFAULT_CLIENT_ID``).

    Args:
        redirect_uri: The OAuth redirect URI (e.g.
            ``http://localhost:8585/callback``).

    Returns:
        A fully-qualified LinkedIn OAuth authorization URL that the user
        should be directed to in their browser.

    Raises:
        AuthError (via raise): With code ``OAUTH_FAILED`` if the client ID
            is not configured.  Because :class:`AuthError` is a
            :class:`TypedDict`, raising it directly will result in a
            :class:`TypeError` at the call site — callers should catch
            ``TypeError`` when testing this path.
    """
    client_id = os.environ.get("LINKEDIN_CLIENT_ID", "") or DEFAULT_CLIENT_ID

    if not client_id:
        raise AuthError(
            code="OAUTH_FAILED",
            message="LINKEDIN_CLIENT_ID is not configured. Cannot initiate OAuth flow.",
            recoverable=False,
        )

    # Generate a cryptographically-secure random state token for CSRF protection
    state = secrets.token_urlsafe(32)

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": LINKEDIN_SCOPES,
    }

    url = f"{LINKEDIN_AUTH_URL}?{urlencode(params)}"
    logger.info("OAuth flow initiated. Redirect URI: %s", redirect_uri)
    return url


def handle_oauth_callback(callback_url: str, expected_state: str) -> LinkedInTokens:
    """Parse an OAuth callback URL, validate state, and exchange the code for tokens.

    This function:
    1. Parses the callback URL for ``code``, ``state``, and ``error`` params.
    2. Validates that the returned ``state`` matches ``expected_state`` (CSRF).
    3. Delegates to :func:`exchange_code_for_tokens` to obtain tokens.

    Args:
        callback_url: The full URL that LinkedIn redirected to (including
            query parameters).
        expected_state: The state value that was sent in the original
            authorization request.

    Returns:
        A :class:`LinkedInTokens` dict on success.

    Raises:
        AuthError (via raise): With code ``OAUTH_FAILED`` on state mismatch,
            missing code, or OAuth error from LinkedIn.  Raises as
            :class:`TypeError` because :class:`AuthError` is a TypedDict.
    """
    parsed = urlparse(callback_url)
    params = parse_qs(parsed.query)

    # Check for OAuth error from LinkedIn (e.g. user cancelled)
    if "error" in params:
        error_code = params["error"][0]
        error_desc = params.get("error_description", ["Unknown error"])[0]
        logger.warning("OAuth error from LinkedIn: %s - %s", error_code, error_desc)
        raise AuthError(
            code="OAUTH_FAILED",
            message=f"LinkedIn OAuth error: {error_desc}",
            recoverable=True,
        )

    # Validate CSRF state parameter
    returned_state = params.get("state", [None])[0]
    if returned_state != expected_state:
        logger.warning(
            "OAuth state mismatch: expected=%s, got=%s", expected_state, returned_state
        )
        raise AuthError(
            code="OAUTH_FAILED",
            message="CSRF state mismatch. The OAuth callback state does not match the expected value.",
            recoverable=True,
        )

    # Extract authorization code
    code_list = params.get("code", [])
    if not code_list or not code_list[0]:
        raise AuthError(
            code="OAUTH_FAILED",
            message="No authorization code received in OAuth callback.",
            recoverable=True,
        )

    auth_code = code_list[0]
    redirect_uri = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    logger.info("OAuth callback received. Exchanging code for tokens.")
    return exchange_code_for_tokens(auth_code, redirect_uri)


def exchange_code_for_tokens(auth_code: str, redirect_uri: str) -> LinkedInTokens:
    """Exchange an authorization code for LinkedIn access tokens.

    Sends a POST request to LinkedIn's token endpoint with the authorization
    code, redirect URI, client ID, and client secret.

    Args:
        auth_code: The authorization code from the OAuth callback.
        redirect_uri: The redirect URI that was used in the authorization
            request (must match exactly).

    Returns:
        A :class:`LinkedInTokens` dict containing the access token,
        expiration timestamp, and optional refresh token.

    Raises:
        AuthError (via raise): With code ``OAUTH_FAILED`` on HTTP errors
            from LinkedIn, ``NETWORK_ERROR`` on connection failures, or
            ``OAUTH_FAILED`` when credentials are missing.
    """
    client_id = os.environ.get("LINKEDIN_CLIENT_ID", "") or DEFAULT_CLIENT_ID
    client_secret = os.environ.get("LINKEDIN_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        raise AuthError(
            code="OAUTH_FAILED",
            message="LinkedIn OAuth credentials (LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET) are not configured.",
            recoverable=False,
        )

    try:
        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            response = client.post(
                LINKEDIN_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": auth_code,
                    "redirect_uri": redirect_uri,
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
    except httpx.HTTPError as exc:
        logger.error("Network error during token exchange: %s", exc)
        raise AuthError(
            code="NETWORK_ERROR",
            message=f"Network error during token exchange: {exc}",
            recoverable=True,
        )

    if response.status_code != 200:
        logger.error(
            "Token exchange failed: %d - %s", response.status_code, response.text
        )
        raise AuthError(
            code="OAUTH_FAILED",
            message=f"LinkedIn token exchange failed with status {response.status_code}: {response.text}",
            recoverable=True,
        )

    data = response.json()

    now = int(time.time())
    expires_in = data.get("expires_in", 5184000)  # Default 60 days

    tokens: LinkedInTokens = {
        "access_token": data["access_token"],
        "expires_at": now + expires_in,
        "refresh_token": data.get("refresh_token"),
    }

    logger.info("Token exchange successful. Expires at: %d", tokens["expires_at"])
    return tokens


# ---------------------------------------------------------------------------
# Local OAuth redirect server
# ---------------------------------------------------------------------------


def start_local_oauth_server(port: int = DEFAULT_PORT) -> tuple[str, Callable[[], Optional[str]]]:
    """Start a local HTTP server to receive the LinkedIn OAuth redirect.

    The server listens on ``localhost:<port>`` and waits for a single GET
    request to ``/callback``.  Once the request is received, the full
    callback URL is captured and the server shuts down.

    Args:
        port: The port to listen on.  Defaults to :data:`DEFAULT_PORT`
            (8585).

    Returns:
        A 2-tuple of ``(redirect_uri, get_callback_url)`` where:
        - ``redirect_uri`` is ``http://localhost:<port>/callback``
        - ``get_callback_url`` is a callable that blocks until the callback
          is received and returns the full callback URL string, or ``None``
          if no callback was received before the server was shut down.

    Raises:
        AuthError (via raise): With code ``PORT_IN_USE`` if the port is
            already bound.
    """
    # Check if the port is available before starting the server
    test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        test_socket.bind(("localhost", port))
    except OSError:
        raise AuthError(
            code="PORT_IN_USE",
            message=f"Port {port} is already in use. Try a different port or close the application using it.",
            recoverable=True,
        )
    finally:
        test_socket.close()

    # Mutable container to capture the callback URL from the handler thread
    callback_result: dict[str, Optional[str]] = {"url": None}
    server_ready = threading.Event()
    callback_received = threading.Event()

    class _OAuthCallbackHandler(BaseHTTPRequestHandler):
        """HTTP request handler that captures the OAuth callback URL."""

        def do_GET(self) -> None:  # noqa: N802
            """Handle GET request from LinkedIn OAuth redirect."""
            # Capture the full callback URL
            callback_result["url"] = f"http://localhost:{port}{self.path}"

            # Send a simple success response to the browser
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h1>Login successful!</h1>"
                b"<p>You can close this tab and return to the CLI.</p>"
                b"</body></html>"
            )

            # Signal that we received the callback
            callback_received.set()

        def log_message(self, format: str, *args: object) -> None:
            """Suppress default HTTP server logging."""
            logger.debug("OAuth server: %s", format % args)

    server = HTTPServer(("localhost", port), _OAuthCallbackHandler)
    server.timeout = 120  # 2-minute timeout

    def _serve() -> None:
        """Run the server in a thread, handling one request."""
        server_ready.set()
        server.handle_request()

    thread = threading.Thread(target=_serve, daemon=True)
    thread.start()
    server_ready.wait()

    redirect_uri = f"http://localhost:{port}/callback"

    def get_callback_url() -> Optional[str]:
        """Block until the OAuth callback is received.

        Returns:
            The full callback URL string, or ``None`` if the server timed
            out or was shut down before receiving a callback.
        """
        # Wait for the handler thread to finish (with the server timeout)
        thread.join(timeout=130)  # Slightly longer than server.timeout
        return callback_result["url"]

    logger.info("Local OAuth server started on port %d", port)
    return redirect_uri, get_callback_url


# ---------------------------------------------------------------------------
# Full login orchestrator
# ---------------------------------------------------------------------------


def run_oauth_login(port: int = DEFAULT_PORT) -> LinkedInTokens:
    """Run the complete OAuth login flow.

    Orchestrates the full login process:
    1. Start a local HTTP server for the redirect.
    2. Generate the authorization URL (with CSPRNG state).
    3. Open the user's browser to the authorization URL.
    4. Wait for the OAuth callback.
    5. Validate state and exchange the code for tokens.

    Args:
        port: The local server port.  Defaults to :data:`DEFAULT_PORT`.

    Returns:
        A :class:`LinkedInTokens` dict on successful authentication.

    Raises:
        AuthError (via raise): On any failure in the OAuth flow.
    """
    # Step 1: Start local server
    redirect_uri, get_callback_url = start_local_oauth_server(port=port)

    # Step 2: Generate authorization URL
    auth_url = initiate_oauth_flow(redirect_uri)
    expected_state = _extract_state_from_url(auth_url)

    # Step 3: Open browser
    logger.info("Opening browser for LinkedIn authentication...")
    webbrowser.open(auth_url)

    # Step 4: Wait for callback
    callback_url = get_callback_url()
    if callback_url is None:
        raise AuthError(
            code="OAUTH_FAILED",
            message="OAuth callback was not received. The login may have timed out or been cancelled.",
            recoverable=True,
        )

    # Step 5: Handle callback (validates state + exchanges code)
    tokens = handle_oauth_callback(callback_url, expected_state)

    logger.info("OAuth login completed successfully.")
    return tokens
