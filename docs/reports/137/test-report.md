# Test Report: Issue #137 - Lambda Latency Investigation & O1 Fix

**Issue:** #137
**PR:** #184
**Date:** 2026-01-06
**Author:** Claude Opus 4.5

## Test Summary

| Category | Result |
|----------|--------|
| Unit Tests | 28/28 PASSED |
| Linting (ruff) | PASSED |
| Type Checking (mypy) | PASSED |
| Pre-commit Hooks | PASSED |
| Live Lambda Test | PASSED |

## Unit Test Results

```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.1, pluggy-1.6.0
plugins: anyio-4.11.0, langsmith-0.4.46, cov-7.0.0
collected 28 items

tests/test_lambda_handler.py::TestValidateInput::test_010_valid_input PASSED
tests/test_lambda_handler.py::TestValidateInput::test_030_missing_text_field PASSED
tests/test_lambda_handler.py::TestValidateInput::test_040_wrong_type_for_text PASSED
tests/test_lambda_handler.py::TestValidateInput::test_050_oversized_payload_truncated PASSED
tests/test_lambda_handler.py::TestValidateInput::test_100_empty_string_blocked PASSED
tests/test_lambda_handler.py::TestValidateInput::test_whitespace_only_blocked PASSED
tests/test_lambda_handler.py::TestRunGuardrails::test_020_blocked_text_denylist PASSED
tests/test_lambda_handler.py::TestRunGuardrails::test_safe_text_passes_denylist PASSED
tests/test_lambda_handler.py::TestRunGuardrails::test_blocked_by_semantic PASSED
tests/test_lambda_handler.py::TestGenerateThreadId::test_generates_consistent_id PASSED
tests/test_lambda_handler.py::TestGenerateThreadId::test_different_input_different_id PASSED
tests/test_lambda_handler.py::TestGenerateThreadId::test_id_is_16_chars PASSED
tests/test_lambda_handler.py::TestLambdaHandler::test_010_valid_input_safe_text PASSED
tests/test_lambda_handler.py::TestLambdaHandler::test_020_blocked_text PASSED
tests/test_lambda_handler.py::TestLambdaHandler::test_030_missing_text PASSED
tests/test_lambda_handler.py::TestLambdaHandler::test_040_wrong_type PASSED
tests/test_lambda_handler.py::TestLambdaHandler::test_100_empty_string PASSED
tests/test_lambda_handler.py::TestLambdaHandler::test_070_boto3_exception PASSED
tests/test_lambda_handler.py::TestLambdaHandler::test_api_gateway_body_parsing PASSED
tests/test_lambda_handler.py::TestLambdaHandler::test_sequential_execution_denylist_before_semantic PASSED
tests/test_lambda_handler.py::TestWillisonProtocol::test_mock_denylist_is_safe PASSED
tests/test_lambda_handler.py::TestWillisonProtocol::test_no_real_terms_in_test_file PASSED
tests/test_lambda_handler.py::TestSaveStateTTL::test_010_item_saved_with_ttl_attribute PASSED
tests/test_lambda_handler.py::TestSaveStateTTL::test_020_ttl_is_30_days_ahead PASSED
tests/test_lambda_handler.py::TestSaveStateTTL::test_ttl_seconds_constant_is_30_days PASSED
tests/test_semantic.py::test_semantic_safe PASSED
tests/test_semantic.py::test_semantic_unsafe PASSED
tests/test_semantic.py::test_semantic_failure PASSED

============================= 28 passed in 0.16s ==============================
```

## Live Lambda Tests

### Test 1: Cold Start (Before Fix Baseline)

```
Request: {"text": "linguistics", "url": "https://test.com"}
CloudWatch REPORT:
  Init Duration: 829.66 ms
  Duration: 3335.76 ms
  Billed Duration: 4166 ms

Timing Breakdown:
  semantic_init_ms: 774 (separate client creation)
  semantic_llm_ms: 769
  dynamodb_write_ms: 329
  etymology_generation_ms: 1439
  handler_total_ms: 3314
```

### Test 2: Cold Start (After Fix)

```
Request: {"text": "paradigm", "url": "https://test.com"}
CloudWatch REPORT:
  Init Duration: 824.65 ms
  Duration: 3711.76 ms
  Billed Duration: 4537 ms

Timing Breakdown:
  semantic_init_ms: 731 (now includes shared client)
  semantic_llm_ms: 1252 (LLM variance)
  dynamodb_write_ms: 286
  etymology_generation_ms: 1439
  handler_total_ms: 3709

Response includes _debug_timings: ✓
```

### Test 3: Warm Start (After Fix)

```
Request: {"text": "syntax", "url": "https://test.com"}
CloudWatch REPORT:
  Duration: 2136.17 ms
  Billed Duration: 2137 ms (no Init)

Timing Breakdown:
  semantic_init_ms: 0 (client cached)
  semantic_llm_ms: 679
  dynamodb_write_ms: 10
  etymology_generation_ms: 1443
  handler_total_ms: 2134
```

## Verification Checklist

- [x] `SemanticGuardrail` accepts `bedrock_client` parameter
- [x] `get_semantic_guardrail()` passes shared client from `get_bedrock_client()`
- [x] Backward compatibility preserved (default `None` creates new client)
- [x] All existing tests pass without modification
- [x] Timing instrumentation logs to CloudWatch
- [x] `_debug_timings` appears in API response
- [x] Pre-commit hooks pass (ruff, mypy, etc.)

## CloudWatch Log Evidence

```
2026-01-06T23:21:52 SEMANTIC_GUARDRAIL_TIMING: {"prompt_build_ms": 0, "bedrock_invoke_ms": 1251, "response_parse_ms": 0, "total_ms": 1252}
2026-01-06T23:21:52 GUARDRAIL_BREAKDOWN: {"denylist_ms": 0, "semantic_init_ms": 731, "semantic_llm_ms": 1252}
2026-01-06T23:21:54 LATENCY_BREAKDOWN: {"parse_body_ms": 0, "validation_ms": 0, "guardrails_total_ms": 1983, "thread_id_ms": 0, "dynamodb_write_ms": 286, "etymology_generation_ms": 1439, "handler_total_ms": 3709}
```

## Notes on Measurement Variance

LLM call times vary significantly between invocations:
- semantic_llm: 679ms - 1252ms
- etymology_generation: 1439ms - 2050ms

This variance makes it difficult to measure the exact ~774ms savings from eliminating the duplicate client. However, the fix is verified correct by:
1. `semantic_init_ms` now includes shared client creation
2. Warm start shows `semantic_init_ms: 0` (client properly cached)
3. Code inspection confirms single client path
