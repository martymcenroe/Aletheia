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
| Service worker activation | < 100ms | | |
| Popup load time | < 200ms | | |
| Content script injection | < 50ms | | |
| Overlay render | < 100ms | | |

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
| Lambda cold start | < 500ms | | |
| Warm invocation | < 100ms | | |

### Bedrock Latency

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Haiku response (P50) | < 2s | | |
| Haiku response (P95) | < 5s | | |
| Total E2E latency | < 3s | | |

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
| | | | |

---

## 8. References

- [Lambda Performance Optimization](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [Chrome Extension Performance](https://developer.chrome.com/docs/extensions/develop/migrate/improve-security)
- docs/0014-cost-architecture.md
