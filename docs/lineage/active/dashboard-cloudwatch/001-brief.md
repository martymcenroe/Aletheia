# Idea: CloudWatch Usage Dashboard (MVP)

**Status:** Active
**Effort:** Low-Medium (1 session)
**Value:** High
**Blocked by:** tiered-rate-limiting (need tier data to emit metrics)

---

## Problem

Once Aletheia is public, the operator needs visibility into request volume, cost, rate limit effectiveness, and system health. No dashboard exists today — the operator is flying blind.

This dashboard must conform to Aletheia's privacy policy — no individual user text content, no PII displayed, aggregate metrics only.

---

## Proposal

CloudWatch-native dashboard using custom metrics emitted from Lambda. Lowest effort path — Lambda already emits CloudWatch metrics, just needs custom ones for tier breakdown and cap utilization.

**Metrics to emit (via `PutMetricData` in auth middleware):**
- `RequestCount` — total requests, dimensioned by `Tier` (free/subscriber/admin)
- `CapUtilization` — percentage of cap consumed per window, dimensioned by `Tier` and `Window` (hourly/daily/monthly)
- `CapDenied` — requests rejected due to cap exceeded, dimensioned by `Tier`
- `BedrockCostEstimate` — estimated Bedrock API cost per request
- `ErrorRate` — 4xx/5xx responses
- `Latency` — p50/p90/p99 response times

**CloudWatch dashboard:**
- Provisioned via AWS CLI in `provision.sh`
- Widgets: request volume over time, tier breakdown pie, cap utilization gauges, cost trend, error rate, latency percentiles
- Active user count (unique user_ids per period — count only, no IDs)

**Alarm:**
- `CapDenied > 10/hour` → SNS notification to operator

**Privacy-first user identification for moderation:**
- Dashboard shows anonymized user IDs (e.g., hashed or truncated) — enough to correlate abuse patterns without exposing PII
- Separate admin CLI tool can resolve anonymous ID to real user for moderation actions (ban for hate speech, etc.)
- Resolution is logged and auditable

**Cost:** $0 incremental (within CloudWatch free tier for custom metrics)

---

## Implementation

- Add `PutMetricData` calls in auth middleware for each metric above
- Create CloudWatch dashboard JSON definition
- Add dashboard creation to `provision.sh`
- Add SNS topic + alarm for cap denial spike
- Add anonymized user ID dimension for moderation correlation

---

## Next Steps

1. [ ] Run requirements workflow to generate issue
