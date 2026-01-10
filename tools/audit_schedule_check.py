#!/usr/bin/env python3
"""
tools/audit_schedule_check.py - Audit Schedule Compliance Check

Enforces audit schedule from 0800-audit-index.md Section 5:
- Quarterly audits: Block if > 90 days overdue, warn at 67 days (75%)
- Monthly audits: Block if > 30 days overdue, warn at 22 days (75%)
- Weekly audits: Block if > 7 days overdue, warn at 5 days (75%)
- Per PR / On Event: Skip (handled separately)

Run in CI to enforce audit schedules.

Reference: Issue #250
"""

import re
import sys
from datetime import datetime
from pathlib import Path

# Thresholds in days
THRESHOLDS = {
    "quarterly": {"block": 90, "warn": 67},  # 75% of 90
    "monthly": {"block": 30, "warn": 22},    # ~75% of 30
    "weekly": {"block": 7, "warn": 5},        # ~75% of 7
}

# Audit frequency mapping from 0800 Section 5.1
AUDIT_FREQUENCY = {
    # Per PR - skip (CI handles)
    # "0813": "per_pr",

    # Weekly
    "0816": "weekly",

    # Monthly + on change (treat as monthly)
    "0811": "monthly",
    "0817": "monthly",

    # Monthly
    "0815": "monthly",
    "0821": "monthly",

    # Quarterly
    "0809": "quarterly",
    "0810": "quarterly",
    "0812": "quarterly",
    "0814": "quarterly",
    "0818": "quarterly",
    "0819": "quarterly",
    "0820": "quarterly",
    "0822": "quarterly",
    "0825": "quarterly",
    "0827": "quarterly",
    "0898": "quarterly",
    "0899": "quarterly",

    # On Event - skip (0808, 0823, 0824)
}


def get_latest_audit_date(content: str) -> datetime | None:
    """
    Extract the most recent audit date from audit record table.

    Expected format:
    | Date | Auditor | Findings Summary | Issues Created |
    |------|---------|------------------|----------------|
    | 2026-01-10 | Claude Opus 4.5 | PASS: ... | None |
    """
    # Find the Audit Record section
    audit_record_match = re.search(r"## \d+\.\s*Audit Record", content)
    if not audit_record_match:
        return None

    # Get content after "Audit Record" heading
    section_content = content[audit_record_match.end():]

    # Find the table (stop at next section)
    next_section = re.search(r"\n## ", section_content)
    if next_section:
        section_content = section_content[:next_section.start()]

    # Parse table rows for dates
    dates = []
    lines = section_content.strip().split("\n")
    in_table = False

    for line in lines:
        if not line.strip().startswith("|"):
            continue

        # Skip separator line
        if re.match(r"\|\s*-+", line):
            in_table = True
            continue

        if not in_table:
            continue

        # Parse data row
        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c]

        if len(cells) >= 1:
            date_str = cells[0]
            # Parse YYYY-MM-DD format
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
                dates.append(date)
            except ValueError:
                continue

    return max(dates) if dates else None


def check_audit_schedule(audit_num: str, file_path: Path, today: datetime) -> dict:
    """
    Check if an audit is overdue.

    Returns dict with:
    - status: "ok", "warn", "block"
    - days_since: days since last audit
    - threshold: applicable threshold
    - frequency: weekly/monthly/quarterly
    """
    frequency = AUDIT_FREQUENCY.get(audit_num)
    if not frequency:
        return {"status": "skip", "reason": "not scheduled"}

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return {"status": "block", "reason": "cannot read file"}

    last_audit = get_latest_audit_date(content)
    if not last_audit:
        # New audit with no prior execution - warn but don't block
        # Blocking would prevent new audit files from being merged
        return {
            "status": "warn",
            "reason": "new audit - needs initial execution",
            "frequency": frequency,
            "days_since": None,
        }

    days_since = (today - last_audit).days
    thresholds = THRESHOLDS[frequency]

    if days_since > thresholds["block"]:
        return {
            "status": "block",
            "days_since": days_since,
            "threshold": thresholds["block"],
            "frequency": frequency,
            "last_audit": last_audit.strftime("%Y-%m-%d"),
        }
    elif days_since > thresholds["warn"]:
        return {
            "status": "warn",
            "days_since": days_since,
            "threshold": thresholds["block"],
            "frequency": frequency,
            "last_audit": last_audit.strftime("%Y-%m-%d"),
        }
    else:
        return {
            "status": "ok",
            "days_since": days_since,
            "frequency": frequency,
            "last_audit": last_audit.strftime("%Y-%m-%d"),
        }


