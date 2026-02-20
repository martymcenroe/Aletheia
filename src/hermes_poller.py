"""Hermes State Change Poller Lambda.

Issue #400: Runs on 5-minute EventBridge schedule.
1. Check protection state (deny policy, kill switch, alarms, budget)
2. Read last-known state from DynamoDB
3. Diff current vs previous
4. If changed: publish to SNS
5. Save current state to DynamoDB

Deployed as: AletheiaHermesPoller
Trigger: EventBridge rate(5 minutes)
"""

import json
import logging
import os
import time
from typing import Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuration
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
ACCOUNT_ID = os.environ.get("AWS_ACCOUNT_ID", "383687041805")
STATE_TABLE = os.environ.get("STATE_TABLE", "aletheia-state")
STATE_KEY = "hermes-state"
SNS_TOPIC_ARN = os.environ.get(
    "SNS_TOPIC_ARN",
    f"arn:aws:sns:{AWS_REGION}:{ACCOUNT_ID}:Aletheia-CapDenialAlerts",
)

# Resource names (from runbook 10902)
LAMBDA_ROLE_NAME = "AletheiaLambdaRole"
DENY_POLICY_NAME = "AletheiaDenyBedrock-BudgetBreach"
AGENT_FUNCTION_NAME = "AletheiaAgent"
BUDGET_NAME = "Aletheia-Monthly-10USD"
DASHBOARD_URL = "https://hermes.aletheia.study"

# Lazy clients
_dynamodb = None
_iam = None
_lambda = None
_cloudwatch = None
_budgets = None
_sns = None


def _client(service: str):
    """Get or create a boto3 client for the given service."""
    clients = {"dynamodb": "_dynamodb", "iam": "_iam", "lambda": "_lambda",
               "cloudwatch": "_cloudwatch", "budgets": "_budgets", "sns": "_sns"}
    attr = clients[service]
    val = globals().get(attr)
    if val is None:
        val = boto3.client(service, region_name=AWS_REGION)
        globals()[attr] = val
    return val


def lambda_handler(event: dict, context: Any) -> dict:
    """Entry point for EventBridge scheduled invocation."""
    try:
        current = fetch_current_state()
        previous = load_previous_state()
        changes = diff_states(previous, current)

        if changes:
            logger.info(f"State changes detected: {json.dumps(changes)}")
            publish_alert(changes, current)
        else:
            logger.info("No state changes detected")

        save_current_state(current)

        return {"statusCode": 200, "changes": len(changes)}

    except Exception as e:
        logger.error(f"Hermes poller failed: {type(e).__name__}: {e}")
        return {"statusCode": 500, "error": str(e)}


