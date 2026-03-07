# Test Report — Issue #528

## New Tests Added
5 tests in `TestDisambiguation` class (`tests/unit/test_etymologist.py`):

1. `test_system_prompt_contains_disambiguation` — SYSTEM_PROMPT has DISAMBIGUATION section
2. `test_system_prompt_nova_contains_disambiguation` — SYSTEM_PROMPT_NOVA has DISAMBIGUATION section
3. `test_context_label_is_directive` — label says "use this to determine which meaning"
4. `test_context_truncated_to_2000` — 5000-char context truncated to 2000
5. `test_short_context_not_truncated` — 500-char context passes through unmodified

## Test Results

### Python Unit Tests
```
969 passed, 2 skipped, 13 warnings in 18.93s
```

### JS Unit Tests
```
1 failed (pre-existing auth test) | 366 passed | 4 skipped
```
Main branch has 2 failures — our branch is net +1 pass (no regression).

### ESLint
Both service workers pass with no errors.
