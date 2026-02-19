"""Admin CLI for subscription management.

Issue #366: Full Billing with Stripe.

Usage:
    poetry run python tools/admin_subscriptions.py view --user-id USER_ID
    poetry run python tools/admin_subscriptions.py list-grace
    poetry run python tools/admin_subscriptions.py adjust --user-id USER_ID --tier premium [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any

import boto3
from botocore.exceptions import ClientError

USERS_TABLE = os.environ.get("USERS_TABLE", "aletheia-users")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")


def get_dynamodb_client():
    """Get DynamoDB client."""
    endpoint = os.environ.get("DYNAMODB_ENDPOINT")
    if endpoint:
        return boto3.client("dynamodb", endpoint_url=endpoint, region_name=AWS_REGION)
    return boto3.client("dynamodb", region_name=AWS_REGION)


def view_subscription(user_id: str) -> dict[str, Any]:
    """View subscription details for a user.

    Args:
        user_id: The user's unique identifier.

    Returns:
        Dict with subscription details.
    """
    client = get_dynamodb_client()

    try:
        result = client.get_item(
            TableName=USERS_TABLE,
            Key={"user_id": {"S": user_id}},
        )
    except ClientError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return {}

    item = result.get("Item")
    if item is None:
        return {"error": "User not found"}

    info: dict[str, Any] = {
        "user_id": item.get("user_id", {}).get("S", ""),
        "tier": item.get("tier", {}).get("S", "free"),
        "stripe_customer_id": item.get("stripe_customer_id", {}).get("S"),
        "stripe_subscription_id": item.get("stripe_subscription_id", {}).get("S"),
    }

    grace_end = int(item.get("grace_period_end", {}).get("N", "0"))
    if grace_end > 0:
        now = int(time.time())
        if grace_end > now:
            info["grace_period"] = {
                "active": True,
                "ends_at": grace_end,
                "days_remaining": max(1, (grace_end - now) // 86400),
            }
        else:
            info["grace_period"] = {"active": False, "expired": True}

    return info


def list_grace_period_users() -> list[dict]:
    """List all users currently in grace period.

    Returns:
        List of user dicts with grace period info.
    """
    client = get_dynamodb_client()
    now = int(time.time())

    try:
        result = client.scan(
            TableName=USERS_TABLE,
            FilterExpression="attribute_exists(grace_period_end) AND grace_period_end > :now",
            ExpressionAttributeValues={":now": {"N": str(now)}},
            ProjectionExpression="user_id, tier, grace_period_end",
        )
    except ClientError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return []

    users = []
    for item in result.get("Items", []):
        grace_end = int(item.get("grace_period_end", {}).get("N", "0"))
        users.append({
            "user_id": item.get("user_id", {}).get("S", ""),
            "tier": item.get("tier", {}).get("S", "free"),
            "grace_period_days_remaining": max(1, (grace_end - now) // 86400),
        })

    return users


def adjust_tier(user_id: str, new_tier: str, dry_run: bool = True) -> dict:
    """Adjust user tier manually.

    Args:
        user_id: The user's unique identifier.
        new_tier: New tier value ("free" or "premium").
        dry_run: If True, only show what would change.

    Returns:
        Dict with operation result.
    """
    if new_tier not in ("free", "premium"):
        return {"error": f"Invalid tier: {new_tier}. Must be 'free' or 'premium'"}

    client = get_dynamodb_client()

    # Get current state
    try:
        result = client.get_item(
            TableName=USERS_TABLE,
            Key={"user_id": {"S": user_id}},
            ProjectionExpression="tier",
        )
    except ClientError as e:
        return {"error": str(e)}

    item = result.get("Item")
    if item is None:
        return {"error": "User not found"}

    current_tier = item.get("tier", {}).get("S", "free")

    if current_tier == new_tier:
        return {"status": "no_change", "tier": current_tier}

    if dry_run:
        return {
            "status": "dry_run",
            "current_tier": current_tier,
            "new_tier": new_tier,
            "would_change": True,
        }

    # Apply change
    try:
        client.update_item(
            TableName=USERS_TABLE,
            Key={"user_id": {"S": user_id}},
            UpdateExpression="SET tier = :tier",
            ExpressionAttributeValues={":tier": {"S": new_tier}},
        )
    except ClientError as e:
        return {"error": str(e)}

    return {
        "status": "applied",
        "previous_tier": current_tier,
        "new_tier": new_tier,
    }


def main():
    parser = argparse.ArgumentParser(description="Aletheia Subscription Admin CLI")
    subparsers = parser.add_subparsers(dest="command")

    # View
    view = subparsers.add_parser("view", help="View user subscription")
    view.add_argument("--user-id", required=True, help="User ID to look up")

    # List grace period
    subparsers.add_parser("list-grace", help="List users in grace period")

    # Adjust
    adj = subparsers.add_parser("adjust", help="Adjust user tier")
    adj.add_argument("--user-id", required=True, help="User ID to adjust")
    adj.add_argument("--tier", required=True, choices=["free", "premium"])
    adj.add_argument("--dry-run", action="store_true", default=True,
                     help="Preview changes without applying (default)")
    adj.add_argument("--apply", action="store_true",
                     help="Actually apply the change")

    args = parser.parse_args()

    if args.command == "view":
        result = view_subscription(args.user_id)
        print(json.dumps(result, indent=2))

    elif args.command == "list-grace":
        users = list_grace_period_users()
        if users:
            print(json.dumps(users, indent=2))
        else:
            print("No users in grace period.")

    elif args.command == "adjust":
        dry_run = not args.apply
        result = adjust_tier(args.user_id, args.tier, dry_run=dry_run)
        print(json.dumps(result, indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
