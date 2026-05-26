# Test Report — Issue #668

## Pytest Run

```
cd Aletheia-668
poetry run pytest tests/unit/ -q
```

**Result:** `835 passed, 13 warnings in 6.50s` — zero failures.

## Tests Deleted

Response-checking tests that asserted canary-not-in-response. Without the revert, they passed; after the revert, they fail because `str(e)` is back. They codified a wrong interpretation of the privacy policy.

| File | Test | Reason for deletion |
|---|---|---|
| `test_semantic.py` | `test_exception_message_not_in_response_reason` | Asserts canary not in result["reason"] — `reason` now contains str(e) again |
| `test_semantic.py` | `test_exception_message_not_in_any_response_field` | Recursive walk asserts canary not in any response field |
| `test_semantic.py` | `test_custom_exception_class_name_preserved` | Asserts class name in `reason` field — irrelevant now |
| `test_etymologist.py` | `test_bedrock_exception_text_not_in_metadata` | Asserts canary not in `metadata["error"]` |
| `test_etymologist.py` | `test_opus_verifier_exception_text_not_in_metadata` | Asserts canary not in `metadata["opus_verifier_error"]` |

## Tests Kept (still pass after revert)

Log-checking tests added in the same arc. The log-side scrubbing is the correct part and stays.

| File | Test |
|---|---|
| `test_semantic.py` | `test_exception_message_not_in_log_output` |
| `test_etymologist.py` | `test_bedrock_exception_text_not_in_log` |
| `test_etymologist.py` | `test_json_decode_error_does_not_log_completion_text` |
| `test_lambda_handler.py` | `TestLambdaFunctionExceptionTextDoesNotLeak::test_unhandled_exception_log_does_not_leak` |
| `test_lambda_auth.py` | All 3 `TestAuthLambdaExceptionTextDoesNotLeak` tests (log + redirect_uri scrubbing) |
| `test_signal_inspector.py` | Both `TestFetcherExceptionTextDoesNotLeak` tests (fetcher.py not reverted) |
| `test_poetic_analyzer.py` | `test_bedrock_exception_text_not_in_log` (poetic_analyzer not reverted) |

## Tests Restored to Original Assertions

Three existing tests had been modified to codify the bad behavior. Each restored:

| File | Test | Before this PR | After this PR |
|---|---|---|---|
| `test_etymologist.py` | `test_bedrock_exception_returns_error` | `metadata.error == "Exception"` | `"Bedrock error" in metadata.error` |
| `test_etymologist.py` | `test_verifier_falls_back_on_opus_exception` | `opus_verifier_error == "Exception"` | `"Opus unavailable" in opus_verifier_error` |
| `test_persistence.py` | `test_020_generation_failure_still_saves` | `"Generation Error" in gem`, `"Bedrock timeout" not in gem` | `"Bedrock timeout" in gem` |

## ESLint / mypy / ruff

All pass (pre-commit gate).

## Conclusion

Safe to merge. After merge, `provision.sh` confirms deploy from clean main produces production-equivalent state.
