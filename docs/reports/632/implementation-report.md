# Implementation Report — Issue #632

## Scope

Remove three orphan Python modules in `src/auth/` and their unit tests. The modules import `httpx` (issue #621), are never imported by any production code path, and exist only as remnants of an earlier CLI-based LinkedIn auth design.

## Files Removed

| File | Reason |
|---|---|
| `src/auth/linkedin_oauth.py` | Orphan; LinkedIn OAuth in production is handled by `lambda_auth_function.py` using `requests`, not this module's `httpx` implementation. |
| `src/auth/token_manager.py` | Orphan; encrypted Fernet-on-disk token storage was for CLI auth, never used in Lambda. |
| `src/auth/auth_state.py` | Orphan; only importer of `token_manager`, itself never imported. |
| `tests/unit/test_linkedin_oauth.py` | Tests for the orphan module above. |
| `tests/unit/test_token_manager.py` | Tests for the orphan module above. |
| `tests/unit/test_auth_state.py` | Tests for the orphan module above. |

## Orphan Verification

Performed during pre-implementation investigation (recorded in #632 body):

1. `grep -rn 'linkedin_oauth\|token_manager\|auth_state' src/` returned a single match: `auth/auth_state.py:22: from .token_manager import ...` (orphan-to-orphan).
2. `lambda_auth_function.py` top-level imports: `html, json, logging, os, time, typing, boto3, requests, botocore.exceptions`. No httpx, no orphan-module imports.
3. `lambda_auth_function.py:474` `handle_token_exchange` calls a local `exchange_code_for_tokens` (uses `requests`), not the orphan `auth/linkedin_oauth.py:exchange_code_for_tokens` (uses `httpx`).
4. `lambda_function.py` imports `auth.auth_middleware` only; transitively reaches `jwt_service`, `rate_limit`, `tier_config_service`, `token_cap_service` — none touch httpx.
5. `auth/__init__.py` re-exports `auth_middleware` only.
6. `aws logs tail /aws/lambda/AletheiaAuth --since 7d --filter-pattern ImportError` returned empty.
7. Live `POST /auth/token` returned `HTTP 400 "Missing code or redirectUri"` in 248ms — cold-start succeeds, no import error.
8. All non-Python matches for these names (in `extensions/`, `tests/mocks/`, `tests/unit/chrome/auth.test.js`, `tests/integration/test_auth_flow.py`) are false positives matching the unrelated browser-side `oauth_state` CSRF cookie or the `_reset_auth_state()` test helper function name.

## Closes

- #632 — this issue
- #621 — undeclared `httpx` (orphan-only importer, mooted by removal)

## Blast Radius

Zero production code paths affected. Test suite shrinks by the count of tests in the three deleted test files (previously failed to collect locally due to missing `httpx`).

## Rollback

`git revert <merge-commit-sha>` restores all 6 files exactly as deleted. No infrastructure or DynamoDB state changes. No `provision.sh` re-run required.
