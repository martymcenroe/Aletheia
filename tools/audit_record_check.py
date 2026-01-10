#!/usr/bin/env python3
"""
tools/audit_record_check.py - Audit Record Compliance Check

Enforces audit record policies from 0800-audit-index.md:
- Section 8.1: Auditor Identity (no empty/TBD/generic entries)
- Section 8.3: Audit Failure → GitHub Issue (FAIL requires issue reference)

Run as pre-commit hook and in CI.

Reference: Issues #249, #253
"""

import re
import sys
from pathlib import Path

# Forbidden auditor entries per 0800 Section 8.2
FORBIDDEN_AUDITORS = {
    "",
    "tbd",
    "todo",
    "agent",
    "-",
    "n/a",
}


def parse_audit_record_table(content: str) -> list[dict]:
    """
    Extract audit record entries from markdown table.

    Expected format:
    | Date | Auditor | Findings Summary | Issues Created |
    |------|---------|------------------|----------------|
    | 2026-01-10 | Claude Opus 4.5 | PASS: ... | None |
    """
    entries: list[dict[str, str]] = []

    # Find the Audit Record section
    audit_record_match = re.search(r"## \d+\.\s*Audit Record", content)
    if not audit_record_match:
        return entries

    # Get content after "Audit Record" heading
    section_content = content[audit_record_match.end():]

    # Find the table (stop at next section)
    next_section = re.search(r"\n## ", section_content)
    if next_section:
        section_content = section_content[:next_section.start()]

    # Parse table rows (skip header and separator)
    lines = section_content.strip().split("\n")
    in_table = False

    for line in lines:
        if not line.strip().startswith("|"):
            continue

        # Skip separator line
        if re.match(r"\|\s*-+", line):
            in_table = True
            continue

        # Skip header
        if not in_table:
            continue

        # Parse data row: | Date | Auditor | Findings | Issues |
        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c]  # Remove empty strings from split

        if len(cells) >= 4:
            entries.append({
                "date": cells[0],
                "auditor": cells[1],
                "findings": cells[2],
                "issues": cells[3],
            })

    return entries


def check_auditor_identity(entry: dict, file_path: Path) -> list[str]:
    """
    Check Section 8.1 - Auditor Identity requirements.

    Forbidden:
    - Empty auditor field
    - "TBD" or "TODO" as auditor
    - Generic "Agent" without model name
    """
    errors = []
    auditor = entry.get("auditor", "").strip().lower()

    if auditor in FORBIDDEN_AUDITORS:
        errors.append(
            f"{file_path}: Forbidden auditor entry '{entry.get('auditor', '')}' "
            f"on {entry.get('date', 'unknown date')}. "
            "Auditor must be model name + version (e.g., 'Claude Opus 4.5')"
        )

    return errors


def check_failure_issue_link(entry: dict, file_path: Path) -> list[str]:
    """
    Check Section 8.3 - Audit Failure → GitHub Issue requirements.

    FAIL findings must have issue reference (#NNN).
    """
    errors = []
    findings = entry.get("findings", "").strip()
    issues = entry.get("issues", "").strip().lower()

    # Check if findings contain FAIL
    if "FAIL" in findings.upper():
        # Check if issues column has a reference
        if not re.search(r"#\d+", issues) and issues not in ("none", ""):
            pass  # Has text but no issue - might be ok

        # Explicit forbidden patterns
        if issues in ("none", "-", "", "n/a"):
            errors.append(
                f"{file_path}: FAIL finding without issue reference "
                f"on {entry.get('date', 'unknown date')}. "
                f"Findings: '{findings[:50]}...' - Issues: '{issues}'. "
                "FAIL requires GitHub issue per 0800 Section 8.3"
            )
        elif not re.search(r"#\d+", entry.get("issues", "")):
            errors.append(
                f"{file_path}: FAIL finding without issue number "
                f"on {entry.get('date', 'unknown date')}. "
                f"Issues column must contain '#NNN' reference"
            )

    return errors


def check_audit_file(file_path: Path) -> list[str]:
    """Check a single audit file for compliance."""
    errors = []

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"{file_path}: Could not read file: {e}"]

    entries = parse_audit_record_table(content)

    for entry in entries:
        # Skip empty/placeholder rows
        date_value = entry.get("date", "")
        if not date_value or date_value.strip() == "":
            continue

        errors.extend(check_auditor_identity(entry, file_path))
        errors.extend(check_failure_issue_link(entry, file_path))

    return errors


def main() -> int:
    """Run audit record compliance check."""
    print("=== Audit Record Compliance Check ===")

    # Find all 08xx audit files
    docs_dir = Path("docs")
    if not docs_dir.exists():
        print("  No docs/ directory found, skipping...")
        return 0

    audit_files = list(docs_dir.glob("08*-audit-*.md"))

    if not audit_files:
        print("  No audit files found, skipping...")
        return 0

    all_errors = []

    for audit_file in sorted(audit_files):
        errors = check_audit_file(audit_file)
        all_errors.extend(errors)

    if all_errors:
        print(f"\nFAILED: {len(all_errors)} violation(s) found:\n")
        for error in all_errors:
            print(f"  ERROR: {error}")
        print("\nSee 0800-audit-index.md Section 8 for audit record requirements.")
        return 1

    print(f"  Checked {len(audit_files)} audit files - OK")
    print("=== AUDIT RECORD CHECK PASSED ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
