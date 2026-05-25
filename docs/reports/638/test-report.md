# Test Report — Issues #638, #650, #651

## Pytest Run

```
cd Aletheia-638
poetry run pytest tests/unit/ -q
```

**Result:** `830 passed, 13 warnings in 5.79s` — zero failures.

Baseline after PR #636 was 827; this PR adds 3 new privacy tests = 830.

## New Tests

`tests/unit/test_lambda_handler.py::TestLambdaFunctionExceptionTextDoesNotLeak`:

| Test | Asserts |
|---|---|
| `test_etymology_exception_not_in_response_gem` | Canary absent from response body (recursive walk) AND log output; `ETYMOLOGY_GENERATION_ERROR` + class name present in log |
| `test_etymology_exception_class_name_preserved_in_gem` | Class name (e.g. `RuntimeError`) appears in gem field; canary absent |
| `test_unhandled_exception_log_does_not_leak` | Catch-all logger preserves class name without leaking message text |

## Updated Test

`tests/unit/test_persistence.py:278` — `test_020_generation_failure_still_saves`

Previously asserted `"Bedrock timeout" in response_data["gem"]` (codifying the leak). Now asserts the inverse plus the new prefix + class-name presence.

## ESLint

Unchanged from baseline — no JS files modified.

## Conclusion

Safe to merge. Pending operator sign-off (or auto-deploy under the audit-umbrella authorization), `provision.sh` + smoke test follow.
