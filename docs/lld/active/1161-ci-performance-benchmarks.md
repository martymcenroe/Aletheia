# 1161 - Chore: Automate Performance Benchmarks in CI

## 1. Context & Goal
* **Issue:** #161
* **Objective:** Add automated performance benchmarks to CI for Lambda and extension metrics.
* **Status:** Draft
* **Related Issues:** #156 (extension latency optimization), #137 (Lambda latency investigation)

### Open Questions
*Questions that need clarification before or during implementation. Remove when resolved.*

- [ ] Should benchmarks run on every PR (slows CI) or on schedule (weekly)?
- [ ] For Lambda benchmarks, do we test against mocked Bedrock or real API? Cost implications?
- [ ] What's the baseline for regression detection? Need to establish first.
- [x] ~~Is 20% regression threshold appropriate, or should it be tighter/looser?~~ **Start with 50% or "Warn Only"**
- [ ] Should we store historical benchmark data somewhere (artifact, DB)?

### Resolved Questions (Gemini Review 2026-01-05)

1. **Q: Is 20% regression threshold appropriate?**
   **A: Start with 50% threshold or "Warn Only" mode.** CI environments (GitHub Actions) are notoriously noisy/variable in performance. A 20% threshold might trigger false alarms. Establish a reliable baseline over several weeks before tightening the threshold or blocking PRs.

## 2. Requirements

Per 0899 Meta-Audit:
1. Benchmark tests added to test suite
2. Baseline metrics documented in 0812
3. Regression detection: **Start with 50% threshold or "Warn Only"** (per Gemini review)
4. Track: Lambda cold/warm start, extension load, click-to-glass
5. Tighten threshold to 20% only after establishing reliable baseline

## 3. Alternatives Considered

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| pytest-benchmark for Lambda | Python-native, easy | Only tests Lambda locally | **Selected** for Lambda |
| Playwright metrics for extension | Integrated with E2E | Requires browser setup | **Selected** for extension |
| Dedicated benchmark workflow (weekly) | Doesn't slow PRs | Less frequent feedback | Consider for live tests |
| CloudWatch-based (production metrics) | Real data | Not pre-merge | Complement |

**Rationale:** Combination approach: pytest-benchmark for unit-level Lambda tests, Playwright for extension E2E.

## 4. Data & Fixtures

### 4.1 Metrics to Track

| Metric | Target | Source |
|--------|--------|--------|
| Lambda cold start | < 500ms | pytest-benchmark (mocked) |
| Lambda warm | < 100ms | pytest-benchmark (mocked) |
| Extension load | < 100ms | Playwright metrics |
| Click-to-glass | < 200ms | Playwright timing |

## 5. Diagram

```mermaid
flowchart TD
    A[CI Workflow] --> B{PR or Schedule?}
    B -->|PR| C[Fast benchmarks only]
    B -->|Weekly| D[Full benchmark suite]
    C --> E[pytest-benchmark Lambda mocked]
    C --> F[Playwright extension metrics]
    D --> E
    D --> F
    D --> G[Live Lambda benchmark]
    E --> H{Regression > 50%?}
    F --> H
    H -->|Yes| I[Warn or Fail CI]
    H -->|No| J[Pass + Store results]
    Note over H: Start with 50% threshold<br/>Tighten after baseline established
```

## 6. Technical Approach

* **Module:**
  - `tests/test_lambda_benchmark.py`
  - `tests/benchmark.spec.ts` (Playwright)
* **Dependencies:** pytest-benchmark, @playwright/test
* **Pattern:** Benchmark functions, compare against baseline

### Lambda Benchmark (pytest-benchmark)

```python
# tests/test_lambda_benchmark.py
import pytest
from unittest.mock import patch

def test_lambda_handler_latency(benchmark):
    """Benchmark Lambda handler with mocked Bedrock."""
    from src.lambda_function import lambda_handler

    mock_event = {
        "text": "test input",
        "url": "https://example.com",
    }

    with patch('src.lambda_function.invoke_bedrock') as mock_bedrock:
        mock_bedrock.return_value = {"response": "mocked"}

        result = benchmark(lambda_handler, mock_event, {})

    assert result['statusCode'] == 200


# Run with: pytest tests/test_lambda_benchmark.py --benchmark-only
```

### Extension Benchmark (Playwright)

```typescript
// tests/benchmark.spec.ts
import { test, expect } from '@playwright/test';

test('extension click-to-glass latency', async ({ page }) => {
  await page.goto('/test-page.html');

  const startTime = Date.now();

  // Trigger extension action
  await page.evaluate(() => {
    // Simulate context menu click or extension trigger
  });

  // Wait for overlay to appear
  await page.waitForSelector('.aletheia-overlay');

  const latency = Date.now() - startTime;

  console.log(`Click-to-glass latency: ${latency}ms`);
  expect(latency).toBeLessThan(200);  // Target from #156
});
```

## 7. Interface Specification

N/A - Test infrastructure.

## 8. Security Considerations

| Concern | Mitigation | Status |
|---------|------------|--------|
| Live benchmarks hit production | Use staging or mock | TODO |

**Fail Mode:** N/A

## 9. Performance Considerations

| Metric | Budget | Approach |
|--------|--------|----------|
| CI time increase | < 60s for fast | Mocked tests |
| CI time (weekly full) | < 5 min | Live tests scheduled |

**Bottlenecks:** Live Bedrock calls expensive; limit to scheduled runs.

## 10. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Flaky timing tests | Med | Med | Run multiple iterations, use median |
| Baseline drift | Med | Med | Document baseline, review periodically |
| CI slowdown | Med | Low | Fast mocked tests for PRs |

## 11. Verification & Testing

### 11.1 Test Scenarios

| ID | Scenario | Type | Input | Expected Output | Pass Criteria |
|----|----------|------|-------|-----------------|---------------|
| 010 | Lambda benchmark runs | Auto | pytest-benchmark | Timing recorded | No errors |
| 020 | Regression detected | Auto | Artificially slow code | CI fails | >20% triggers failure |
| 030 | Extension timing | Auto | Playwright | Latency logged | < 200ms |

### 11.2 Test Commands

```bash
# Lambda benchmarks
poetry run pytest tests/test_lambda_benchmark.py --benchmark-only

# Playwright benchmarks
npx playwright test benchmark

# Compare against baseline
poetry run pytest --benchmark-compare
```

## 12. Definition of Done

### Code
- [ ] Lambda benchmark tests created
- [ ] Playwright timing tests created
- [ ] CI workflow includes benchmark step

### Tests
- [ ] Benchmarks run without errors
- [ ] Baseline established and documented

### Documentation
- [ ] 0812 Performance Audit updated with baselines
- [ ] 0899 Meta-Audit recommendation resolved

---

## Appendix: Gemini Review Response

**Review Date:** 2026-01-05
**Reviewer:** Gemini 3 Pro

### Tier 3 Issues (SUGGESTIONS) - Addressed

| Issue | Resolution |
|-------|------------|
| CI environment flakiness | Start with 50% threshold or "Warn Only" mode for first few weeks |
| 20% threshold may cause false alarms | Tighten only after establishing reliable baseline |

**Verdict:** APPROVED - Proceed with implementation.
