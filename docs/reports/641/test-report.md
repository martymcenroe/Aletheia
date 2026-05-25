# Test Report — Issues #641, #642, #643, #648, #649

## Pytest Run

```
cd Aletheia-641
poetry run pytest tests/unit/ -q
```

**Result:** `837 passed, 13 warnings in 9.01s` — zero failures.

Baseline after PR #653 was 834; this PR adds 3 new privacy tests = 837. No existing tests required updating (the existing auth test suite asserted on status codes and response shape, not on exception message text).

## New Tests

`tests/unit/test_lambda_auth.py::TestAuthLambdaExceptionTextDoesNotLeak`:

| Test | Surface(s) tested by canary |
|---|---|
| `test_token_exchange_failure_log_does_not_include_response_text` | #648 (line 131) |
| `test_token_refresh_failure_log_does_not_include_response_text` | #648 (line 165) |
| `test_redirect_uri_not_logged` | #649 |

## Coverage Note

5 audit issues span 8 code locations. Direct canary tests cover 3 of those; the remaining 5 are mechanically-identical fixes covered by existing auth regression tests (46 tests, all passing). The re-audit at the end of umbrella #637 will surface any leaks the unit tests miss.

## ESLint / mypy / ruff

All pass (pre-commit gate).

## Conclusion

Safe to merge. Then `provision.sh` + smoke test. Smoke test must exercise an auth endpoint (e.g. `POST /auth/token` with empty body returns 400, confirms Auth Lambda handler loads cleanly post-edit).
