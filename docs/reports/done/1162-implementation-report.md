# Implementation Report: Issue #162 - NoArchive Transform Layer

**Issue:** #162
**Date:** 2026-01-07
**Author:** Claude Opus 4.5
**Status:** Complete

---

## Summary

Implemented the NoArchive Transform Layer to respect publisher `<meta name="robots" content="noarchive">` signals. When this signal is present, Aletheia generates the etymology response for the user but does NOT persist the query or response to DynamoDB.

**Key Principle:** Generate but don't persist. The user still receives their analysis - we just don't store it.

---

## Changes Made

### 1. Extension: content-check.js

Added `checkNoArchive()` function that:
- Queries both `<meta name="robots">` and `<meta name="googlebot">` tags
- Returns `true` if either contains "noarchive" directive
- Handles comma-separated directive lists (e.g., "noindex, noarchive")

Updated `checkPageSignals()` to return combined result including `noarchive` boolean.

**Lines changed:** 67-112

### 2. Extension: service-worker.js

- Added `tabNoArchive` Map to store noarchive signals per tab (line 27)
- Updated `checkTabForAgeRestriction()` to extract and store noarchive signal (lines 61-65)
- Added cleanup on tab close (line 133)
- Updated payload to include `signals: { noarchive: boolean }` (lines 317-328)

### 3. Lambda: lambda_function.py

- Added signal extraction: `signals = body.get("signals", {})` (line 330)
- Added skip flag: `skip_persistence = signals.get("noarchive", False)` (line 331)
- Modified `finally` block to conditionally call `save_state()` (lines 360-381)
- Added logging when skipping: `NOARCHIVE: Skipping persistence for thread_id=...`

---

## Files Changed

| File | Lines | Change |
|------|-------|--------|
| `extensions/chrome/content-check.js` | +47 | Added `checkNoArchive()` and `checkPageSignals()` |
| `extensions/chrome/service-worker.js` | +15 | Store/send noarchive signal |
| `src/lambda_function.py` | +12 | Conditional persistence skip |
| `tests/test_noarchive.py` | +230 | New test file (5 tests) |
| `tests/fixtures/html/test-noarchive.html` | +57 | Test fixture |

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Page        │     │   Extension     │     │     Lambda      │
│                 │     │                 │     │                 │
│ <meta robots    │────▶│ checkNoArchive()│────▶│ if noarchive:   │
│  noarchive>     │     │ signals.noarchive│     │   skip save_state│
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │  User sees      │
                                                │  etymology      │
                                                │  (no DynamoDB)  │
                                                └─────────────────┘
```

---

## Security Notes

- **Client can lie:** A malicious client could always send `noarchive=true`. This is acceptable - it's a "fail-safe" state (less persistence, not more).
- **No PII in logs:** The skip event is logged but NOT the content that was skipped.
- **Rollback risk:** Rolling back this feature means ignoring publisher signals, which has compliance implications.

---

## Verification

1. All 5 new unit tests pass
2. All 189 existing tests pass (no regressions)
3. CloudWatch logs will show `NOARCHIVE: Skipping persistence` when triggered
