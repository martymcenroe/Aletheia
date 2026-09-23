"""
Unit tests for Issues #869 and #870.

#869: analysis records carry no user identifier and expire after 30 days.
#870: the operator's own records are the permanent exception. They are
      attributed to the operator and written with NO ttl, and no cleanup
      tool may modify or delete them. Operator directive; inviolable.

The operator ID used here is a fake. The real one lives in SSM and the Lambda
environment, never in this public repository.
"""
import importlib.util
import json
import logging
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.lambda_function import (
    TTL_SECONDS,
    is_operator,
    lambda_handler,
    operator_user_ids,
    save_state,
)

OPERATOR = "operator-fake-id"
OTHER_USER = "someone-else-id"
MOCK_DENYLIST = {"test_block_term"}
TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"


def _load_tool(name: str):
    spec = importlib.util.spec_from_file_location(name, TOOLS_DIR / f"{name}.py")
    assert spec is not None and spec.loader is not None, f"cannot load tools/{name}.py"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _saved_item(data: dict) -> dict:
    with patch("src.lambda_function.get_dynamodb_client") as mock_dynamo:
        client = MagicMock()
        mock_dynamo.return_value = client
        save_state("thread", {"text": "apple", "url": "https://example.com", **data})
        return client.put_item.call_args.kwargs["Item"]


# --- Operator identification -------------------------------------------------


class TestOperatorIds:
    def test_parses_comma_pipe_and_whitespace(self, monkeypatch):
        monkeypatch.setenv("OPERATOR_USER_IDS", " a, b|c  d ")
        assert operator_user_ids() == frozenset({"a", "b", "c", "d"})

    def test_unset_means_no_operator(self, monkeypatch):
        monkeypatch.delenv("OPERATOR_USER_IDS", raising=False)
        assert operator_user_ids() == frozenset()
        assert not is_operator(OPERATOR)

    def test_exact_match_only(self, monkeypatch):
        monkeypatch.setenv("OPERATOR_USER_IDS", OPERATOR)
        assert is_operator(OPERATOR)
        assert not is_operator(OPERATOR[:-1])
        assert not is_operator(OPERATOR + "x")
        assert not is_operator(OPERATOR.upper())
        assert not is_operator(None)
        assert not is_operator("")


# --- save_state ---------------------------------------------------------------


class TestSaveStateAttribution:
    def test_operator_record_is_attributed_and_never_expires(self, monkeypatch):
        """#870: operator rows carry user_id and have NO ttl."""
        monkeypatch.setenv("OPERATOR_USER_IDS", OPERATOR)
        item = _saved_item({"userId": OPERATOR})
        assert item["user_id"] == {"S": OPERATOR}
        assert "ttl" not in item

    def test_other_user_record_is_unattributed_and_expires(self, monkeypatch):
        """#869: an authenticated non-operator row has no user_id and a 30-day ttl."""
        monkeypatch.setenv("OPERATOR_USER_IDS", OPERATOR)
        before = int(time.time())
        item = _saved_item({"userId": OTHER_USER})
        assert "user_id" not in item
        assert before + TTL_SECONDS <= int(item["ttl"]["N"]) <= int(time.time()) + TTL_SECONDS

    def test_anonymous_record_is_unattributed_and_expires(self, monkeypatch):
        monkeypatch.setenv("OPERATOR_USER_IDS", OPERATOR)
        item = _saved_item({})
        assert "user_id" not in item
        assert "ttl" in item

    def test_no_user_id_attribute_for_anyone_when_unconfigured(self, monkeypatch, caplog):
        """Without configuration nobody is attributed, and the gap is logged."""
        monkeypatch.delenv("OPERATOR_USER_IDS", raising=False)
        with caplog.at_level(logging.WARNING):
            item = _saved_item({"userId": OPERATOR})
        assert "user_id" not in item
        assert "ttl" in item
        assert "OPERATOR_USER_IDS_UNSET" in caplog.text
        assert OPERATOR not in caplog.text


# --- Handler: attribution comes from authentication, never the body ------------


def _handler_item(event: dict) -> dict:
    with patch("src.lambda_function.get_semantic_guardrail") as mock_semantic, \
         patch("src.lambda_function.get_dynamodb_client") as mock_dynamo, \
         patch("src.lambda_function.get_bedrock_client") as mock_bedrock:
        guard = MagicMock()
        guard.check_safety.return_value = {"is_safe": True, "reason": "None", "scores": {}}
        mock_semantic.return_value = guard
        client = MagicMock()
        mock_dynamo.return_value = client
        body = json.dumps({"content": [{"type": "text", "text":
            '{"signal": "green", "gem": "A fruit.", "context": "Apple."}'}]})
        mock_bedrock.return_value.invoke_model.return_value = {
            "body": MagicMock(read=MagicMock(return_value=body.encode()))
        }
        result = lambda_handler(event, None, denylist=MOCK_DENYLIST)
        assert result["statusCode"] == 200
        return client.put_item.call_args.kwargs["Item"]


