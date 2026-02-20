"""Tests for Hermes state change poller.

Issue #400: Hermes Dashboard — state change alerting.
"""

import json
import os
from unittest.mock import MagicMock, patch


os.environ.setdefault("AWS_REGION", "us-east-1")
os.environ.setdefault("STATE_TABLE", "aletheia-state")

from src.hermes_poller import (  # noqa: E402
    diff_states,
    fetch_current_state,
    lambda_handler,
    load_previous_state,
    publish_alert,
    save_current_state,
)


class TestDiffStates:
    """Tests for state comparison logic."""

    def test_no_changes(self):
        prev = {"deny_policy_attached": False, "kill_switch_active": False, "budget_percent": 50}
        curr = {"deny_policy_attached": False, "kill_switch_active": False, "budget_percent": 50, "checked_at": "now"}
        assert diff_states(prev, curr) == []

    def test_deny_policy_change(self):
        prev = {"deny_policy_attached": False}
        curr = {"deny_policy_attached": True, "checked_at": "now"}
        changes = diff_states(prev, curr)
        assert len(changes) == 1
        assert changes[0]["field"] == "deny_policy_attached"
        assert changes[0]["old"] is False
        assert changes[0]["new"] is True

    def test_kill_switch_change(self):
        prev = {"kill_switch_active": False}
        curr = {"kill_switch_active": True, "checked_at": "now"}
        changes = diff_states(prev, curr)
        assert any(c["field"] == "kill_switch_active" for c in changes)

    def test_auth_change(self):
        prev = {"auth_enabled": False}
        curr = {"auth_enabled": True, "checked_at": "now"}
        changes = diff_states(prev, curr)
        assert any(c["field"] == "auth_enabled" for c in changes)

    def test_budget_threshold_crossing(self):
        prev = {"budget_percent": 35}
        curr = {"budget_percent": 45, "checked_at": "now"}
        changes = diff_states(prev, curr)
        # Should detect crossing 40% threshold
        threshold_changes = [c for c in changes if "budget_threshold" in c["field"]]
        assert len(threshold_changes) == 1
        assert "40" in threshold_changes[0]["field"]

    def test_budget_multiple_thresholds(self):
        prev = {"budget_percent": 35}
        curr = {"budget_percent": 96, "checked_at": "now"}
        changes = diff_states(prev, curr)
        threshold_changes = [c for c in changes if "budget_threshold" in c["field"]]
        # Should cross 40, 80, and 95
        assert len(threshold_changes) == 3

    def test_budget_threshold_crossing_down(self):
        prev = {"budget_percent": 85}
        curr = {"budget_percent": 75, "checked_at": "now"}
        changes = diff_states(prev, curr)
        threshold_changes = [c for c in changes if "budget_threshold" in c["field"]]
        assert len(threshold_changes) == 1
        assert "below" in threshold_changes[0]["new"]

    def test_empty_previous_state(self):
        prev = {}
        curr = {"deny_policy_attached": False, "kill_switch_active": False, "checked_at": "now"}
        changes = diff_states(prev, curr)
        # First run: no changes reported
        assert changes == []

    def test_none_current_value_skipped(self):
        prev = {"deny_policy_attached": False}
        curr = {"deny_policy_attached": None, "checked_at": "now"}
        changes = diff_states(prev, curr)
        # None means API error — don't alert
        assert changes == []


class TestFetchCurrentState:
    """Tests for AWS API calls."""

    @patch("src.hermes_poller._client")
    def test_fetch_all_healthy(self, mock_client):
        iam = MagicMock()
        lam = MagicMock()
        cw = MagicMock()
        budgets = MagicMock()

        def client_router(service):
            return {"iam": iam, "lambda": lam, "cloudwatch": cw, "budgets": budgets}[service]

        mock_client.side_effect = client_router

        iam.list_attached_role_policies.return_value = {
            "AttachedPolicies": [{"PolicyName": "AWSLambdaBasicExecutionRole"}]
        }
        lam.get_function_concurrency.return_value = {"ReservedConcurrentExecutions": 10}
        lam.get_function_configuration.return_value = {
            "Environment": {"Variables": {"AUTH_ENABLED": "true"}}
        }
        budgets.describe_budget.return_value = {
            "Budget": {
                "BudgetLimit": {"Amount": "25"},
                "CalculatedSpend": {"ActualSpend": {"Amount": "10"}},
            }
        }

        state = fetch_current_state()
        assert state["deny_policy_attached"] is False
        assert state["kill_switch_active"] is False
        assert state["auth_enabled"] is True
        assert state["budget_percent"] == 40.0
        assert "checked_at" in state


