"""Admin CLI for resolving anonymized user IDs.

Issue #376: Admin ID Resolution CLI.

The CloudWatch Usage Dashboard (#369) logs anonymized user hashes for privacy.
This tool lets admins map between real user IDs and their anonymized hashes.

Usage:
    poetry run python tools/admin_id_resolve.py forward USER_ID
    poetry run python tools/admin_id_resolve.py reverse HASH --confirm
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import boto3
from botocore.exceptions import ClientError

from src.auth.anonymize import anonymize_user_id

USERS_TABLE = os.environ.get("USERS_TABLE", "aletheia-users")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")


def get_dynamodb_client():
    """Get DynamoDB client."""
    endpoint = os.environ.get("DYNAMODB_ENDPOINT")
    if endpoint:
        return boto3.client("dynamodb", endpoint_url=endpoint, region_name=AWS_REGION)
    return boto3.client("dynamodb", region_name=AWS_REGION)


def forward_resolve(user_id: str) -> dict:
    """Hash a known user_id to its anonymized form.

    Args:
        user_id: The raw user ID (e.g., LinkedIn sub claim).

    Returns:
        Dict with user_id and its anonymized hash.
    """
    return {
        "user_id": user_id,
        "anonymized_hash": anonymize_user_id(user_id),
    }


def reverse_resolve(target_hash: str, dry_run: bool = True) -> dict:
    """Scan users table and find which user_id maps to a given hash.

    This is a brute-force scan that hashes every user_id in the table
    and compares against the target. Requires --confirm flag because
    it reveals PII (the real user_id behind an anonymized hash).

    Args:
        target_hash: The 12-character anonymized hash to resolve.
        dry_run: If True, refuse to reveal PII (require --confirm).

    Returns:
        Dict with match result or dry_run notice.
    """
    if dry_run:
        return {
            "status": "dry_run",
            "message": "Reverse lookup reveals PII. Use --confirm to proceed.",
            "target_hash": target_hash,
        }

    client = get_dynamodb_client()

    try:
        paginator = client.get_paginator("scan")
        page_iterator = paginator.paginate(
            TableName=USERS_TABLE,
            ProjectionExpression="user_id",
        )

        scanned = 0
        for page in page_iterator:
            for item in page.get("Items", []):
                uid = item.get("user_id", {}).get("S", "")
                scanned += 1
                if anonymize_user_id(uid) == target_hash:
                    return {
                        "status": "found",
                        "user_id": uid,
                        "anonymized_hash": target_hash,
                        "users_scanned": scanned,
                    }

        return {
            "status": "not_found",
            "target_hash": target_hash,
            "users_scanned": scanned,
        }

    except ClientError as e:
        return {"status": "error", "message": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Aletheia Admin ID Resolution CLI"
    )
    subparsers = parser.add_subparsers(dest="command")

    # Forward resolve
    fwd = subparsers.add_parser(
        "forward", help="Hash a user_id to its anonymized form"
    )
    fwd.add_argument("user_id", help="The raw user ID to hash")

    # Reverse resolve
    rev = subparsers.add_parser(
        "reverse", help="Find which user_id maps to an anonymized hash"
    )
    rev.add_argument("hash", help="The 12-character anonymized hash to resolve")
    rev.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm PII reveal (required for reverse lookup)",
    )

    args = parser.parse_args()

    if args.command == "forward":
        result = forward_resolve(args.user_id)
        print(json.dumps(result, indent=2))

    elif args.command == "reverse":
        result = reverse_resolve(args.hash, dry_run=not args.confirm)
        print(json.dumps(result, indent=2))

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
