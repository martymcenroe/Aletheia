# Implementation Report: #245 - Tool Integrity Verification in CI

## Summary

Added output verification to CI jobs to detect silent tool failures. Tools that crash or fail to process files now trigger explicit errors instead of being treated as "passed".

## Problem

From 0813 Code Quality Audit (2026-01-08):
> ESLint security plugins were declared but never installed. ESLint crashed with ERR_MODULE_NOT_FOUND. The audit noted 'NPM unmet dependencies' as MEDIUM priority without realizing this meant zero security linting.

A crashed tool produces no output. No output looks like "passed". This is invisible failure.

## Solution

Added explicit output verification after each tool run:

### Python Tools (`test` job)

| Tool | Verification Pattern | Failure Detection |
|------|---------------------|-------------------|
| **Ruff** | "All checks passed" or file count | No recognizable output = fail |
| **Mypy** | "Success" or "Found N error" | No recognizable output = fail |
| **Pytest** | "collected N items" with N > 0 | 0 tests collected = fail |

### JavaScript Tools (`extension-lint` job)

| Tool | Verification Pattern | Failure Detection |
|------|---------------------|-------------------|
| **ESLint** | File paths or "N problems" | No recognizable output = fail |
| **web-ext lint** | "Validation" or "linting" | No recognizable output = fail |

## Changes

### File Modified

| File | Change |
|------|--------|
| `.github/workflows/ci.yml` | Added output verification to 6 tool steps |

### Verification Pattern

```bash
# Capture output
TOOL_COMMAND 2>&1 | tee output.txt
EXIT_CODE=${PIPESTATUS[0]}

# Verify tool actually ran
if grep -qE "expected_pattern" output.txt; then
  echo "✓ Tool processed files"
else
  echo "✗ ERROR: Tool produced no recognizable output"
  exit 1
fi

# Preserve original exit code
exit $EXIT_CODE
```

## Acceptance Criteria

- [x] CI job verifies ESLint actually ran (check for expected output pattern)
- [x] CI job verifies pytest collected > 0 test items
- [x] CI job verifies ruff processed files (not empty run)
- [x] Fail-loud if any tool appears broken
- [x] No silent failures treated as pass