class TestLoadPreviousState:
    """Tests for DynamoDB state loading."""

    @patch("src.hermes_poller._client")
    def test_load_existing_state(self, mock_client):
        db = MagicMock()
        mock_client.return_value = db
        db.get_item.return_value = {
            "Item": {
                "thread_id": {"S": "hermes-state"},
                "checkpoint_id": {"S": "latest"},
                "state": {"S": json.dumps({"deny_policy_attached": False})},
            }
        }
        state = load_previous_state()
        assert state["deny_policy_attached"] is False

    @patch("src.hermes_poller._client")
    def test_load_missing_state(self, mock_client):
        from botocore.exceptions import ClientError

        db = MagicMock()
        mock_client.return_value = db
        db.get_item.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException", "Message": ""}},
            "GetItem",
        )
        state = load_previous_state()
        assert state == {}


class TestSaveState:
    """Tests for DynamoDB state saving."""

    @patch("src.hermes_poller._client")
    def test_save_state(self, mock_client):
        db = MagicMock()
        mock_client.return_value = db
        save_current_state({"deny_policy_attached": False, "checked_at": "2026-02-20T00:00:00Z"})
        db.put_item.assert_called_once()
        call_args = db.put_item.call_args
        item = call_args[1]["Item"] if "Item" in call_args[1] else call_args[0][0]
        assert item["thread_id"]["S"] == "hermes-state"


class TestPublishAlert:
    """Tests for SNS alert publishing."""

    @patch("src.hermes_poller._client")
    def test_publish_critical_alert(self, mock_client):
        sns = MagicMock()
        mock_client.return_value = sns

        changes = [{"field": "deny_policy_attached", "old": False, "new": True}]
        current = {"checked_at": "2026-02-20T00:00:00Z"}
        publish_alert(changes, current)

        sns.publish.assert_called_once()
        call_kwargs = sns.publish.call_args[1]
        assert "CRITICAL" in call_kwargs["Subject"]
        assert "deny_policy_attached" in call_kwargs["Message"]
        assert "runbook 10902" in call_kwargs["Message"]

    @patch("src.hermes_poller._client")
    def test_publish_info_alert(self, mock_client):
        sns = MagicMock()
        mock_client.return_value = sns

        changes = [{"field": "auth_enabled", "old": False, "new": True}]
        current = {"checked_at": "2026-02-20T00:00:00Z"}
        publish_alert(changes, current)

        call_kwargs = sns.publish.call_args[1]
        assert "INFO" in call_kwargs["Subject"]


class TestLambdaHandler:
    """Integration tests for the handler."""

    @patch("src.hermes_poller.save_current_state")
    @patch("src.hermes_poller.load_previous_state")
    @patch("src.hermes_poller.fetch_current_state")
    def test_no_changes(self, mock_fetch, mock_load, mock_save):
        state = {"deny_policy_attached": False, "kill_switch_active": False, "checked_at": "now"}
        mock_fetch.return_value = state
        mock_load.return_value = {"deny_policy_attached": False, "kill_switch_active": False}

        result = lambda_handler({}, None)
        assert result["statusCode"] == 200
        assert result["changes"] == 0
        mock_save.assert_called_once_with(state)

    @patch("src.hermes_poller.publish_alert")
    @patch("src.hermes_poller.save_current_state")
    @patch("src.hermes_poller.load_previous_state")
    @patch("src.hermes_poller.fetch_current_state")
    def test_with_changes(self, mock_fetch, mock_load, mock_save, mock_publish):
        mock_fetch.return_value = {"deny_policy_attached": True, "checked_at": "now"}
        mock_load.return_value = {"deny_policy_attached": False}

        result = lambda_handler({}, None)
        assert result["statusCode"] == 200
        assert result["changes"] == 1
        mock_publish.assert_called_once()
