# 0014 - Cost Architecture

## 1. Overview

This document defines Aletheia's cost model, budget controls, and optimization strategies for AWS services.

**Status:** Active (2026-02-16)
**Related Issues:** #137 (Lambda Latency), #95 (WAF/CloudFront), #349 (CloudFlare Migration), #351 (Shared Secret)
**Related ADRs:** [10216](../adrs/10216-ADR-cloudflare-migration.md) (CloudFront→CloudFlare)

---

## 2. Cost Model

### 2.1 Service Breakdown

```
┌─────────────────────────────────────────────────────────────┐
│           Cost per Request Flow (2026-02-16)                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User Request                                               │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────┐                                           │
│  │ CloudFlare  │  $0 (Free tier — DDoS, rate limiting)     │
│  │  + Worker   │  $0 (100K req/day free)                   │
│  └──────┬──────┘                                           │
│         │  X-Origin-Secret header (shared secret)          │
│         ▼                                                   │
│  ┌─────────────┐                                           │
│  │   Lambda    │  $0.20 / 1M requests                      │
│  │             │  $0.0000166667 / GB-second                │
│  └──────┬──────┘                                           │
│         │                                                   │
│    ┌────┴────┐                                             │
│    ▼         ▼                                             │
│ ┌──────┐ ┌────────────┐                                    │
│ │ DDB  │ │  Bedrock   │                                    │
│ │      │ │ (Nova Micro)│                                   │
│ └──────┘ └────────────┘                                    │
│ $1.25/M  $0.000035/1K  $0.00014/1K                         │
│ writes   input tok     output tok                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Replaced: CloudFront+WAF ($7/month fixed) → CloudFlare Free ($0/month)
Replaced: Claude Sonnet → Nova Micro (2.76x faster, ~90% cheaper)
See: ADR 10216, Issue #349
```

### 2.2 Per-Service Pricing (us-east-1)

| Service | Metric | Price | Free Tier |
|---------|--------|-------|-----------|
| **Lambda** | Requests | $0.20 / 1M | 1M/month |
| **Lambda** | Duration | $0.0000166667 / GB-sec | 400K GB-sec/month |
| **DynamoDB** | Write | $1.25 / 1M WCU | 25 WCU/month |
| **DynamoDB** | Read | $0.25 / 1M RCU | 25 RCU/month |
| **DynamoDB** | Storage | $0.25 / GB/month | 25 GB |
| **Bedrock (Nova Micro)** | Input | $0.000035 / 1K tokens | None |
| **Bedrock (Nova Micro)** | Output | $0.00014 / 1K tokens | None |
| **CloudFlare** | DNS/Proxy | $0 | Free tier (unlimited) |
| **CloudFlare** | Rate Limiting | $0 | Free tier (1 rule) |
| **CloudFlare** | Workers | $0 | 100K req/day free |
| **SSM Parameter Store** | Standard params | $0 | Free (standard tier) |

**Removed services (2026-02-16):** CloudFront ($0.0085/10K req), WAF ($5/month + $0.60/1M req + $1/rule). See ADR 10216.

### 2.3 Cost Per Request Estimate

**Typical "Explain Word" Request (Post-Migration):**

| Component | Calculation | Cost |
|-----------|-------------|------|
| CloudFlare | DNS + Worker proxy | $0.00 |
| Lambda | 1 req + 2s × 256MB | $0.0000010 |
| DynamoDB | 1 write (1KB) | $0.00000125 |
| Bedrock (Semantic) | 500 input + 100 output tokens (Nova Micro) | $0.0000315 |
| Bedrock (Generation) | 1000 input + 500 output tokens (Nova Micro) | $0.000105 |
| **Total** | | **~$0.00014** |

**Key Insight:** Nova Micro + CloudFlare dropped per-request cost from ~$0.011 to ~$0.00014 — a **~79x reduction**. Bedrock is still the dominant cost but at micro-pennies, not cents.

---

## 3. Cost Scenarios

### 3.1 Development (Current — Post-Migration)

| Metric | Value | Monthly Cost |
|--------|-------|--------------|
| Requests | ~100 | ~$0.014 |
| Lambda | Free tier | $0.00 |
| DynamoDB storage | <1 GB | $0.00 (free tier) |
| CloudFlare | Free tier | $0.00 |
| SSM Parameter Store | 1 standard param | $0.00 |
| **Total** | | **~$0.01** |

**Savings vs. previous:** ~$7-10/month → ~$0.01/month (WAF+CloudFront eliminated, Nova Micro replaced Sonnet).

### 3.2 MVP Launch (Projected)

| Metric | Value | Monthly Cost |
|--------|-------|--------------|
| Daily Active Users | 100 | |
| Requests/user/day | 5 | |
| Monthly requests | 15,000 | |
| Bedrock cost | 15K × $0.00014 | $2.10 |
| Lambda | Free tier | $0.00 |
| DynamoDB | Free tier | $0.00 |
| CloudFlare | Free tier | $0.00 |
| **Total** | | **~$2.10** |

