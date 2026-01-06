# Implementation Report: Issue #153 - Fix Smoke Test Fixture Errors

**Issue:** #153
**Date:** 2026-01-05
**Implementer:** Claude Opus 4.5

## Summary

Fixed pytest fixture errors in `tools/smoke_test.py` by renaming `test_*` functions to `verify_*`, preventing pytest from collecting them as unit tests.

## Problem

`tools/smoke_test.py` contained 5 functions starting with `test_` that pytest collected as unit tests. These functions expected a `url` parameter which pytest interpreted as a missing fixture, causing 5 errors per test run.

## Solution

Renamed all 5 functions from `test_*` to `verify_*`:

| Before | After |
|--------|-------|
| `test_valid_input()` | `verify_valid_input()` |
| `test_blocked_input()` | `verify_blocked_input()` |
| `test_empty_input()` | `verify_empty_input()` |
| `test_prompt_injection()` | `verify_prompt_injection()` |
| `test_tone_neutrality()` | `verify_tone_neutrality()` |

Also updated:
- Function docstrings (Test → Verify)
- Function calls in `main()` to use new names

## Files Modified

| File | Change |
|------|--------|
| `tools/smoke_test.py` | Renamed 5 function definitions, updated 5 calls in main() |

## Rationale

Per LLD `docs/1153-smoke-test-fixture-fix.md`:
- These are **smoke tests** for manual/post-deployment verification, NOT unit tests
- They test live deployed endpoints, not mocked fixtures
- Renaming to `verify_*` clearly communicates intent and excludes from pytest

## Alternatives Rejected

1. **Create URL fixture** - Defeats purpose of smoke tests (they hit live endpoints)
2. **pytest.mark.skip** - Confusing intent, still collected
3. **Delete file** - Loses smoke test capability
