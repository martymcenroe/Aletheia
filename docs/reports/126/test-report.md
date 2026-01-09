# Test Report: Issue #126 - Hard vs. Soft Blocking Logic

## Summary

All tests pass. 7 new tests added for block type logic. 4 existing tests updated to use new return format.

## Test Results

```
218 passed in 11.59s
```

## New Tests Added

### tests/unit/test_semantic.py - TestHardSoftBlockingLogic

| ID | Test | Description | Status |
|----|------|-------------|--------|
| 010 | test_hate_category_returns_hard_block | Hate speech returns BLOCK_TYPE_HARD | PASS |
| 020 | test_archaic_category_returns_soft_block | Archaic words return BLOCK_TYPE_SOFT | PASS |
| 030 | test_provocative_category_returns_soft_block | Provocative content returns BLOCK_TYPE_SOFT | PASS |
| 040 | test_none_category_returns_no_block | Safe content returns BLOCK_TYPE_NONE | PASS |
| 050 | test_neologism_category_returns_no_block | Neologisms return BLOCK_TYPE_NONE | PASS |
| 060 | test_error_returns_soft_block_with_fallback | Errors return BLOCK_TYPE_SOFT with fallback flag | PASS |

### tests/unit/test_lambda_handler.py - TestRunGuardrails

| ID | Test | Description | Status |
|----|------|-------------|--------|
| 070 | test_archaic_returns_soft_block | Archaic words return soft block from run_guardrails | PASS |

## Tests Updated

The following tests were updated to expect the new return format `(block_type, category, metadata)` instead of `(is_safe, reason, metadata)`:

| File | Test | Change |
|------|------|--------|
| test_lambda_handler.py | test_020_blocked_text_denylist | Expects `block_type == BLOCK_TYPE_HARD` |
| test_lambda_handler.py | test_safe_text_passes_denylist | Expects `block_type == BLOCK_TYPE_NONE` |
| test_lambda_handler.py | test_blocked_by_semantic_hard | Expects `block_type == BLOCK_TYPE_HARD` |
| test_lambda_handler.py | test_010_valid_input_safe_text | Mock includes `block_type` in response |
| test_lambda_handler.py | test_070_boto3_exception | Mock includes `block_type` in response |

## Code Verification

### Verification: Block Type Constants Exported

```bash
$ grep -n "BLOCK_TYPE" src/guardrails/semantic.py
22:BLOCK_TYPE_HARD = "hard"
23:BLOCK_TYPE_SOFT = "soft"
24:BLOCK_TYPE_NONE = "none"
27:HARD_BLOCK_CATEGORIES = {"Hate"}
28:SOFT_BLOCK_CATEGORIES = {"Archaic", "Provocative"}
```
**Result:** PASS - Constants defined and exported

### Verification: Lambda Imports Block Types

```bash
$ grep -n "BLOCK_TYPE" src/lambda_function.py
29:    BLOCK_TYPE_HARD,
30:    BLOCK_TYPE_SOFT,
31:    BLOCK_TYPE_NONE,
```
**Result:** PASS - Block types imported and used

### Verification: All Pre-commit Hooks Pass

```
trim trailing whitespace.................................................Passed
fix end of files.........................................................Passed
check for added large files..............................................Passed
detect private key.......................................................Passed
ruff.....................................................................Passed
mypy.....................................................................Passed
Detect hardcoded secrets.................................................Passed
Project Policy Compliance................................................Passed
```
**Result:** PASS - All hooks pass

## Test Matrix

| Input | Denylist | Semantic | Expected Block Type | Expected HTTP |
|-------|----------|----------|---------------------|---------------|
| N-word | Match | N/A | HARD | 403 |
| "forsooth" | No match | Archaic | SOFT | 200 + warning |
| "hello" | No match | None | NONE | 200 |
| (error) | No match | Error | SOFT + fallback | 200 + warning |

## Live Verification

After deployment, the following curl commands verify behavior:

```bash
# Formal word - should pass as Clean (verified earlier in session)
curl -s -X POST https://sqrqfnypgswudwtcheeasq5xri0aryfx.lambda-url.us-east-1.on.aws/ \
  -H "Content-Type: application/json" \
  -d '{"text": "immiserate"}'
# Expected: 200 with signal="Formal Academic Term", no warning field

# True archaic - should be blocked (verified earlier in session)
curl -s -X POST https://sqrqfnypgswudwtcheeasq5xri0aryfx.lambda-url.us-east-1.on.aws/ \
  -H "Content-Type: application/json" \
  -d '{"text": "forsooth"}'
# Expected: {"blocked": "Content blocked: Archaic"}
# NOTE: Current deployment still uses old logic - will show warning after redeployment
```

## Conclusion

**Test Status:** PASS (218/218)

All unit tests pass. Implementation verified through:
1. New tests for each block type category
2. Updated tests for new return format
3. Pre-commit hooks (ruff, mypy) pass
4. Backwards compatibility via `is_safe` field

## Deployment Note

Lambda needs redeployment to activate the new hard/soft blocking logic in production. Current production still uses the pre-#126 code that returns 403 for Archaic.
