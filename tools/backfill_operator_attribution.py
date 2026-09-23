#!/usr/bin/env python3
"""
Attribute the operator's legacy analysis records to the operator (Issue #870).

The rows in AletheiaAgentState that carry neither `user_id` nor `ttl` predate
TTL and are the operator's own usage. This sets `user_id` on them to the
operator's ID and leaves `ttl` absent, so they are retained forever.

It never deletes anything and never adds a ttl. It only touches rows that have
no `user_id` AND no `ttl`, and each write is conditional on that still being
true when it lands.

The operator ID is read from SSM `/aletheia/operator-user-ids` (never from git;
public repo). Before any write, the keys it will touch are saved to
`data/backfill-870-<timestamp>.json` so the change can be reversed exactly.

Usage:
    poetry run python tools/backfill_operator_attribution.py            # dry run
    poetry run python tools/backfill_operator_attribution.py --apply    # write

Rollback (per saved key):
    aws dynamodb update-item --table-name AletheiaAgentState \\
        --key '{"thread_id":{"S":"..."},"checkpoint_id":{"S":"..."}}' \\
        --update-expression "REMOVE user_id"
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

TABLE_NAME = "AletheiaAgentState"
REGION = "us-east-1"
OPERATOR_IDS_PARAM = "/aletheia/operator-user-ids"
DATA_DIR = Path(__file__).parent.parent / "data"


def parse_operator_ids(raw: str) -> list[str]:
    """Split on comma, pipe or whitespace; order preserved, duplicates dropped."""
    seen: list[str] = []
    for part in re.split(r"[,|\s]+", raw or ""):
        if part and part not in seen:
            seen.append(part)
    return seen


def resolve_operator_id(configured: list[str], requested: str | None) -> str:
    """
    Pick the single ID to attribute to.

    With one configured ID, use it. With several, --user-id must name one of
    them. A requested ID that is not configured is refused, so this script can
    never attribute rows to anyone the Lambda would not also treat as operator.
    """
    if not configured:
        raise ValueError(f"{OPERATOR_IDS_PARAM} is empty")
    if requested is not None:
        if requested not in configured:
            raise ValueError("--user-id is not one of the configured operator IDs")
        return requested
    if len(configured) > 1:
        raise ValueError("several operator IDs configured; pass --user-id")
    return configured[0]


def is_candidate(item: dict) -> bool:
    """Legacy row: no user_id and no ttl (low-level DynamoDB item format)."""
    return "user_id" not in item and "ttl" not in item


def scan_candidates(client) -> tuple[int, list[dict]]:
    """Return (rows scanned, keys of candidate rows). Reads keys only."""
    scanned = 0
    keys: list[dict] = []
    kwargs = {
        "TableName": TABLE_NAME,
        "ProjectionExpression": "thread_id, checkpoint_id, user_id, #t",
        "ExpressionAttributeNames": {"#t": "ttl"},
    }
    while True:
        response = client.scan(**kwargs)
        for item in response.get("Items", []):
            scanned += 1
            if is_candidate(item):
                keys.append({
                    "thread_id": item["thread_id"],
                    "checkpoint_id": item["checkpoint_id"],
                })
        if "LastEvaluatedKey" not in response:
            return scanned, keys
        kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]


def attribute(client, key: dict, operator_id: str) -> bool:
    """Set user_id on one row, only if it still has neither user_id nor ttl."""
    try:
        client.update_item(
            TableName=TABLE_NAME,
            Key=key,
            UpdateExpression="SET user_id = :uid",
            ConditionExpression="attribute_not_exists(user_id) AND attribute_not_exists(#t)",
            ExpressionAttributeNames={"#t": "ttl"},
            ExpressionAttributeValues={":uid": {"S": operator_id}},
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--apply", action="store_true",
                        help="Write the attribution (default: dry run)")
    parser.add_argument("--user-id",
                        help="Which configured operator ID to use, if several")
    args = parser.parse_args()

    ssm = boto3.client("ssm", region_name=REGION)
    try:
        raw = ssm.get_parameter(Name=OPERATOR_IDS_PARAM)["Parameter"]["Value"]
        operator_id = resolve_operator_id(parse_operator_ids(raw), args.user_id)
    except ClientError as e:
        print(f"ERROR: cannot read {OPERATOR_IDS_PARAM}: {e.response['Error']['Code']}")
        return 1
    except ValueError as e:
        print(f"ERROR: {e}")
        return 1

    client = boto3.client("dynamodb", region_name=REGION)
    scanned, keys = scan_candidates(client)
    print(f"Scanned {scanned} rows; {len(keys)} have no user_id and no ttl.")

    if not args.apply:
        print("DRY RUN: nothing written. Re-run with --apply to attribute them.")
        return 0

    if not keys:
        print("Nothing to do.")
        return 0

    DATA_DIR.mkdir(exist_ok=True)
    record = DATA_DIR / f"backfill-870-{int(time.time())}.json"
    record.write_text(json.dumps(keys, indent=2), encoding="utf-8")
    print(f"Keys saved for rollback: {record}")

    written = sum(1 for key in keys if attribute(client, key, operator_id))
    skipped = len(keys) - written
    print(f"Attributed {written} rows; {skipped} changed underneath and were left alone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
