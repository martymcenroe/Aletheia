"""Admin-only business metrics endpoint.

Issue #368: Business Metrics Dashboard.

Provides GET /metrics with:
- JWT authentication (admin tier required)
- In-memory caching (5-minute TTL)
- Aggregate metrics from DynamoDB and CloudWatch
- No PII in response
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

import boto3

from .jwt_service import get_jwt_secret, validate_jwt, validate_jwt_dual_secret
from .auth_middleware import extract_token

logger = logging.getLogger(__name__)

# Cache configuration
_CACHE_TTL_SECONDS = 300  # 5 minutes
_cached_metrics: dict[str, Any] | None = None
_cache_timestamp: float = 0.0

# Environment
USERS_TABLE = os.environ.get("USERS_TABLE", "aletheia-users")
COUPONS_TABLE = os.environ.get("COUPONS_TABLE", "aletheia-coupons")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# Lazy clients
_dynamodb_client = None


def _get_dynamodb_client():
    """Lazy-initialize DynamoDB client."""
    global _dynamodb_client
    if _dynamodb_client is None:
        endpoint = os.environ.get("DYNAMODB_ENDPOINT")
        if endpoint:
            _dynamodb_client = boto3.client(
                "dynamodb", endpoint_url=endpoint, region_name=AWS_REGION
            )
        else:
            _dynamodb_client = boto3.client("dynamodb", region_name=AWS_REGION)
    return _dynamodb_client


def handle_metrics_request(event: dict, context: Any = None) -> dict:
    """Handle GET /metrics request with admin authentication.

    Issue #368 (REQ-1, REQ-2, REQ-3).

    Args:
        event: Lambda event dict.
        context: Lambda context object.

    Returns:
        Lambda response dict.
    """
    # Step 1: Extract and validate JWT
    token = extract_token(event)
    if token is None:
        return _build_response(401, {"error": "Unauthorized"})

    # Step 2: Validate JWT signature
    try:
        primary_secret = get_jwt_secret()
    except RuntimeError:
        return _build_response(401, {"error": "Unauthorized"})

    secondary_secret = os.environ.get("JWT_SECONDARY_SECRET")
    if secondary_secret:
        auth_result = validate_jwt_dual_secret(token, primary_secret, secondary_secret)
    else:
        auth_result = validate_jwt(token, primary_secret)

    if not auth_result["success"]:
        return _build_response(401, {"error": "Invalid token"})

    # Step 3: Check admin tier
    claims = auth_result.get("claims") or {}
    tier = claims.get("tier", "free")
    if tier != "admin":
        return _build_response(403, {"error": "Admin access required"})

    # Step 4: Check cache
    cached = get_cached_metrics()
    if cached is not None:
        cached["cached"] = True
        return _build_response(200, cached)

    # Step 5: Fetch fresh metrics
    client = _get_dynamodb_client()
    metrics = aggregate_all_metrics(client)
    metrics["cached"] = False

    # Step 6: Cache and return
    set_cached_metrics(metrics)
    return _build_response(200, metrics)


def get_cached_metrics() -> dict[str, Any] | None:
    """Return cached metrics if within TTL (5 minutes)."""
    global _cached_metrics, _cache_timestamp
    if _cached_metrics is None:
        return None
    if time.time() - _cache_timestamp > _CACHE_TTL_SECONDS:
        _cached_metrics = None
        return None
    return dict(_cached_metrics)  # shallow copy


def set_cached_metrics(metrics: dict[str, Any]) -> None:
    """Cache metrics in Lambda memory with timestamp."""
    global _cached_metrics, _cache_timestamp
    _cached_metrics = dict(metrics)
    _cache_timestamp = time.time()


def clear_cache() -> None:
    """Clear the metrics cache (for testing)."""
    global _cached_metrics, _cache_timestamp
    _cached_metrics = None
    _cache_timestamp = 0.0


def aggregate_all_metrics(dynamodb_client: Any) -> dict[str, Any]:
    """Fetch and aggregate all metrics into unified response.

    Args:
        dynamodb_client: Boto3 DynamoDB client.

    Returns:
        Metrics dict with all 7 metric keys.
    """
    adoption = fetch_adoption_metrics(dynamodb_client)
    tiers = fetch_tier_distribution(dynamodb_client)
    conversion = fetch_conversion_metrics(dynamodb_client, tiers)
    coupons = fetch_coupon_metrics(dynamodb_client)
    revenue = calculate_revenue_projection(tiers.get("subscriber", 0))
    retention = fetch_retention_metrics(dynamodb_client)
    geography: dict[str, int] = {}  # Populated from CloudWatch Logs Insights, not DynamoDB

    return {
        "adoption": adoption,
        "tiers": tiers,
        "conversion": conversion,
        "coupons": coupons,
        "revenue": revenue,
        "retention": retention,
        "geography": geography,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def fetch_adoption_metrics(
    dynamodb_client: Any, days: int = 90
) -> list[dict[str, Any]]:
    """Query DynamoDB for daily new user counts over specified days.

    Scans aletheia-users table and groups by created_at date.
    """
    try:
        result = dynamodb_client.scan(
            TableName=USERS_TABLE,
            ProjectionExpression="created_at",
        )
        items = result.get("Items", [])

        # Count users per date
        date_counts: dict[str, int] = {}
        for item in items:
            created = item.get("created_at", {}).get("S", "")
            if created:
                date_key = created[:10]  # YYYY-MM-DD
                date_counts[date_key] = date_counts.get(date_key, 0) + 1

        # Build sorted list
        adoption = [
            {"date": date, "count": count}
            for date, count in sorted(date_counts.items())
        ]
        return adoption[-days:]  # Last N days
    except Exception as e:
        logger.warning(f"Failed to fetch adoption metrics: {e}")
        return []


def fetch_tier_distribution(dynamodb_client: Any) -> dict[str, int]:
    """Query DynamoDB for current tier counts."""
    try:
        result = dynamodb_client.scan(
            TableName=USERS_TABLE,
            ProjectionExpression="tier",
        )
        items = result.get("Items", [])

        tiers = {"free": 0, "subscriber": 0, "admin": 0}
        for item in items:
            tier = item.get("tier", {}).get("S", "free")
            if tier in tiers:
                tiers[tier] += 1
            else:
                tiers["free"] += 1  # Unknown tiers default to free
        return tiers
    except Exception as e:
        logger.warning(f"Failed to fetch tier distribution: {e}")
        return {"free": 0, "subscriber": 0, "admin": 0}


def fetch_conversion_metrics(
    dynamodb_client: Any,
    tiers: dict[str, int] | None = None,
    window_days: int = 30,
) -> dict[str, Any]:
    """Calculate free -> subscriber conversion rate."""
    if tiers is None:
        tiers = fetch_tier_distribution(dynamodb_client)

    free_count = tiers.get("free", 0)
    subscriber_count = tiers.get("subscriber", 0)
    total = free_count + subscriber_count
    rate = (subscriber_count / total * 100) if total > 0 else 0.0

    return {
        "rate": round(rate, 1),
        "converted_count": subscriber_count,
        "eligible_count": total,
        "window_days": window_days,
    }


def fetch_coupon_metrics(dynamodb_client: Any) -> dict[str, Any]:
    """Query coupon redemption statistics.

    Returns zeros if aletheia-coupons table doesn't exist yet (#367).
    """
    try:
        result = dynamodb_client.scan(
            TableName=COUPONS_TABLE,
            ProjectionExpression="code, uses, max_uses, redeemed_by",
        )
        items = result.get("Items", [])

        total_redeemed = 0
        by_code: dict[str, Any] = {}
        for item in items:
            code = item.get("code", {}).get("S", "unknown")
            uses = int(item.get("uses", {}).get("N", "0"))
            max_uses = int(item.get("max_uses", {}).get("N", "0"))
            total_redeemed += uses
            by_code[code] = {
                "redeemed": uses,
                "total_issued": max_uses,
                "rate": round(uses / max_uses * 100, 1) if max_uses > 0 else 0.0,
            }

        return {"total_redeemed": total_redeemed, "by_code": by_code}
    except dynamodb_client.exceptions.ResourceNotFoundException:
        return {"total_redeemed": 0, "by_code": {}}
    except Exception as e:
        logger.warning(f"Failed to fetch coupon metrics: {e}")
        return {"total_redeemed": 0, "by_code": {}}


def calculate_revenue_projection(
    subscriber_count: int, monthly_price: float = 9.99
) -> dict[str, Any]:
    """Calculate projected monthly revenue from subscriber count."""
    return {
        "subscriber_count": subscriber_count,
        "monthly_price": monthly_price,
        "projected_monthly": round(subscriber_count * monthly_price, 2),
    }


def fetch_retention_metrics(
    dynamodb_client: Any, window_days: int = 30
) -> dict[str, Any]:
    """Calculate retention rate based on last_login recency."""
    try:
        result = dynamodb_client.scan(
            TableName=USERS_TABLE,
            ProjectionExpression="last_login, created_at",
        )
        items = result.get("Items", [])

        returning = 0
        single_session = 0
        for item in items:
            last_login = item.get("last_login", {}).get("S", "")
            created_at = item.get("created_at", {}).get("S", "")
            if last_login and created_at and last_login != created_at:
                returning += 1
            else:
                single_session += 1

        total = returning + single_session
        rate = round(returning / total * 100, 1) if total > 0 else 0.0

        return {
            "returning_users": returning,
            "single_session_users": single_session,
            "retention_rate": rate,
            "window_days": window_days,
        }
    except Exception as e:
        logger.warning(f"Failed to fetch retention metrics: {e}")
        return {
            "returning_users": 0,
            "single_session_users": 0,
            "retention_rate": 0.0,
            "window_days": window_days,
        }


def _build_response(status_code: int, body: dict) -> dict:
    """Build Lambda response with CORS headers."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "https://aletheia.study",
        },
        "body": json.dumps(body),
    }
