# Test Report — Issues #639, #640, #646, #647

## Pytest Run

```
cd Aletheia-639
poetry run pytest tests/unit/ -q
```

**Result:** `834 passed, 13 warnings in 9.03s` — zero failures.

Baseline after PR #652 was 830; this PR adds 4 new privacy tests = 834. Two existing tests were updated in place (no count change).

## New Tests

`tests/unit/test_etymologist.py::TestEtymologistExceptionTextDoesNotLeak`:

| Test | Asserts |
|---|---|
| `test_bedrock_exception_text_not_in_metadata` | Canary absent from `metadata.error`; class name IS present |
| `test_bedrock_exception_text_not_in_log` | Canary absent from log; `BEDROCK_INVOCATION_ERROR` + class name present |
| `test_opus_verifier_exception_text_not_in_metadata` | Canary absent from `metadata.opus_verifier_error`; class name IS present |
| `test_json_decode_error_does_not_log_completion_text` | Canary (embedded in malformed JSON) absent from log; `JSON_DECODE_FAILED` + `JSONDecodeError` token present |

## Updated Tests

- `test_etymologist.py::test_bedrock_exception_returns_error` — flipped from asserting `"Bedrock error" in metadata.error` (codifying leak) to asserting `metadata.error == "Exception"` (class name only).
- `test_etymologist.py::test_verifier_falls_back_on_opus_exception` — flipped same way for `opus_verifier_error`.

## ESLint / mypy / ruff

All pass (per pre-commit hooks at commit time).

## Conclusion

Safe to merge. Then `provision.sh` + smoke test, same pattern as PR #652.
