# 0014 - Cost Architecture

## 1. Overview

This document defines Aletheia's cost model, budget controls, and optimization strategies for AWS services.

**Status:** Active (2026-01-04)
**Related Issues:** #137 (Lambda Latency), #95 (WAF/CloudFront)

---

## 2. Cost Model

### 2.1 Service Breakdown

```
┌─────────────────────────────────────────────────────────────┐
│                 Cost per Request Flow                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User Request                                               │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────┐                                           │
│  │ CloudFront  │  $0.0085 / 10K requests (US)              │
│  │ + WAF       │  $0.60 / 1M requests                      │
│  └──────┬──────┘                                           │
│         ▼                                                   │
│  ┌─────────────┐                                           │
│  │   Lambda    │  $0.20 / 1M requests                      │
│  │             │  $0.0000166667 / GB-second                │
│  └──────┬──────┘                                           │
│         │                                                   │
│    ┌────┴────┐                                             │
│    ▼         ▼                                             │
│ ┌──────┐ ┌──────────┐                                      │
│ │ DDB  │ │ Bedrock  │                                      │
│ │      │ │ (Sonnet) │                                      │
│ └──────┘ └──────────┘                                      │
│ $1.25/M  $0.003/1K   $0.015/1K                             │
│ writes   input tok   output tok                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Per-Service Pricing (us-east-1)

| Service | Metric | Price | Free Tier |
|---------|--------|-------|-----------|
| **Lambda** | Requests | $0.20 / 1M | 1M/month |
| **Lambda** | Duration | $0.0000166667 / GB-sec | 400K GB-sec/month |
| **DynamoDB** | Write | $1.25 / 1M WCU | 25 WCU/month |
| **DynamoDB** | Read | $0.25 / 1M RCU | 25 RCU/month |
| **DynamoDB** | Storage | $0.25 / GB/month | 25 GB |
| **Bedrock (Claude Sonnet)** | Input | $0.003 / 1K tokens | None |
| **Bedrock (Claude Sonnet)** | Output | $0.015 / 1K tokens | None |
| **Bedrock (Claude Haiku)** | Input | $0.00025 / 1K tokens | None |
| **Bedrock (Claude Haiku)** | Output | $0.00125 / 1K tokens | None |
| **CloudFront** | Requests | $0.0085 / 10K (US) | 10M/month (first year) |
| **CloudFront** | Data Out | $0.085 / GB (US) | 1 TB/month (first year) |
| **WAF** | Requests | $0.60 / 1M | None |
| **WAF** | Web ACL | $5.00 / month | None |
| **WAF** | Rules | $1.00 / rule/month | None |

### 2.3 Cost Per Request Estimate

**Typical "Explain Word" Request:**

| Component | Calculation | Cost |
|-----------|-------------|------|
| CloudFront | 1 request | $0.00000085 |
| WAF | 1 request | $0.0000006 |
| Lambda | 1 req + 5s × 256MB | $0.0000021 |
| DynamoDB | 1 write (1KB) | $0.00000125 |
| Bedrock (Semantic) | 500 input + 100 output tokens (Haiku) | $0.00025 |
| Bedrock (Generation) | 1000 input + 500 output tokens (Sonnet) | $0.0105 |
| **Total** | | **~$0.011** |

**Key Insight:** Bedrock dominates cost at ~95% of per-request spend. Lambda/DynamoDB are negligible.

---

## 3. Cost Scenarios

### 3.1 Development (Current)

| Metric | Value | Monthly Cost |
|--------|-------|--------------|
| Requests | ~100 | ~$1.10 |
| Lambda ON time | ~10 hours | $0.00 (free tier) |
| DynamoDB storage | <1 GB | $0.00 (free tier) |
| WAF | Active | $5.00 + rules |
| **Total** | | **~$7-10** |

### 3.2 MVP Launch (Projected)

| Metric | Value | Monthly Cost |
|--------|-------|--------------|
| Daily Active Users | 100 | |
| Requests/user/day | 5 | |
| Monthly requests | 15,000 | |
| Bedrock cost | 15K × $0.011 | $165 |
| Lambda | Free tier | $0.00 |
| DynamoDB | Free tier | $0.00 |
| WAF | Fixed | $7.00 |
| CloudFront | Free tier (year 1) | $0.00 |
| **Total** | | **~$175** |

### 3.3 Growth (1000 DAU)

| Metric | Value | Monthly Cost |
|--------|-------|--------------|
| Monthly requests | 150,000 | |
| Bedrock cost | 150K × $0.011 | $1,650 |
| Lambda | Exceeds free tier | ~$30 |
| DynamoDB | Exceeds free tier | ~$20 |
| WAF | Fixed | $7.00 |
| CloudFront | ~$15 | $15 |
| **Total** | | **~$1,720** |

**Break-even analysis:** At $0.011/request, need ~$0.02/request revenue to be sustainable (ads, premium tier, or usage limits for free tier).

---

## 4. Budget Controls

### 4.1 AWS Budgets Setup

```bash
# Create monthly budget alert
aws budgets create-budget \
  --account-id $(aws sts get-caller-identity --query Account --output text) \
  --budget '{
    "BudgetName": "Aletheia-Monthly",
    "BudgetLimit": {"Amount": "50", "Unit": "USD"},
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }' \
  --notifications-with-subscribers '[{
    "Notification": {
      "NotificationType": "ACTUAL",
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 80,
      "ThresholdType": "PERCENTAGE"
    },
    "Subscribers": [{
      "SubscriptionType": "EMAIL",
      "Address": "your-email@example.com"
    }]
  }]'
