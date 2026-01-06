#!/usr/bin/env python3
"""
DynamoDB Data Hygiene Tool.

Cleans up the Aletheia database by:
1. Normalizing schema to current format (--normalize)
2. Backfilling TTL on historical data (--backfill-ttl)
3. Removing duplicate entries (--deduplicate)
4. Deleting common/boring words, keeping novel ones (--clean-common)

See: docs/1150-dynamodb-data-hygiene.md

Usage:
    # Scan and report statistics (dry run, no changes)
    python tools/data_hygiene.py --scan

    # Normalize schema first (RECOMMENDED before other operations)
    python tools/data_hygiene.py --normalize --dry-run
    python tools/data_hygiene.py --normalize --no-dry-run

    # Backfill TTL on items missing it
    python tools/data_hygiene.py --backfill-ttl --dry-run
    python tools/data_hygiene.py --backfill-ttl --no-dry-run

    # Remove duplicates (same input+url, keep newest)
    python tools/data_hygiene.py --deduplicate --dry-run
    python tools/data_hygiene.py --deduplicate --no-dry-run

    # Delete common words
    python tools/data_hygiene.py --clean-common --dry-run
    python tools/data_hygiene.py --clean-common --no-dry-run

    # Full pipeline: normalize -> backfill -> deduplicate -> clean
    python tools/data_hygiene.py --normalize --backfill-ttl --deduplicate --clean-common --no-dry-run
"""

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

# Configuration
TABLE_NAME = "AletheiaAgentState"
REGION = "us-east-1"
TTL_SECONDS = 2592000  # 30 days

# Paths
SCRIPT_DIR = Path(__file__).parent
COMMON_WORDS_FILE = SCRIPT_DIR / "data" / "common_words.txt"

# Global state
COMMON_WORDS: set[str] = set()


@dataclass
class CleanupStats:
    """Statistics from a cleanup run."""

    total_scanned: int = 0
    missing_ttl: int = 0
    ttl_backfilled: int = 0
    common_words_found: int = 0
    common_words_deleted: int = 0
    novel_words_kept: int = 0
    needs_normalization: int = 0
    normalized: int = 0
    duplicates_found: int = 0
    duplicates_deleted: int = 0
    errors: int = 0


def load_common_words() -> None:
    """Load common words list from file."""
    global COMMON_WORDS

    if not COMMON_WORDS_FILE.exists():
        print(f"ERROR: Common words file not found: {COMMON_WORDS_FILE}")
        sys.exit(1)

    with open(COMMON_WORDS_FILE, encoding="utf-8") as f:
        COMMON_WORDS = {line.strip().lower() for line in f if line.strip()}

    # Add explicit stop words to ensure coverage
    stop_words = {
        "the", "a", "an", "in", "on", "at", "to", "for", "of", "and", "or", "but",
        "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
        "do", "does", "did", "will", "would", "could", "should", "may", "might",
        "must", "shall", "i", "you", "he", "she", "it", "we", "they", "me", "him",
        "her", "us", "them", "my", "your", "his", "its", "our", "their", "this",
        "that", "these", "those", "what", "which", "who", "whom", "test", "hello",
        "hi", "bye", "yes", "no", "ok", "okay",
    }
    COMMON_WORDS = COMMON_WORDS.union(stop_words)
    print(f"Loaded {len(COMMON_WORDS):,} common words")


def is_common_word(word: str) -> bool:
    """Check if word is in common vocabulary."""
    return word.lower().strip() in COMMON_WORDS


def should_delete(word: str) -> bool:
    """
    Determine if a word should be deleted.

    DELETE if:
    - Word length < 3 (fragments like "a", "hi")
    - Word is in common words list (boring)

    KEEP if:
    - Word is NOT in common list (novel/interesting)
    """
    word = word.strip()

    # Delete very short fragments
    if len(word) < 3:
        return True

    # Delete common words
    if is_common_word(word):
        return True

    # Keep everything else (novel words, even typos)
    return False


def get_input_text(item: dict) -> str:
    """Extract the input text from an item, handling schema variations."""
    return item.get("input") or item.get("user_input") or item.get("word") or ""


def needs_schema_normalization(item: dict) -> bool:
    """Check if item needs schema normalization."""
    # Critical: Items with checkpoint_id="raw_capture" need delete/recreate
    if item.get("checkpoint_id") == "raw_capture":
        return True
    # Also flag items using old field names (can be updated in place)
    has_old_input = "user_input" in item or "word" in item
    return has_old_input


def get_dynamodb_table():
    """Get DynamoDB table resource."""
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    return dynamodb.Table(TABLE_NAME)


def scan_all_items() -> list[dict]:
    """Scan all items from DynamoDB table with pagination."""
    table = get_dynamodb_table()
    items = []

    try:
        response = table.scan()
        items.extend(response.get("Items", []))

        # Handle pagination
        while "LastEvaluatedKey" in response:
            response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))
            print(f"  Scanned {len(items):,} items so far...")

    except ClientError as e:
        print(f"ERROR: DynamoDB scan failed: {e.response['Error']['Message']}")
        raise

    return items


def normalize_schema(dry_run: bool = True) -> CleanupStats:
    """
    Normalize items to current schema format.

    Two types of migrations:
    1. Items with checkpoint_id="raw_capture" -> DELETE and RE-CREATE
       (Sort key cannot be updated, must delete/recreate)
    2. Items with old field names (user_input/word) -> UPDATE in place
    """
    stats = CleanupStats()
    table = get_dynamodb_table()
    now = int(time.time())
    ttl_value = now + TTL_SECONDS

    print("=" * 60)
    print("SCHEMA NORMALIZATION")
    print(f"  Table: {TABLE_NAME}")
    print(f"  Dry run: {dry_run}")
    print("  Migrations:")
    print("    - checkpoint_id='raw_capture' -> DELETE + RE-CREATE with timestamp")
    print("    - user_input/word -> input (update in place)")
    print("=" * 60)

    items = scan_all_items()
    stats.total_scanned = len(items)

    print(f"\nScanning {stats.total_scanned:,} items...\n")

    for item in items:
        thread_id = item.get("thread_id")
        checkpoint_id = item.get("checkpoint_id")
        input_text = get_input_text(item)

        if not needs_schema_normalization(item):
            continue

        stats.needs_normalization += 1

        # Case 1: checkpoint_id="raw_capture" -> Must delete and recreate
        if checkpoint_id == "raw_capture":
            new_checkpoint_id = str(int(time.time() * 1000))

            if dry_run:
                print(f'[DRY-RUN] Would normalize: "{input_text}" '
                      f'("raw_capture" -> "{new_checkpoint_id}")')
            else:
                try:
                    # Delete the old item
                    table.delete_item(
                        Key={"thread_id": thread_id, "checkpoint_id": checkpoint_id}
                    )

                    # Create new item with proper schema
                    new_item = {
                        "thread_id": thread_id,
                        "checkpoint_id": new_checkpoint_id,
                        "input": input_text,
                        "url": item.get("url", "N/A"),
                        "title": item.get("title", "N/A"),
                        "ttl": ttl_value,
                    }

                    # Preserve optional fields if they exist
                    if "raw_context" in item:
                        new_item["raw_context"] = item["raw_context"]
                    if "status" in item:
                        new_item["status"] = item["status"]

                    table.put_item(Item=new_item)
                    stats.normalized += 1
                    print(f'[NORMALIZED] "{input_text}" '
                          f'("raw_capture" -> "{new_checkpoint_id}")')

                except ClientError as e:
                    stats.errors += 1
                    print(f'[ERROR] Failed to normalize "{input_text}": {e}')

        # Case 2: Old field names but valid checkpoint_id -> Update in place
        else:
            if dry_run:
                print(f'[DRY-RUN] Would normalize: "{input_text}" (update fields)')
            else:
                try:
                    # Build update expression
                    update_parts = []
                    remove_parts = []
                    attr_names = {}
                    attr_values = {}

                    # Migrate input field if needed
                    if "input" not in item:
                        update_parts.append("#input = :input_val")
                        attr_names["#input"] = "input"
                        attr_values[":input_val"] = input_text

                    if "user_input" in item:
                        remove_parts.append("#user_input")
                        attr_names["#user_input"] = "user_input"

                    if "word" in item:
                        remove_parts.append("#word")
                        attr_names["#word"] = "word"

                    # Remove old timestamp field if present
                    if "timestamp" in item:
                        remove_parts.append("#timestamp")
                        attr_names["#timestamp"] = "timestamp"

                    # Build the full expression
                    expression_parts = []
                    if update_parts:
                        expression_parts.append("SET " + ", ".join(update_parts))
                    if remove_parts:
                        expression_parts.append("REMOVE " + ", ".join(remove_parts))

                    if expression_parts:
                        update_kwargs = {
                            "Key": {"thread_id": thread_id, "checkpoint_id": checkpoint_id},
                            "UpdateExpression": " ".join(expression_parts),
                            "ExpressionAttributeNames": attr_names,
                        }
                        if attr_values:
                            update_kwargs["ExpressionAttributeValues"] = attr_values

                        table.update_item(**update_kwargs)
                        stats.normalized += 1
                        print(f'[NORMALIZED] "{input_text}" (updated fields)')

                except ClientError as e:
                    stats.errors += 1
                    print(f'[ERROR] Failed to normalize "{input_text}": {e}')

    print("\n" + "-" * 60)
    print(f"Total scanned: {stats.total_scanned:,}")
    print(f"Needs normalization: {stats.needs_normalization:,}")
    if not dry_run:
        print(f"Normalized: {stats.normalized:,}")
        print(f"Errors: {stats.errors:,}")

    return stats


