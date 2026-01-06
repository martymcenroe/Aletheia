#!/usr/bin/env python3
"""
Generate Onboard Digest

Creates a compact executive summary (0000b-ONBOARD-DIGEST.md) from:
- 0000a-IMMEDIATE-PLAN.md (current sprint)
- 6000-open-issues.md (issue titles/labels only)
- Latest session log entries (last 3)

This reduces onboarding token cost from ~23K to ~1.5K tokens.

Usage:
    python tools/generate_onboard_digest.py
    python tools/generate_onboard_digest.py --dry-run  # Preview without writing
"""

import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path


def get_current_branch():
    """Get current git branch."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "unknown"


def get_latest_commit():
    """Get latest commit hash (short)."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "unknown"


def get_lambda_status():
    """Check Lambda concurrency status."""
    try:
        result = subprocess.run(
            [
                "aws",
                "lambda",
                "get-function-concurrency",
                "--function-name",
                "aletheia-agent",
            ],
            capture_output=True,
            text=True,
            env={"MSYS_NO_PATHCONV": "1", **dict(__import__("os").environ)},
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            concurrency = data.get("ReservedConcurrentExecutions", None)
            return "OFF" if concurrency == 0 else "ON"
        return "UNKNOWN"
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
        return "UNKNOWN"


def fetch_open_issues_summary():
    """Fetch open issues from GitHub (titles and labels only)."""
    try:
        result = subprocess.run(
            [
                "gh",
                "issue",
                "list",
                "--repo",
                "martymcenroe/Aletheia",
                "--state",
                "open",
                "--limit",
                "100",
                "--json",
                "number,title,labels",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        issues = json.loads(result.stdout)

        # Format as compact list
        lines = []
        for issue in sorted(issues, key=lambda x: x["number"]):
            labels = [lbl["name"] for lbl in issue.get("labels", [])]
            label_str = f" [{', '.join(labels)}]" if labels else ""
            lines.append(f"- #{issue['number']}: {issue['title']}{label_str}")

        return len(issues), "\n".join(lines)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return 0, "(Unable to fetch issues - gh CLI error)"


def get_open_prs_count():
    """Get count of open PRs."""
    try:
        result = subprocess.run(
            [
                "gh",
                "pr",
                "list",
                "--repo",
                "martymcenroe/Aletheia",
                "--state",
                "open",
                "--json",
                "number",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        prs = json.loads(result.stdout)
        return len(prs)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return -1


def extract_current_focus(immediate_plan_path):
    """Extract current sprint focus from IMMEDIATE-PLAN."""
    try:
        content = immediate_plan_path.read_text(encoding="utf-8")

        # Extract status line
        status_match = re.search(r"\*\*Status:\*\*\s*(.+)", content)
        status = status_match.group(1).strip() if status_match else "Unknown"

        # Extract next action
        next_match = re.search(
            r"## Next Action\s*\n\n\*\*([^*]+)\*\*:?\s*(.+?)(?=\n\n|\Z)",
            content,
            re.DOTALL,
        )
        if next_match:
            next_action = f"{next_match.group(1).strip()}: {next_match.group(2).strip()}"
        else:
            next_action = "See 0000a-IMMEDIATE-PLAN.md"

        # Extract current state table
        state_lines = []
        in_state = False
        for line in content.split("\n"):
            if "## Current State" in line:
                in_state = True
                continue
            if in_state and line.startswith("|") and "---" not in line:
                state_lines.append(line)
            if in_state and line.startswith("##") and "Current State" not in line:
                break

        return status, next_action, "\n".join(state_lines[:10])  # Limit to 10 rows
    except (FileNotFoundError, Exception) as e:
        return "Unknown", str(e), ""


def get_recent_session_entries(session_logs_dir, count=3):
    """Get the last N session log entries."""
    try:
        # Find most recent session log
        logs = sorted(session_logs_dir.glob("Week-starting-*.md"), reverse=True)
        if not logs:
            return "(No session logs found)"

        latest_log = logs[0]
        content = latest_log.read_text(encoding="utf-8")

        # Split by session entries (## YYYY-MM-DD pattern)
        entries = re.split(r"(?=^## \d{4}-\d{2}-\d{2})", content, flags=re.MULTILINE)
        entries = [e.strip() for e in entries if e.strip() and e.startswith("## 2")]

        # Get last N entries
        recent = entries[-count:] if len(entries) >= count else entries

        # Condense each entry (keep Summary and State on Exit only)
        condensed = []
        for entry in recent:
            lines = entry.split("\n")
            header = lines[0] if lines else ""

            # Extract summary
            summary_match = re.search(
                r"### Summary\s*\n(.+?)(?=###|\Z)", entry, re.DOTALL
            )
            summary = summary_match.group(1).strip()[:200] if summary_match else ""

            # Extract state on exit
            state_match = re.search(
                r"### State on Exit\s*\n(.+?)(?=###|---|\Z)", entry, re.DOTALL
            )
            state = state_match.group(1).strip() if state_match else ""

            condensed.append(f"{header}\n{summary}...\n\n**Exit:** {state}")

        return "\n\n---\n\n".join(condensed)
    except Exception as e:
        return f"(Error reading session logs: {e})"


def generate_digest():
    """Generate the onboard digest content."""
    docs_dir = Path("docs")
    immediate_plan = docs_dir / "0000a-IMMEDIATE-PLAN.md"
    session_logs = docs_dir / "session-logs"

    # Gather data
    branch = get_current_branch()
    commit = get_latest_commit()
    lambda_status = get_lambda_status()
    status, next_action, state_table = extract_current_focus(immediate_plan)
    issue_count, issues_list = fetch_open_issues_summary()
    open_prs = get_open_prs_count()
    recent_sessions = get_recent_session_entries(session_logs, count=3)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M CT")

    # Generate markdown
    digest = f"""# 0000b - Onboard Digest (Auto-Generated)

**Generated:** {timestamp}
**Branch:** `{branch}` @ `{commit}`
**Lambda:** {lambda_status}
**Open PRs:** {open_prs}
**Open Issues:** {issue_count}

---

## Current Sprint

**Status:** {status}

**Next Action:** {next_action}

### Component State
{state_table}

---

## Open Issues (Titles Only)

{issues_list}

---

## Recent Session Activity

{recent_sessions}

---

## Quick Reference

### Bash Rules (MANDATORY)
- ONE command per Bash call
- Use absolute paths: `/c/Users/mcwiz/Projects/Aletheia/`
- Use `git -C /path` instead of `cd /path && git`
- **BANNED:** `&&`, `|`, `;`

### Forbidden Commands
- `git reset`, `git push --force`, `git clean -fd`
- `pip install` (use `poetry add`)
- `/tmp` (use project-local `tmp/`)

### Key Workflows
- **Code changes:** Create worktree first (`git worktree add`)
- **Before merge:** Create reports, stage files, STOP for review
- **Commit format:** `type: description (ref #ID)`

---

*This digest is auto-generated by `tools/generate_onboard_digest.py`.*
*For full context, run `/onboard --full` or read `docs/0000-GUIDE.md`.*
"""

    return digest


def main():
    parser = argparse.ArgumentParser(description="Generate onboard digest")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print digest without writing to file"
    )
    args = parser.parse_args()

    digest = generate_digest()

    if args.dry_run:
        print(digest)
        print("\n--- DRY RUN - File not written ---")
    else:
        output_path = Path("docs/0000b-ONBOARD-DIGEST.md")
        output_path.write_text(digest, encoding="utf-8")
        print(f"Digest written to {output_path}")

        # Show size comparison
        full_size = 0
        for f in [
            "docs/0000-GUIDE.md",
            "docs/0000a-IMMEDIATE-PLAN.md",
            "docs/6000-open-issues.md",
        ]:
            try:
                full_size += Path(f).stat().st_size
            except FileNotFoundError:
                pass

        digest_size = output_path.stat().st_size
        reduction = (1 - digest_size / full_size) * 100 if full_size else 0

        print("\nSize comparison:")
        print(f"  Full onboard: ~{full_size // 1024}KB (~{full_size // 4} tokens)")
        print(f"  Digest:       ~{digest_size // 1024}KB (~{digest_size // 4} tokens)")
        print(f"  Reduction:    {reduction:.0f}%")


if __name__ == "__main__":
    main()
