# Issue Review: CloudWatch Usage Dashboard (MVP)

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Technical Product Manager & Governance Lead.

## Pre-Flight Gate
PASSED

## Review Summary
The issue is well-structured and covers privacy concerns well. However, there is a **critical Cost/Architecture blocker** regarding the use of User IDs as metric dimensions. The proposed approach utilizes a "High Cardinality" pattern that will cause CloudWatch billing to scale linearly with the user base, creating a significant cost risk. This must be refactored before approval.

## Tier 1: BLOCKING Issues

### Security
- [ ] No issues found. Input sanitization (hashing) is adequate.

### Safety
- [ ] **Fail-Safe Strategy:** The document implies adding synchronous `put_metric_data` calls to the critical path (`middleware.py`). It does not specify error handling.
    - **Recommendation:** Explicitly state that metric emission must be wrapped in `try/except` blocks (fail-open). Observability failures must **never** block the user request or cause an API 500 error.

### Cost
- [ ] **High Cardinality Dimension (CRITICAL):** Scenario 3 and the "Anonymization" section propose using the hashed `UserID` as a metric dimension. In CloudWatch, **each unique dimension value creates a distinct Metric Stream**.
    - *Impact:* If you have 5,000 users, you generate 5,000 custom metrics. At ~$0.30/metric/month, this is $1,500/month just for this dashboard.
    - **Recommendation:** Remove `UserID` as a custom metric dimension.
        - Option A: Use **CloudWatch Embedded Metric Format (EMF)** (which was rejected in Open Questions, but is actually the correct solution here).
        - Option B: Use **CloudWatch Logs Insights** or **Contributor Insights** to analyze per-user patterns from logs, rather than metrics.
        - Option C: Only emit per-user metrics for "Top Talkers" (requires application state).

### Legal
- [ ] No issues found. PII handling is explicitly defined.

## Tier 2: HIGH PRIORITY Issues

### Quality
- [ ] **Unfeasible Requirement (`ActiveUsers`):** The requirement "Auth middleware emits ActiveUsers metric (unique user count per period)" is technically impossible with standard CloudWatch `PutMetricData`.
    - *Reasoning:* CloudWatch standard metrics perform aggregations (Sum, Count, Avg) on data points. They cannot calculate "Cardinality/Uniqueness" (HyperLogLog) natively without external state or sending the ID as a dimension (see Cost blocker).
    - **Recommendation:** Redefine this requirement. Either remove it, or specify that it will be calculated via Logs Insights queries, not emitted as a real-time gauge.

### Architecture
- [ ] **Latency Impact:** Calling `boto3.client('cloudwatch').put_metric_data()` involves an HTTP network round-trip. Doing this on *every* request (middleware) adds significant latency to the API.
    - **Recommendation:** Use the **CloudWatch Agent** (async UDP/TCP listener) or **EMF (over logs)** which is non-blocking. If direct `PutMetricData` is strictly required for MVP, explicit acknowledgement of the latency penalty (20-100ms) is required in the "Risk Checklist".

## Tier 3: SUGGESTIONS
- **Taxonomy:** Add `observability` and `ops` labels.
- **Testing:** Add a test case to verify the dashboard JSON is valid JSON before attempting `provision.sh`.

## Questions for Orchestrator
1. Given the Cost Blocker regarding High Cardinality (User IDs), should we mandate the use of CloudWatch Contributor Insights (log-based) instead of Custom Metrics for the "Abuse Pattern" scenario?

## Verdict
[ ] **APPROVED** - Ready to enter backlog
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision
