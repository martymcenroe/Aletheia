"""
Unit tests for verify_audits.py - CI Job to Verify Audit Execution Claims.

See: docs/lld/active/1248-ci-audit-verification.md Section 11.

Test scenarios from LLD:
- 010: Valid claim with matching record
- 020: Claim with no matching record
- 030: Claim outside date window
- 040: Multiple claims same audit
- 050: Malformed session log
- 060: Empty audit record section
- 070: Weekly log with multiple sessions
- 080: PASS/FAIL status mismatch
- 090: Audit mention outside Summary
"""

# Import from tools module - adjust path since tools isn't a package
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

import tempfile  # noqa: E402
from datetime import datetime  # noqa: E402

import pytest  # noqa: E402

from verify_audits import (  # noqa: E402
    AuditClaim,
    AuditRecord,
    parse_session_logs,
    parse_audit_records,
    verify_claims,
    generate_report,
    SESSION_HEADER_PATTERN,
    AUDIT_CLAIM_PATTERN,
    AUDIT_RESULT_PATTERN,
    AUDIT_TIER_PATTERN,
    AUDIT_RECORD_PATTERN,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_session_log_with_claim(temp_dir):
    """Create a session log with a valid audit claim."""
    log_dir = temp_dir / "session-logs"
    log_dir.mkdir()
    log_file = log_dir / "2026-01-06.md"
    log_file.write_text(
        """# Session Log 2026-01-06

## 2026-01-06 13:06 CT | Claude Opus 4.5

### Summary

Tier 1 audit (0809/0810) passed. All security checks complete.

### Details

Ran the standard security checks.
""",
        encoding="utf-8",
    )
    return log_dir


@pytest.fixture
def mock_audit_file_with_record(temp_dir):
    """Create an audit file with matching record."""
    audit_file = temp_dir / "0809-audit-security.md"
    audit_file.write_text(
        """# 0809 Security Audit

## 1. Overview

Security audit checklist.

## 2. Audit Record

| Date | Auditor | Findings Summary | Issues Created |
|------|---------|------------------|----------------|
| 2026-01-06 | Claude Opus 4.5 | **PASS** - All sections passed | None |
| 2026-01-01 | Claude Opus 4.5 | **PASS** - Clean run | None |
""",
        encoding="utf-8",
    )
    return temp_dir


class TestRegexPatterns:
    """Tests for regex pattern matching."""

    def test_session_header_pattern(self):
        """Session header pattern matches expected format."""
        text = "## 2026-01-06 13:06 CT | Claude Opus 4.5"
        match = SESSION_HEADER_PATTERN.search(text)
        assert match is not None
        assert match.group(1) == "2026-01-06"
        assert match.group(2) == "13:06"
        assert match.group(3) == "Claude Opus 4.5"

    def test_session_header_pattern_multiple(self):
        """Session header pattern finds multiple sessions."""
        text = """## 2026-01-06 10:00 CT | Model A

Content

## 2026-01-06 14:00 CT | Model B

More content"""
        matches = list(SESSION_HEADER_PATTERN.finditer(text))
        assert len(matches) == 2
        assert matches[0].group(3) == "Model A"
        assert matches[1].group(3) == "Model B"

    def test_audit_tier_pattern(self):
        """Tier pattern matches 'Tier 1 audit (0809/0810) passed'."""
        text = "Tier 1 audit (0809/0810) passed"
        match = AUDIT_TIER_PATTERN.search(text)
        assert match is not None
        assert match.group(1) == "09"  # Captures just the 2 digits after 08
        assert match.group(2).upper() == "PASSED"

    def test_audit_tier_pattern_single(self):
        """Tier pattern matches single audit ID."""
        text = "audit (0809) PASS"
        match = AUDIT_TIER_PATTERN.search(text)
        assert match is not None
        assert match.group(1) == "09"
        assert match.group(2).upper() == "PASS"

    def test_audit_claim_pattern(self):
        """Basic claim pattern matches 'ran 0809'."""
        text = "ran 0809 PASS"  # Status must immediately follow for this pattern
        match = AUDIT_CLAIM_PATTERN.search(text)
        assert match is not None
        assert match.group(1) == "09"
        # Status group may not match depending on text format
        # The AUDIT_RESULT_PATTERN handles "0809 Security - PASS" format instead

    def test_audit_result_pattern(self):
        """Result pattern matches '0809 Security - PASS'."""
        text = "0809 Security audit completed - PASS"
        match = AUDIT_RESULT_PATTERN.search(text)
        assert match is not None
        assert match.group(1) == "09"
        assert match.group(2).upper() == "PASS"

    def test_audit_record_pattern(self):
        """Record pattern matches table row."""
        text = "| 2026-01-06 | Claude Opus 4.5 | **PASS** - All good | None |"
        match = AUDIT_RECORD_PATTERN.search(text)
        assert match is not None
        assert match.group(1) == "2026-01-06"
        assert "Claude" in match.group(2)
        assert match.group(3).upper() == "PASS"


class TestParseSessionLogs:
    """Tests for parse_session_logs function."""

    def test_010_valid_claim_extracted(self, mock_session_log_with_claim):
        """Scenario 010: Valid audit claim is extracted."""
        claims = parse_session_logs(mock_session_log_with_claim)
        assert len(claims) >= 1
        claim = claims[0]
        assert claim["audit_id"] == "0809"
        assert "2026-01-06" in claim["session_date"]
        assert claim["claimed_status"] == "PASS"

    def test_050_malformed_log_graceful(self, temp_dir):
        """Scenario 050: Malformed session log doesn't crash."""
        log_dir = temp_dir / "session-logs"
        log_dir.mkdir()
        log_file = log_dir / "2026-01-06.md"
        log_file.write_text(
            """This is not a valid session log format.
No headers, no structure, just text.
Random mention of 0809 but not in summary.""",
            encoding="utf-8",
        )
        claims = parse_session_logs(log_dir)
        assert claims == []  # No crash, no claims extracted

    def test_070_multiple_sessions_in_weekly_log(self, temp_dir):
        """Scenario 070: Weekly log with multiple sessions extracts all dates."""
        log_dir = temp_dir / "session-logs"
        log_dir.mkdir()
        log_file = log_dir / "Week-starting-2026-01-06.md"
        log_file.write_text(
            """# Weekly Log

## 2026-01-06 10:00 CT | Agent A

### Summary

Ran 0809 Security audit - PASS.

---

## 2026-01-07 14:00 CT | Agent B

### Summary

Executed 0810 Privacy audit - PASS.

---

## 2026-01-08 09:00 CT | Agent C

### Summary

Completed 0812 Performance audit - FAIL.
""",
            encoding="utf-8",
        )
        claims = parse_session_logs(log_dir)
        # Multiple patterns may match, producing duplicates
        # Key test: all 3 dates and audit IDs are extracted correctly
        assert len(claims) >= 3  # At least one per session

        dates = [c["session_date"].split()[0] for c in claims]
        assert "2026-01-06" in dates
        assert "2026-01-07" in dates
        assert "2026-01-08" in dates

        audit_ids = [c["audit_id"] for c in claims]
        assert "0809" in audit_ids
        assert "0810" in audit_ids
        assert "0812" in audit_ids

        # Verify claims are assigned to correct sessions (not all same date)
        claims_by_date = {}
        for c in claims:
            date = c["session_date"].split()[0]
            if date not in claims_by_date:
                claims_by_date[date] = []
            claims_by_date[date].append(c["audit_id"])

        assert "0809" in claims_by_date.get("2026-01-06", [])
        assert "0810" in claims_by_date.get("2026-01-07", [])
        assert "0812" in claims_by_date.get("2026-01-08", [])

    def test_090_mention_outside_summary_ignored(self, temp_dir):
        """Scenario 090: Audit mention outside Summary section is NOT extracted."""
        log_dir = temp_dir / "session-logs"
        log_dir.mkdir()
        log_file = log_dir / "2026-01-06.md"
        log_file.write_text(
            """# Session Log

## 2026-01-06 10:00 CT | Agent A

### Summary

Did some work today. Nothing special.

### Details

We discussed the 0809 Security audit requirements but did not run it.
Also talked about 0810 Privacy audit.
""",
            encoding="utf-8",
        )
        claims = parse_session_logs(log_dir)
        assert claims == []  # Should NOT extract mentions from Details section

    def test_since_filter(self, temp_dir):
        """Claims from logs before 'since' date are filtered out."""
        log_dir = temp_dir / "session-logs"
        log_dir.mkdir()

        # Old log
        old_log = log_dir / "2025-12-01.md"
        old_log.write_text(
            """## 2025-12-01 10:00 CT | Agent

### Summary

Ran 0809 audit - PASS.""",
            encoding="utf-8",
        )

        # Recent log
        new_log = log_dir / "2026-01-06.md"
        new_log.write_text(
            """## 2026-01-06 10:00 CT | Agent

### Summary

Ran 0810 audit - PASS.""",
            encoding="utf-8",
        )

        # Filter to only recent logs
        since = datetime(2026, 1, 1)
        claims = parse_session_logs(log_dir, since=since)

        audit_ids = [c["audit_id"] for c in claims]
        assert "0809" not in audit_ids  # Old log filtered
        assert "0810" in audit_ids  # Recent log included


class TestParseAuditRecords:
    """Tests for parse_audit_records function."""

    def test_records_extracted(self, mock_audit_file_with_record):
        """Records are extracted from audit file."""
        records = parse_audit_records(mock_audit_file_with_record)
        assert "0809" in records
        assert len(records["0809"]) == 2

    def test_060_empty_record_section(self, temp_dir):
        """Scenario 060: Empty audit record section returns zero records."""
        audit_file = temp_dir / "0809-audit-security.md"
        audit_file.write_text(
            """# 0809 Security Audit

## 1. Overview

Security audit.

## 2. Audit Record

| Date | Auditor | Findings Summary | Issues Created |
|------|---------|------------------|----------------|

(No audits yet)
""",
            encoding="utf-8",
        )
        records = parse_audit_records(temp_dir)
        assert records.get("0809", []) == []

    def test_status_extracted_correctly(self, temp_dir):
        """PASS and FAIL status extracted from records."""
        audit_file = temp_dir / "0809-audit-security.md"
        audit_file.write_text(
            """# 0809 Security Audit

## 2. Audit Record

| Date | Auditor | Findings Summary | Issues Created |
|------|---------|------------------|----------------|
| 2026-01-05 | Agent | **PASS** - Good | None |
| 2026-01-04 | Agent | **FAIL** - Issues | #123 |
""",
            encoding="utf-8",
        )
        records = parse_audit_records(temp_dir)
        statuses = [r["status"] for r in records["0809"]]
        assert "PASS" in statuses
        assert "FAIL" in statuses


class TestVerifyClaims:
    """Tests for verify_claims function."""

    def test_010_valid_claim_verified(self):
        """Scenario 010: Valid claim with matching record is VERIFIED."""
        claims = [
            AuditClaim(
                session_date="2026-01-06 13:00",
                audit_id="0809",
                agent="Claude Opus 4.5",
                session_file="test.md",
                raw_text="ran 0809 - PASS",
                claimed_status="PASS",
            )
        ]
        records = {
            "0809": [
                AuditRecord(
                    date="2026-01-06",
                    auditor="Claude Opus 4.5",
                    findings="PASS",
                    status="PASS",
                    audit_file="0809-audit.md",
                )
            ]
        }
        results = verify_claims(claims, records)
        assert len(results) == 1
        assert results[0]["status"] == "VERIFIED"
        assert results[0]["record"] is not None

    def test_020_claim_no_matching_record(self):
        """Scenario 020: Claim with no matching record is UNVERIFIED."""
        claims = [
            AuditClaim(
                session_date="2026-01-06 13:00",
                audit_id="0815",  # No records for this audit
                agent="Agent",
                session_file="test.md",
                raw_text="ran 0815",
                claimed_status=None,
            )
        ]
        records = {}  # No records at all
        results = verify_claims(claims, records)
        assert len(results) == 1
        assert results[0]["status"] == "UNVERIFIED"
        assert "No audit records found" in results[0]["reason"]

    def test_030_claim_outside_date_window(self):
        """Scenario 030: Claim outside date tolerance is UNVERIFIED."""
        claims = [
            AuditClaim(
                session_date="2026-01-10 13:00",  # 10 days after record
                audit_id="0809",
                agent="Agent",
                session_file="test.md",
                raw_text="ran 0809",
                claimed_status=None,
            )
        ]
        records = {
            "0809": [
                AuditRecord(
                    date="2025-12-31",  # More than 3 days ago
                    auditor="Agent",
                    findings="PASS",
                    status="PASS",
                    audit_file="0809-audit.md",
                )
            ]
        }
        results = verify_claims(claims, records, date_tolerance_days=3)
        assert len(results) == 1
        assert results[0]["status"] == "UNVERIFIED"
        assert "No record within" in results[0]["reason"]

    def test_040_multiple_claims_same_audit(self):
        """Scenario 040: Multiple claims, one record - first verified, second not."""
        claims = [
            AuditClaim(
                session_date="2026-01-06 10:00",
                audit_id="0809",
                agent="Agent",
                session_file="test.md",
                raw_text="ran 0809",
                claimed_status="PASS",
            ),
            AuditClaim(
                session_date="2026-01-15 10:00",  # No matching record
                audit_id="0809",
                agent="Agent",
                session_file="test.md",
                raw_text="ran 0809",
                claimed_status="PASS",
            ),
        ]
        records = {
            "0809": [
                AuditRecord(
                    date="2026-01-06",
                    auditor="Agent",
                    findings="PASS",
                    status="PASS",
                    audit_file="0809-audit.md",
                )
            ]
        }
        results = verify_claims(claims, records)
        statuses = [r["status"] for r in results]
        assert "VERIFIED" in statuses
        assert "UNVERIFIED" in statuses

    def test_080_status_mismatch(self):
        """Scenario 080: Claim says PASS, record says FAIL - MISMATCH."""
        claims = [
            AuditClaim(
                session_date="2026-01-06 13:00",
                audit_id="0809",
                agent="Agent",
                session_file="test.md",
                raw_text="ran 0809 - PASS",
                claimed_status="PASS",  # Claims PASS
            )
        ]
        records = {
            "0809": [
                AuditRecord(
                    date="2026-01-06",
                    auditor="Agent",
                    findings="FAIL",
                    status="FAIL",  # Record says FAIL
                    audit_file="0809-audit.md",
                )
            ]
        }
        results = verify_claims(claims, records)
        assert len(results) == 1
        assert results[0]["status"] == "MISMATCH"
        assert "Claimed PASS but record shows FAIL" in results[0]["reason"]

    def test_date_tolerance_configurable(self):
        """Date tolerance can be configured."""
        claims = [
            AuditClaim(
                session_date="2026-01-06 13:00",
                audit_id="0809",
                agent="Agent",
                session_file="test.md",
                raw_text="ran 0809",
                claimed_status=None,
            )
        ]
        records = {
            "0809": [
                AuditRecord(
                    date="2026-01-01",  # 5 days before claim
                    auditor="Agent",
                    findings="PASS",
                    status="PASS",
                    audit_file="0809-audit.md",
                )
            ]
        }

        # With default 3-day tolerance, should be UNVERIFIED
        results_3day = verify_claims(claims, records, date_tolerance_days=3)
        assert results_3day[0]["status"] == "UNVERIFIED"

        # With 7-day tolerance, should be VERIFIED
        results_7day = verify_claims(claims, records, date_tolerance_days=7)
        assert results_7day[0]["status"] == "VERIFIED"


class TestGenerateReport:
    """Tests for generate_report function."""

    def test_report_generation(self, temp_dir):
        """Report is generated with correct format."""
        results = [
            {
                "claim": AuditClaim(
                    session_date="2026-01-06 13:00",
                    audit_id="0809",
                    agent="Claude Opus 4.5",
                    session_file="test.md",
                    raw_text="ran 0809",
                    claimed_status="PASS",
                ),
                "record": AuditRecord(
                    date="2026-01-06",
                    auditor="Claude",
                    findings="PASS",
                    status="PASS",
                    audit_file="0809.md",
                ),
                "status": "VERIFIED",
                "reason": "Matched record from 2026-01-06",
            }
        ]
        output_path = temp_dir / "report.md"
        summary = generate_report(results, output_path)

        assert "AUDIT VERIFICATION REPORT" in summary
        assert "Verified:" in summary
        assert "1" in summary
        assert output_path.exists()

        report_content = output_path.read_text(encoding="utf-8")
        assert "VERIFIED" in report_content
        assert "0809" in report_content

    def test_report_counts(self, temp_dir):
        """Report correctly counts verified/unverified/mismatched."""
        results = [
            {
                "claim": AuditClaim(
                    session_date="2026-01-06 13:00",
                    audit_id="0809",
                    agent="Agent",
                    session_file="test.md",
                    raw_text="ran 0809",
                    claimed_status=None,
                ),
                "record": None,
                "status": "VERIFIED",
                "reason": "OK",
            },
            {
                "claim": AuditClaim(
                    session_date="2026-01-07 13:00",
                    audit_id="0810",
                    agent="Agent",
                    session_file="test.md",
                    raw_text="ran 0810",
                    claimed_status=None,
                ),
                "record": None,
                "status": "UNVERIFIED",
                "reason": "No record",
            },
            {
                "claim": AuditClaim(
                    session_date="2026-01-08 13:00",
                    audit_id="0812",
                    agent="Agent",
                    session_file="test.md",
                    raw_text="ran 0812",
                    claimed_status=None,
                ),
                "record": None,
                "status": "MISMATCH",
                "reason": "Status mismatch",
            },
        ]
        output_path = temp_dir / "report.md"
        summary = generate_report(results, output_path)

        assert "Verified:      1" in summary
        assert "Unverified:    1" in summary
        assert "Mismatched:    1" in summary


class TestIntegration:
    """End-to-end integration tests."""

    def test_full_verification_flow(self, temp_dir):
        """Full flow: parse logs, parse records, verify, report."""
        # Create session log
        log_dir = temp_dir / "session-logs"
        log_dir.mkdir()
        log_file = log_dir / "2026-01-06.md"
        log_file.write_text(
            """## 2026-01-06 13:00 CT | Claude Opus 4.5

### Summary

Tier 1 audit (0809/0810) passed. All checks complete.
""",
            encoding="utf-8",
        )

        # Create audit file
        audit_file = temp_dir / "0809-audit-security.md"
        audit_file.write_text(
            """# 0809 Security Audit

## 2. Audit Record

| Date | Auditor | Findings Summary | Issues Created |
|------|---------|------------------|----------------|
| 2026-01-06 | Claude Opus 4.5 | **PASS** - All good | None |
""",
            encoding="utf-8",
        )

        # Run verification
        claims = parse_session_logs(log_dir)
        records = parse_audit_records(temp_dir)
        results = verify_claims(claims, records)

        # Should find the 0809 claim and verify it
        verified = [r for r in results if r["status"] == "VERIFIED"]
        assert len(verified) >= 1
        assert any(r["claim"]["audit_id"] == "0809" for r in verified)