def backfill_ttl(dry_run: bool = True) -> CleanupStats:
    """
    Add TTL attribute to items missing it.

    Sets TTL to now + 30 days for all items without a ttl attribute.
    """
    stats = CleanupStats()
    table = get_dynamodb_table()
    ttl_value = int(time.time()) + TTL_SECONDS

    print("=" * 60)
    print("TTL BACKFILL")
    print(f"  Table: {TABLE_NAME}")
    print(f"  TTL value: {ttl_value} (30 days from now)")
    print(f"  Dry run: {dry_run}")
    print("=" * 60)

    items = scan_all_items()
    stats.total_scanned = len(items)

    print(f"\nScanning {stats.total_scanned:,} items...\n")

    for item in items:
        thread_id = item.get("thread_id")
        checkpoint_id = item.get("checkpoint_id")
        input_text = get_input_text(item)

        if "ttl" not in item:
            stats.missing_ttl += 1

            if dry_run:
                print(f'[DRY-RUN] Would backfill TTL: "{input_text}"')
            else:
                try:
                    table.update_item(
                        Key={"thread_id": thread_id, "checkpoint_id": checkpoint_id},
                        UpdateExpression="SET #ttl = :ttl",
                        ExpressionAttributeNames={"#ttl": "ttl"},
                        ExpressionAttributeValues={":ttl": ttl_value},
                    )
                    stats.ttl_backfilled += 1
                    print(f'[UPDATED] Backfilled TTL: "{input_text}"')
                except ClientError as e:
                    stats.errors += 1
                    print(f'[ERROR] Failed to update "{input_text}": {e}')

    print("\n" + "-" * 60)
    print(f"Total scanned: {stats.total_scanned:,}")
    print(f"Missing TTL: {stats.missing_ttl:,}")
    if not dry_run:
        print(f"TTL backfilled: {stats.ttl_backfilled:,}")
        print(f"Errors: {stats.errors:,}")

    return stats


