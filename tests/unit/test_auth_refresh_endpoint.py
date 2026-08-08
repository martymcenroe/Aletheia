"""Unit tests for POST /auth/refresh minting a JWT from an Aletheia token.

Issue: #811 - the endpoint previously called LinkedIn's grant_type=refresh_token
and returned only a LinkedIn access token, never a JWT. It could not have
worked in any case: the extension requests 'openid profile', for which
LinkedIn does not issue refresh tokens.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import jwt as pyjwt
import pytest

import src.lambda_auth_function as auth_func

# 32+ bytes: below that PyJWT emits InsecureKeyLengthWarning for HS256.
TEST_SECRET = "test-signing-secret-padded-to-32-bytes-minimum"
TEST_USER = "linkedin-user-001"


def _decode(body: dict) -> dict:
    return pyjwt.decode(body["jwt"], TEST_SECRET, algorithms=["HS256"])


def test_missing_token_returns_400():
    response = auth_func.handle_token_refresh({})

    assert response["statusCode"] == 400
    assert "aletheiaRefreshToken" in json.loads(response["body"])["error"]


def test_invalid_token_returns_401():
    with patch.object(auth_func, "validate_refresh_token", return_value=None):
        response = auth_func.handle_token_refresh(
            {"aletheiaRefreshToken": "bogus"}
        )

    assert response["statusCode"] == 401
    assert json.loads(response["body"])["error"] == "Unauthorized"


def test_valid_token_mints_a_jwt_for_the_stored_user():
    with (
        patch.object(auth_func, "validate_refresh_token", return_value=TEST_USER),
        patch.object(auth_func, "get_jwt_secret", return_value=TEST_SECRET),
        patch.object(auth_func, "get_user_tier", return_value=("free", 1)),
    ):
        response = auth_func.handle_token_refresh(
            {"aletheiaRefreshToken": "valid-token"}
        )

    assert response["statusCode"] == 200
    claims = _decode(json.loads(response["body"]))
    assert claims["user_id"] == TEST_USER


@pytest.mark.parametrize(
    "tier,anchor_day",
    [("free", 1), ("pro", 15), ("unlimited", 28)],
)
def test_refresh_preserves_tier_and_billing_anchor(tier, anchor_day):
    """A renewal must never silently downgrade a paying user to free.

    create_jwt defaults tier to 'free'; if the refresh path omitted the tier
    lookup, every renewal would quietly strip a paid user's entitlement.
    """
    with (
        patch.object(auth_func, "validate_refresh_token", return_value=TEST_USER),
        patch.object(auth_func, "get_jwt_secret", return_value=TEST_SECRET),
        patch.object(
            auth_func, "get_user_tier", return_value=(tier, anchor_day)
        ),
    ):
        response = auth_func.handle_token_refresh(
            {"aletheiaRefreshToken": "valid-token"}
        )

    claims = _decode(json.loads(response["body"]))
    assert claims["tier"] == tier
    assert claims["billing_anchor_day"] == anchor_day


def test_tier_is_reread_on_every_refresh():
    """An upgrade must take effect without forcing a re-login."""
    with (
        patch.object(auth_func, "validate_refresh_token", return_value=TEST_USER),
        patch.object(auth_func, "get_jwt_secret", return_value=TEST_SECRET),
        patch.object(auth_func, "get_user_tier") as mock_tier,
    ):
        mock_tier.return_value = ("free", 1)
        first = auth_func.handle_token_refresh({"aletheiaRefreshToken": "t"})

        mock_tier.return_value = ("pro", 1)
        second = auth_func.handle_token_refresh({"aletheiaRefreshToken": "t"})

    assert _decode(json.loads(first["body"]))["tier"] == "free"
    assert _decode(json.loads(second["body"]))["tier"] == "pro"


def test_refresh_never_calls_linkedin():
    """LinkedIn proves identity once at login and is never consulted again."""
    with (
        patch.object(auth_func, "validate_refresh_token", return_value=TEST_USER),
        patch.object(auth_func, "get_jwt_secret", return_value=TEST_SECRET),
        patch.object(auth_func, "get_user_tier", return_value=("free", 1)),
        patch.object(auth_func, "get_linkedin_user_info") as mock_linkedin_info,
    ):
        response = auth_func.handle_token_refresh(
            {"aletheiaRefreshToken": "valid-token"}
        )

    assert response["statusCode"] == 200
    mock_linkedin_info.assert_not_called()


def test_linkedin_refresh_path_no_longer_exists():
    """Issue #816: the dead LinkedIn refresh path is gone, not merely unwired.

    It could never have worked — LinkedIn issues no refresh token for the
    'openid profile' scopes the extension requests — and a plausible-looking
    but non-functional auth path in the tree is what made the original session
    defect hard to diagnose.
    """
    assert not hasattr(auth_func, "refresh_access_token")


def test_refresh_response_carries_no_token_material():
    """The response must expose the JWT only, never the refresh token."""
    with (
        patch.object(auth_func, "validate_refresh_token", return_value=TEST_USER),
        patch.object(auth_func, "get_jwt_secret", return_value=TEST_SECRET),
        patch.object(auth_func, "get_user_tier", return_value=("free", 1)),
    ):
        response = auth_func.handle_token_refresh(
            {"aletheiaRefreshToken": "super-secret-refresh-token"}
        )

    assert "super-secret-refresh-token" not in response["body"]
