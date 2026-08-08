"""Unit tests for Aletheia-issued refresh tokens.

Issue: #811 - LinkedIn's 'openid profile' scopes never return a refresh token
and /auth/refresh could not mint a JWT, so a signed-in user was locked out
24 hours after login.

Coverage:
- Token generation entropy and uniqueness
- Only the hash is persisted; plaintext is never stored
- Round-trip store -> validate
- Rejection of unknown, revoked, and expired tokens
- The returned user_id comes from storage, never from the caller
"""

from __future__ import annotations

import importlib
import time
from unittest.mock import MagicMock

import boto3
import pytest
from moto import mock_aws

TABLE_NAME = "test-refresh-tokens"
TEST_USER = "linkedin-user-001"
OTHER_USER = "linkedin-user-002"


@pytest.fixture
def svc(monkeypatch):
    """Import the service with the table name pointed at the moto fixture."""
    monkeypatch.setenv("REFRESH_TOKENS_TABLE", TABLE_NAME)
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    import auth.refresh_token_service as module

    importlib.reload(module)
    return module


@pytest.fixture
def table(svc):
    """Create the refresh-token table in moto and yield a live client."""
    with mock_aws():
        client = boto3.client("dynamodb", region_name="us-east-1")
        client.create_table(
            TableName=TABLE_NAME,
            AttributeDefinitions=[
                {"AttributeName": "token_hash", "AttributeType": "S"}
            ],
            KeySchema=[{"AttributeName": "token_hash", "KeyType": "HASH"}],
            BillingMode="PAY_PER_REQUEST",
        )
        yield client


# --------------------------------------------------------------------------- #
# Generation and hashing
# --------------------------------------------------------------------------- #


def test_generated_tokens_are_unique(svc):
    tokens = {svc.generate_refresh_token() for _ in range(200)}
    assert len(tokens) == 200


def test_generated_token_has_sufficient_entropy(svc):
    token = svc.generate_refresh_token()
    # 32 bytes urlsafe-base64 encodes to at least 43 characters.
    assert len(token) >= 43


def test_hash_is_deterministic_and_differs_per_token(svc):
    a = svc.generate_refresh_token()
    b = svc.generate_refresh_token()
    assert svc.hash_token(a) == svc.hash_token(a)
    assert svc.hash_token(a) != svc.hash_token(b)


def test_only_the_hash_is_persisted_never_the_plaintext(svc, table):
    """A read of the table must not yield a usable credential."""
    token = svc.generate_refresh_token()
    svc.store_refresh_token(TEST_USER, token, client=table)

    scanned = table.scan(TableName=TABLE_NAME)["Items"]
    assert len(scanned) == 1
    serialized = str(scanned[0])

    assert token not in serialized
    assert svc.hash_token(token) in serialized


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #


def test_store_then_validate_returns_owning_user(svc, table):
    token = svc.generate_refresh_token()
    svc.store_refresh_token(TEST_USER, token, client=table)

    assert svc.validate_refresh_token(token, client=table) == TEST_USER


def test_unknown_token_is_rejected(svc, table):
    assert svc.validate_refresh_token("not-a-real-token", client=table) is None


def test_empty_or_non_string_token_is_rejected(svc, table):
    assert svc.validate_refresh_token("", client=table) is None
    assert svc.validate_refresh_token(None, client=table) is None


def test_revoked_token_is_rejected(svc, table):
    token = svc.generate_refresh_token()
    svc.store_refresh_token(TEST_USER, token, client=table)

    assert svc.revoke_refresh_token(token, client=table) is True
    assert svc.validate_refresh_token(token, client=table) is None


def test_expired_token_is_rejected_in_code_not_left_to_dynamodb_ttl(svc, table):
    """DynamoDB TTL deletion lags up to 48h, so expiry must be enforced here."""
    token = svc.generate_refresh_token()
    svc.store_refresh_token(TEST_USER, token, client=table, ttl_days=1)

    # Rewrite ttl into the past, leaving the row present exactly as a lagging
    # DynamoDB sweeper would.
    table.update_item(
        TableName=TABLE_NAME,
        Key={"token_hash": {"S": svc.hash_token(token)}},
        UpdateExpression="SET #t = :past",
        ExpressionAttributeNames={"#t": "ttl"},
        ExpressionAttributeValues={":past": {"N": str(int(time.time()) - 60)}},
    )

    assert svc.validate_refresh_token(token, client=table) is None


def test_returned_user_id_comes_from_storage_not_the_caller(svc, table):
    """A valid token must never mint a session for a different user.

    There is no caller-supplied identifier in the signature at all; this
    asserts that two distinct tokens resolve strictly to their own owners.
    """
    token_a = svc.generate_refresh_token()
    token_b = svc.generate_refresh_token()
    svc.store_refresh_token(TEST_USER, token_a, client=table)
    svc.store_refresh_token(OTHER_USER, token_b, client=table)

    assert svc.validate_refresh_token(token_a, client=table) == TEST_USER
    assert svc.validate_refresh_token(token_b, client=table) == OTHER_USER


def test_last_used_is_recorded_on_successful_validation(svc, table):
    token = svc.generate_refresh_token()
    svc.store_refresh_token(TEST_USER, token, client=table)

    table.update_item(
        TableName=TABLE_NAME,
        Key={"token_hash": {"S": svc.hash_token(token)}},
        UpdateExpression="SET last_used_at = :old",
        ExpressionAttributeValues={":old": {"N": "0"}},
    )

    svc.validate_refresh_token(token, client=table)

    item = table.get_item(
        TableName=TABLE_NAME,
        Key={"token_hash": {"S": svc.hash_token(token)}},
    )["Item"]
    assert int(item["last_used_at"]["N"]) > 0


def test_touch_failure_does_not_deny_a_valid_refresh(svc, table):
    """Bookkeeping must never be able to lock a user out."""
    token = svc.generate_refresh_token()
    svc.store_refresh_token(TEST_USER, token, client=table)

    flaky = MagicMock()
    flaky.get_item.side_effect = table.get_item
    flaky.update_item.side_effect = RuntimeError("throttled")

    assert svc.validate_refresh_token(token, client=flaky) == TEST_USER


def test_lookup_failure_fails_closed(svc):
    """A datastore error must deny, not admit."""
    broken = MagicMock()
    broken.get_item.side_effect = RuntimeError("boom")

    assert svc.validate_refresh_token("anything", client=broken) is None


def test_lookup_failure_does_not_log_exception_text(svc, caplog):
    """Project rule: exception text must never reach logs in auth paths."""
    canary = "CANARY_SENSITIVE_DETAIL"
    broken = MagicMock()
    broken.get_item.side_effect = RuntimeError(canary)

    with caplog.at_level("ERROR"):
        svc.validate_refresh_token("anything", client=broken)

    assert canary not in "\n".join(r.getMessage() for r in caplog.records)
