# Implementation Report — Issues #638, #650, #651 (audit umbrella #637)

## Scope

PR 1 of 5 in the audit-umbrella #637 fix arc. Applies the class-name-only pattern (established by PR #636 / close #619) to all 3 exception-text leak surfaces in `src/lambda_function.py`.

## Changes

### `src/lambda_function.py:503-512` (closes #638 + #651)

The etymology-generation `except Exception as e` block previously did:

```python
response_data = {
    "signal": "error",
    "gem": str(e),               # #638 (HIGH): exception text → response field → client
    "context": "Generation failed",
}
logger.error(f"Etymology generation failed: {e}")  # #651 (LOW): exception text → CloudWatch
```

Replaced with:

```python
error_class = e.__class__.__name__
response_data = {
    "signal": "error",
    "gem": f"Generation Error: {error_class}",
    "context": "Generation failed",
}
logger.error(f"ETYMOLOGY_GENERATION_ERROR: {error_class}")
```

### `src/lambda_function.py:760-762` (closes #650)

The catch-all unhandled-exception logger previously did:

```python
logger.error(f"CRITICAL: Unhandled exception: {type(e).__name__}: {e}")  # trailing {e} is the leak
```

Replaced with:

```python
logger.error(f"CRITICAL: Unhandled exception: {e.__class__.__name__}")
```

The class name is preserved for diagnostic value; only the trailing `{e}` interpolation is removed.

## Test Updates

### New: `TestLambdaFunctionExceptionTextDoesNotLeak` in `tests/unit/test_lambda_handler.py`

3 tests using a canary string in the raised exception:

- `test_etymology_exception_not_in_response_gem` — exception text absent from response body AND log output; `ETYMOLOGY_GENERATION_ERROR` token + class name present
- `test_etymology_exception_class_name_preserved_in_gem` — class name appears in gem field for diagnostic value
- `test_unhandled_exception_log_does_not_leak` — catch-all logger preserves class name without leaking the message text

### Updated: `tests/unit/test_persistence.py:278` (test_020_generation_failure_still_saves)

The existing test asserted `"Bedrock timeout" in response_data["gem"]` — that assertion codified the leaky behavior we just fixed. Updated to assert the privacy-preserving behavior:

```python
assert "Bedrock timeout" not in response_data["gem"]   # canary absent
assert "Generation Error" in response_data["gem"]      # prefix preserved
assert "Exception" in response_data["gem"]             # class name present
```

## Closes

- #638 (H1, HIGH)
- #650 (L13, LOW)
- #651 (L14, LOW)

Part of umbrella #637 (4 of 14 surfaces resolved; 10 remaining across the next 4 PRs).

## Blast Radius

Code change in `src/lambda_function.py` only — code-only deploy via `provision.sh`. Only `AletheiaAgent` Lambda repackages. Rollback: `aws lambda update-function-code` to previous zip.
