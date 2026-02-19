# Implementation Report — Issue #390

**Title:** fix: feature-flag @require_auth to restore API (401 regression)
**Date:** 2026-02-19
**Status:** Complete

## Summary

Added `AUTH_ENABLED` environment variable (default `false`) to control whether JWT authentication is required for HTTP requests. This restores API functionality while keeping auth code in place for future activation.

## Changes

| File | Change |
|------|--------|
| `src/lambda_function.py:652-662` | Conditional auth gate: checks `AUTH_ENABLED` env var before applying `@require_auth` |
| `provision.sh:441` | Added `AUTH_ENABLED=false` to Lambda create env vars |
| `provision.sh:460` | Added `AUTH_ENABLED=false` to Lambda update env vars |
| `tests/unit/test_lambda_handler.py` | Added `TestAuthFeatureFlag` class with 3 tests |

## Design Decisions

- **Feature flag over removal:** Keeps auth code deployed and testable. Flip `AUTH_ENABLED=true` when auth infra (DynamoDB users table, auth Lambda) is deployed.
- **Default false:** Fail-open for the auth gate since no client can provide JWTs yet.
- **Env var naming:** `AUTH_ENABLED` is explicit and matches the pattern of other Lambda env vars.

## Risk Assessment

- **Low risk:** The change only affects the code path for HTTP requests with `requestContext`.
- **Backward compatible:** Direct Lambda invocations (tests, SDK) are unaffected.
- **Reversible:** Set `AUTH_ENABLED=true` to re-enable auth at any time.
