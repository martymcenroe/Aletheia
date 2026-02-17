# Issue Review: Manual Subscriptions with Coupon Codes (MVP)

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Technical Product Manager & Governance Lead.

## Pre-Flight Gate
PASSED

## Review Summary
The design document is comprehensively detailed and meets the "Definition of Ready." It explicitly handles PII concerns, defines strict security boundaries (sanitization, rate limiting), and includes a robust testing strategy with offline mocks. The dependency on the rate-limiting architecture is clearly identified.

## Tier 1: BLOCKING Issues
No blocking issues found. Issue is actionable.

### Security
- [ ] **Input Sanitization:** Regex `^[A-Z0-9]{16}$` is specified for coupons, and RFC 5322 for emails.
- [ ] **Access Control:** Admin CLI and API authentication requirements are clearly defined.

### Safety
- [ ] **Concurrency:** Use of DynamoDB atomic counters and conditional writes addresses race conditions for multi-use coupons.

### Cost
- [ ] **Budget:** Impact is negligible (DynamoDB read/write units); no external paid APIs involved.

### Legal
- [ ] **PII Handling:** The document explicitly identifies Email collection as PII, defines the storage region (`us-east-1`), and correctly lists the `privacy-policy.md` update as a blocking requirement for the definition of done.

## Tier 2: HIGH PRIORITY Issues
No high-priority issues found. Context is complete.

### Quality
- [ ] **Acceptance Criteria:** Criteria are binary and quantifiable (e.g., specific regex matching, exact error code returns).

### Architecture
- [ ] **Dependencies:** Correctly identifies Issue #389 as a hard blocking dependency.
- [ ] **Offline Development:** Mock strategy (`REACT_APP_USE_MOCKS`) and fixture path are explicitly defined.

## Tier 3: SUGGESTIONS
- **Labels:** Recommended labels: `feature`, `mvp`, `backend`, `security`.
- **CLI Output:** Ensure `tools/admin_coupons.py` provides a clean CSV or JSON output option to easily export generated codes for distribution.

## Questions for Orchestrator
1. None.

## Verdict
[x] **APPROVED** - Ready to enter backlog
[ ] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision
