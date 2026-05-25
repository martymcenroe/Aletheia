# Test Report — Issue #645

## Pytest Run

```
cd Aletheia-645
poetry run pytest tests/unit/ -q
```

**Result:** `840 passed, 13 warnings in 10.45s` — zero failures.

Baseline after PR #655 was 839; this PR adds 1 new privacy test = 840.

## New Test

`tests/unit/test_poetic_analyzer.py::TestPoeticAnalyzerExceptionTextDoesNotLeak::test_bedrock_exception_text_not_in_log` — canary string asserts: canary absent from log, `POETIC_ANALYSIS_ERROR` + class name present in log, error fallback returned.

## ESLint / mypy / ruff

All pass (pre-commit gate).

## Conclusion

Safe to merge. Then `provision.sh` (poetic_analyzer is in AletheiaAgent's reach graph) + smoke test. After deploy lands, all 14 audit-identified surfaces will be resolved; re-audit can then confirm clean state and umbrella #637 can close.
