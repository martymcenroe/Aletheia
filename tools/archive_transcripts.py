#!/usr/bin/env python3
"""
Archive verbatim session transcripts older than 7 days.

Moves *.jsonl files from the active transcript directory to archive/YYYY-MM/
based on modification time. Subagent files (agent-*.jsonl) are skipped.

Usage:
    poetry run python tools/archive_transcripts.py [--dry-run]

Options:
    --dry-run    Show what would be archived without moving files
"""

import argparse
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import TypedDict


class ArchiveResult(TypedDict):
    """Result of archive operation."""

    archived_count: int
    skipped_count: int
    active_count: int
    errors: list[str]


# Claude Code stores transcripts here (Windows path with Unix-style separators)
TRANSCRIPT_DIR = Path.home() / ".claude/projects/C--Users-mcwiz-Projects-Aletheia"
ARCHIVE_DIR = TRANSCRIPT_DIR / "archive"
RETENTION_DAYS = 7


def get_file_age_days(filepath: Path) -> float:
    """Return age of file in days based on modification time."""
    mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
    age = datetime.now() - mtime
    return age.total_seconds() / 86400  # Convert to days


def archive_transcripts(dry_run: bool = False) -> ArchiveResult:
    """
    Archive transcripts older than RETENTION_DAYS.

    Returns:
        dict with keys: archived_count, skipped_count, active_count, errors
    """
    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)

    result: ArchiveResult = {
        "archived_count": 0,
        "skipped_count": 0,
        "active_count": 0,
        "errors": [],
    }

    if not TRANSCRIPT_DIR.exists():
        print(f"ERROR: Transcript directory not found: {TRANSCRIPT_DIR}")
        result["errors"].append(f"Directory not found: {TRANSCRIPT_DIR}")
        return result

    for jsonl in TRANSCRIPT_DIR.glob("*.jsonl"):
        # Skip subagent files
        if jsonl.name.startswith("agent-"):
            result["skipped_count"] += 1
            continue

        try:
            mtime = datetime.fromtimestamp(jsonl.stat().st_mtime)
            age_days = get_file_age_days(jsonl)

            if mtime < cutoff:
                # File is old, archive it
                month_str = mtime.strftime("%Y-%m")
                month_dir = ARCHIVE_DIR / month_str

                if dry_run:
                    print(f"[DRY-RUN] Would archive: {jsonl.name} -> archive/{month_str}/ ({age_days:.1f} days old)")
                else:
                    month_dir.mkdir(parents=True, exist_ok=True)
                    dest = month_dir / jsonl.name
                    shutil.move(str(jsonl), str(dest))
                    print(f"Archived: {jsonl.name} -> archive/{month_str}/")

                result["archived_count"] += 1
            else:
                # File is recent, keep it active
                result["active_count"] += 1

        except Exception as e:
            error_msg = f"Error processing {jsonl.name}: {e}"
            print(f"ERROR: {error_msg}")
            result["errors"].append(error_msg)

    return result


def print_summary(result: ArchiveResult, dry_run: bool = False) -> None:
    """Print summary of archival operation."""
    prefix = "[DRY-RUN] " if dry_run else ""
    print()
    print(f"{prefix}=== Archive Summary ===")
    print(f"{prefix}Archived: {result['archived_count']} transcripts")
    print(f"{prefix}Active (< {RETENTION_DAYS} days): {result['active_count']} transcripts")
    print(f"{prefix}Skipped (agent-*): {result['skipped_count']} files")

    if result["errors"]:
        print(f"{prefix}Errors: {len(result['errors'])}")
        for error in result["errors"]:
            print(f"  - {error}")

    if not dry_run:
        # Count total files in archive
        if ARCHIVE_DIR.exists():
            archived_total = sum(1 for _ in ARCHIVE_DIR.glob("**/*.jsonl"))
            print(f"Total in archive: {archived_total} transcripts")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Archive verbatim session transcripts older than 7 days."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be archived without moving files"
    )
    args = parser.parse_args()

    print(f"Transcript directory: {TRANSCRIPT_DIR}")
    print(f"Archive directory: {ARCHIVE_DIR}")
    print(f"Retention: {RETENTION_DAYS} days")
    print()

    result = archive_transcripts(dry_run=args.dry_run)
    print_summary(result, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
