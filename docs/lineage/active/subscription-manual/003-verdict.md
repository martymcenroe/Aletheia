# Issue Review: Manual Subscriptions with Coupon Codes (MVP)

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Technical Product Manager & Governance Lead.

## Pre-Flight Gate
PASSED

## Review Summary
The issue is well-defined with clear User Stories, Acceptance Criteria, and a solid Technical Approach for an MVP. However, strictly adhering to governance protocols, there is a blocking ambiguity regarding PII Data Residency and a high-priority gap in offline development capabilities.

## Tier 1: BLOCKING Issues

### Security
- [ ] No blocking issues found. Input sanitization and rate limiting are well-specified.

### Safety
- [ ] No blocking issues found. Fail-safe/atomic strategies are in place.

### Cost
- [ ] No blocking issues found. Infrastructure impact is negligible and documented.

### Legal
- [ ] **Privacy & Data Residency (PII):** The issue involves collecting user emails (PII) and storing them in DynamoDB. While it mentions updating the privacy policy, it does not explicitly state the **AWS Region** where this data will be processed and stored.
    *   **Recommendation:** Explicitly state the target AWS Region (e.g., `us-east-1`) in the Technical Approach or Legal section to ensure alignment with the Privacy Policy and Data Residency laws (GDPR/CCPA) before backlog entry.

## Tier 2: HIGH PRIORITY Issues

### Quality
- [ ] No high-priority issues found. Acceptance Criteria are binary and quantifiable.

### Architecture
- [ ] **Offline Development:** The Technical Approach and Testing Notes rely on live API interaction. There is no mention of Static Fixtures or Mocking for the UI.
    *   **Recommendation:** Add a requirement for `mock-coupon-response.json` or a mock API client mode. This allows frontend development and testing without spinning up the full Lambda/DynamoDB stack.
- [ ] **Dependency Linking:** The issue mentions "Depends on tiered-rate-limiting issue".
    *   **Recommendation:** Please explicitly link the GitHub Issue ID for "tiered-rate-limiting" and confirm it is in a `DONE` or `IN_PROGRESS` state to prevent blocking during implementation.

## Tier 3: SUGGESTIONS
- Add label: `feature:monetization`
- Add label: `security:pii`
- Estimated Effort: Small/Medium (S/M) - Backend logic is straightforward, UI is minimal.

## Questions for Orchestrator
1. Does the existing `aletheia-users` table already have a defined and documented region that covers this new PII collection, or does this require a new Data Processing Agreement review?

## Verdict
[ ] **APPROVED** - Ready to enter backlog
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision
