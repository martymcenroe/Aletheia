"""Tests for EMF metric emission functions.

Issue #369: CloudWatch Usage Dashboard.
TDD: Tests written before implementation.
"""

import json
import os

import pytest

from src.observability import (
    emit_request_metric,
    emit_cap_utilization_metric,
    emit_cap_denied_metric,
    emit_bedrock_cost_metric,
    emit_error_rate_metric,
    emit_latency_metric,
)


class TestEMFStructure:
    """T040, T190: Valid EMF structure and namespace tests."""

    def test_emit_request_metric_valid_emf(self, capsys):
        """T040: Output is valid EMF JSON with _aws block (REQ-1)."""
        emit_request_metric("free")
        captured = capsys.readouterr()
        payload = json.loads(captured.out.strip())
        assert "_aws" in payload
        assert "CloudWatchMetrics" in payload["_aws"]
        assert "Timestamp" in payload["_aws"]
        metrics_def = payload["_aws"]["CloudWatchMetrics"][0]
        assert "Namespace" in metrics_def
        assert "Dimensions" in metrics_def
        assert "Metrics" in metrics_def

    def test_emf_namespace_correct(self, capsys):
        """T190: Namespace is 'Aletheia/API' (REQ-1)."""
        emit_request_metric("free")
        captured = capsys.readouterr()
        payload = json.loads(captured.out.strip())
        namespace = payload["_aws"]["CloudWatchMetrics"][0]["Namespace"]
        assert namespace == "Aletheia/API"


class TestFailOpen:
    """T050, T120: Fail-open behavior tests."""

    def test_emit_request_metric_fail_open(self, monkeypatch):
        """T050: Exception in metric code does not propagate (REQ-7)."""
        # Monkey-patch print to raise an exception
        def bad_print(*args, **kwargs):
            raise OSError("CloudWatch unreachable")

        monkeypatch.setattr("builtins.print", bad_print)
        # Should not raise
        emit_request_metric("free")

    def test_fail_open_cloudwatch_unreachable(self, monkeypatch):
        """T120: API completes when CloudWatch unreachable (REQ-8)."""
        def bad_print(*args, **kwargs):
            raise ConnectionError("Network failure")

        monkeypatch.setattr("builtins.print", bad_print)
        # All emission functions should silently fail
        emit_request_metric("free")
        emit_cap_utilization_metric("free", "hourly", 75.0)
        emit_cap_denied_metric("free")
        emit_bedrock_cost_metric(0.0025)
        emit_error_rate_metric(500)
        emit_latency_metric(150.5)


class TestCapUtilization:
    """T060: CapUtilization metric tests."""

    def test_emit_cap_utilization_metric(self, capsys):
        """T060: CapUtilization emitted with percentage 0-100 (REQ-2)."""
        emit_cap_utilization_metric("free", "hourly", 75.0)
        captured = capsys.readouterr()
        payload = json.loads(captured.out.strip())
        assert payload["CapUtilization"] == 75.0
        metrics = payload["_aws"]["CloudWatchMetrics"][0]["Metrics"]
        metric_names = [m["Name"] for m in metrics]
        assert "CapUtilization" in metric_names
        cap_metric = next(m for m in metrics if m["Name"] == "CapUtilization")
        assert cap_metric["Unit"] == "Percent"


class TestCapDenied:
    """T070: CapDenied metric tests."""

    def test_emit_cap_denied_metric(self, capsys):
        """T070: CapDenied metric emitted with count=1 (REQ-3)."""
        emit_cap_denied_metric("free")
        captured = capsys.readouterr()
        payload = json.loads(captured.out.strip())
        assert payload["CapDenied"] == 1
        metrics = payload["_aws"]["CloudWatchMetrics"][0]["Metrics"]
        metric_names = [m["Name"] for m in metrics]
        assert "CapDenied" in metric_names


class TestBedrockCost:
    """T080: BedrockCostEstimate metric tests."""

    def test_emit_bedrock_cost_metric(self, capsys):
        """T080: Cost value emitted as float USD (REQ-4)."""
        emit_bedrock_cost_metric(0.0025)
        captured = capsys.readouterr()
        payload = json.loads(captured.out.strip())
        assert payload["BedrockCostEstimate"] == 0.0025
        metrics = payload["_aws"]["CloudWatchMetrics"][0]["Metrics"]
        metric_names = [m["Name"] for m in metrics]
        assert "BedrockCostEstimate" in metric_names
        cost_metric = next(
            m for m in metrics if m["Name"] == "BedrockCostEstimate"
        )
        assert cost_metric["Unit"] == "None"


