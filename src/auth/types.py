"""Type definitions for LinkedIn OAuth authentication.

Provides TypedDict and Literal-based types used across the auth package
for structured representation of tokens, user profiles, authentication
state, and error conditions.

Issue: #116
"""

from __future__ import annotations

from typing import Literal, Optional

from typing_extensions import TypedDict


class LinkedInTokens(TypedDict):
    """LinkedIn OAuth token set.

    Attributes:
        access_token: LinkedIn access token (60-day validity).
        expires_at: Unix timestamp of token expiration.
        refresh_token: Optional refresh token (if available from LinkedIn).
    """

    access_token: str
    expires_at: int
    refresh_token: Optional[str]


class UserProfile(TypedDict):
    """LinkedIn user profile information.

    Attributes:
        linkedin_id: LinkedIn member ID (``sub`` claim from OpenID Connect).
        email: User's email address.
        display_name: Full name for UI display.
        profile_picture: Optional avatar URL.
    """

    linkedin_id: str
    email: str
    display_name: str
    profile_picture: Optional[str]


class AuthState(TypedDict):
    """Authentication state for the current CLI session.

    Attributes:
        is_authenticated: Whether the user is currently authenticated.
        user: User profile information, or ``None`` if not yet fetched.
        tokens: LinkedIn token set, or ``None`` if not authenticated.
        last_validated: Unix timestamp of the last backend token validation.
    """

    is_authenticated: bool
    user: Optional[UserProfile]
    tokens: Optional[LinkedInTokens]
    last_validated: int


class AuthError(TypedDict):
    """Structured authentication error.

    Attributes:
        code: Machine-readable error code identifying the failure type.
        message: Human-readable error description.
        recoverable: Whether the error can be recovered from (e.g. retry).
    """

    code: Literal[
        "OAUTH_FAILED",
        "TOKEN_EXPIRED",
        "VALIDATION_FAILED",
        "NETWORK_ERROR",
        "PORT_IN_USE",
    ]
    message: str
    recoverable: bool
