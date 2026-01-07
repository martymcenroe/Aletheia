# Implementation Report: Issue #137 - Lambda Latency Investigation & O1 Fix

**Issue:** #137 - Investigate 5-second Lambda latency
**PR:** #184
**Date:** 2026-01-06
**Author:** Claude Opus 4.5

## Objective

Investigate why Lambda takes ~5 seconds even with `max_tokens=10`, identify bottlenecks, and implement O1 optimization (shared boto3 client).

## Investigation Findings

### Root Causes Identified

1. **Two sequential LLM calls** (by design - semantic guardrail must block before etymology)
   - Semantic guardrail: ~769-1252ms
   - Etymology generation: ~1439-2050ms

2. **Duplicate boto3 client initialization** (O1 - FIXED)
   - SemanticGuardrail created its own bedrock-runtime client in `__init__`
   - This duplicated the client created by `get_bedrock_client()` for etymology
   - Cost: ~774ms on cold start

3. **DynamoDB in critical path** (O2 - deferred)
   - Blocking write: 47-329ms
   - Not addressed in this PR

### Timing Breakdown (Before Fix)

| Stage | Cold (ms) | Warm (ms) |
|-------|-----------|-----------|
| INIT | 830 | 0 |
| semantic_init | 774 | 0 |
| semantic_llm | 769 | 1123 |
| dynamodb_write | 329 | 47 |
| etymology_generation | 1439 | 2050 |
| **handler_total** | **3314** | **3221** |

## Implementation

### O1: Shared boto3 Client

**Problem:** `SemanticGuardrail.__init__()` created its own bedrock-runtime client:
```python
# Before (semantic.py:15-16)
def __init__(self, region_name: str = "us-east-1", model_id: str = "..."):
    self.client = boto3.client("bedrock-runtime", region_name=region_name)
```

**Solution:** Accept optional `bedrock_client` parameter for dependency injection:
```python
# After (semantic.py:18-25)
def __init__(
    self,
    region_name: str = "us-east-1",
    model_id: str = "anthropic.claude-3-haiku-20240307-v1:0",
    bedrock_client=None,
):
    self.client = bedrock_client or boto3.client("bedrock-runtime", region_name=region_name)
```

**Caller update:** `get_semantic_guardrail()` now passes shared client:
```python
# lambda_function.py:74-78
_semantic_guardrail = SemanticGuardrail(
    region_name=AWS_REGION,
    bedrock_client=get_bedrock_client(),
)
```

### Timing Instrumentation Added

Added comprehensive timing logs for future monitoring:

1. **LATENCY_BREAKDOWN** - All handler stages:
   - `parse_body_ms`, `validation_ms`, `guardrails_total_ms`
   - `thread_id_ms`, `dynamodb_write_ms`, `etymology_generation_ms`
   - `handler_total_ms`

2. **GUARDRAIL_BREAKDOWN** - Guardrail sub-timings:
   - `denylist_ms`, `semantic_init_ms`, `semantic_llm_ms`

3. **SEMANTIC_GUARDRAIL_TIMING** - Bedrock invoke details:
   - `prompt_build_ms`, `bedrock_invoke_ms`, `response_parse_ms`, `total_ms`

4. **Response field** - `_debug_timings` in API response for debugging

## Files Changed

| File | Changes |
|------|---------|
| `src/guardrails/semantic.py` | Added `bedrock_client` parameter, timing instrumentation |
| `src/lambda_function.py` | Pass shared client, timing instrumentation, type fix |
| `docs/0211-latency-optimization.md` | ADR documenting investigation and decisions |

## Design Decisions

1. **Sequential LLM calls kept** - By design, semantic guardrail must block unsafe content before etymology generation

2. **Model progression noted** - Current Haiku-only config is for cost management; future: Sonnet (semantic) + Opus (etymology)

3. **Caching rejected** - Low usage doesn't justify complexity

4. **O2 deferred** - Async DynamoDB is more complex; evaluate after O1 impact

## Backward Compatibility

- `bedrock_client` parameter is optional with `None` default
- If not provided, falls back to creating new client (preserves existing behavior)
- All existing tests pass without modification
