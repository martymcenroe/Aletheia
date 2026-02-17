# Issue Review: LinkedIn Follower Incentive (Coupon for Follows)

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Technical Product Manager & Governance Lead.

## Pre-Flight Gate
PASSED

## Review Summary
The document provides a strong foundation for the LinkedIn integration but is currently **not ready for backlog entry**. It contains self-identified blocking open questions regarding the OAuth flow and coupon value that must be decided to finalize the detailed design. Additionally, strict data residency declarations and dependency links are missing.

## Tier 1: BLOCKING Issues

### Cost
- [ ] **Budget Estimate Missing:** While "minimal" is stated, a specific monthly budget estimate (e.g., "$50/mo for Lambda/SES scaling to 10k users") is required to approve the new infrastructure.

### Legal
- [ ] **Privacy & Data Residency:** The document mentions storing LinkedIn access tokens and user mappings but does not explicitly state *where* this data is processed and stored (e.g., "AWS US-East-1"). **Action:** Explicitly state the region for data residency compliance.
- [ ] **Terms of Service:** Confirm that storing the `coupon_code` alongside `user_id` does not inadvertently create a "profile" that violates LinkedIn's data retention policies regarding "storing data derived from LinkedIn". (Likely fine, but explicit check required).

### Security
- [ ] **OAuth Flow Decision (Open Question Resolution):** The document lists "LinkedIn account linking" as a blocking open question.
    - **Recommendation:** **Mandate "Inline OAuth"**. Do not require a separate linking step beforehand. When "I followed" is clicked:
        1. Check if User has linked LinkedIn account.
        2. If NO: Trigger OAuth popup immediately to link account.
        3. If YES (or after successful link): Proceed to call `/verify-follow`.
    - *Rationale:* Reducing friction maximizes conversion.

## Tier 2: HIGH PRIORITY Issues

### Quality
- [ ] **Coupon Specification (Open Question Resolution):** The document lists "Coupon value" as a blocking open question.
    - **Recommendation:** **Define as "One-Time Resource Boost"** (e.g., "+50 Requests") rather than a subscription tier upgrade.
    - *Rationale:* Tier upgrades create billing complexity (proration, downgrading later). A resource boost is a clean, one-off transaction that aligns with a "single-use" coupon.
- [ ] **Acceptance Criteria completeness:** AC mentions "User applies coupon to upgrade tier". This contradicts the recommendation above and is vague. Update AC to reflect the specific reward (e.g., "User applies coupon to receive 50 bonus credits").

### Architecture
- [ ] **Unresolved Dependency:** The document references `Issue #TBD (subscription-model)`. An issue cannot be approved with TBD dependencies. This dependency must be linked to a concrete issue ID that is in the "Ready" or "In Progress" state.
- [ ] **Idempotency Strategy:** The flow mentions "Scenario 3: User Already Claimed". The Architecture should specify if this check happens at the *Extension* level (checking local storage/state) to save API calls, or strictly at the *API* level. **Recommendation:** API level is mandatory for security, UI level is optional for UX.

## Tier 3: SUGGESTIONS
- **Taxonomy:** Add labels `growth`, `integration`, `marketing-api`.
- **Effort Estimate:** Recommended T-Shirt Size: **M** (Due to OAuth complexity and testing).
- **Test Data:** Ensure LinkedIn test accounts are provisioned before sprint start (as noted in "Dependencies", this is manual).

## Questions for Orchestrator
1. Does the "subscription-model" (#TBD) currently support "Resource Boost" coupons, or only "Tier Upgrade" coupons? This dictates the complexity of the reward mechanism.

## Verdict
[ ] **APPROVED** - Ready to enter backlog
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision
