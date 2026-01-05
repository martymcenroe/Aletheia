# 1137 - Investigation: 5-Second Lambda Latency

## 1. Context & Goal
* **Issue:** #137
* **Objective:** Investigate and resolve the ~5 second Lambda response time.
* **Status:** Draft
* **Related Issues:** #156 (extension latency - different), #161 (benchmarks)

### Open Questions
*Questions that need clarification before or during implementation. Remove when resolved.*

- [ ] What's the current measured latency breakdown? (Cold start vs Bedrock API vs DynamoDB vs guardrails)
- [ ] Is this cold start latency only, or also warm Lambda?
- [ ] Has CloudWatch X-Ray tracing been enabled to identify bottlenecks?
- [ ] What's the Lambda memory allocation? Would increasing it help?
- [ ] Is Bedrock API itself slow, or is it our invocation pattern?
- [ ] Are semantic guardrails (denylist check) contributing significant time?

## 2. Requirements

1. Identify root cause of 5-second latency
2. Document findings with evidence
3. Propose remediation plan
4. Target: <2 second total response time (or document why not achievable)

## 3. Alternatives Considered

N/A - Investigation phase; alternatives will emerge from findings.

## 4. Data & Fixtures

### 4.1 Data Sources

| Attribute | Value |
|-----------|-------|
| Source | CloudWatch Logs, X-Ray traces |
| Format | Log entries, trace data |
| Analysis | Timing breakdown |

## 5. Diagram

### Suspected Latency Contributors

```mermaid
flowchart LR
    A[Request] --> B[Cold Start?]
    B --> C[Load Dependencies]
    C --> D[Guardrails Check]
    D --> E[Bedrock API Call]
    E --> F[DynamoDB Write]
    F --> G[Response]

    style B fill:#ff9999
    style E fill:#ff9999
    Note1[Suspected bottlenecks in red]
```

## 6. Technical Approach

### Phase 1: Measurement

* **Module:** CloudWatch, X-Ray
* **Tools:** AWS Console, CLI

```bash
# Enable X-Ray tracing (if not already)
aws lambda update-function-configuration \
    --function-name AletheiaLambda \
    --tracing-config Mode=Active

# Check recent invocation durations
aws logs filter-log-events \
    --log-group-name /aws/lambda/AletheiaLambda \
    --filter-pattern "REPORT" \
    --limit 20
```

### Phase 2: Analysis

Break down timing:
1. **Cold Start:** Compare first invocation vs subsequent
2. **Bedrock API:** Time the `invoke_model` call specifically
3. **DynamoDB:** Time `put_item` call
4. **Guardrails:** Time denylist check

```python
# Add timing instrumentation
import time

def lambda_handler(event, context):
    timings = {}

    start = time.time()
    # ... guardrails check ...
    timings['guardrails'] = time.time() - start

    start = time.time()
    # ... bedrock call ...
    timings['bedrock'] = time.time() - start

    start = time.time()
    # ... dynamodb write ...
    timings['dynamodb'] = time.time() - start

    print(f"Timings: {timings}")
```

### Phase 3: Remediation (Based on Findings)

| Finding | Remediation |
|---------|-------------|
| Cold start | Provisioned concurrency |
| Bedrock slow | Check model, streaming response |
| DynamoDB slow | Check capacity mode |
| Dependencies slow | Layer optimization |

## 7. Interface Specification

N/A - Investigation, no new interfaces.

## 8. Security Considerations

| Concern | Mitigation | Status |
|---------|------------|--------|
| Timing data in logs | Don't log sensitive content | TODO |

**Fail Mode:** N/A

## 9. Performance Considerations

This IS the performance investigation.

**Target Metrics:**
| Metric | Current | Target |
|--------|---------|--------|
| Total latency | ~5000ms | <2000ms |
| Cold start | Unknown | <500ms |
| Bedrock API | Unknown | <1500ms |

## 10. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Bedrock API is inherently slow | High | Med | Consider caching, streaming |
| Provisioned concurrency cost | Med | Med | Calculate ROI |
| Issue is client-side, not Lambda | Med | Low | Measure E2E vs Lambda-only |

## 11. Verification & Testing

### 11.1 Test Scenarios

| ID | Scenario | Type | Input | Expected Output | Pass Criteria |
|----|----------|------|-------|-----------------|---------------|
| 010 | Measure cold start | Manual | Fresh Lambda | Timing data | Baseline established |
| 020 | Measure warm Lambda | Manual | Repeat request | Timing data | Compare to cold |
| 030 | X-Ray trace analysis | Manual | Enable tracing | Trace segments | Bottleneck identified |

### 11.2 Test Commands

```bash
# Invoke and measure
time aws lambda invoke \
    --function-name AletheiaLambda \
    --payload '{"text":"test","url":"https://example.com"}' \
    response.json

# Check X-Ray traces
aws xray get-trace-summaries \
    --start-time $(date -d '1 hour ago' +%s) \
    --end-time $(date +%s)
```

## 12. Definition of Done

### Investigation
- [ ] Timing instrumentation added
- [ ] X-Ray traces captured
- [ ] Root cause identified with evidence

### Documentation
- [ ] Findings documented in this LLD
- [ ] Remediation plan proposed

### Remediation (Separate PR)
- [ ] Fix implemented based on findings
- [ ] Latency reduced to target
- [ ] 0812 Performance Audit updated
