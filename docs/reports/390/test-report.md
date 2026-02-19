# Test Report — Issue #390

**Title:** fix: feature-flag @require_auth to restore API (401 regression)
**Date:** 2026-02-19
**Status:** All passing

## Test Results

```
40 passed in 2.57s
```

## New Tests

| Test | Description | Result |
|------|-------------|--------|
| `test_auth_disabled_bypasses_jwt` | HTTP request without JWT succeeds when AUTH_ENABLED=false | PASS |
| `test_auth_enabled_requires_jwt` | HTTP request without JWT returns 401 when AUTH_ENABLED=true | PASS |
| `test_direct_invocation_unaffected` | Direct invocation (no requestContext) works regardless of flag | PASS |

## Existing Tests

All 37 existing tests continue to pass. No regressions.

## Coverage

The three new tests cover:
- The feature flag default (false) path
- The feature flag enabled path (401 rejection)
- The direct invocation path (flag irrelevant)
