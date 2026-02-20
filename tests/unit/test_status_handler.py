"""Tests for admin status endpoint.

Issue #400: Hermes Dashboard — /admin/status endpoint.
"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

# Set env vars before importing
os.environ.setdefault("AWS_REGION", "us-east-1")
os.environ.setdefault("JWT_SECRET_NAME", "aletheia/jwt-signing-key")

from src.auth.status_handler import (  # noqa: E402
    _build_response,
    _check_alarm_states,
    _check_budget,
    _check_deny_policy,
    _check_kill_switch,
    _fetch_protection_status,
    clear_cache,
    handle_status_request,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    """Clear cache before each test."""
    clear_cache()
    yield
    clear_cache()


def _make_event(token=None):
    """Build a minimal Lambda event with optional JWT."""
    headers = {}
    if token:
        headers["authorization"] = f"Bearer {token}"
    return {
        "headers": headers,
        "requestContext": {"http": {"method": "GET", "path": "/admin/status"}},
    }


class TestAuth:
    """Authentication and authorization tests."""

    def test_no_token_returns_401(self):
        event = _make_event()
        result = handle_status_request(event)
        assert result["statusCode"] == 401

    @patch("src.auth.status_handler.get_jwt_secret", side_effect=RuntimeError("no secret"))
    def test_secret_unavailable_returns_401(self, _mock):
        event = _make_event(token="some.jwt.token")
        result = handle_status_request(event)
        assert result["statusCode"] == 401

    @patch("src.auth.status_handler.get_jwt_secret", return_value="test-secret")
    @patch("src.auth.status_handler.validate_jwt")
    def test_invalid_token_returns_401(self, mock_validate, _mock_secret):
        mock_validate.return_value = {
            "success": False,
            "user_id": None,
            "error": "bad",
            "reason": "invalid_signature",
            "claims": None,
        }
        event = _make_event(token="bad.jwt.token")
        result = handle_status_request(event)
        assert result["statusCode"] == 401

    @patch("src.auth.status_handler.get_jwt_secret", return_value="test-secret")
    @patch("src.auth.status_handler.validate_jwt")
    def test_non_admin_returns_403(self, mock_validate, _mock_secret):
        mock_validate.return_value = {
            "success": True,
            "user_id": "user123",
            "error": None,
            "reason": None,
            "claims": {"tier": "free"},
        }
        event = _make_event(token="valid.jwt.token")
        result = handle_status_request(event)
        assert result["statusCode"] == 403
        body = json.loads(result["body"])
        assert body["error"] == "Admin access required"


class TestDenyPolicy:
    """Tests for deny policy detection."""

    @patch("src.auth.status_handler._get_iam_client")
    def test_deny_policy_attached(self, mock_client_fn):
        client = MagicMock()
        mock_client_fn.return_value = client
        client.list_attached_role_policies.return_value = {
            "AttachedPolicies": [
                {"PolicyName": "AWSLambdaBasicExecutionRole", "PolicyArn": "arn:..."},
                {"PolicyName": "AletheiaDenyBedrock-BudgetBreach", "PolicyArn": "arn:..."},
            ]
        }
        assert _check_deny_policy() is True

    @patch("src.auth.status_handler._get_iam_client")
    def test_deny_policy_not_attached(self, mock_client_fn):
        client = MagicMock()
        mock_client_fn.return_value = client
        client.list_attached_role_policies.return_value = {
            "AttachedPolicies": [
                {"PolicyName": "AWSLambdaBasicExecutionRole", "PolicyArn": "arn:..."},
            ]
        }
        assert _check_deny_policy() is False

    @patch("src.auth.status_handler._get_iam_client")
    def test_deny_policy_error_returns_false(self, mock_client_fn):
        from botocore.exceptions import ClientError

        client = MagicMock()
        mock_client_fn.return_value = client
        client.list_attached_role_policies.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "denied"}}, "ListAttachedRolePolicies"
        )
        assert _check_deny_policy() is False


class TestKillSwitch:
    """Tests for kill switch detection."""

    @patch("src.auth.status_handler._get_lambda_client")
    def test_kill_switch_active(self, mock_client_fn):
        client = MagicMock()
        mock_client_fn.return_value = client
        client.get_function_concurrency.return_value = {"ReservedConcurrentExecutions": 0}
        assert _check_kill_switch() is True

    @patch("src.auth.status_handler._get_lambda_client")
    def test_kill_switch_not_active(self, mock_client_fn):
        client = MagicMock()
        mock_client_fn.return_value = client
        client.get_function_concurrency.return_value = {"ReservedConcurrentExecutions": 5}
        assert _check_kill_switch() is False

    @patch("src.auth.status_handler._get_lambda_client")
    def test_no_concurrency_setting(self, mock_client_fn):
        from botocore.exceptions import ClientError

        client = MagicMock()
        mock_client_fn.return_value = client
        client.get_function_concurrency.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException", "Message": "not found"}},
            "GetFunctionConcurrency",
        )
        assert _check_kill_switch() is False


class TestAlarmStates:
    """Tests for alarm state detection."""

    @patch("src.auth.status_handler._get_cloudwatch_client")
    def test_alarm_states(self, mock_client_fn):
        client = MagicMock()
        mock_client_fn.return_value = client
        client.describe_alarms.return_value = {
            "MetricAlarms": [
                {"AlarmName": "AletheiaAgent-InvocationSpike", "StateValue": "OK"},
                {"AlarmName": "AletheiaAgent-Throttles", "StateValue": "ALARM"},
                {"AlarmName": "AletheiaKillSwitch-Failure", "StateValue": "OK"},
            ]
        }
        states = _check_alarm_states()
        assert states["AletheiaAgent-InvocationSpike"] == "OK"
        assert states["AletheiaAgent-Throttles"] == "ALARM"
        assert states["AletheiaKillSwitch-Failure"] == "OK"
        # Missing alarms get NOT_FOUND
        assert states["Aletheia-LambdaErrors"] == "NOT_FOUND"


class TestBudget:
    """Tests for budget status detection."""

    @patch("src.auth.status_handler._get_budgets_client")
    def test_budget_check(self, mock_client_fn):
        client = MagicMock()
        mock_client_fn.return_value = client
        client.describe_budget.return_value = {
            "Budget": {
                "BudgetLimit": {"Amount": "25.0", "Unit": "USD"},
                "CalculatedSpend": {
                    "ActualSpend": {"Amount": "12.91", "Unit": "USD"},
                    "ForecastedSpend": {"Amount": "19.58", "Unit": "USD"},
                },
            }
        }
        budget = _check_budget()
        assert budget["limit"] == 25.0
        assert budget["actual"] == 12.91
        assert budget["forecasted"] == 19.58
        assert budget["percent_used"] == 51.6


class TestOverallStatus:
    """Tests for overall status determination."""

    @patch("src.auth.status_handler._check_budget")
    @patch("src.auth.status_handler._check_alarm_states")
    @patch("src.auth.status_handler._check_kill_switch")
    @patch("src.auth.status_handler._check_deny_policy")
    def test_healthy_status(self, mock_deny, mock_kill, mock_alarms, mock_budget):
        mock_deny.return_value = False
        mock_kill.return_value = False
        mock_alarms.return_value = {"AletheiaAgent-InvocationSpike": "OK"}
        mock_budget.return_value = {"limit": 25, "actual": 5, "forecasted": 10, "percent_used": 20}

        status = _fetch_protection_status()
        assert status["overall_status"] == "healthy"
        assert len(status["issues"]) == 0

    @patch("src.auth.status_handler._check_budget")
    @patch("src.auth.status_handler._check_alarm_states")
    @patch("src.auth.status_handler._check_kill_switch")
    @patch("src.auth.status_handler._check_deny_policy")
    def test_down_when_deny_policy(self, mock_deny, mock_kill, mock_alarms, mock_budget):
        mock_deny.return_value = True
        mock_kill.return_value = False
        mock_alarms.return_value = {}
        mock_budget.return_value = {"limit": 25, "actual": 24, "forecasted": 30, "percent_used": 96}

        status = _fetch_protection_status()
        assert status["overall_status"] == "down"
        assert "Bedrock deny policy attached" in status["issues"]

    @patch("src.auth.status_handler._check_budget")
    @patch("src.auth.status_handler._check_alarm_states")
    @patch("src.auth.status_handler._check_kill_switch")
    @patch("src.auth.status_handler._check_deny_policy")
    def test_down_when_kill_switch(self, mock_deny, mock_kill, mock_alarms, mock_budget):
        mock_deny.return_value = False
        mock_kill.return_value = True
        mock_alarms.return_value = {}
        mock_budget.return_value = {"limit": 25, "actual": 5, "forecasted": 10, "percent_used": 20}

        status = _fetch_protection_status()
        assert status["overall_status"] == "down"
        assert "Kill switch active (concurrency=0)" in status["issues"]

    @patch("src.auth.status_handler._check_budget")
    @patch("src.auth.status_handler._check_alarm_states")
    @patch("src.auth.status_handler._check_kill_switch")
    @patch("src.auth.status_handler._check_deny_policy")
    def test_degraded_when_alarm_firing(self, mock_deny, mock_kill, mock_alarms, mock_budget):
        mock_deny.return_value = False
        mock_kill.return_value = False
        mock_alarms.return_value = {"AletheiaAgent-InvocationSpike": "ALARM"}
        mock_budget.return_value = {"limit": 25, "actual": 5, "forecasted": 10, "percent_used": 20}

        status = _fetch_protection_status()
        assert status["overall_status"] == "degraded"

    @patch("src.auth.status_handler._check_budget")
    @patch("src.auth.status_handler._check_alarm_states")
    @patch("src.auth.status_handler._check_kill_switch")
    @patch("src.auth.status_handler._check_deny_policy")
    def test_degraded_when_budget_high(self, mock_deny, mock_kill, mock_alarms, mock_budget):
        mock_deny.return_value = False
        mock_kill.return_value = False
        mock_alarms.return_value = {"AletheiaAgent-InvocationSpike": "OK"}
        mock_budget.return_value = {"limit": 25, "actual": 22, "forecasted": 28, "percent_used": 88}

        status = _fetch_protection_status()
        assert status["overall_status"] == "degraded"
        assert any("Budget at 88" in issue for issue in status["issues"])


class TestCaching:
    """Tests for response caching."""

    @patch("src.auth.status_handler._fetch_protection_status")
    @patch("src.auth.status_handler.get_jwt_secret", return_value="secret")
    @patch("src.auth.status_handler.validate_jwt")
    def test_cache_hit(self, mock_validate, _secret, mock_fetch):
        mock_validate.return_value = {
            "success": True,
            "user_id": "admin1",
            "error": None,
            "reason": None,
            "claims": {"tier": "admin"},
        }
        mock_fetch.return_value = {
            "protection": {},
            "overall_status": "healthy",
            "issues": [],
            "generated_at": "2026-02-20T00:00:00Z",
        }

        event = _make_event(token="admin.jwt.token")

        # First call fetches
        result1 = handle_status_request(event)
        assert result1["statusCode"] == 200
        body1 = json.loads(result1["body"])
        assert body1["cached"] is False

        # Second call uses cache
        result2 = handle_status_request(event)
        body2 = json.loads(result2["body"])
        assert body2["cached"] is True

        # fetch was only called once
        assert mock_fetch.call_count == 1


class TestBuildResponse:
    """Tests for response formatting."""

    def test_cors_header(self):
        resp = _build_response(200, {"test": True})
        assert resp["headers"]["Access-Control-Allow-Origin"] == "https://hermes.aletheia.study"

    def test_json_body(self):
        resp = _build_response(200, {"status": "ok"})
        body = json.loads(resp["body"])
        assert body["status"] == "ok"