def clean_common_words(dry_run: bool = True) -> CleanupStats:
    """
    Delete items where the input text is a common word.

    Keeps novel/interesting words, deletes boring common ones.
    """
    stats = CleanupStats()
    table = get_dynamodb_table()

    print("=" * 60)
    print("CLEAN COMMON WORDS (Novelty Filter)")
    print(f"  Table: {TABLE_NAME}")
    print(f"  Common words loaded: {len(COMMON_WORDS):,}")
    print(f"  Dry run: {dry_run}")
    print("=" * 60)

    items = scan_all_items()
    stats.total_scanned = len(items)

    print(f"\nScanning {stats.total_scanned:,} items...\n")

    for item in items:
        thread_id = item.get("thread_id")
        checkpoint_id = item.get("checkpoint_id")
        input_text = get_input_text(item)

        if should_delete(input_text):
            stats.common_words_found += 1

            if dry_run:
                print(f'[DRY-RUN] Would delete: "{input_text}"')
            else:
                try:
                    table.delete_item(
                        Key={"thread_id": thread_id, "checkpoint_id": checkpoint_id}
                    )
                    stats.common_words_deleted += 1
                    print(f'[DELETED] "{input_text}"')
                except ClientError as e:
                    stats.errors += 1
                    print(f'[ERROR] Failed to delete "{input_text}": {e}')
        else:
            stats.novel_words_kept += 1

    print("\n" + "-" * 60)
    print(f"Total scanned: {stats.total_scanned:,}")
    print(f"Common words found: {stats.common_words_found:,}")
    print(f"Novel words kept: {stats.novel_words_kept:,}")
    if not dry_run:
        print(f"Deleted: {stats.common_words_deleted:,}")
        print(f"Errors: {stats.errors:,}")

    return stats


def deduplicate(dry_run: bool = True) -> CleanupStats:
    """
    Remove duplicate entries, keeping only the most recent per (input, url).

    Groups items by (input.lower(), url) tuple.
    For each group with >1 item, keeps the one with highest checkpoint_id
    (which is a timestamp in milliseconds) and deletes the rest.
    """
    stats = CleanupStats()
    table = get_dynamodb_table()

    print("=" * 60)
    print("DEDUPLICATE")
    print(f"  Table: {TABLE_NAME}")
    print(f"  Dry run: {dry_run}")
    print("  Logic: Group by (input, url), keep newest, delete rest")
    print("=" * 60)

    items = scan_all_items()
    stats.total_scanned = len(items)

    print(f"\nGrouping {stats.total_scanned:,} items by (input, url)...\n")

    # Group by (input, url)
    groups: dict[tuple[str, str], list[dict]] = {}
    for item in items:
        input_text = get_input_text(item).lower().strip()
        url = item.get("url", "N/A")
        key = (input_text, url)
        if key not in groups:
            groups[key] = []
        groups[key].append(item)

    # Process groups with duplicates
    for (input_text, url), group_items in groups.items():
        if len(group_items) > 1:
            # Count extra copies (total - 1 that we keep)
            extra_copies = len(group_items) - 1
            stats.duplicates_found += extra_copies

            # Sort by checkpoint_id descending (keep newest)
            # Cast to int to avoid lexicographical sorting bugs (e.g., "9" > "10")
            sorted_items = sorted(
                group_items,
                key=lambda x: int(x.get("checkpoint_id", 0)),
                reverse=True,
            )
            delete_items = sorted_items[1:]

            if dry_run:
                print(
                    f"[DRY-RUN] Found duplicate '{input_text}' "
                    f"({len(group_items)} copies). "
                    f"Would delete {len(delete_items)}, keep 1."
                )
            else:
                for item in delete_items:
                    try:
                        table.delete_item(
                            Key={
                                "thread_id": item["thread_id"],
                                "checkpoint_id": item["checkpoint_id"],
                            }
                        )
                        stats.duplicates_deleted += 1
                        print(f"[DELETED] Duplicate '{input_text}'")
                    except ClientError as e:
                        stats.errors += 1
                        print(f"[ERROR] Failed to delete duplicate: {e}")

    print("\n" + "-" * 60)
    print(f"Total scanned: {stats.total_scanned:,}")
    print(f"Unique (input, url) groups: {len(groups):,}")
    print(f"Duplicates found: {stats.duplicates_found:,}")
    if not dry_run:
        print(f"Duplicates deleted: {stats.duplicates_deleted:,}")
        print(f"Errors: {stats.errors:,}")

    return stats


