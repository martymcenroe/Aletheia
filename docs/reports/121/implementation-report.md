# 121 - Implementation Report: Wikipedia Denylist Integration

## 1. Metadata

| Field | Value |
|-------|-------|
| **Issue** | #121 |
| **LLD** | `docs/1121-wikipedia-denylist.md` |
| **Test Report** | `docs/reports/121/test-report.md` |
| **Implementer** | Claude Opus 4.5 via Claude Code |
| **Date** | 2026-01-01 |
| **PR** | #130 |

## 2. Summary

Implemented Wikipedia-based denylist fetcher to replace the deprecated RSDB approach. The tool fetches ethnic slurs and profanity from Wikipedia's curated lists using the MediaWiki API, applying multi-pass wikitext parsing to extract terms from tables, definitions, and bullet lists. Safety mechanisms include a stop-list of common words, term count thresholds, and canary assertions.

## 3. Files Created

| File | Description |
|------|-------------|
| `tools/fetch_denylist.py` | Main fetcher script (~620 lines) with MediaWiki API integration |
| `tests/test_fetch_denylist.py` | 26 unit tests with mocked API responses |

## 4. Files Modified

| File | Changes | Description |
|------|---------|-------------|
| `src/guardrails/resources/denylist.json` | Updated | Populated with 803 terms from Wikipedia |

## 5. Deviations from LLD

| Deviation | Reason | Impact |
|-----------|--------|--------|
| Added seed terms (19) | Category:Profanity contains articles ABOUT profanity, not the words themselves | Ensures Seven Dirty Words baseline coverage |
| Rate limiting at 1.0s | More conservative than LLD's 0.5s | Safer for Wikipedia API politeness |
| Multi-pass parsing | Wikitext complexity required table, definition, AND bullet parsing | More comprehensive term extraction |

## 6. Test Harness

- **Test file:** `tests/test_fetch_denylist.py`
- **Fixtures:** Mocked MediaWiki API responses (tables, wikitext, category members)
- **Test data:** Inline mock data simulating Wikipedia response formats
- **Utilities:** `@patch` decorators for requests isolation

## 7. Test Coverage

| Area | Coverage | Notes |
|------|----------|-------|
| Table parsing | Covered | Tests 010-030 |
| Definition parsing | Covered | Tests 040-050 |
| Stop-list filtering | Covered | Tests 060-070 |
| Category enumeration | Covered | Tests 080-090 |
| Threshold assertions | Covered | Tests 100-110 |
| Canary checks | Covered | Tests 120-130 |
| API error handling | Covered | Tests 140-150 |
| Rate limiting | Partial | Timing not tested, just presence of sleep() |

**Willison Protocol Compliance:**
- [x] Automated tests written
- [x] Tests fail on revert (verified)
- [x] Proof captured in Test Report

## 8. Lessons Learned

- **Wikipedia categories are descriptive, not prescriptive:** Category:Profanity lists articles about profanity concepts, not actual profane words. Required adding seed terms.
- **Wikitext is complex:** Required three parsing passes (tables, definitions, bullets) to capture all term formats.
- **Safety stop-list is essential:** Without it, common words like "the", "and" would be blocked.

## 9. Open Issues

| Issue | Type | Description |
|-------|------|-------------|
| N/A | Note | Consider adding more seed terms if coverage gaps discovered |
| N/A | Note | Monitor Wikipedia API for format changes (canary tests help) |

## 10. Orchestrator Review Notes

**Reviewer:** Gemini 3.0 Pro (Architect Review)
**Date:** 2025-12-31

### In-Scope Observations
- Enforced automated integrity checks (thresholds, canaries)
- Required safety stop-list to prevent data poisoning
- Mandated multi-pass parsing for wikitext complexity

### New-Scope Observations
- None created

### Meta Observations
- Established "Tier 1" (Safety), "Tier 2" (Tooling), "Tier 3" (Enhancement) review framework
- Added mandatory LLD review gate to CLAUDE.md

### Approval
- [x] Code reviewed
- [x] Automated tests passed (26/26)
- [x] Ready for merge
