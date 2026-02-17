# Issue Filed

URL: https://github.com/martymcenroe/Aletheia/issues/369

---

# CloudWatch Usage Dashboard (MVP)

## User Story
As an Aletheia operator,
I want a CloudWatch dashboard showing request volume, tier breakdown, cap utilization, and cost estimates,
So that I can monitor system health, understand usage patterns, and detect abuse without exposing user PII.

## Objective
Provide real-time operational visibility into Aletheia API usage through privacy-preserving CloudWatch metrics and dashboards.

## UX Flow

### Scenario 1: Operator Checks Daily Usage
1. Operator opens AWS CloudWatch console
2. Navigates to "Aletheia Usage" dashboard
3. Views widgets showing: request volume (24h), tier breakdown pie chart, cap utilization gauges, cost trend, latency percentiles
4. Result: Operator understands current system load and cost trajectory

### Scenario 2: Cap Denial Spike Alert
1. Free tier users exhaust hourly caps simultaneously
2. `CapDenied` metric exceeds 10/hour threshold
3. CloudWatch alarm triggers SNS notification to operator email
4. Operator reviews dashboard to identify tier and window causing spike
5. Result: Operator can decide whether to adjust caps or investigate abuse

### Scenario 3: Investigating Abuse Pattern
1. Operator notices unusual request pattern on dashboard
2. Operator runs CloudWatch Logs Insights query against API logs to identify high-volume anonymized user IDs
3. Query aggregates request counts by hashed user ID, sorted descending
4. Operator uses separate admin CLI tool to resolve anonymous ID for moderation
5. Resolution action is logged with timestamp and reason
6. Result: Operator can take moderation action while maintaining audit trail

### Scenario 4: Cost Projection
1. Operator views `BedrockCostEstimate` trend widget
2. Sees daily/weekly cost aggregation
3. Result: Operator can project monthly costs and adjust tier limits if needed

## Requirements

### Metric Emission
1. Auth middleware emits `RequestCount` metric with `Tier` dimension (free/subscriber/admin)
2. Auth middleware emits `CapUtilization` metric with `Tier` and `Window` dimensions (hourly/daily/monthly)
3. Auth middleware emits `CapDenied` metric when request rejected due to cap exceeded
4. Response handler emits `BedrockCostEstimate` metric with estimated cost per request
5. Response handler emits `ErrorRate` metric for 4xx/5xx responses
6. Response handler emits `Latency` metric (p50/p90/p99 calculated by CloudWatch)
7. All metric emission wrapped in `try/except` with fail-open behavior (metric failures must not block requests)

### Active Users Analysis (Log-Based)
1. Auth middleware logs anonymized user ID (SHA-256 hash truncated to 12 chars) to CloudWatch Logs
2. CloudWatch Logs Insights query provided to calculate unique users per period
3. Query stored in `infrastructure/logs-insights-queries/active-users.sql`

### Abuse Pattern Detection (Log-Based via Contributor Insights)
1. CloudWatch Contributor Insights rule created for "Top Talkers" analysis
2. Rule aggregates request counts by anonymized user ID from logs
3. No per-user custom metrics emitted (avoids high-cardinality cost explosion)

### Dashboard Provisioning
1. Dashboard JSON definition stored in `infrastructure/cloudwatch-dashboard.json`
2. `provision.sh` creates dashboard via `aws cloudwatch put-dashboard`
3. Dashboard includes: request volume time series, tier breakdown pie, cap utilization gauges, cost trend line, error rate graph, latency percentiles
4. Dashboard JSON validated via `jq` before `aws cloudwatch put-dashboard` call

### Alerting
1. SNS topic created for operator notifications
2. CloudWatch alarm triggers when `CapDenied > 10` in 1-hour period
3. Alarm sends notification to SNS topic

### Privacy Compliance
1. No individual user text content in metrics
2. No PII (email, name) in metric dimensions
3. User identification via anonymized ID (SHA-256 hash truncated to 12 chars) in logs only
4. Anonymized IDs enable pattern correlation without exposing identity

