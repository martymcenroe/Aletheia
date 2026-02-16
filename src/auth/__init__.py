"""Authentication package for LinkedIn OAuth.

Implements LinkedIn OAuth 2.0 authentication flow for the Python CLI/Agent.
Reference: LLD #116 - Feature: Authenticate users via LinkedIn OAuth
"""

from auth.types import (
    AuthError,
    AuthState,
    LinkedInTokens,
    UserProfile,
)

__all__ = [
    "AuthError",
    "AuthState",
    "LinkedInTokens",
    "UserProfile",
]
