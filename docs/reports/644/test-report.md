# Test Report — Issue #644

## Pytest Run

```
cd Aletheia-644
poetry run pytest tests/unit/ -q
```

**Result:** `839 passed, 13 warnings in 10.77s` — zero failures.

Baseline after PR #654 was 837; this PR adds 2 new privacy tests = 839.

## New Tests

`tests/unit/test_signal_inspector.py::TestFetcherExceptionTextDoesNotLeak`:

| Test | Mechanism |
|---|---|
| `test_request_exception_does_not_leak_url_or_message_into_log` | `responses` library, no matcher registered → ConnectionError → asserts canary URL not in log |
| `test_request_exception_does_not_leak_message_into_return_tuple` | Same mechanism, asserts canary URL not in 4th tuple element of `fetch_page` return |

## ESLint / mypy / ruff

All pass (pre-commit gate).

## Conclusion

Safe to merge. **No `provision.sh` deploy needed** — `signal_inspector` is not in any Lambda's import path (CLI-only module).