class TestHandlerAttributionSource:
    def test_authenticated_operator_is_attributed(self, monkeypatch):
        monkeypatch.setenv("OPERATOR_USER_IDS", OPERATOR)
        item = _handler_item({"text": "apple", "url": "https://e.com", "auth_user_id": OPERATOR})
        assert item["user_id"] == {"S": OPERATOR}
        assert "ttl" not in item

    def test_body_userid_cannot_claim_the_carve_out(self, monkeypatch):
        """Any client can write body.userId, so it must never attribute a row."""
        monkeypatch.setenv("OPERATOR_USER_IDS", OPERATOR)
        item = _handler_item({"text": "apple", "url": "https://e.com", "userId": OPERATOR})
        assert "user_id" not in item
        assert "ttl" in item

    def test_other_authenticated_user_spoofing_body_is_not_attributed(self, monkeypatch):
        monkeypatch.setenv("OPERATOR_USER_IDS", OPERATOR)
        item = _handler_item({"text": "apple", "url": "https://e.com",
                              "auth_user_id": OTHER_USER, "userId": OPERATOR})
        assert "user_id" not in item
        assert "ttl" in item


# --- tools/data_hygiene.py: retained records are never touched -----------------


def _hygiene_rows() -> list[dict]:
    """Rows that each trigger one destructive mode, plus unprotected controls."""
    op = {"user_id": OPERATOR, "ttl": 1, "url": "u"}
    return [
        # Operator rows WITH a ttl: protected by user_id alone.
        {"thread_id": "op-common", "checkpoint_id": "1", "input": "the", **op},
        {"thread_id": "op-dup-a", "checkpoint_id": "2", "input": "lexeme", **op},
        {"thread_id": "op-dup-b", "checkpoint_id": "3", "input": "lexeme", **op},
        {"thread_id": "op-raw", "checkpoint_id": "raw_capture", "input": "logos", **op},
        {"thread_id": "op-old", "checkpoint_id": "4", "word": "logos", **op},
        # Legacy rows with no ttl and no user_id: protected by the missing ttl.
        {"thread_id": "legacy-common", "checkpoint_id": "5", "input": "the", "url": "u"},
        {"thread_id": "legacy-raw", "checkpoint_id": "raw_capture", "input": "x", "url": "u"},
        # Controls: ordinary expiring rows that each mode SHOULD act on.
        {"thread_id": "ctl-common", "checkpoint_id": "6", "input": "the", "url": "u", "ttl": 1},
        {"thread_id": "ctl-dup-a", "checkpoint_id": "7", "input": "gnosis", "url": "u", "ttl": 1},
        {"thread_id": "ctl-dup-b", "checkpoint_id": "8", "input": "gnosis", "url": "u", "ttl": 1},
        {"thread_id": "ctl-old", "checkpoint_id": "9", "word": "sophia", "url": "u", "ttl": 1},
    ]


def _touched(table: MagicMock) -> set[str]:
    touched = set()
    for call in table.delete_item.call_args_list + table.update_item.call_args_list:
        touched.add(call.kwargs["Key"]["thread_id"])
    return touched


@pytest.fixture
def hygiene():
    module = _load_tool("data_hygiene")
    module.OPERATOR_USER_IDS = frozenset({OPERATOR})
    module.load_common_words()
    table = MagicMock()
    with patch.object(module, "scan_all_items", return_value=_hygiene_rows()), \
         patch.object(module, "get_dynamodb_table", return_value=table):
        yield module, table


RETAINED = {"op-common", "op-dup-a", "op-dup-b", "op-raw", "op-old",
            "legacy-common", "legacy-raw"}


