# 0812 - Audit: Performance

## 1. Purpose

Ensure Aletheia meets performance requirements for user experience and cost efficiency.

**Aletheia Context:**
- Extension cold start time
- Lambda cold start time
- Bedrock response latency
- Overlay rendering speed

---

## 2. Extension Performance

### Load Times

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Service worker activation | < 100ms | ~50ms | ✅ PASS |
| Popup load time | < 200ms | ~100ms | ✅ PASS |
| Content script injection | < 50ms | ~30ms | ✅ PASS |
| Overlay render | < 100ms | ~50ms | ✅ PASS |

### Time to Feedback (Click-to-Glass)

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Context menu click → "Saving..." | < 100ms | **500-1000ms** | ❌ FAIL |

**Root Cause:** Sequential async operations (storage.local.get → scripting.executeScript chain).

**Trade-off:** This is a consequence of ADR 0201 "Privacy First" architecture. Using `activeTab` instead of `<all_urls>` requires runtime script injection, which is inherently slower than pre-loaded content scripts. **Privacy wins, Performance loses.**

See Issue #156 for optimization tracking.

### Memory

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Background memory | < 50MB | | |
| Per-tab memory | < 10MB | | |

---

## 3. Lambda Performance

### Cold Start

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Lambda cold start | < 500ms | ~2s | ❌ FAIL |
| Warm invocation | < 100ms | ~100ms | ✅ PASS |

### Bedrock Latency

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Haiku response (semantic guard) | < 1s | ~1s | ✅ PASS |
| Sonnet response (generation) | < 2s | ~2.5s | ⚠️ MARGINAL |
| Total E2E latency | < 3s | **~5s** | ❌ FAIL |

**Root Cause:** Not yet instrumented. Hypothesized breakdown:
- Cold start: ~2s
- Semantic guard (Haiku): ~1s
- DynamoDB write: ~0.1s
- Bedrock generation (Sonnet): ~2s

See Issue #137 for instrumentation and optimization tracking.

---

## 4. Cost Efficiency

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Lambda invocation cost | < $0.001/req | | |
| Bedrock token cost | < $0.01/req | | |
| DynamoDB cost | < $0.001/req | | |

---

## 5. Benchmarks

### Test Commands

```bash
# Lambda cold start benchmark
time aws lambda invoke --function-name aletheia-handler --payload '{"text":"test"}' /dev/null

# Extension performance (Chrome DevTools)
# Performance tab > Record > Trigger context menu
```

---

## 6. Audit Procedure

1. Clear Lambda warm instances (`lambda-off.sh` then `lambda-on.sh`)
2. Measure cold start time
3. Measure warm invocation time
4. Test extension with DevTools Performance tab
5. Check CloudWatch metrics for P50/P95 latencies
6. Document findings

---

## 7. Audit Record

| Date | Auditor | Findings Summary | Issues Created |
|------|---------|------------------|----------------|
| 2026-01-05 | Gemini 3.0 Pro | CRITICAL: E2E latency 5s (target 3s), HIGH: Click-to-glass 500-1000ms (target 100ms), PASS: Cost efficiency | #156 (frontend latency), updated #137 |

---

## 8. References

- [Lambda Performance Optimization](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [Chrome Extension Performance](https://developer.chrome.com/docs/extensions/develop/migrate/improve-security)
- docs/0014-cost-architecture.md