def main() -> int:
    """Run audit schedule compliance check."""
    print("=== Audit Schedule Compliance Check ===")

    docs_dir = Path("docs")
    if not docs_dir.exists():
        print("  No docs/ directory found, skipping...")
        return 0

    today = datetime.now()
    blocks = []
    warns = []
    oks = []

    for audit_num, frequency in sorted(AUDIT_FREQUENCY.items()):
        # Find the audit file
        pattern = f"{audit_num}-audit-*.md"
        matches = list(docs_dir.glob(pattern))

        if not matches:
            # Try alternate patterns (e.g., 0898 horizon scanning, 0899 meta-audit)
            alt_pattern = f"{audit_num}-*.md"
            matches = list(docs_dir.glob(alt_pattern))

        if not matches:
            blocks.append({
                "audit": audit_num,
                "status": "block",
                "reason": f"audit file not found (pattern: {pattern})",
            })
            continue

        file_path = matches[0]
        result = check_audit_schedule(audit_num, file_path, today)
        result["audit"] = audit_num
        result["file"] = file_path.name

        if result["status"] == "block":
            blocks.append(result)
        elif result["status"] == "warn":
            warns.append(result)
        elif result["status"] == "ok":
            oks.append(result)

    # Print results
    print(f"\n  Today: {today.strftime('%Y-%m-%d')}")
    print(f"  Checked: {len(AUDIT_FREQUENCY)} scheduled audits\n")

    if oks:
        print("  OK:")
        for item in oks:
            print(f"    {item['audit']} ({item['frequency']}): "
                  f"last run {item['last_audit']} ({item['days_since']}d ago)")

    if warns:
        print("\n  WARNING (approaching deadline or needs attention):")
        for item in warns:
            if item.get("days_since") is not None:
                days_left = item["threshold"] - item["days_since"]
                print(f"    {item['audit']} ({item['frequency']}): "
                      f"last run {item['last_audit']} ({item['days_since']}d ago) - "
                      f"{days_left}d until overdue")
            else:
                print(f"    {item['audit']} ({item['frequency']}): "
                      f"{item.get('reason', 'needs attention')}")

    if blocks:
        print("\n  BLOCKED (overdue):")
        for item in blocks:
            days_since_val = item.get("days_since")
            threshold_val = item.get("threshold")
            if isinstance(days_since_val, int) and isinstance(threshold_val, int):
                overdue = days_since_val - threshold_val
                print(f"    {item['audit']} ({item['frequency']}): "
                      f"last run {item['last_audit']} ({days_since_val}d ago) - "
                      f"{overdue}d OVERDUE")
            else:
                print(f"    {item['audit']}: {item.get('reason', 'unknown error')}")

    print()

    if blocks:
        print(f"FAILED: {len(blocks)} audit(s) overdue. Run these audits before merging.")
        print("See 0800-audit-index.md Section 5 for audit schedule requirements.")
        return 1

    if warns:
        print(f"PASSED with {len(warns)} warning(s). Consider running these audits soon.")
    else:
        print("=== AUDIT SCHEDULE CHECK PASSED ===")

    return 0


if __name__ == "__main__":
    sys.exit(main())
