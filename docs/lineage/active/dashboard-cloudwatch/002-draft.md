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
2. Dashboard shows anonymized user ID (hashed) with high request volume
3. Operator uses separate admin CLI tool to resolve anonymous ID for moderation
4. Resolution action is logged with timestamp and reason
5. Result: Operator can take moderation action while maintaining audit trail

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
7. Auth middleware emits `ActiveUsers` metric (unique user count per period, no IDs)

### Dashboard Provisioning
1. Dashboard JSON definition stored in `infrastructure/cloudwatch-dashboard.json`
2. `provision.sh` creates dashboard via `aws cloudwatch put-dashboard`
3. Dashboard includes: request volume time series, tier breakdown pie, cap utilization gauges, cost trend line, error rate graph, latency percentiles

### Alerting
1. SNS topic created for operator notifications
2. CloudWatch alarm triggers when `CapDenied > 10` in 1-hour period
3. Alarm sends notification to SNS topic

### Privacy Compliance
1. No individual user text content in metrics
2. No PII (email, name) in metric dimensions
3. User identification via anonymized ID (SHA-256 hash truncated to 12 chars)
4. Anonymized IDs enable pattern correlation without exposing identity

## Technical Approach
- **Metric Emission:** Use `boto3.client('cloudwatch').put_metric_data()` in auth middleware and response handler
- **Namespace:** `Aletheia/API` for all custom metrics
- **Dashboard:** JSON definition with widget configurations, provisioned via AWS CLI
- **Alarm:** CloudWatch alarm with SNS action, threshold-based on `CapDenied` metric
- **Anonymization:** `hashlib.sha256(user_id.encode()).hexdigest()[:12]` for user dimension

## Risk Checklist
*Quick assessment - details go in LLD. Check all that apply and add brief notes.*

- [x] **Architecture:** Adds CloudWatch integration to Lambda auth middleware
- [x] **Cost:** `PutMetricData` calls (~$0.30/million custom metrics, likely within free tier)
- [x] **Legal/PII:** User IDs are hashed before emission; no PII in metrics
- [ ] **Legal/External Data:** N/A — no external data sources
- [ ] **Safety:** N/A — read-only dashboard, no data mutation

## Security Considerations
- **Path Validation:** N/A — no file operations
- **Input Sanitization:** User IDs are hashed before use in metric dimensions; prevents injection
- **Permissions:** Dashboard access controlled by AWS IAM; only operators with CloudWatch access can view
- **Audit Trail:** Admin ID resolution (anonymous → real) logged with timestamp and operator identity

## Files to Create/Modify
- `src/auth/middleware.py` — Add `PutMetricData` calls for request/cap metrics
- `src/handlers/response.py` — Add `PutMetricData` calls for latency/error/cost metrics
- `src/auth/anonymize.py` — New file with user ID hashing function
- `infrastructure/cloudwatch-dashboard.json` — Dashboard widget definitions
- `infrastructure/provision.sh` — Add dashboard and alarm creation commands
- `infrastructure/sns-alarm.json` — SNS topic and alarm configuration

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
- [x] Should we use CloudWatch Embedded Metric Format (EMF)? → Resolved: No, direct PutMetricData is simpler for MVP; EMF adds complexity
- [x] How long to retain metrics? → Resolved: CloudWatch default (15 months for 1-minute resolution); no custom retention needed
- [x] What anonymization scheme for user IDs? → Resolved: SHA-256 truncated to 12 chars; sufficient for correlation without collision risk
-->

## Acceptance Criteria
- [ ] `RequestCount` metric emitted with `Tier` dimension on every API request
- [ ] `CapUtilization` metric emitted with percentage value (0-100) when cap checked
- [ ] `CapDenied` metric emitted with count=1 when request rejected for cap exceeded
- [ ] `BedrockCostEstimate` metric emitted with estimated USD value per request
- [ ] `ErrorRate` metric emitted with HTTP status code dimension for 4xx/5xx responses
- [ ] `Latency` metric emitted with response time in milliseconds
- [ ] CloudWatch dashboard "Aletheia-Usage" exists after running `provision.sh`
- [ ] Dashboard contains widgets: RequestVolume, TierBreakdown, CapUtilization, CostTrend, ErrorRate, LatencyPercentiles
- [ ] CloudWatch alarm "Aletheia-CapDenialSpike" triggers when `CapDenied > 10` in 1 hour
- [ ] SNS notification sent to configured email when alarm triggers
- [ ] User IDs in metric dimensions are anonymized (12-char hex hash, not raw ID)
- [ ] No PII (email, name, request content) appears in any metric dimension or value

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
- [ ] Run 0810 Privacy Audit - PASS (anonymization verification)
- [ ] Run 0817 Wiki Alignment Audit - PASS (if wiki updated)

## Testing Notes
- **Metric emission:** Use `aws cloudwatch get-metric-data` to verify metrics appear in `Aletheia/API` namespace
- **Dashboard:** Verify via `aws cloudwatch get-dashboard --dashboard-name Aletheia-Usage`
- **Alarm testing:** Manually set alarm state via `aws cloudwatch set-alarm-state` to verify SNS notification
- **Anonymization:** Unit test that verifies `anonymize_user_id("test@example.com")` returns 12-char hex string, not the original email
- **Privacy verification:** Grep CloudWatch metrics for known test email addresses; must return zero matches