class TestDataHygieneGuard:
    @pytest.mark.parametrize("mode,control", [
        ("clean_common_words", "ctl-common"),
        ("deduplicate", "ctl-dup-a"),
        ("normalize_schema", "ctl-old"),
    ])
    def test_mode_never_touches_retained_rows(self, hygiene, mode, control):
        module, table = hygiene
        getattr(module, mode)(dry_run=False)
        touched = _touched(table)
        assert not touched & RETAINED, f"{mode} touched retained rows: {touched & RETAINED}"
        # Control: the mode really ran and acted, so a pass above means something.
        assert control in touched, f"{mode} did not act on its control row"

    def test_backfill_ttl_never_expires_a_retained_row(self, hygiene):
        module, table = hygiene
        module.backfill_ttl(dry_run=False)
        assert not _touched(table) & RETAINED
        table.put_item.assert_not_called()

    def test_normalize_never_recreates_a_retained_row(self, hygiene):
        """normalize deletes and re-puts raw_capture rows, dropping user_id."""
        module, table = hygiene
        module.normalize_schema(dry_run=False)
        for call in table.put_item.call_args_list:
            assert call.kwargs["Item"]["thread_id"] not in RETAINED

    def test_is_retained_rules(self, hygiene):
        module, _ = hygiene
        assert module.is_retained({"user_id": OPERATOR, "ttl": 1})
        assert module.is_retained({})  # no ttl
        assert not module.is_retained({"ttl": 1})
        assert not module.is_retained({"user_id": OTHER_USER, "ttl": 1})

    def test_refuses_to_scan_for_changes_when_guard_not_loaded(self):
        module = _load_tool("data_hygiene")
        module.OPERATOR_USER_IDS = frozenset()
        with patch.object(module, "scan_all_items", return_value=_hygiene_rows()):
            with pytest.raises(RuntimeError, match="#870"):
                module.scan_modifiable_items(module.CleanupStats())

    def test_main_exits_when_ssm_unreadable(self, monkeypatch):
        from botocore.exceptions import ClientError

        module = _load_tool("data_hygiene")
        ssm = MagicMock()
        ssm.get_parameter.side_effect = ClientError(
            {"Error": {"Code": "ParameterNotFound", "Message": "x"}}, "GetParameter")
        monkeypatch.setattr("sys.argv", ["data_hygiene.py", "--clean-common", "--no-dry-run"])
        with patch.object(module.boto3, "client", return_value=ssm), \
             patch.object(module, "scan_all_items") as scan:
            with pytest.raises(SystemExit):
                module.main()
            scan.assert_not_called()

    def test_main_exits_when_ssm_value_empty(self, monkeypatch):
        module = _load_tool("data_hygiene")
        ssm = MagicMock()
        ssm.get_parameter.return_value = {"Parameter": {"Value": "  "}}
        monkeypatch.setattr("sys.argv", ["data_hygiene.py", "--deduplicate", "--no-dry-run"])
        with patch.object(module.boto3, "client", return_value=ssm), \
             patch.object(module, "scan_all_items") as scan:
            with pytest.raises(SystemExit):
                module.main()
            scan.assert_not_called()


# --- tools/backfill_operator_attribution.py ------------------------------------


class TestBackfillOperatorAttribution:
    @pytest.fixture
    def backfill(self):
        return _load_tool("backfill_operator_attribution")

    def test_candidates_are_rows_with_neither_user_id_nor_ttl(self, backfill):
        assert backfill.is_candidate({"thread_id": {"S": "a"}})
        assert not backfill.is_candidate({"ttl": {"N": "1"}})
        assert not backfill.is_candidate({"user_id": {"S": OPERATOR}})

    def test_single_configured_id_is_used(self, backfill):
        assert backfill.resolve_operator_id([OPERATOR], None) == OPERATOR

    def test_unconfigured_id_is_refused(self, backfill):
        with pytest.raises(ValueError):
            backfill.resolve_operator_id([OPERATOR], OTHER_USER)

    def test_several_ids_require_a_choice(self, backfill):
        with pytest.raises(ValueError):
            backfill.resolve_operator_id([OPERATOR, "second"], None)
        assert backfill.resolve_operator_id([OPERATOR, "second"], "second") == "second"

    def test_empty_configuration_is_refused(self, backfill):
        with pytest.raises(ValueError):
            backfill.resolve_operator_id([], None)

    def test_write_is_conditional_and_never_sets_ttl(self, backfill):
        client = MagicMock()
        key = {"thread_id": {"S": "a"}, "checkpoint_id": {"S": "1"}}
        assert backfill.attribute(client, key, OPERATOR)
        kwargs = client.update_item.call_args.kwargs
        assert kwargs["UpdateExpression"] == "SET user_id = :uid"
        assert "attribute_not_exists(user_id)" in kwargs["ConditionExpression"]
        assert "attribute_not_exists(#t)" in kwargs["ConditionExpression"]
        assert kwargs["ExpressionAttributeValues"] == {":uid": {"S": OPERATOR}}

    def test_scan_selects_only_candidates(self, backfill):
        client = MagicMock()
        client.scan.return_value = {"Items": [
            {"thread_id": {"S": "legacy"}, "checkpoint_id": {"S": "1"}},
            {"thread_id": {"S": "expiring"}, "checkpoint_id": {"S": "2"}, "ttl": {"N": "9"}},
            {"thread_id": {"S": "attributed"}, "checkpoint_id": {"S": "3"},
             "user_id": {"S": OPERATOR}},
        ]}
        scanned, keys = backfill.scan_candidates(client)
        assert scanned == 3
        assert [k["thread_id"]["S"] for k in keys] == ["legacy"]
