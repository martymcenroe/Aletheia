"""Tests for admin business metrics endpoint.

Issue #368: Business Metrics Dashboard.
"""

import json
import time
from unittest.mock import MagicMock, patch

import jwt

from src.auth.metrics_handler import (
    calculate_revenue_projection,
    clear_cache,
    fetch_conversion_metrics,
    fetch_tier_distribution,
    get_cached_metrics,
    handle_metrics_request,
    set_cached_metrics,
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

JWT_SECRET = "test-secret-key-for-metrics-handler-testing-only-32chars!"


def _make_jwt(tier: str = "admin", user_id: str = "user-123") -> str:
    """Create a test JWT with all required fields."""
    import uuid
    payload = {
        "user_id": user_id,
        "tier": tier,
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def _make_event(token: str | None = None) -> dict:
    """Create a Lambda event with optional JWT."""
    headers: dict[str, str] = {}
    if token:
        headers["authorization"] = f"Bearer {token}"
    return {
        "requestContext": {"http": {"method": "GET", "path": "/metrics"}},
        "headers": headers,
    }


# --------------------------------------------------------------------------- #
# Auth Tests
# --------------------------------------------------------------------------- #


class TestMetricsAuth:
    """T010-T030: Authentication and authorization tests."""

    def setup_method(self):
        clear_cache()

    @patch("src.auth.metrics_handler.get_jwt_secret", return_value=JWT_SECRET)
    def test_401_no_jwt(self, mock_secret):
        """T010: Returns 401 when no Authorization header (REQ-1)."""
        event = _make_event(token=None)
        result = handle_metrics_request(event)
        assert result["statusCode"] == 401
        body = json.loads(result["body"])
        assert "Unauthorized" in body["error"]

    @patch("src.auth.metrics_handler.get_jwt_secret", return_value=JWT_SECRET)
    def test_401_invalid_jwt(self, mock_secret):
        """T020: Returns 401 when JWT signature invalid (REQ-1)."""
        bad_token = jwt.encode(
            {"user_id": "u", "tier": "admin", "exp": time.time() + 3600},
            "wrong-secret",
            algorithm="HS256",
        )
        event = _make_event(token=bad_token)
        result = handle_metrics_request(event)
        assert result["statusCode"] == 401

    @patch("src.auth.metrics_handler.get_jwt_secret", return_value=JWT_SECRET)
    @patch("src.auth.metrics_handler._get_dynamodb_client")
    def test_403_non_admin(self, mock_ddb, mock_secret):
        """T030: Returns 403 when tier is 'free' (REQ-2)."""
        token = _make_jwt(tier="free")
        event = _make_event(token=token)
        result = handle_metrics_request(event)
        assert result["statusCode"] == 403
        body = json.loads(result["body"])
        assert "Admin access required" in body["error"]

    @patch("src.auth.metrics_handler.get_jwt_secret", return_value=JWT_SECRET)
    @patch("src.auth.metrics_handler._get_dynamodb_client")
    def test_403_subscriber(self, mock_ddb, mock_secret):
        """T030b: Returns 403 when tier is 'subscriber' (REQ-2)."""
        token = _make_jwt(tier="subscriber")
        event = _make_event(token=token)
        result = handle_metrics_request(event)
        assert result["statusCode"] == 403


# --------------------------------------------------------------------------- #
# Successful Response Tests
# --------------------------------------------------------------------------- #


class TestMetricsResponse:
    """T040: Successful metrics response tests."""

    def setup_method(self):
        clear_cache()

    @patch("src.auth.metrics_handler.get_jwt_secret", return_value=JWT_SECRET)
    @patch("src.auth.metrics_handler._get_dynamodb_client")
    def test_200_admin_all_keys(self, mock_ddb, mock_secret):
        """T040: Returns 200 with all metric keys for admin (REQ-3)."""
        mock_client = MagicMock()
        mock_client.scan.return_value = {"Items": []}
        mock_client.exceptions = MagicMock()
        mock_client.exceptions.ResourceNotFoundException = type(
            "ResourceNotFoundException", (Exception,), {}
        )
        mock_ddb.return_value = mock_client

        token = _make_jwt(tier="admin")
        event = _make_event(token=token)
        result = handle_metrics_request(event)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        expected_keys = [
            "adoption",
            "tiers",
            "conversion",
            "coupons",
            "revenue",
            "retention",
            "geography",
        ]
        for key in expected_keys:
            assert key in body, f"Missing key: {key}"

    @patch("src.auth.metrics_handler.get_jwt_secret", return_value=JWT_SECRET)
    @patch("src.auth.metrics_handler._get_dynamodb_client")
    def test_no_pii_in_response(self, mock_ddb, mock_secret):
        """T110: Response contains no email, user_id, or IP (REQ-10)."""
        mock_client = MagicMock()
        mock_client.scan.return_value = {"Items": []}
        mock_client.exceptions = MagicMock()
        mock_client.exceptions.ResourceNotFoundException = type(
            "ResourceNotFoundException", (Exception,), {}
        )
        mock_ddb.return_value = mock_client

        token = _make_jwt(tier="admin")
        event = _make_event(token=token)
        result = handle_metrics_request(event)

        body_str = result["body"]
        assert "user_id" not in body_str.lower() or "user_id" not in json.loads(body_str)
        assert "@" not in body_str  # No email addresses
        # IP addresses pattern check
        import re
        assert not re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", body_str)

    @patch("src.auth.metrics_handler.get_jwt_secret", return_value=JWT_SECRET)
    @patch("src.auth.metrics_handler._get_dynamodb_client")
    def test_cors_headers(self, mock_ddb, mock_secret):
        """T120: Response includes correct CORS headers (REQ-3)."""
        mock_client = MagicMock()
        mock_client.scan.return_value = {"Items": []}
        mock_client.exceptions = MagicMock()
        mock_client.exceptions.ResourceNotFoundException = type(
            "ResourceNotFoundException", (Exception,), {}
        )
        mock_ddb.return_value = mock_client

        token = _make_jwt(tier="admin")
        event = _make_event(token=token)
        result = handle_metrics_request(event)

        assert result["headers"]["Access-Control-Allow-Origin"] == "https://aletheia.study"


# --------------------------------------------------------------------------- #
# Cache Tests
# --------------------------------------------------------------------------- #


class TestMetricsCache:
    """T050, T060: Cache behavior tests."""

    def setup_method(self):
        clear_cache()

    def test_cache_miss_returns_none(self):
        """Cache returns None when empty."""
        assert get_cached_metrics() is None

    def test_cache_hit_within_ttl(self):
        """T050: Returns cached response within 5 minutes (REQ-12)."""
        metrics = {"adoption": [], "cached": False}
        set_cached_metrics(metrics)
        result = get_cached_metrics()
        assert result is not None
        assert result["adoption"] == []

    def test_cache_miss_after_ttl(self, monkeypatch):
        """T060: Returns None after cache expiry (REQ-12)."""
        metrics = {"adoption": []}
        set_cached_metrics(metrics)
        # Fast-forward time
        import src.auth.metrics_handler as m
        m._cache_timestamp = time.time() - 301  # 5 min + 1 sec
        result = get_cached_metrics()
        assert result is None

    @patch("src.auth.metrics_handler.get_jwt_secret", return_value=JWT_SECRET)
    @patch("src.auth.metrics_handler._get_dynamodb_client")
    def test_second_call_uses_cache(self, mock_ddb, mock_secret):
        """T050b: Second call within 5 min returns cached data (REQ-12)."""
        mock_client = MagicMock()
        mock_client.scan.return_value = {"Items": []}
        mock_client.exceptions = MagicMock()
        mock_client.exceptions.ResourceNotFoundException = type(
            "ResourceNotFoundException", (Exception,), {}
        )
        mock_ddb.return_value = mock_client

        token = _make_jwt(tier="admin")
        event = _make_event(token=token)

        # First call - fresh
        r1 = handle_metrics_request(event)
        assert json.loads(r1["body"])["cached"] is False

        # Second call - cached
        r2 = handle_metrics_request(event)
        assert json.loads(r2["body"])["cached"] is True


# --------------------------------------------------------------------------- #
# Individual Metric Tests
# --------------------------------------------------------------------------- #


class TestTierDistribution:
    """T080: Tier distribution tests."""

    def test_counts_tiers_correctly(self):
        """T080: Returns correct counts per tier (REQ-3)."""
        mock_client = MagicMock()
        mock_client.scan.return_value = {
            "Items": [
                {"tier": {"S": "free"}},
                {"tier": {"S": "free"}},
                {"tier": {"S": "subscriber"}},
                {"tier": {"S": "admin"}},
            ]
        }
        result = fetch_tier_distribution(mock_client)
        assert result == {"free": 2, "subscriber": 1, "admin": 1}


class TestConversionMetrics:
    """T090: Conversion rate tests."""

    def test_conversion_rate_calculation(self):
        """T090: Calculates percentage correctly (REQ-3)."""
        tiers = {"free": 90, "subscriber": 10, "admin": 1}
        result = fetch_conversion_metrics(MagicMock(), tiers)
        assert result["rate"] == 10.0
        assert result["converted_count"] == 10
        assert result["eligible_count"] == 100

    def test_zero_users(self):
        """Handles zero users gracefully."""
        tiers = {"free": 0, "subscriber": 0, "admin": 0}
        result = fetch_conversion_metrics(MagicMock(), tiers)
        assert result["rate"] == 0.0


class TestRevenueProjection:
    """T100: Revenue projection tests."""

    def test_revenue_projection(self):
        """T100: Multiplies subscriber count by price (REQ-3)."""
        result = calculate_revenue_projection(50, monthly_price=9.99)
        assert result["subscriber_count"] == 50
        assert result["monthly_price"] == 9.99
        assert result["projected_monthly"] == 499.50

    def test_zero_subscribers(self):
        """Zero subscribers = zero revenue."""
        result = calculate_revenue_projection(0)
        assert result["projected_monthly"] == 0.0


class TestMockMetricsJson:
    """T130: Mock mode fixture tests."""

    def test_mock_metrics_json_valid(self):
        """T130: mock-metrics.json is valid JSON with required keys."""
        import os
        fixture_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "static",
            "admin",
            "mock-metrics.json",
        )
        with open(fixture_path) as f:
            data = json.load(f)
        expected_keys = [
            "adoption", "tiers", "conversion", "coupons",
            "revenue", "retention", "geography",
        ]
        for key in expected_keys:
            assert key in data, f"Missing key in mock data: {key}"