## Technical Approach
- **Metric Emission:** Use CloudWatch Embedded Metric Format (EMF) via structured JSON logs for non-blocking emission (no HTTP round-trip latency)
- **Namespace:** `Aletheia/API` for all custom metrics
- **Active Users:** CloudWatch Logs Insights query on anonymized user ID field (cardinality calculation, not real-time metric)
- **Abuse Detection:** CloudWatch Contributor Insights rule for top talkers (log-based, not custom metrics)
- **Dashboard:** JSON definition with widget configurations, provisioned via AWS CLI
- **Alarm:** CloudWatch alarm with SNS action, threshold-based on `CapDenied` metric
- **Anonymization:** `hashlib.sha256(user_id.encode()).hexdigest()[:12]` logged to CloudWatch Logs (not as metric dimension)
- **Fail-Open:** All metric/logging code wrapped in `try/except` — observability failures never block user requests

## Risk Checklist
*Quick assessment - details go in LLD. Check all that apply and add brief notes.*

- [x] **Architecture:** Adds CloudWatch EMF integration to Lambda auth middleware; uses structured logging instead of direct PutMetricData to avoid latency impact
- [x] **Cost:** EMF metrics via logs (~$0.50/GB ingestion); avoids high-cardinality custom metric cost explosion by using Logs Insights for per-user analysis
- [x] **Legal/PII:** User IDs are hashed before logging; no PII in metrics or logs
- [ ] **Legal/External Data:** N/A — no external data sources
- [ ] **Safety:** N/A — read-only dashboard, no data mutation; fail-open metric emission ensures observability failures don't impact API availability

## Security Considerations
- **Path Validation:** N/A — no file operations
- **Input Sanitization:** User IDs are hashed before use in logs; prevents injection
- **Permissions:** Dashboard access controlled by AWS IAM; only operators with CloudWatch access can view
- **Audit Trail:** Admin ID resolution (anonymous → real) logged with timestamp and operator identity

## Files to Create/Modify
- `src/auth/middleware.py` — Add EMF structured logging for request/cap metrics with try/except fail-open
- `src/handlers/response.py` — Add EMF structured logging for latency/error/cost metrics with try/except fail-open
- `src/auth/anonymize.py` — New file with user ID hashing function
- `infrastructure/cloudwatch-dashboard.json` — Dashboard widget definitions
- `infrastructure/provision.sh` — Add dashboard and alarm creation commands with JSON validation
- `infrastructure/sns-alarm.json` — SNS topic and alarm configuration
- `infrastructure/contributor-insights-rules/top-talkers.json` — Contributor Insights rule for abuse detection
- `infrastructure/logs-insights-queries/active-users.sql` — Logs Insights query for unique user count

## Dependencies
- Issue #XXX (tiered-rate-limiting) must be completed first — provides tier data needed for metric dimensions

## Out of Scope (Future)
- Admin CLI tool for anonymous ID resolution — separate issue for moderation tooling
- Custom metric dimensions beyond tier/window — keep MVP simple
- Grafana integration — CloudWatch native for MVP
- Historical data export — use CloudWatch's built-in retention
- Per-endpoint breakdown — aggregate metrics only for MVP

## Open Questions
- None (all questions resolved)
<!-- Resolved questions:
- [x] Should we use CloudWatch Embedded Metric Format (EMF)? → Resolved: Yes, EMF avoids HTTP latency penalty of direct PutMetricData and is non-blocking
- [x] How long to retain metrics? → Resolved: CloudWatch default (15 months for 1-minute resolution); no custom retention needed
- [x] What anonymization scheme for user IDs? → Resolved: SHA-256 truncated to 12 chars; logged to CloudWatch Logs, NOT emitted as metric dimension
- [x] How to handle high-cardinality user analysis? → Resolved: Use CloudWatch Logs Insights and Contributor Insights for per-user patterns; avoids $0.30/metric/month cost explosion
- [x] How to calculate ActiveUsers (unique count)? → Resolved: Logs Insights query with count_distinct(), not real-time metric (CloudWatch metrics cannot calculate cardinality natively)
-->

