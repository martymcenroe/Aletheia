# 0211 - Lambda Latency Optimization

**Status:** Accepted (O1 implemented, O2 pending)
**Issue:** #137
**Date:** 2026-01-06

## Context

Lambda latency was observed at ~5 seconds even with `max_tokens=10`. Investigation revealed the bottleneck is **not** LLM generation time, but architectural overhead.

## Investigation Findings

### Timing Breakdown (Cold Start)

| Stage | Time (ms) | Notes |
|-------|-----------|-------|
| INIT (runtime + denylist) | 830 | Fixed overhead |
| semantic_init | 774 | Duplicate boto3 client |
| semantic_llm | 769 | **Hidden LLM call** |
| dynamodb_write | 329 | Blocking write |
| etymology_generation | 1439 | Main LLM call |
| **handler_total** | **3314** | |

### Warm Start

| Stage | Time (ms) |
|-------|-----------|
| semantic_llm | 1123 |
| dynamodb_write | 47 |
| etymology_generation | 2050 |
| **handler_total** | **3221** |

### Root Causes

1. **Two sequential LLM calls** - Semantic guardrail (~1s) + Etymology (~2s)
2. **Duplicate boto3 client** - SemanticGuardrail creates its own client
3. **DynamoDB in critical path** - Blocking write before response

## Design Decisions

### Sequential LLM Calls (KEEP)

The semantic guardrail must run before etymology to block unsafe content. This is by design - we pay ~1s latency to avoid generating responses for blocked content.

**Future model progression:**
- Semantic guardrail: Haiku → **Sonnet** (better classification)
- Etymology generation: Haiku → **Opus** (richer analysis)

Current Haiku-only configuration is for cost management during testing.

### Caching (NOT IMPLEMENTING)

Considered caching semantic results for repeated terms, but rejected:
- Low expected usage doesn't justify complexity
- Terms are often contextual (same word, different meaning)
- Cache invalidation adds maintenance burden

## Proposed Optimizations

### O1: Share boto3 Client (IMPLEMENTED)

**Problem:** SemanticGuardrail created its own bedrock-runtime client in `__init__`, duplicating the client created by `get_bedrock_client()`.

**Solution:** Inject shared client via dependency injection.

```python
# Before
semantic = SemanticGuardrail(region_name=AWS_REGION)

# After
semantic = SemanticGuardrail(bedrock_client=get_bedrock_client())
```

**Expected savings:** ~774ms cold start (eliminates duplicate client initialization)
**Actual:** Verified working - `semantic_init_ms` now includes shared client creation, etymology reuses it
**Risk:** Low (simple refactor)
**Effort:** Small

### O2: Async DynamoDB Write (CONSIDER)

**Current:** `save_state()` blocks for 47-329ms before etymology.

**Options:**
| Option | Description | Savings | Complexity |
|--------|-------------|---------|------------|
| A | Lambda extension | 329ms | High |
| B | asyncio handler | 329ms | Medium |
| C | Reorder after etymology | 0ms* | Low |

*Option C doesn't save time but unblocks etymology to start sooner if combined with parallelization.

**Recommendation:** Start with O1, evaluate O2 after measuring impact.

## Instrumentation

Branch `137-latency-investigation` contains timing instrumentation that logs:
- `LATENCY_BREAKDOWN` - Handler stage timings
- `GUARDRAIL_BREAKDOWN` - Denylist vs semantic split
- `SEMANTIC_GUARDRAIL_TIMING` - Bedrock invoke timing

Response includes `_debug_timings` field for debugging.

## References

- Issue #137: Investigate 5-second Lambda latency
- `src/lambda_function.py` - Main handler with timing
- `src/guardrails/semantic.py` - Semantic guardrail with timing
- CloudWatch logs: `/aws/lambda/AletheiaAgent`
