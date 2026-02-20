"""Admin-only protection status endpoint.

Issue #400: Hermes Dashboard — /admin/status endpoint.

Provides GET /admin/status with:
- JWT authentication (admin tier required)
- In-memory caching (60-second TTL)
- Aggregated protection state from 4 AWS APIs
- No PII in response

Pattern follows: src/auth/metrics_handler.py
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

import boto3
from botocore.exceptions import ClientError

from .jwt_service import get_jwt_secret, validate_jwt, validate_jwt_dual_secret
from .auth_middleware import extract_token

logger = logging.getLogger(__name__)

# Cache configuration — shorter TTL than metrics since status is more urgent
_CACHE_TTL_SECONDS = 60  # 1 minute
_cached_status: dict[str, Any] | None = None
_cache_timestamp: float = 0.0

# Environment
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
ACCOUNT_ID = os.environ.get("AWS_ACCOUNT_ID", "383687041805")

# Resource names (from runbook 10902)
LAMBDA_ROLE_NAME = "AletheiaLambdaRole"
DENY_POLICY_NAME = "AletheiaDenyBedrock-BudgetBreach"
AGENT_FUNCTION_NAME = "AletheiaAgent"
BUDGET_NAME = "Aletheia-Monthly-10USD"
ALARM_NAMES = [
    "AletheiaAgent-InvocationSpike",
    "AletheiaAgent-Throttles",
    "AletheiaKillSwitch-Failure",
    "Aletheia-LambdaErrors",
    "Aletheia-HighLatency",
    "Aletheia-CapDenied",
]

# CORS origin for Hermes dashboard
HERMES_ORIGIN = "https://hermes.aletheia.study"

# Lazy-initialized clients
_iam_client = None
_lambda_client = None
_cloudwatch_client = None
_budgets_client = None


def _get_iam_client():
    global _iam_client
    if _iam_client is None:
        _iam_client = boto3.client("iam", region_name=AWS_REGION)
    return _iam_client


def _get_lambda_client():
    global _lambda_client
    if _lambda_client is None:
        _lambda_client = boto3.client("lambda", region_name=AWS_REGION)
    return _lambda_client


def _get_cloudwatch_client():
    global _cloudwatch_client
    if _cloudwatch_client is None:
        _cloudwatch_client = boto3.client("cloudwatch", region_name=AWS_REGION)
    return _cloudwatch_client


def _get_budgets_client():
    global _budgets_client
    if _budgets_client is None:
        _budgets_client = boto3.client("budgets", region_name=AWS_REGION)
    return _budgets_client


def handle_status_request(event: dict, context: Any = None) -> dict:
    """Handle GET /admin/status request with admin authentication.

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
    cached = _get_cached_status()
    if cached is not None:
        cached["cached"] = True
        return _build_response(200, cached)

    # Step 5: Fetch fresh status
    status = _fetch_protection_status()
    status["cached"] = False

    # Step 6: Cache and return
    _set_cached_status(status)
    return _build_response(200, status)


