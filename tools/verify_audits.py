#!/usr/bin/env python3
"""
verify_audits.py - Verify audit execution claims against audit records.

Issue #248: CI job to verify audit execution claims.
LLD: docs/lld/active/1248-ci-audit-verification.md

This script scans session logs for audit claims and cross-references them
against actual audit record updates in 08xx-audit-*.md files.

Exit codes:
    0 - All claims verified (or dry-run mode)
    1 - Unverified claims found
    2 - Error during execution
"""

import argparse
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import TypedDict


class AuditClaim(TypedDict):
    """Audit claim extracted from session log."""

    session_date: str  # From session header (YYYY-MM-DD HH:MM)
    audit_id: str  # e.g., "0809", "0825"
    agent: str  # e.g., "Claude Opus 4.5"
    session_file: str  # Source file path
    raw_text: str  # Original claim text
    claimed_status: str | None  # "PASS", "FAIL", or None


class AuditRecord(TypedDict):
    """Audit record from 08xx-audit-*.md file."""

    date: str  # ISO 8601 date
    auditor: str  # e.g., "Claude Opus 4.5"
    findings: str  # PASS/FAIL summary
    status: str  # Extracted "PASS" or "FAIL"
    audit_file: str  # Source audit file


class VerificationResult(TypedDict):
    """Result of verifying a claim against records."""

    claim: AuditClaim
    record: AuditRecord | None
    status: str  # "VERIFIED", "UNVERIFIED", "MISMATCH"
    reason: str  # Human-readable explanation


# Regex patterns per LLD
SESSION_HEADER_PATTERN = re.compile(
    r"^## (\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) CT \| (.+)$", re.MULTILINE
)

# Audit ID pattern - restricted to 08xx range per Gemini G1.HIGH
# Matches: "ran 0809", "audit 0809", "executed 0810"
AUDIT_CLAIM_PATTERN = re.compile(
    r"(?:ran|executed|completed|audit)\s*(?:the\s+)?0?8(\d{2}).*?(PASS|FAIL|pass|fail)?",
    re.IGNORECASE,
)

# Alternative pattern for "0809 Security - PASS" style
AUDIT_RESULT_PATTERN = re.compile(
    r"08(\d{2})\s+(?:Security|Privacy|Performance|Accessibility|Code Quality|"
    r"License|Wiki|Dependabot|Agentic|Safety|Bias|Incident|Supply Chain|"
    r"Explainability|Management|Infrastructure|Browser|Permission|Meta|Horizon)"
    r".*?(PASS|FAIL|pass|fail)",
    re.IGNORECASE,
)

# Pattern for "Tier 1 audit (0809/0810) passed" or "audit (0809) PASS"
AUDIT_TIER_PATTERN = re.compile(
    r"audit[s]?\s*\(0?8(\d{2})(?:/0?8\d{2})*\)\s*(passed|PASS|failed|FAIL)",
    re.IGNORECASE,
)

# Pattern for "ran all 24 audits (08xx suite)" - captures the event but not individual IDs
AUDIT_SUITE_PATTERN = re.compile(
    r"ran\s+(?:all\s+)?\d+\s+audits?\s*\(08xx",
    re.IGNORECASE,
)

# Audit record table pattern
AUDIT_RECORD_PATTERN = re.compile(
    r"\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*([^|]+)\s*\|\s*\*{0,2}(PASS|FAIL)\*{0,2}",
    re.IGNORECASE,
)


def parse_session_logs(
    log_dir: Path,
    since: datetime | None = None,
    files: list[Path] | None = None,
) -> list[AuditClaim]:
    """
    Extract audit claims from session logs within date range.

    Args:
        log_dir: Directory containing session log files
        since: Only scan logs after this date (None = no filter)
        files: Explicit file list (overrides since)

    Returns:
        List of AuditClaim dictionaries
    """
    claims: list[AuditClaim] = []

    # Get files to scan
    if files:
        log_files = files
    else:
        log_files = sorted(log_dir.glob("*.md"))

    for log_file in log_files:
        # Skip files older than since date based on filename
        # Filenames are either YYYY-MM-DD.md or Week-starting-YYYY-MM-DD.md
        if since is not None:
            try:
                date_match = re.search(r"(\d{4}-\d{2}-\d{2})", log_file.name)
                if date_match:
                    file_date = datetime.strptime(date_match.group(1), "%Y-%m-%d")
                    if file_date < since:
                        continue
            except ValueError:
                pass  # Can't parse date, include the file

        try:
            content = log_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue  # Skip unreadable files

        # Parse individual session headers and their content
        sessions = list(SESSION_HEADER_PATTERN.finditer(content))

        for i, session_match in enumerate(sessions):
            session_date = session_match.group(1)
            session_time = session_match.group(2)
            agent = session_match.group(3).strip()

            # Get content until next session or end of file
            start_pos = session_match.end()
            end_pos = sessions[i + 1].start() if i + 1 < len(sessions) else len(content)
            session_content = content[start_pos:end_pos]

            # Only extract claims from ### Summary sections (per Gemini G1.HIGH)
            summary_match = re.search(
                r"### Summary\s*\n(.+?)(?=\n###|\n---|\Z)",
                session_content,
                re.DOTALL,
            )
            if not summary_match:
                continue

            summary_text = summary_match.group(1)

            # Look for audit claims in summary using multiple patterns
            for pattern in [AUDIT_CLAIM_PATTERN, AUDIT_RESULT_PATTERN, AUDIT_TIER_PATTERN]:
                for match in pattern.finditer(summary_text):
                    audit_num = match.group(1)
                    status_raw = match.group(2) if len(match.groups()) > 1 else None
                    status = None
                    if status_raw:
                        status_upper = status_raw.upper()
                        if "PASS" in status_upper:
                            status = "PASS"
                        elif "FAIL" in status_upper:
                            status = "FAIL"

                    claims.append(
                        AuditClaim(
                            session_date=f"{session_date} {session_time}",
                            audit_id=f"08{audit_num}",
                            agent=agent,
                            session_file=str(log_file),
                            raw_text=match.group(0).strip(),
                            claimed_status=status,
                        )
                    )

    return claims


