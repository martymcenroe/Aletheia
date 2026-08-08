"""Unit tests for 401 discriminators.

Issue: #815 - all three 401 branches returned an identical opaque
"Unauthorized", so neither a client nor an operator could tell a missing
credential from an expired one from a revoked one.

The distinction is load-bearing for the client: an expired credential is
renewable and should be retried silently, while a revoked one means renewal is
futile and the user must sign in. Without a discriminator the client has to
guess, and guessing wrong either strands the user or hammers the auth Lambda.
"""

from __future__ import annotations

import json

import pytest

from auth.auth_middleware import (
    REASON_EXPIRED_TOKEN,
    REASON_INVALID_TOKEN,
    REASON_MISSING_TOKEN,
    REASON_SERVER_ERROR,
    _build_401_response,
    _public_reason,
)

PUBLIC_ENUM = {
    REASON_MISSING_TOKEN,
    REASON_EXPIRED_TOKEN,
    REASON_INVALID_TOKEN,
    REASON_SERVER_ERROR,
}


@pytest.mark.parametrize(
    "internal,expected",
    [
        ("missing_header", REASON_MISSING_TOKEN),
        ("invalid_format", REASON_MISSING_TOKEN),
        ("token_expired", REASON_EXPIRED_TOKEN),
        ("invalid_signature", REASON_INVALID_TOKEN),
        ("malformed", REASON_INVALID_TOKEN),
        ("invalid_token", REASON_INVALID_TOKEN),
    ],
)
def test_internal_reasons_map_to_public_enum(internal, expected):
    assert _public_reason(internal) == expected


def test_expired_is_distinguishable_from_invalid():
    """The whole point of the issue: these must not collapse together.

    An expired credential is renewable; a revoked one is not. If these ever
    return the same discriminator, the client is back to guessing.
    """
    assert _public_reason("token_expired") != _public_reason("invalid_signature")


def test_secret_unavailable_is_not_reported_as_a_bad_credential():
    """A missing signing secret is our failure, not the user's.

    Mapping it to invalid_token would make a client discard a perfectly good
    session over a transient server problem.
    """
    assert _public_reason("secret_unavailable") == REASON_SERVER_ERROR
    assert _public_reason("secret_unavailable") != REASON_INVALID_TOKEN


def test_unknown_internal_reason_is_not_echoed():
    """A future internal reason string must never leak through this boundary."""
    assert _public_reason("some_new_internal_reason") == REASON_INVALID_TOKEN
    assert _public_reason(None) == REASON_INVALID_TOKEN
    assert _public_reason("") == REASON_INVALID_TOKEN


def test_response_carries_the_reason_and_keeps_the_human_message():
    response = _build_401_response("Unauthorized", REASON_EXPIRED_TOKEN)
    body = json.loads(response["body"])

    assert response["statusCode"] == 401
    assert body["error"] == "Unauthorized"
    assert body["reason"] == REASON_EXPIRED_TOKEN


def test_default_reason_is_the_conservative_one():
    """An un-annotated call must not imply a renewable condition."""
    body = json.loads(_build_401_response("Unauthorized")["body"])
    assert body["reason"] == REASON_INVALID_TOKEN


@pytest.mark.parametrize("internal", [
    "missing_header", "invalid_format", "token_expired",
    "invalid_signature", "malformed", "invalid_token",
    "secret_unavailable", "unknown", None,
])
def test_no_reason_escapes_the_fixed_enum(internal):
    """The enum is closed. Anything outside it is a leak surface."""
    assert _public_reason(internal) in PUBLIC_ENUM


def test_401_body_never_carries_token_or_claim_material():
    """Deliberately excluded: token contents, claims, identifiers, exception text."""
    body = json.loads(_build_401_response("Unauthorized", REASON_EXPIRED_TOKEN)["body"])

    assert set(body.keys()) == {"error", "reason"}
    for forbidden in ("user_id", "jti", "exp", "claims", "token", "sub"):
        assert forbidden not in body