**Savings vs. previous projection:** ~$175/month → ~$2.10/month.

### 3.3 Growth (1000 DAU)

| Metric | Value | Monthly Cost |
|--------|-------|--------------|
| Monthly requests | 150,000 | |
| Bedrock cost | 150K × $0.00014 | $21 |
| Lambda | Free tier | $0.00 |
| DynamoDB | Free tier | $0.00 |
| CloudFlare | Free tier | $0.00 |
| **Total** | | **~$21** |

**Savings vs. previous projection:** ~$1,720/month → ~$21/month (~82x reduction).

**Break-even analysis:** At $0.00014/request, even 1M requests/month costs only ~$140. Revenue needs are minimal at this price point.

---

## 4. Budget Controls

### 4.1 AWS Budgets (Deployed)

**Budget:** `Aletheia-Monthly-10USD` — $10/month (was $50, reduced post-migration)

| Threshold | Alert | Action |
|-----------|-------|--------|
| 50% ($5) | Email | Investigate — something unusual at this spend level |
| 80% ($8) | Email | Investigate + review CloudWatch metrics |
| 100% ($10) | Email | Run `./tools/aws/lambda-off.sh` if abuse detected |

### 4.2 Defense-in-Depth Cost Protection (7 Layers)

| Layer | Control | Stops What |
|-------|---------|------------|
| 1 | CloudFlare DDoS (automatic) | Volumetric attacks |
| 2 | CloudFlare rate limiting (3 req/10s/IP) | Per-IP flooding |
| 3 | Shared secret header (#351) | Direct Lambda access |
| 4 | Client version header (#349) | Non-extension requests |
| 5 | CloudWatch alarm (100 invocations/5min) | Lambda kill switch |
| 6 | AWS Budget ($10/month) | Overall spend cap |
| 7 | Lambda concurrency limit | Hard invocation cap |

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
| CloudFlare Free (replaced CloudFront+WAF) | ADR 10216, #349 | $7/month fixed cost eliminated |
| Nova Micro (replaced Sonnet+Haiku) | Model swap | ~79x per-request reduction |
| Shared secret lockdown | #351 | Prevents unauthorized Bedrock calls |
| Lambda concurrency control | `tools/aws/lambda-*.sh` | 100% when OFF |
| Naked Python (no deps) | ADR 0211 | Faster cold start, lower duration |
| CloudFlare rate limiting | #349 (replaces WAF #95) | Prevents abuse spikes |
| DynamoDB TTL | #145 | Storage costs capped (auto-delete after 24-48h) |

### 5.2 Planned

| Strategy | Issue | Potential Savings |
|----------|-------|-------------------|
| Response caching | TBD | 50%+ for repeated terms |
| Token limit tuning | #137 | 20-30% on generation |
| Data hygiene cleanup | #150 | One-time storage reduction |
| Migrate Secrets Manager to env var | #349 Step 7 | $0.40/month |

### 5.3 Optimization Decision Matrix

| Optimization | Effort | Savings | Priority |
|--------------|--------|---------|----------|
| Reduce max_tokens | Low | 10-20% | Medium |
| Cache common terms | Medium | 30-50% | **High** |
| Implement user quotas | Medium | Prevents abuse | Medium |
| Provisioned concurrency | Low | -$$ (costs more) | Don't |

> **Note:** Priority has shifted — with ~79x per-request cost reduction, optimization urgency is much lower. Caching is the main remaining win.

---

## 6. Issue #137: Latency vs Cost Analysis

### 6.1 Current State

Response time ~2s with Nova Micro (was ~5s with Sonnet). Breakdown:

| Component | Hypothesis | Cost Impact |
|-----------|------------|-------------|
| Cold start | Lambda container spin-up | Duration cost |
| Semantic guard | Nova Micro call before generation | ~$0.00003/req |
| DynamoDB | Write in critical path | Negligible |
| Bedrock | Model inference (Nova Micro) | Dominates (but cheap) |

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
    # ... semantic guard (Nova Micro) ...
    timings['semantic'] = time.time() - t2

    t3 = time.time()
    # ... DynamoDB write ...
    timings['dynamodb'] = time.time() - t3

    t4 = time.time()
    # ... Bedrock generation (Nova Micro) ...
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
| CloudFlare DDoS | Automatic (free tier) | Volumetric attacks absorbed |
| CloudFlare rate limit | 3 req/10s/IP on POST / | Prevents per-IP flooding |
| Shared secret | X-Origin-Secret header (#351) | Blocks direct Lambda access |
| Client version header | X-Aletheia-Client-Version (#349) | Blocks non-extension requests |
| CloudWatch kill switch | 100 invocations/5min alarm | Auto-disable Lambda |
| Allowlist gate | Must enable per-site in extension | Reduces casual abuse |

### 7.2 Cost Impact of Attacks

| Attack Type | Reaches Lambda? | Cost per 1M requests | Protection |
|-------------|-----------------|----------------------|------------|
| DDoS (volumetric) | No | $0 | CloudFlare absorbs |
| Rate-limited IP | No (after 3 req) | $0 | CloudFlare blocks |
| Direct Lambda (no secret) | Yes, but rejected in ~10ms | ~$0.20 (invocations only) | No Bedrock call |
| Valid secret (compromised) | Yes, full processing | ~$140 | Kill switch at 100/5min |

**Key insight:** Even if an attacker bypasses CloudFlare and hammers Lambda directly, they cannot trigger Bedrock calls without the shared secret. Lambda charges ~$0.0000002/rejected request. 1M rejected requests = $0.20. Free tier covers the first 1M/month.

### 7.3 Future Controls (Post-MVP)

| Control | Issue | Protection |
|---------|-------|------------|
| Per-user quotas | #117 | 50 req/day free tier |
| LinkedIn auth | #116 | Identity verification |
| Request signing | TBD | Prevents replay attacks |

### 7.4 Abuse Response Playbook

**Symptoms of abuse:**
- Sudden cost spike (>2x normal)
- High request volume from single IP
- CloudWatch kill switch triggered

**Response:**
1. Check CloudWatch metrics for request patterns
2. Check CloudFlare analytics for blocked requests
3. If attack in progress: `./tools/aws/lambda-off.sh`
4. Analyze, add CloudFlare rules, re-enable
5. See also: [Runbook 10902](../runbooks/10902-runbook-cost-incident-response.md)

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
| CloudFlare | DNS, proxy, DDoS, Workers (100K/day) | Always (free tier) |
| SSM Parameter Store | Standard parameters | Always (free) |
| S3 | 5 GB, 20K GET, 2K PUT | First 12 months |

### 9.2 Staying Under Free Tier

**Lambda:** 1M requests = ~33K/day. Easily covered.
**DynamoDB:** 25 WCU = 25 writes/sec sustained. Easily covered.
**CloudFlare Workers:** 100K req/day = more than enough.

**Bedrock (Nova Micro) has NO free tier.** This is your only real cost — but at $0.00014/request it's negligible until thousands of daily users.

---

## 10. Summary

### Key Takeaways

1. **CloudFlare migration cut fixed costs to $0** — WAF+CloudFront ($7/month) replaced with CloudFlare Free.
2. **Nova Micro cut per-request cost by ~79x** — from ~$0.011 to ~$0.00014.
3. **Shared secret locks Lambda to CloudFlare** — attackers can't trigger Bedrock calls.
4. **7-layer defense-in-depth** protects against cost-based attacks (see §4.2).
5. **Lambda kill switch** is the emergency brake.
6. **Free tier covers** Lambda, DynamoDB, CloudFlare easily.
7. **Budget alert at $10/month** catches anomalies early.

### Cost Control Checklist

- [x] AWS Budget created (`Aletheia-Monthly-10USD`, $10/month)
- [x] Lambda ON (production - Chrome Web Store live)
- [x] CloudFlare rate limiting active (#349)
- [x] Shared secret deployed (#351)
- [x] DynamoDB TTL enabled (#145)
- [x] CloudWatch kill switch alarm (100 invocations/5min)
- [ ] Resources tagged for Cost Explorer
- [ ] Monthly cost review scheduled
- [x] Delete legacy WAF+CloudFront resources (#349 Step 6) — deleted 2026-02-16

> **Note:** Lambda kill switch (`lambda-off.sh`) is reserved for emergencies only (security incidents, budget overruns). Do not disable for routine cost control.

---

## 11. Migration History

### 11.1 CloudFront+WAF → CloudFlare (2026-02-16)

| Before | After | Savings |
|--------|-------|---------|
| CloudFront ($0.0085/10K req) | CloudFlare Free ($0) | ~$2/month at scale |
| WAF ($5/month + $1/rule + $0.60/1M) | CloudFlare rate limiting ($0) | $7/month fixed |
| Claude Sonnet ($0.003/$0.015 per 1K tokens) | Nova Micro ($0.000035/$0.00014) | ~79x per-request |
| No origin protection | Shared secret header | Prevents unauthorized Bedrock |

**Total impact:** Development cost from ~$7-10/month → ~$0.01/month. Growth (1K DAU) from ~$1,720/month → ~$21/month.

See: [ADR 10216](../adrs/10216-ADR-cloudflare-migration.md), Issues #349, #351

---

## 12. References

- [AWS Lambda Pricing](https://aws.amazon.com/lambda/pricing/)
- [Amazon Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)
- [DynamoDB Pricing](https://aws.amazon.com/dynamodb/pricing/)
- [CloudFlare Plans](https://www.cloudflare.com/plans/)
- [Runbook 10902: Cost Incident Response](../runbooks/10902-runbook-cost-incident-response.md)
- [ADR 10216: CloudFront→CloudFlare Migration](../adrs/10216-ADR-cloudflare-migration.md)
- Issue #349: CloudFlare Migration
- Issue #351: Shared Secret Header
- Issue #137: Lambda Latency Investigation
- ADR 0211: Naked Python Architecture