def scan_only() -> CleanupStats:
    """Scan and report statistics without making any changes."""
    stats = CleanupStats()

    print("=" * 60)
    print("SCAN REPORT (Read-Only)")
    print(f"  Table: {TABLE_NAME}")
    print("=" * 60)

    items = scan_all_items()
    stats.total_scanned = len(items)

    print(f"\nAnalyzing {stats.total_scanned:,} items...\n")

    raw_capture_count = 0

    # Group by (input, url) for duplicate detection
    groups: dict[tuple[str, str], list[dict]] = {}

    for item in items:
        input_text = get_input_text(item)

        if "ttl" not in item:
            stats.missing_ttl += 1

        if item.get("checkpoint_id") == "raw_capture":
            raw_capture_count += 1

        if needs_schema_normalization(item):
            stats.needs_normalization += 1

        if should_delete(input_text):
            stats.common_words_found += 1
        else:
            stats.novel_words_kept += 1

        # Track for duplicate detection
        key = (input_text.lower().strip(), item.get("url", "N/A"))
        if key not in groups:
            groups[key] = []
        groups[key].append(item)

    # Count duplicates (extra copies beyond the first)
    for group_items in groups.values():
        if len(group_items) > 1:
            stats.duplicates_found += len(group_items) - 1

    print("-" * 60)
    print(f"Total items: {stats.total_scanned:,}")
    print(f"Needs schema normalization: {stats.needs_normalization:,}")
    print(f"  - checkpoint_id='raw_capture': {raw_capture_count:,}")
    print(f"Missing TTL: {stats.missing_ttl:,}")
    print(f"Duplicates (would delete): {stats.duplicates_found:,}")
    print(f"Common words (would delete): {stats.common_words_found:,}")
    print(f"Novel words (would keep): {stats.novel_words_kept:,}")

    return stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="DynamoDB Data Hygiene Tool for Aletheia",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --scan                      # Report statistics only
  %(prog)s --normalize --dry-run       # Preview schema normalization
  %(prog)s --normalize --no-dry-run    # Actually normalize schema
  %(prog)s --backfill-ttl --dry-run    # Preview TTL backfill
  %(prog)s --deduplicate --dry-run     # Preview duplicate removal
  %(prog)s --clean-common --dry-run    # Preview common word cleanup

Recommended order: --normalize, --backfill-ttl, --deduplicate, --clean-common
        """,
    )

    parser.add_argument(
        "--scan",
        action="store_true",
        help="Scan and report statistics (no changes)",
    )
    parser.add_argument(
        "--normalize",
        action="store_true",
        help="Normalize schema (fix 'raw_capture' items, migrate old fields)",
    )
    parser.add_argument(
        "--backfill-ttl",
        action="store_true",
        help="Add TTL (30 days) to items missing it",
    )
    parser.add_argument(
        "--clean-common",
        action="store_true",
        help="Delete items with common/boring words",
    )
    parser.add_argument(
        "--deduplicate",
        action="store_true",
        help="Remove duplicate (input, url) entries, keeping the newest",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Preview changes without modifying data (default: True)",
    )
    parser.add_argument(
        "--no-dry-run",
        action="store_true",
        help="Actually make changes (DANGER: modifies/deletes data)",
    )

    args = parser.parse_args()

    # Determine dry_run mode
    dry_run = not args.no_dry_run

    # Must specify at least one action
    if not any([args.scan, args.normalize, args.backfill_ttl, args.deduplicate, args.clean_common]):
        parser.print_help()
        sys.exit(1)

    # Load common words if needed
    if args.clean_common or args.scan:
        load_common_words()

    # Execute requested actions in recommended order
    if args.scan:
        scan_only()

    if args.normalize:
        normalize_schema(dry_run=dry_run)

    if args.backfill_ttl:
        backfill_ttl(dry_run=dry_run)

    if args.deduplicate:
        deduplicate(dry_run=dry_run)

    if args.clean_common:
        clean_common_words(dry_run=dry_run)

    # Summary
    if dry_run and (args.normalize or args.backfill_ttl or args.deduplicate or args.clean_common):
        print("")
        print("=" * 60)
        print("DRY RUN COMPLETE - No changes were made.")
        print("To apply changes, run with --no-dry-run")
        print("=" * 60)


if __name__ == "__main__":
    main()