## Acceptance Criteria
- [ ] `RequestCount` metric emitted with `Tier` dimension on every API request via EMF
- [ ] `CapUtilization` metric emitted with percentage value (0-100) when cap checked via EMF
- [ ] `CapDenied` metric emitted with count=1 when request rejected for cap exceeded via EMF
- [ ] `BedrockCostEstimate` metric emitted with estimated USD value per request via EMF
- [ ] `ErrorRate` metric emitted with HTTP status code dimension for 4xx/5xx responses via EMF
- [ ] `Latency` metric emitted with response time in milliseconds via EMF
- [ ] All metric emission code wrapped in try/except; metric failure returns gracefully without blocking request
- [ ] API request completes successfully even when CloudWatch is unreachable (fail-open verified)
- [ ] CloudWatch dashboard "Aletheia-Usage" exists after running `provision.sh`
- [ ] Dashboard JSON passes `jq .` validation before provisioning
- [ ] Dashboard contains widgets: RequestVolume, TierBreakdown, CapUtilization, CostTrend, ErrorRate, LatencyPercentiles
- [ ] CloudWatch alarm "Aletheia-CapDenialSpike" triggers when `CapDenied > 10` in 1 hour
- [ ] SNS notification sent to configured email when alarm triggers
- [ ] Anonymized user ID (12-char hex hash) logged to CloudWatch Logs on each request
- [ ] Contributor Insights rule "Aletheia-TopTalkers" created and queries logs for high-volume users
- [ ] Logs Insights query `active-users.sql` returns unique user count for specified time period
- [ ] No PII (email, name, request content) appears in any metric dimension, value, or log field
- [ ] No custom metric dimensions contain user IDs (verified via `aws cloudwatch list-metrics --namespace Aletheia/API`)

## Reviewer Suggestions

*Non-blocking recommendations from the reviewer.*

- **Cost Precision:** The "Original Brief" mentions "$0 incremental (within CloudWatch free tier)". Note that the free tier allows 10 custom metrics. With ~6 metric types across ~3 tiers, you may slightly exceed the free tier (~18 metric streams), resulting in a negligible cost (~$2.40/mo), but it is not strictly zero.
- **IaC:** While `provision.sh` is acceptable for MVP, consider moving dashboard definitions to Terraform/SAM/CDK in the future to avoid state drift.
- **Testing:** Ensure the `anonymize_user_id` function is tested with a salt or strictly defined encoding to prevent rainbow table attacks if the user base allows it (though for an MVP internal dashboard, simple SHA-256 is acceptable).

## Definition of Done

### Implementation
- [ ] Core feature implemented
- [ ] Unit tests written and passing

### Tools
- [ ] Update/create relevant CLI tools in `tools/` (if applicable)
- [ ] Document tool usage

### Documentation
- [ ] Update wiki pages affected by this change
- [ ] Update README.md if user-facing
- [ ] Update relevant ADRs or create new ones
- [ ] Add new files to `docs/0003-file-inventory.md`

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created

### Verification
- [ ] Run 0809 Security Audit - PASS (IAM permissions, metric data handling)
- [ ] Run 0810 Privacy Audit - PASS (anonymization verification, no PII in logs)
- [ ] Run 0817 Wiki Alignment Audit - PASS (if wiki updated)

## Testing Notes
- **Metric emission:** Use `aws cloudwatch get-metric-data` to verify metrics appear in `Aletheia/API` namespace
- **EMF verification:** Check CloudWatch Logs for structured JSON with `_aws` EMF metadata block
- **Dashboard:** Verify via `aws cloudwatch get-dashboard --dashboard-name Aletheia-Usage`
- **Dashboard JSON validation:** Run `jq . infrastructure/cloudwatch-dashboard.json` before provisioning; must exit 0
- **Alarm testing:** Manually set alarm state via `aws cloudwatch set-alarm-state` to verify SNS notification
- **Anonymization:** Unit test that verifies `anonymize_user_id("test@example.com")` returns 12-char hex string, not the original email
- **Privacy verification:** Grep CloudWatch Logs for known test email addresses; must return zero matches
- **Fail-open verification:** Mock CloudWatch client to raise exception; verify API request still returns 200
- **Contributor Insights:** Verify rule exists via `aws cloudwatch describe-insight-rules`
- **Logs Insights:** Run `active-users.sql` query via console or CLI; verify returns integer count

## Labels
`observability`, `ops`, `cloudwatch`, `privacy`

## Original Brief (user's ideation notes)
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
