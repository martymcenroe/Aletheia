"""Admin CLI for coupon management.

Issue #367: Manual Subscriptions with Coupons.

Usage:
    poetry run python tools/admin_coupons.py generate --tier subscriber --count 10 --expires-days 30
    poetry run python tools/admin_coupons.py list [--status active|all]
    poetry run python tools/admin_coupons.py revoke --code ABCD1234EFGH5678
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import string
import sys
import time
from typing import Any

import boto3
from botocore.exceptions import ClientError

# Safety limit
MAX_BATCH_SIZE = 1000

# Table and region
COUPONS_TABLE = os.environ.get("COUPONS_TABLE", "aletheia-coupons")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# Character set for code generation (uppercase + digits, no ambiguous chars)
_CODE_CHARS = string.ascii_uppercase + string.digits


def get_dynamodb_client():
    """Get DynamoDB client."""
    endpoint = os.environ.get("DYNAMODB_ENDPOINT")
    if endpoint:
        return boto3.client("dynamodb", endpoint_url=endpoint, region_name=AWS_REGION)
    return boto3.client("dynamodb", region_name=AWS_REGION)


def generate_coupon_code() -> str:
    """Generate a single 16-character uppercase alphanumeric coupon code."""
    return "".join(secrets.choice(_CODE_CHARS) for _ in range(16))


def generate_coupons(
    tier: str,
    count: int,
    expires_days: int,
    max_uses: int = 1,
    created_by: str = "admin-cli",
) -> list[str]:
    """Generate and store coupon codes in DynamoDB.

    Args:
        tier: Target subscription tier.
        count: Number of codes to generate.
        expires_days: Days until expiry (0 = no expiry).
        max_uses: Maximum redemptions per code.
        created_by: Admin identifier for audit trail.

    Returns:
        List of generated coupon codes.

    Raises:
        ValueError: If count exceeds MAX_BATCH_SIZE.
    """
    if count > MAX_BATCH_SIZE:
        raise ValueError(f"Batch size {count} exceeds maximum {MAX_BATCH_SIZE}")
    if count <= 0:
        raise ValueError("Count must be positive")

    client = get_dynamodb_client()
    now = int(time.time())
    expiry = now + (expires_days * 86400) if expires_days > 0 else 0
    codes: list[str] = []

    for _ in range(count):
        code = generate_coupon_code()
        item: dict[str, Any] = {
            "code": {"S": code},
            "tier": {"S": tier},
            "expiry": {"N": str(expiry)},
            "max_uses": {"N": str(max_uses)},
            "uses": {"N": "0"},
            "created_by": {"S": created_by},
            "created_at": {"N": str(now)},
            "revoked": {"BOOL": False},
        }

        try:
            client.put_item(TableName=COUPONS_TABLE, Item=item)
            codes.append(code)
        except ClientError as e:
            print(f"ERROR: Failed to create coupon: {e}", file=sys.stderr)

    return codes


def list_coupons(status: str = "active") -> list[dict]:
    """List coupons from DynamoDB.

    Args:
        status: "active" (excludes expired/revoked) or "all".

    Returns:
        List of coupon dicts.
    """
    client = get_dynamodb_client()
    result = client.scan(TableName=COUPONS_TABLE)
    items = result.get("Items", [])

    coupons = []
    now = int(time.time())

    for item in items:
        coupon = {
            "code": item.get("code", {}).get("S", ""),
            "tier": item.get("tier", {}).get("S", ""),
            "expiry": int(item.get("expiry", {}).get("N", "0")),
            "max_uses": int(item.get("max_uses", {}).get("N", "1")),
            "uses": int(item.get("uses", {}).get("N", "0")),
            "revoked": item.get("revoked", {}).get("BOOL", False),
            "created_by": item.get("created_by", {}).get("S", ""),
        }

        if status == "active":
            if coupon["revoked"]:
                continue
            if coupon["expiry"] > 0 and coupon["expiry"] < now:
                continue
            if coupon["uses"] >= coupon["max_uses"]:
                continue

        coupons.append(coupon)

    return coupons


def revoke_coupon(code: str) -> bool:
    """Revoke a coupon code.

    Args:
        code: The coupon code to revoke.

    Returns:
        True if revoked, False if not found or already revoked.
    """
    client = get_dynamodb_client()
    code = code.strip().upper()

    try:
        client.update_item(
            TableName=COUPONS_TABLE,
            Key={"code": {"S": code}},
            UpdateExpression="SET revoked = :true",
            ExpressionAttributeValues={":true": {"BOOL": True}},
            ConditionExpression="attribute_exists(code)",
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise


def main():
    parser = argparse.ArgumentParser(description="Aletheia Coupon Admin CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Generate
    gen = subparsers.add_parser("generate", help="Generate coupon codes")
    gen.add_argument("--tier", required=True, help="Target tier (subscriber/premium)")
    gen.add_argument("--count", type=int, default=1, help="Number of codes")
    gen.add_argument("--expires-days", type=int, default=30, help="Days until expiry (0=never)")
    gen.add_argument("--max-uses", type=int, default=1, help="Max redemptions per code")

    # List
    lst = subparsers.add_parser("list", help="List coupon codes")
    lst.add_argument("--status", choices=["active", "all"], default="active")

    # Revoke
    rev = subparsers.add_parser("revoke", help="Revoke a coupon code")
    rev.add_argument("--code", required=True, help="Code to revoke")

    args = parser.parse_args()

    if args.command == "generate":
        codes = generate_coupons(
            tier=args.tier,
            count=args.count,
            expires_days=args.expires_days,
            max_uses=args.max_uses,
        )
        print(f"Generated {len(codes)} coupon(s):")
        for code in codes:
            print(f"  {code}")

    elif args.command == "list":
        coupons = list_coupons(status=args.status)
        print(json.dumps(coupons, indent=2))

    elif args.command == "revoke":
        if revoke_coupon(args.code):
            print(f"Revoked: {args.code.upper()}")
        else:
            print(f"Not found or already revoked: {args.code.upper()}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