def parse_audit_records(audit_dir: Path) -> dict[str, list[AuditRecord]]:
    """
    Extract audit records from 08xx-audit-*.md files.

    Args:
        audit_dir: Directory containing audit files

    Returns:
        Dictionary mapping audit ID to list of AuditRecord
    """
    records: dict[str, list[AuditRecord]] = {}

    for audit_file in audit_dir.glob("08*-audit*.md"):
        # Extract audit ID from filename (e.g., 0809 from 0809-audit-security.md)
        id_match = re.match(r"(08\d{2})", audit_file.name)
        if not id_match:
            continue

        audit_id = id_match.group(1)

        try:
            content = audit_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        # Find the Audit Record section
        record_section = re.search(
            r"## \d+\. Audit Record\s*\n(.+?)(?=\n## |\Z)",
            content,
            re.DOTALL,
        )
        if not record_section:
            continue

        section_content = record_section.group(1)

        # Parse record table rows
        for match in AUDIT_RECORD_PATTERN.finditer(section_content):
            date = match.group(1)
            auditor = match.group(2).strip()
            status = match.group(3).upper()

            if audit_id not in records:
                records[audit_id] = []

            records[audit_id].append(
                AuditRecord(
                    date=date,
                    auditor=auditor,
                    findings=match.group(0),
                    status=status,
                    audit_file=str(audit_file),
                )
            )

    return records


def verify_claims(
    claims: list[AuditClaim],
    records: dict[str, list[AuditRecord]],
    date_tolerance_days: int = 3,
) -> list[VerificationResult]:
    """
    Cross-reference claims against records, checking date and status.

    Args:
        claims: List of audit claims from session logs
        records: Dictionary of audit records by audit ID
        date_tolerance_days: How many days difference allowed between claim and record

    Returns:
        List of VerificationResult
    """
    results: list[VerificationResult] = []

    for claim in claims:
        audit_id = claim["audit_id"]

        # Check if any records exist for this audit
        if audit_id not in records or not records[audit_id]:
            results.append(
                VerificationResult(
                    claim=claim,
                    record=None,
                    status="UNVERIFIED",
                    reason=f"No audit records found for {audit_id}",
                )
            )
            continue

        # Parse claim date
        try:
            claim_date = datetime.strptime(
                claim["session_date"].split()[0], "%Y-%m-%d"
            )
        except ValueError:
            results.append(
                VerificationResult(
                    claim=claim,
                    record=None,
                    status="UNVERIFIED",
                    reason=f"Could not parse claim date: {claim['session_date']}",
                )
            )
            continue

        # Find matching record within date tolerance
        best_match: AuditRecord | None = None
        best_delta = timedelta(days=date_tolerance_days + 1)

        for record in records[audit_id]:
            try:
                record_date = datetime.strptime(record["date"], "%Y-%m-%d")
                delta = abs(record_date - claim_date)
                if delta <= timedelta(days=date_tolerance_days) and delta < best_delta:
                    best_match = record
                    best_delta = delta
            except ValueError:
                continue

        if best_match is None:
            results.append(
                VerificationResult(
                    claim=claim,
                    record=None,
                    status="UNVERIFIED",
                    reason=f"No record within {date_tolerance_days} days of {claim['session_date']}",
                )
            )
            continue

        # Check status match if claim includes status
        if claim["claimed_status"] and claim["claimed_status"] != best_match["status"]:
            results.append(
                VerificationResult(
                    claim=claim,
                    record=best_match,
                    status="MISMATCH",
                    reason=f"Claimed {claim['claimed_status']} but record shows {best_match['status']}",
                )
            )
            continue

        # Verified!
        results.append(
            VerificationResult(
                claim=claim,
                record=best_match,
                status="VERIFIED",
                reason=f"Matched record from {best_match['date']}",
            )
        )

    return results


def generate_report(results: list[VerificationResult], output_path: Path | None) -> str:
    """
    Generate verification report.

    Args:
        results: List of verification results
        output_path: Path to write detailed report (None = stdout only)

    Returns:
        Summary string for stdout
    """
    verified = [r for r in results if r["status"] == "VERIFIED"]
    unverified = [r for r in results if r["status"] == "UNVERIFIED"]
    mismatched = [r for r in results if r["status"] == "MISMATCH"]

    # Summary for stdout
    summary_lines = [
        "=" * 60,
        "AUDIT VERIFICATION REPORT",
        "=" * 60,
        f"Total claims:  {len(results)}",
        f"Verified:      {len(verified)} [OK]",
        f"Unverified:    {len(unverified)} [FAIL]",
        f"Mismatched:    {len(mismatched)} [WARN]",
        "=" * 60,
    ]

    if unverified:
        summary_lines.append("\nUNVERIFIED CLAIMS:")
        for r in unverified:
            summary_lines.append(
                f"  - {r['claim']['audit_id']} on {r['claim']['session_date']}: {r['reason']}"
            )

    if mismatched:
        summary_lines.append("\nMISMATCHED CLAIMS:")
        for r in mismatched:
            summary_lines.append(
                f"  - {r['claim']['audit_id']} on {r['claim']['session_date']}: {r['reason']}"
            )

    summary = "\n".join(summary_lines)

    # Detailed report to file
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        report_lines = [
            "# Audit Verification Report",
            f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')} CT",
            "\n## Summary",
            "\n| Status | Count |",
            "|--------|-------|",
            f"| Verified | {len(verified)} |",
            f"| Unverified | {len(unverified)} |",
            f"| Mismatched | {len(mismatched)} |",
            f"| **Total** | **{len(results)}** |",
        ]

        if results:
            report_lines.append("\n## Details\n")
            report_lines.append(
                "| Claim Date | Audit | Agent | Status | Reason |"
            )
            report_lines.append("|------------|-------|-------|--------|--------|")
            for r in results:
                status_icon = {"VERIFIED": "[OK]", "UNVERIFIED": "[X]", "MISMATCH": "[!]"}[
                    r["status"]
                ]
                report_lines.append(
                    f"| {r['claim']['session_date']} | {r['claim']['audit_id']} | "
                    f"{r['claim']['agent'][:20]} | {status_icon} {r['status']} | {r['reason']} |"
                )

        output_path.write_text("\n".join(report_lines), encoding="utf-8")

    return summary


def main() -> int:
    """
    CLI entry point.

    Returns:
        0 = all verified or dry-run, 1 = unverified claims, 2 = error
    """
    parser = argparse.ArgumentParser(
        description="Verify audit execution claims against audit records.",
        epilog="Issue #248 - LLD: docs/lld/active/1248-ci-audit-verification.md",
    )
    parser.add_argument(
        "--since",
        type=str,
        help="Only scan logs after DATE (YYYY-MM-DD). Default: 4 weeks ago.",
    )
    parser.add_argument(
        "--files",
        nargs="+",
        type=Path,
        help="Explicit list of log files to scan (overrides --since).",
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=Path("docs"),
        help="Path to docs directory. Default: docs/",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tmp/audit-verification-report.md"),
        help="Path for detailed report. Default: tmp/audit-verification-report.md",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print report without exit code check.",
    )
    parser.add_argument(
        "--tolerance",
        type=int,
        default=3,
        help="Days tolerance for date matching. Default: 3",
    )

    args = parser.parse_args()

    # Parse since date — default to 4 weeks ago for CLI usage
    since: datetime | None = None
    if args.files:
        since = None  # Explicit file list overrides date filtering
    elif args.since:
        try:
            since = datetime.strptime(args.since, "%Y-%m-%d")
        except ValueError:
            print(f"ERROR: Invalid date format: {args.since}", file=sys.stderr)
            return 2
    else:
        since = datetime.now() - timedelta(weeks=4)

    # Validate paths
    log_dir = args.docs_dir / "session-logs"
    audit_dir = args.docs_dir

    if not log_dir.exists():
        print(f"ERROR: Session logs directory not found: {log_dir}", file=sys.stderr)
        return 2

    try:
        # Parse data
        claims = parse_session_logs(log_dir, since=since, files=args.files)
        records = parse_audit_records(audit_dir)

        # Verify
        results = verify_claims(claims, records, date_tolerance_days=args.tolerance)

        # Report
        summary = generate_report(results, args.output)
        print(summary)

        if args.output:
            print(f"\nDetailed report: {args.output}")

        # Exit code
        if args.dry_run:
            return 0

        unverified = [r for r in results if r["status"] in ("UNVERIFIED", "MISMATCH")]
        return 1 if unverified else 0

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