class TestErrorRate:
    """T090, T100: ErrorRate metric tests."""

    def test_emit_error_rate_metric_4xx(self, capsys):
        """T090: ErrorRate emitted for 4xx status (REQ-5)."""
        emit_error_rate_metric(404)
        captured = capsys.readouterr()
        payload = json.loads(captured.out.strip())
        assert payload["ErrorRate"] == 1
        assert payload["StatusCode"] == 404

    def test_emit_error_rate_metric_5xx(self, capsys):
        """T100: ErrorRate emitted for 5xx status (REQ-5)."""
        emit_error_rate_metric(500)
        captured = capsys.readouterr()
        payload = json.loads(captured.out.strip())
        assert payload["ErrorRate"] == 1
        assert payload["StatusCode"] == 500


class TestLatency:
    """T110: Latency metric tests."""

    def test_emit_latency_metric_milliseconds(self, capsys):
        """T110: Latency value in correct unit (REQ-6)."""
        emit_latency_metric(150.5)
        captured = capsys.readouterr()
        payload = json.loads(captured.out.strip())
        assert payload["Latency"] == 150.5
        metrics = payload["_aws"]["CloudWatchMetrics"][0]["Metrics"]
        latency_metric = next(m for m in metrics if m["Name"] == "Latency")
        assert latency_metric["Unit"] == "Milliseconds"


class TestNoUserIdDimension:
    """T200: No user ID in metric dimensions (REQ-18)."""

    def test_emf_no_user_id_dimension(self, capsys):
        """T200: No user ID in metric dimensions (REQ-18)."""
        emit_request_metric("free")
        captured = capsys.readouterr()
        payload = json.loads(captured.out.strip())
        dims = payload["_aws"]["CloudWatchMetrics"][0]["Dimensions"]
        flat_dims = [d for group in dims for d in group]
        assert "user_id" not in flat_dims
        assert "UserId" not in flat_dims
        assert "UserID" not in flat_dims


class TestDashboardJson:
    """T130, T140: Dashboard JSON validation tests."""

    @pytest.fixture
    def dashboard_path(self):
        return os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "docs",
            "runbooks",
            "cloudwatch-dashboard.json",
        )

    def test_dashboard_json_valid(self, dashboard_path):
        """T130: cloudwatch-dashboard.json passes JSON parse (REQ-10)."""
        with open(dashboard_path) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_dashboard_widgets_complete(self, dashboard_path):
        """T140: Dashboard has 6 required widgets (REQ-11)."""
        with open(dashboard_path) as f:
            data = json.load(f)
        widgets = data.get("widgets", [])
        assert len(widgets) >= 6
        widget_titles = []
        for w in widgets:
            props = w.get("properties", {})
            title = props.get("title", "")
            widget_titles.append(title)
        expected = [
            "RequestVolume",
            "TierBreakdown",
            "CapUtilization",
            "CostTrend",
            "ErrorRate",
            "LatencyPercentiles",
        ]
        for title in expected:
            assert title in widget_titles, f"Missing widget: {title}"


class TestAlarmConfig:
    """T150, T160: Alarm configuration tests."""

    @pytest.fixture
    def alarm_path(self):
        return os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "docs",
            "runbooks",
            "sns-alarm.json",
        )

    def test_alarm_threshold_correct(self, alarm_path):
        """T150: Alarm threshold=10, period=3600 (REQ-12)."""
        with open(alarm_path) as f:
            data = json.load(f)
        alarm = data.get("alarm", {})
        assert alarm["Threshold"] == 10
        assert alarm["Period"] == 3600

    def test_sns_config_valid(self, alarm_path):
        """T160: SNS alarm config is valid JSON with TopicArn (REQ-13)."""
        with open(alarm_path) as f:
            data = json.load(f)
        assert "sns_topic" in data
        assert "TopicArn" in data["sns_topic"] or "Name" in data["sns_topic"]


class TestContributorInsights:
    """T170: Contributor Insights rule tests."""

    @pytest.fixture
    def rule_path(self):
        return os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "docs",
            "runbooks",
            "contributor-insights-top-talkers.json",
        )

    def test_contributor_insights_rule_valid(self, rule_path):
        """T170: Top talkers rule JSON is valid (REQ-15)."""
        with open(rule_path) as f:
            data = json.load(f)
        assert "RuleName" in data


class TestLogsInsightsQuery:
    """T180: Logs Insights query tests."""

    @pytest.fixture
    def query_path(self):
        return os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "docs",
            "runbooks",
            "logs-insights-active-users.sql",
        )

    def test_logs_insights_query_syntax(self, query_path):
        """T180: SQL query contains count_distinct (REQ-16)."""
        with open(query_path) as f:
            query = f.read()
        assert "count_distinct" in query
