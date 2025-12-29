# 0113 - Template: Test Report

## Usage
Use this template to record test execution results for an issue/feature.
This is separate from the Test Script (0111) which defines WHAT to test.
This report records WHAT HAPPENED when tests were run.

Target Location: `docs/reports/` or embedded in Implementation Report (0103).

---

## Template

# Test Report: {Feature Name}

**Issue:** #{IssueID}
**LLD Ref:** docs/1{IssueID}-{feature-name}.md
**Test Script Ref:** {TS-{IssueID} or "Embedded in LLD"}

## 1. Test Execution Summary

| Date | Tester | Environment | Overall Result |
|------|--------|-------------|----------------|
| {YYYY-MM-DD} | {Name/Model} | {Local/Dev/Prod} | PASS / FAIL |

## 2. Test Results

### Automated Tests (pytest)

```
{Paste pytest output here}
```

**Coverage:** {X%}
**Failures:** {0 or list failed tests}

### Manual Tests

| ID | Scenario | Result | Notes |
|----|----------|--------|-------|
| 010 | {Happy Path} | PASS | |
| 020 | {Edge Case} | PASS | |
| 030 | {Error Case} | PASS | |
| 040 | {Scenario} | FAIL | {Brief reason} |

## 3. Failed Tests Detail

### {Test ID}: {Scenario Name}

**Expected:** {What should have happened}
**Actual:** {What actually happened}
**Root Cause:** {If known}
**Resolution:** {Fixed in commit X / Deferred to Issue #Y / Won't Fix}

## 4. Regression Check

| Area | Verified | Notes |
|------|----------|-------|
| Existing functionality X | [ ] | |
| Existing functionality Y | [ ] | |
| Performance | [ ] | {No degradation observed} |

## 5. Environment Notes

- **Browser:** {Chrome 120, Firefox 121, etc.}
- **OS:** {Windows 11, macOS 14, etc.}
- **Extension Version:** {From manifest.json}
- **Lambda:** {Deployed / Local SAM}
- **Special Config:** {e.g., Concurrency=1, Debug mode ON}

## 6. Sign-Off

| Role | Name | Date | Approval |
|------|------|------|----------|
| Tester | {Name/Model} | {Date} | Tests executed |
| Developer | {Name/Model} | {Date} | Failures addressed |
| Reviewer | {Human} | {Date} | Approved for merge |

## 7. Attachments

- [ ] Screenshots (if applicable)
- [ ] Log excerpts (if applicable)
- [ ] Performance metrics (if applicable)
