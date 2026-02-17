# LLD Review: 367-Feature: Manual Subscriptions with Coupon Codes (MVP)

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Software Architect & AI Governance Lead.

## Pre-Flight Gate
PASSED

## Review Summary
The LLD presents a solid MVP design for the coupon system, leveraging DynamoDB atomic counters and a separate table structure that aligns well with the project's existing architecture. The mechanical validation of paths is appreciated. However, there is a **critical disconnect between Section 3 Requirements and Section 10 Test Scenarios** specifically regarding the Email Collection feature and Privacy Policy documentation, resulting in failed traceability. Additionally, a minor safety guard is needed for the CLI tool.

## Open Questions Resolved
No open questions found in Section 1.

## Requirement Coverage Analysis (MANDATORY)

**Section 3 Requirements:**
| # | Requirement | Test(s) | Status |
|---|-------------|---------|--------|
| 1 | Admin can generate cryptographically random 16-character coupon codes via CLI | 010, 020 | ✓ Covered |
| 2 | Codes support configurable expiry (days from creation) and usage limits | 170, 180 | ✓ Covered |
| 3 | Codes are stored in DynamoDB with full audit trail | 030, 110 | ✓ Covered |
| 4 | Users can redeem valid codes via API endpoint | 040 | ✓ Covered |
| 5 | Redemption atomically upgrades user tier and increments code usage | 090, 100, 160 | ✓ Covered |
| 6 | Invalid/expired/exhausted codes return specific error messages | 050, 060, 070, 080 | ✓ Covered |
| 7 | Admin can list codes by status and revoke active codes | 120, 130 | ✓ Covered |
| 8 | DynamoDB table design is documented for infrastructure provisioning | 190 | ✓ Covered |
| 9 | Privacy policy update requirements are documented (blocking gate) | - | **GAP** |
| 10 | Test fixtures provide mock data for automated testing | 200 | ✓ Covered |

**Coverage Calculation:** 9 requirements covered / 10 total = **90%**

**Verdict:** **BLOCK** (Must be ≥95%)

**Missing Scenarios:**
- **REQ-9 Coverage:** The Traceability Matrix links REQ-9 to tests 140/150, but those tests verify *email format validation*, not *documentation existence*.
- **Missing Requirement:** Tests 140 and 150 (Email Validation) exist in Section 10 but have no corresponding requirement in Section 3. You must add a Requirement for "User email collection and validation" to Section 3 to fix the orphan tests and correct the REQ-9 mismatch.

## Tier 1: BLOCKING Issues

### Cost
- [ ] **Unbounded Loop in CLI:** The `generate_coupons` function loops based on the `--count` argument (`range(count)`). A typo (e.g., `--count 1000000`) could cause significant delays or throttle DynamoDB.
    - **Recommendation:** Add a hardcoded safety limit (e.g., `MAX_BATCH_SIZE = 1000`) in `tools/admin_coupons.py` and raise an error if exceeded.

### Safety
- [ ] No issues found.

### Security
- [ ] No issues found.

### Legal
- [ ] No issues found.

## Tier 2: HIGH PRIORITY Issues

### Architecture
- [ ] No issues found.

### Observability
- [ ] **Missing Audit Logging:** While the database tracks `redeemed_by`, there is no explicit requirement or test for server-side logging of redemption attempts (especially failed ones) to CloudWatch. This is crucial for debugging user complaints about "invalid codes".
    - **Recommendation:** Add a logging step in `redeem_coupon` and a corresponding check in the LLD (Section 2.5 or Observability section).

### Quality
- [ ] **Requirement Coverage Mismatch:** As detailed in the Coverage Analysis, REQ-9 is not tested, and Tests 140/150 map to a non-existent requirement.
    - **Action:** Update Section 3 to include "System collects and validates user email addresses" as a distinct requirement. Remap Tests 140/150 to this new requirement. Update REQ-9 to strictly refer to the documentation or remove it if it's a process gate rather than a code requirement.

## Tier 3: SUGGESTIONS
- **UX:** Consider checking for "confusing characters" (0 vs O, 1 vs I) even though standard alphanumeric is used, or explicitly state in the CLI output that 0 is Zero. (Current plan uses A-Z0-9 which includes both, but logic handles it fine).
- **Maintenance:** The `redeemed_by` list in DynamoDB could hit the 400KB item limit if a "universal" code is used by thousands of users. For `max_uses > 1000`, consider not storing the full list of user IDs in the coupon item, or use a separate adjacency table. (Acceptable for MVP if usage is low).

## Questions for Orchestrator
1. None.

## Verdict
[ ] **APPROVED** - Ready for implementation
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision
