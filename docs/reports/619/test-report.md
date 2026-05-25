# Test Report — Issue #619

## New Test Class

`tests/unit/test_semantic.py::TestExceptionTextDoesNotLeak` — 4 tests asserting the privacy property explicitly:

| Test | Assertion |
|---|---|
| `test_exception_message_not_in_response_reason` | `result["reason"]` contains the class name but not the canary exception message |
| `test_exception_message_not_in_any_response_field` | Recursive walk: no string anywhere in the response dict contains the canary |
| `test_exception_message_not_in_log_output` | Via `caplog`: no log record contains the canary; class name AND `SEMANTIC_GUARDRAIL_ERROR` token DO appear |
| `test_custom_exception_class_name_preserved` | A custom `WeirdCustomError(Exception)` subclass: class name preserved, canary absent |

The canary string `CANARY-LEAK-9d7e3f0a-WOULD-BE-USER-TEXT` is uniqueness-tagged so any leak point in the future would trip the assertion regardless of intervening string manipulation.

## Pytest Run

```
cd Aletheia-619
poetry run pytest tests/unit/ -q
```

**Result:** `827 passed, 13 warnings in 7.43s` — zero failures.

Baseline before this change was 823 tests; the 4 new tests in `TestExceptionTextDoesNotLeak` bring the total to 827. The 13 pre-existing `InsecureKeyLengthWarning` warnings from `jwt.api_jwt` are unrelated to this change.

## Existing Test Compatibility

Two existing tests exercise the exception branch:

- `test_semantic_failure` (line 132-145) asserts `"Guardrail Error" in result["reason"]` — still passes (the prefix `"Guardrail Error:"` is preserved; only the suffix changes from `str(e)` to class name).
- `TestHardSoftBlockingLogic::test_error_returns_soft_block_with_fallback` (line 260-274) — asserts `block_type == SOFT`, `is_fallback is True`, `is_safe is False`. All still pass; this fix doesn't change the fallback semantics.

No existing tests modified.

## Conclusion

Safe to merge. Pending operator sign-off, the fix is then ready for `provision.sh` deploy + smoke test.