def _fetch_protection_status() -> dict[str, Any]:
    """Fetch aggregated protection state from AWS APIs.

    Makes 4 read-only API calls:
    - IAM: ListAttachedRolePolicies (deny policy check)
    - Lambda: GetFunctionConcurrency (kill switch check)
    - CloudWatch: DescribeAlarms (alarm states)
    - Budgets: DescribeBudget (spend vs limit)
    """
    protection: dict[str, Any] = {}
    issues: list[str] = []

    # 1. Check deny policy attachment
    protection["deny_policy_attached"] = _check_deny_policy()

    # 2. Check kill switch (concurrency = 0)
    protection["kill_switch_active"] = _check_kill_switch()

    # 3. Get alarm states
    protection["alarm_states"] = _check_alarm_states()

    # 4. Get budget info
    protection["budget"] = _check_budget()

    # 5. Auth enabled flag (from own Lambda env)
    protection["auth_enabled"] = (
        os.environ.get("AUTH_ENABLED", "false").lower() == "true"
    )

    # Determine overall status
    if protection["deny_policy_attached"] or protection["kill_switch_active"]:
        overall = "down"
        if protection["deny_policy_attached"]:
            issues.append("Bedrock deny policy attached")
        if protection["kill_switch_active"]:
            issues.append("Kill switch active (concurrency=0)")
    elif any(
        state == "ALARM" for state in protection["alarm_states"].values()
    ):
        overall = "degraded"
        alarming = [
            name
            for name, state in protection["alarm_states"].items()
            if state == "ALARM"
        ]
        issues.append(f"Alarms firing: {', '.join(alarming)}")
    else:
        overall = "healthy"

    budget = protection.get("budget", {})
    if budget.get("percent_used", 0) >= 80:
        if overall == "healthy":
            overall = "degraded"
        issues.append(f"Budget at {budget['percent_used']}%")

    return {
        "protection": protection,
        "overall_status": overall,
        "issues": issues,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def _check_deny_policy() -> bool:
    """Check if the Bedrock deny policy is attached to the Lambda role."""
    try:
        client = _get_iam_client()
        response = client.list_attached_role_policies(RoleName=LAMBDA_ROLE_NAME)
        for policy in response.get("AttachedPolicies", []):
            if DENY_POLICY_NAME in policy.get("PolicyName", ""):
                return True
        return False
    except ClientError as e:
        logger.warning(f"Failed to check deny policy: {e}")
        return False  # Fail open for read-only status check


def _check_kill_switch() -> bool:
    """Check if Lambda concurrency is set to 0 (kill switch active)."""
    try:
        client = _get_lambda_client()
        response = client.get_function_concurrency(FunctionName=AGENT_FUNCTION_NAME)
        return response.get("ReservedConcurrentExecutions", -1) == 0
    except ClientError as e:
        # ResourceNotFoundException means no reserved concurrency → not active
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            return False
        logger.warning(f"Failed to check kill switch: {e}")
        return False


def _check_alarm_states() -> dict[str, str]:
    """Get current state of all monitored CloudWatch alarms."""
    states: dict[str, str] = {}
    try:
        client = _get_cloudwatch_client()
        response = client.describe_alarms(AlarmNames=ALARM_NAMES)
        for alarm in response.get("MetricAlarms", []):
            states[alarm["AlarmName"]] = alarm.get("StateValue", "UNKNOWN")
        # Fill in any alarms not found
        for name in ALARM_NAMES:
            if name not in states:
                states[name] = "NOT_FOUND"
    except ClientError as e:
        logger.warning(f"Failed to check alarms: {e}")
        for name in ALARM_NAMES:
            states[name] = "ERROR"
    return states


def _check_budget() -> dict[str, Any]:
    """Get current budget status (spend vs limit)."""
    try:
        client = _get_budgets_client()
        response = client.describe_budget(
            AccountId=ACCOUNT_ID,
            BudgetName=BUDGET_NAME,
        )
        budget = response.get("Budget", {})
        limit_amount = float(budget.get("BudgetLimit", {}).get("Amount", "0"))
        actual = float(
            budget.get("CalculatedSpend", {})
            .get("ActualSpend", {})
            .get("Amount", "0")
        )
        forecasted = float(
            budget.get("CalculatedSpend", {})
            .get("ForecastedSpend", {})
            .get("Amount", "0")
        )
        percent_used = round(actual / limit_amount * 100, 1) if limit_amount > 0 else 0

        return {
            "limit": limit_amount,
            "actual": round(actual, 2),
            "forecasted": round(forecasted, 2),
            "percent_used": percent_used,
        }
    except ClientError as e:
        logger.warning(f"Failed to check budget: {e}")
        return {"limit": 0, "actual": 0, "forecasted": 0, "percent_used": 0}


# ---- Cache helpers ----

def _get_cached_status() -> dict[str, Any] | None:
    """Return cached status if within TTL."""
    global _cached_status, _cache_timestamp
    if _cached_status is None:
        return None
    if time.time() - _cache_timestamp > _CACHE_TTL_SECONDS:
        _cached_status = None
        return None
    return dict(_cached_status)


def _set_cached_status(status: dict[str, Any]) -> None:
    """Cache status in Lambda memory with timestamp."""
    global _cached_status, _cache_timestamp
    _cached_status = dict(status)
    _cache_timestamp = time.time()


def clear_cache() -> None:
    """Clear the status cache (for testing)."""
    global _cached_status, _cache_timestamp
    _cached_status = None
    _cache_timestamp = 0.0


def _build_response(status_code: int, body: dict) -> dict:
    """Build Lambda response with CORS headers for Hermes dashboard."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": HERMES_ORIGIN,
        },
        "body": json.dumps(body),
    }
