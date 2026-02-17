# Issue Review: Manual Subscriptions with Coupon Codes (MVP)

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Technical Product Manager & Governance Lead.

## Pre-Flight Gate
PASSED

## Review Summary
The design is robust, with clear user stories, acceptance criteria, and specific attention to security and PII handling. The inclusion of offline development mocks and specific fail states is excellent. However, there is a technical contradiction regarding coupon code generation that needs to be resolved before implementation to prevent functional defects.

## Tier 1: BLOCKING Issues
No blocking issues found. Issue is actionable.

### Security
- [ ] No issues found. Input sanitization and entropy appear sufficient, subject to the fix in Tier 2.

### Safety
- [ ] No issues found.

### Cost
- [ ] No issues found. "Negligible" is accepted for this MVP scope, assuming standard DynamoDB pricing for low-volume text data.

### Legal
- [ ] **Privacy Policy Dependency:** The document correctly identifies that the Privacy Policy *must* be updated. Ensure this is treated as a blocking release gate. The data residency (`us-east-1`) is explicitly defined and compliant.

## Tier 2: HIGH PRIORITY Issues

### Quality
- [ ] **Code Generation Logic Mismatch:** The Requirement states "16 alphanumeric characters". The Technical Approach specifies `secrets.token_urlsafe(12)`. `token_urlsafe` generates characters including `-` and `_` (non-alphanumeric). Additionally, simply uppercasing Base64 reduces entropy and causes collisions (`a` and `A` become the same).
    - **Recommendation:** Change Technical Approach to use `secrets.choice` with a defined alphabet (e.g., `string.ascii_uppercase + string.digits`) to ensure strict alphanumeric compliance and predictable entropy.

### Architecture
- [ ] **Dependency Verification:** This issue depends on Issue #389 (tiered-rate-limiting).
    - **Recommendation:** Confirm Issue #389 is in "Done" state. If Tiers do not exist in the codebase yet, this implementation will be blocked immediately.

## Tier 3: SUGGESTIONS
- **Operational Health:** Add a CloudWatch Alarm for the `aletheia-coupons` table `ConsumedWriteCapacityUnits` to detect if a script goes rogue during generation.
- **UX:** Clarify if the "Email" field in the popup should auto-populate if the user has previously saved it (Scenario 4 implies saving, but not viewing/editing existing).

## Questions for Orchestrator
1. Is Issue #389 fully deployed, providing the necessary "Tier" enumeration required for the `aletheia-coupons` table schema?

## Verdict
[ ] **APPROVED** - Ready to enter backlog
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision
