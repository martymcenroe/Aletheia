# 10216 - ADR: CloudFront+WAF to CloudFlare Migration

**Status:** Implemented
**Date:** 2026-02-16
**Categories:** Security, Infrastructure, Cost Optimization

## 1. Context

Aletheia's API routing used AWS CloudFront + WAF to protect the Lambda Function URL:

```
Extension → CloudFront → WAF (2 rules) → Lambda Function URL → Lambda
```

**Problem:** WAF costs $7/month fixed (1 Web ACL @ $5 + 2 rules @ $1 each) regardless of traffic. With zero public users, this was the largest single AWS cost. The extension has been approved on both Chrome Web Store and Firefox Add-ons but not yet published — the cost model needed fixing before launch.

**Additional findings during investigation (Issue #349):**
- The Lambda Function URL was `AuthType: NONE` and publicly accessible, meaning anyone could bypass CloudFront+WAF entirely by calling Lambda directly
- No billing alerts existed — a denial-of-wallet attack could run uncapped
- CloudFront provided CDN caching for an API that should never be cached

The domain `aletheia.study` was already on CloudFlare Free (active since 2026-01-11).

## 2. Decision

**We will replace CloudFront+WAF with CloudFlare Free tier for API protection, using a CloudFlare Worker as the proxy layer, and lock Lambda to CloudFlare-only access via a shared secret header.**

## 3. Alternatives Considered

### Option A: CloudFlare Free + Worker + Shared Secret — SELECTED

**Description:** Route traffic through CloudFlare's proxy network using a Worker to forward requests to Lambda. Rate limiting at CloudFlare edge. Shared secret header to prevent direct Lambda access.

**Pros:**
- $0/month (saves $7/month)
- Unlimited DDoS protection included
- Rate limiting at edge (before request reaches AWS)
- Shared secret prevents Lambda bypass
- Custom domain (api.aletheia.study) instead of CloudFront hash

**Cons:**
- CloudFlare Worker has 100K requests/day limit on free tier
- Rate limiting constrained to 10-second windows on free tier
- Adds dependency on CloudFlare (vendor lock-in)

### Option B: Keep CloudFront+WAF — Rejected

**Description:** Maintain current architecture.

**Pros:**
- Already working
- AWS-native, single vendor

**Cons:**
- $7/month fixed cost at zero traffic ← **deciding factor**
- Lambda Function URL still publicly accessible (false sense of security)
- No billing alerts were configured

### Option C: API Gateway + Lambda — Rejected

**Description:** Replace CloudFront+WAF with API Gateway for throttling and auth.

**Pros:**
- AWS-native
- Built-in throttling, API keys, usage plans

**Cons:**
- API Gateway costs $3.50/million requests + $1/million WebSocket messages
- Adds latency (API Gateway → Lambda vs direct Function URL)
- More complex configuration

### Option D: Remove all protection — Rejected

**Description:** Let Lambda Function URL handle everything directly.

**Pros:**
- Simplest architecture
- Zero cost

**Cons:**
- No DDoS protection
- No rate limiting
- Denial-of-wallet wide open ← **unacceptable**

## 4. Rationale

CloudFlare Free provides strictly better protection than CloudFront+WAF at $0/month:

| Capability | CloudFront+WAF ($7/mo) | CloudFlare Free ($0/mo) |
|------------|------------------------|-------------------------|
| DDoS protection | Basic (CloudFront edge) | Unlimited, unmetered |
| Rate limiting | WAF rule ($1/mo) | Free (1 rule, 10s windows) |
| Client header check | WAF rule ($1/mo) | Lambda handler (~free) |
| Origin lockdown | None (Lambda public) | Shared secret header |
| Custom domain | No (d1xxx.cloudfront.net) | Yes (api.aletheia.study) |

The 100K requests/day Worker limit is ~69 requests/minute sustained — well above realistic usage for a side project. If the project grows beyond this, upgrading to Workers Paid ($5/month, 10M requests) is still cheaper than WAF.

## 5. Security Risk Analysis

| Risk | Impact | Likelihood | Severity | Mitigation |
|------|--------|------------|----------|------------|
| CloudFlare outage blocks API | Med (2) | Low (1) | 2 - Low | Lambda Function URL remains as emergency fallback. Shared secret can be temporarily disabled. |
| Attacker discovers shared secret | High (3) | Low (1) | 3 - Low | Secret stored only in env vars (CloudFlare + Lambda), never in code. 64-char random alphanumeric. Rotation requires updating 2 env vars. |
| CloudFlare Worker hits 100K/day limit | Med (2) | Low (1) | 2 - Low | At current scale, impossible. Alert at 80% usage. Upgrade path exists. |
| Rate limit too permissive (10s window) | Med (2) | Med (2) | 4 - Moderate | Backed by CloudWatch alarm (>100 invocations/5min → kill switch) and AWS Budget auto-deny at $9.50. |
| Vendor lock-in to CloudFlare | Low (1) | Med (2) | 2 - Low | Worker is 6 lines of JS. Migration to any reverse proxy trivial. Lambda code is vendor-agnostic. |

**Residual Risk:** An attacker who somehow obtains the shared secret could bypass CloudFlare and hit Lambda directly. Mitigated by: secret rotation capability, CloudWatch kill switch, AWS Budget auto-deny, account concurrency limit (10 Lambdas max).

## 6. Consequences

### Positive
- Eliminates $7/month fixed cost (largest single cost at zero traffic)
- Better DDoS protection (CloudFlare unlimited vs CloudFront basic)
- Professional custom domain (api.aletheia.study)
- Origin lockdown closes the Lambda bypass vulnerability

### Negative
- CloudFlare dependency — but trivially replaceable (6-line Worker)
- Rate limiting windows constrained to 10 seconds on free tier

### Neutral
- Extension update required to use new endpoint (not yet published, so no user impact)

## 7. Implementation

- **Related Issues:** #349 (investigation + migration), #351 (shared secret lockdown)
- **Related LLDs:** None (infrastructure change, not feature)
- **Status:** In Progress (Steps 1-5 complete, Step 6 blocked on #351)

### Defense-in-Depth Layers (deployed)

1. CloudFlare DDoS protection (edge)
2. CloudFlare rate limiting (3 req/10s per IP)
3. CloudFlare Worker shared secret (Issue #351)
4. Lambda header check (client version)
5. CloudWatch alarm → kill switch (>100 invocations/5min)
6. AWS Budget → IAM deny policy (95% of $10)
7. Account Lambda concurrency limit (10)

## 8. References

- Issue #349: WAF charges investigation
- Issue #351: Shared secret lockdown
- PR #350: Migration code changes
- `docs/runbooks/10902-runbook-cost-incident-response.md`: Cost incident response
- `docs/standards/10014-cost-architecture.md`: AWS cost model

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-02-16 | Claude Opus 4.6 | Initial draft |