```

### 4.2 Alert Thresholds

| Threshold | Action |
|-----------|--------|
| 50% of budget | Email notification |
| 80% of budget | Email + investigate |
| 100% of budget | Email + disable Lambda |
| 120% of budget | Emergency: Lambda OFF, investigate abuse |

### 4.3 Lambda Kill Switch

**Immediate cost stop:**
```bash
# Disable Lambda (zero concurrency = zero invocations = zero Bedrock calls)
./tools/aws/lambda-off.sh
```

This is the nuclear option but effective. Bedrock has no direct kill switch, but Lambda concurrency=0 prevents any requests from reaching Bedrock.

---

## 5. Cost Optimization Strategies

### 5.1 Implemented

| Strategy | Implementation | Savings |
|----------|----------------|---------|
| Lambda concurrency control | `tools/aws/lambda-*.sh` | 100% when OFF |
| Naked Python (no deps) | ADR 0211 | Faster cold start, lower duration |
| WAF rate limiting | #95 | Prevents abuse spikes |
| Haiku for semantic check | `semantic.py` | 90% vs Sonnet for guard |

### 5.2 Planned

| Strategy | Issue | Potential Savings |
|----------|-------|-------------------|
| Response caching | TBD | 50%+ for repeated terms |
| Token limit tuning | #137 | 20-30% on generation |
| Batch inference | TBD | Bedrock batch pricing |
| Reserved capacity | TBD | ~30% with commitment |

### 5.3 Optimization Decision Matrix

| Optimization | Effort | Savings | Priority |
|--------------|--------|---------|----------|
| Reduce max_tokens | Low | 10-20% | **High** |
| Cache common terms | Medium | 30-50% | **High** |
| Use Haiku for more tasks | Low | 50-80% | Medium |
| Implement user quotas | Medium | Prevents abuse | **High** |
| Provisioned concurrency | Low | -$$ (costs more) | Don't |

---

## 6. Issue #137: Latency vs Cost Analysis

### 6.1 Current State

5-second response time with breakdown unknown. Hypotheses:

| Component | Hypothesis | Cost Impact |
|-----------|------------|-------------|
| Cold start | Lambda container spin-up | Duration cost |
| Semantic guard | Haiku call before generation | +$0.00025/req |
| DynamoDB | Write in critical path | Negligible |
| Bedrock | Model inference | Dominates |

### 6.2 Investigation Plan

```python
# Add timing instrumentation to lambda_function.py
import time

def lambda_handler(event, context):
    timings = {}

    t0 = time.time()
    # ... validation ...
    timings['validation'] = time.time() - t0

    t1 = time.time()
    # ... denylist check ...
    timings['denylist'] = time.time() - t1

    t2 = time.time()
    # ... semantic guard (Haiku) ...
    timings['semantic'] = time.time() - t2

    t3 = time.time()
    # ... DynamoDB write ...
    timings['dynamodb'] = time.time() - t3

    t4 = time.time()
    # ... Bedrock generation (Sonnet) ...
    timings['bedrock'] = time.time() - t4

    # Log timings
    print(f"TIMING: {json.dumps(timings)}")
```

### 6.3 Optimization Options

| Option | Latency Impact | Cost Impact |
|--------|----------------|-------------|
| Provisioned concurrency | -2s (no cold start) | +$15/month |
| Async DynamoDB write | -0.1s | None |
| Skip semantic on allowlisted terms | -1s | -$0.00025/req |
| Reduce max_tokens | Minimal | -10-20% |
| Stream response earlier | Perceived -2s | None |

**Recommendation:** Start with instrumentation, then async DynamoDB, then streaming. Provisioned concurrency is expensive for current volume.

---

## 7. Abuse Prevention (Cost Protection)

### 7.1 Current Controls

| Control | Implementation | Protection |
|---------|----------------|------------|
| WAF rate limit | 100 req/5min/IP | Prevents flooding |
| Allowlist gate | Must enable per-site | Reduces casual abuse |
| No anonymous API | Extension-only access | No direct API abuse |

### 7.2 Future Controls (Post-MVP)

| Control | Issue | Protection |
|---------|-------|------------|
| Per-user quotas | #117 | 50 req/day free tier |
| LinkedIn auth | #116 | Identity verification |
| Request signing | TBD | Prevents replay attacks |

### 7.3 Abuse Response Playbook

**Symptoms of abuse:**
- Sudden cost spike (>2x normal)
- High request volume from single IP
- Repeated identical requests

**Response:**
1. Check CloudWatch metrics for request patterns
2. Check WAF logs for blocked requests
3. If attack in progress: `./tools/aws/lambda-off.sh`
4. Analyze, add WAF rules, re-enable

---

## 8. Monitoring & Alerts

### 8.1 CloudWatch Metrics to Watch

| Metric | Alarm Threshold | Action |
|--------|-----------------|--------|
| Lambda Invocations | >1000/hour | Investigate |
| Lambda Duration | >10s average | Check Bedrock |
| Lambda Errors | >5% | Investigate |
| DynamoDB ConsumedWCU | >100/hour | Check for abuse |
| Bedrock TokenCount | >100K/day | Budget review |

### 8.2 Cost Explorer Tags

```bash
# Tag all Aletheia resources for cost tracking
aws lambda tag-resource \
  --resource arn:aws:lambda:us-east-1:ACCOUNT:function:aletheia-handler \
  --tags Project=Aletheia,Environment=Production
```

Then filter Cost Explorer by `Project=Aletheia`.

---

## 9. Free Tier Maximization

### 9.1 What's Free

| Service | Free Tier | Resets |
|---------|-----------|--------|
| Lambda | 1M requests + 400K GB-sec | Monthly |
| DynamoDB | 25 WCU, 25 RCU, 25 GB | Always |
| CloudFront | 10M requests, 1 TB out | First 12 months |
| S3 | 5 GB, 20K GET, 2K PUT | First 12 months |

### 9.2 Staying Under Free Tier

**Lambda:** 1M requests = ~33K/day. Easily covered.
**DynamoDB:** 25 WCU = 25 writes/sec sustained. Easily covered.
**CloudFront:** 10M/month = 333K/day. Easily covered.

**Bedrock has NO free tier.** This is your only real cost.

---

## 10. Summary

### Key Takeaways

1. **Bedrock is 95% of cost.** Optimize there first.
2. **Lambda kill switch** is your emergency brake.
3. **WAF rate limiting** prevents abuse-driven cost spikes.
4. **Free tier covers** Lambda/DynamoDB/CloudFront easily.
5. **Budget alerts** are essential - set them up.

### Cost Control Checklist

- [ ] AWS Budget created with email alerts
- [ ] Lambda OFF when not testing (`./tools/aws/lambda-off.sh`)
- [ ] WAF rate limiting active (#95)
- [ ] CloudWatch alarms for anomalies
- [ ] Resources tagged for Cost Explorer
- [ ] Monthly cost review scheduled

---

## 11. References

- [AWS Lambda Pricing](https://aws.amazon.com/lambda/pricing/)
- [Amazon Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)
- [DynamoDB Pricing](https://aws.amazon.com/dynamodb/pricing/)
- [CloudFront Pricing](https://aws.amazon.com/cloudfront/pricing/)
- [AWS WAF Pricing](https://aws.amazon.com/waf/pricing/)
- Issue #137: Lambda Latency Investigation
- Issue #95: Security Hardening (WAF)
- ADR 0211: Naked Python Architecture
