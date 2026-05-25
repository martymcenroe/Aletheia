# Implementation Report — Issue #645 (audit umbrella #637)

## Scope

PR 5 of 5 — the **final PR** in the audit-umbrella #637 arc. Fixes the single exception-text leak in `src/poetic_analyzer.py:333`.

## Change

`src/poetic_analyzer.py:333`:

```python
# Before
logger.error(f"Poetic analysis failed: {type(e).__name__}: {e}")

# After
logger.error(f"POETIC_ANALYSIS_ERROR: {e.__class__.__name__}")
```

The class name prefix was already present; only the trailing `{e}` interpolation is removed. Bedrock invocation errors can carry request-payload echoes.

## Deploy Disposition

`poetry_analyzer` IS imported by `src/etymologist.py` and `src/lambda_function.py` — so it IS in the `AletheiaAgent` Lambda's reach graph. `provision.sh` deploy required after merge.

## Test Updates

### New: `TestPoeticAnalyzerExceptionTextDoesNotLeak` (1 test)

| Test | Asserts |
|---|---|
| `test_bedrock_exception_text_not_in_log` | Canary absent from log; `POETIC_ANALYSIS_ERROR` + class name present; result returns error status |

## Resolves

- #645 (M8, MEDIUM)

This is the **14th of 14** surfaces resolved. After this PR + deploy + re-audit confirms clean, the audit umbrella #637 can close.

## Blast Radius

Code-only deploy via `provision.sh`. `AletheiaAgent` Lambda repackages. Rollback: previous zip.
