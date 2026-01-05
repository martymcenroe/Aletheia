#!/usr/bin/env python3
"""
Append Session Log Entry

Appends a new session log entry to the correct week file without reading
the entire file. Solves the token limit problem for large session logs.

Usage:
    poetry run python tools/append_session_log.py --model "Claude Opus 4.5" --summary "Did stuff" --commit abc1234
    poetry run python tools/append_session_log.py --template  # Just append template for manual fill-in

The script determines the correct week file based on the current date.
Week boundary: Monday 3:00 AM CT to following Monday 2:59 AM CT.
"""

import argparse
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


# Configuration
SESSION_LOGS_DIR = Path("docs/session-logs")
CT_TIMEZONE = ZoneInfo("America/Chicago")


def get_week_start_date() -> datetime:
    """
    Get the Monday that starts the current week.

    Week boundary: Monday 3:00 AM CT to following Monday 2:59 AM CT.
    """
    now = datetime.now(CT_TIMEZONE)

    # Find the most recent Monday
    days_since_monday = now.weekday()  # Monday = 0
    monday = now - timedelta(days=days_since_monday)

    # If it's Monday but before 3:00 AM, use previous Monday
    if days_since_monday == 0 and now.hour < 3:
        monday = monday - timedelta(days=7)

    # Return just the date portion
    return monday.replace(hour=0, minute=0, second=0, microsecond=0)


def get_week_filename() -> str:
    """Get the filename for the current week's session log."""
    monday = get_week_start_date()
    return f"Week-starting-{monday.strftime('%Y-%m-%d')}.md"


def get_current_timestamp() -> str:
    """Get current timestamp in CT."""
    now = datetime.now(CT_TIMEZONE)
    return now.strftime("%Y-%m-%d %H:%M")


def get_current_commit() -> str:
    """Get the current HEAD commit SHA (short form)."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "<unknown>"


def get_current_branch() -> str:
    """Get the current git branch name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "<unknown>"


def format_entry(
    model: str,
    summary: str | None = None,
    issues_created: str | None = None,
    issues_closed: str | None = None,
    commit: str | None = None,
    next_action: str | None = None,
    template_only: bool = False,
) -> str:
    """Format a session log entry."""
    timestamp = get_current_timestamp()
    branch = get_current_branch()
    commit_sha = commit or get_current_commit()

    if template_only:
        # Return template with placeholders
        return f"""
---

## {timestamp} CT | {model}

### Summary
[One paragraph describing the session's main accomplishment]

### Issues
- Created: [#XX, #YY or None]
- Closed: [#ZZ or None]

### State on Exit
- Branch: {branch} @ {commit_sha}
- Open PRs: [count]
- Next: [What the next session should pick up]
"""
    else:
        # Return filled-in entry
        created = issues_created or "None"
        closed = issues_closed or "None"
        next_step = next_action or "Per user direction"

        return f"""
---

## {timestamp} CT | {model}

### Summary
{summary}

### Issues
- Created: {created}
- Closed: {closed}

### State on Exit
- Branch: {branch} @ {commit_sha}
- Open PRs: 0
- Next: {next_step}
"""


def ensure_week_file_exists(filepath: Path) -> None:
    """Create week file with header if it doesn't exist."""
    if not filepath.exists():
        monday = get_week_start_date()
        # Calculate the Sunday that ends the week
        sunday = monday + timedelta(days=6)

        header = f"""# Session Log: Week of {monday.strftime('%Y-%m-%d')}

**Week:** {monday.strftime('%Y-%m-%d')} (Mon) to {sunday.strftime('%Y-%m-%d')} (Sun)

---
"""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(header, encoding="utf-8")
        print(f"Created new week file: {filepath}")


def append_entry(entry: str) -> Path:
    """Append entry to the current week's session log."""
    filename = get_week_filename()
    filepath = SESSION_LOGS_DIR / filename

    ensure_week_file_exists(filepath)

    # Append the entry
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(entry)

    return filepath


def main():
    parser = argparse.ArgumentParser(
        description="Append a session log entry to the current week's file"
    )
    parser.add_argument(
        "--model",
        default="Claude Opus 4.5",
        help="Model name (default: Claude Opus 4.5)",
    )
    parser.add_argument(
        "--summary",
        help="One paragraph summary of the session",
    )
    parser.add_argument(
        "--created",
        help="Issues created (e.g., '#123, #124' or 'None')",
    )
    parser.add_argument(
        "--closed",
        help="Issues closed (e.g., '#125' or 'None')",
    )
    parser.add_argument(
        "--commit",
        help="Commit SHA (auto-detected if not provided)",
    )
    parser.add_argument(
        "--next",
        dest="next_action",
        help="What the next session should pick up",
    )
    parser.add_argument(
        "--template",
        action="store_true",
        help="Append a template with placeholders for manual fill-in",
    )

    args = parser.parse_args()

    # Validate: either --template or --summary required
    if not args.template and not args.summary:
        print("Error: Either --template or --summary is required", file=sys.stderr)
        print("  Use --template for a placeholder template", file=sys.stderr)
        print("  Use --summary 'text' for a filled-in entry", file=sys.stderr)
        sys.exit(1)

    entry = format_entry(
        model=args.model,
        summary=args.summary,
        issues_created=args.created,
        issues_closed=args.closed,
        commit=args.commit,
        next_action=args.next_action,
        template_only=args.template,
    )

    filepath = append_entry(entry)

    print(f"Appended session log entry to: {filepath}")
    print(f"Timestamp: {get_current_timestamp()} CT")
    if args.template:
        print("Note: Template appended - edit file to fill in placeholders")


if __name__ == "__main__":
    main()