def fetch_current_state() -> dict[str, Any]:
    """Fetch current protection state from AWS APIs."""
    state: dict[str, Any] = {}

    # Deny policy
    try:
        resp = _client("iam").list_attached_role_policies(RoleName=LAMBDA_ROLE_NAME)
        state["deny_policy_attached"] = any(
            DENY_POLICY_NAME in p.get("PolicyName", "")
            for p in resp.get("AttachedPolicies", [])
        )
    except ClientError:
        state["deny_policy_attached"] = None

    # Kill switch
    try:
        resp = _client("lambda").get_function_concurrency(FunctionName=AGENT_FUNCTION_NAME)
        state["kill_switch_active"] = resp.get("ReservedConcurrentExecutions", -1) == 0
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            state["kill_switch_active"] = False
        else:
            state["kill_switch_active"] = None

    # Budget
    try:
        resp = _client("budgets").describe_budget(
            AccountId=ACCOUNT_ID, BudgetName=BUDGET_NAME
        )
        budget = resp.get("Budget", {})
        limit = float(budget.get("BudgetLimit", {}).get("Amount", "0"))
        actual = float(
            budget.get("CalculatedSpend", {}).get("ActualSpend", {}).get("Amount", "0")
        )
        state["budget_percent"] = round(actual / limit * 100, 1) if limit > 0 else 0
    except ClientError:
        state["budget_percent"] = None

    # Auth enabled (read from Agent Lambda env)
    try:
        resp = _client("lambda").get_function_configuration(FunctionName=AGENT_FUNCTION_NAME)
        env_vars = resp.get("Environment", {}).get("Variables", {})
        state["auth_enabled"] = env_vars.get("AUTH_ENABLED", "false").lower() == "true"
    except ClientError:
        state["auth_enabled"] = None

    state["checked_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return state


def load_previous_state() -> dict[str, Any]:
    """Load last-known state from DynamoDB."""
    try:
        resp = _client("dynamodb").get_item(
            TableName=STATE_TABLE,
            Key={
                "thread_id": {"S": STATE_KEY},
                "checkpoint_id": {"S": "latest"},
            },
        )
        item = resp.get("Item", {})
        state_json = item.get("state", {}).get("S", "{}")
        return json.loads(state_json)
    except (ClientError, json.JSONDecodeError) as e:
        logger.warning(f"No previous state found: {e}")
        return {}


def save_current_state(state: dict[str, Any]) -> None:
    """Save current state to DynamoDB."""
    try:
        _client("dynamodb").put_item(
            TableName=STATE_TABLE,
            Item={
                "thread_id": {"S": STATE_KEY},
                "checkpoint_id": {"S": "latest"},
                "state": {"S": json.dumps(state)},
                "updated_at": {"S": state.get("checked_at", "")},
            },
        )
    except ClientError as e:
        logger.error(f"Failed to save state: {e}")


def diff_states(
    previous: dict[str, Any], current: dict[str, Any]
) -> list[dict[str, Any]]:
    """Compare previous and current states, return list of changes."""
    changes = []
    # Keys to monitor (skip checked_at which always changes)
    monitored_keys = [
        "deny_policy_attached",
        "kill_switch_active",
        "auth_enabled",
        "budget_percent",
    ]

    for key in monitored_keys:
        old_val = previous.get(key)
        new_val = current.get(key)

        # Skip if current value is None (API error)
        if new_val is None:
            continue

        # Skip if no previous state (first run)
        if old_val is None and not previous:
            continue

        if old_val != new_val:
            changes.append({
                "field": key,
                "old": old_val,
                "new": new_val,
            })

    # Special threshold check for budget
    budget_pct = current.get("budget_percent")
    prev_budget = previous.get("budget_percent")
    if budget_pct is not None and prev_budget is not None:
        # Alert on threshold crossings: 40%, 80%, 95%
        for threshold in [40, 80, 95]:
            crossed_up = prev_budget < threshold <= budget_pct
            crossed_down = budget_pct < threshold <= prev_budget
            if crossed_up or crossed_down:
                direction = "above" if crossed_up else "below"
                changes.append({
                    "field": f"budget_threshold_{threshold}",
                    "old": f"{prev_budget}%",
                    "new": f"{budget_pct}% ({direction} {threshold}%)",
                })

    return changes


def publish_alert(changes: list[dict], current_state: dict) -> None:
    """Publish state change alert to SNS."""
    now = current_state.get("checked_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

    lines = [f"Changes at {now}:"]
    for change in changes:
        lines.append(f"- {change['field']}: {change['old']} -> {change['new']}")

    lines.append("")
    lines.append("See runbook 10902 Section 3.")
    lines.append(f"Dashboard: {DASHBOARD_URL}")

    message = "\n".join(lines)

    # Determine severity for subject
    severity = "INFO"
    for change in changes:
        if change["field"] in ("deny_policy_attached", "kill_switch_active"):
            if change["new"] is True:
                severity = "CRITICAL"
                break
        if "budget_threshold_95" in change["field"]:
            severity = "CRITICAL"
            break
        if "budget_threshold_80" in change["field"]:
            severity = "WARNING"

    subject = f"HERMES [{severity}]: Protection State Changed"

    try:
        _client("sns").publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject[:100],  # SNS subject max 100 chars
            Message=message,
        )
        logger.info(f"Alert published: {subject}")
    except ClientError as e:
        logger.error(f"Failed to publish SNS alert: {e}")
