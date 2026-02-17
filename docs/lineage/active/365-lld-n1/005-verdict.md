# LLD Review: 365 - Feature: LinkedIn Follower Incentive

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Software Architect & AI Governance Lead.

## Pre-Flight Gate: PASSED
All required elements (Issue Link, Context, Proposed Changes) are present.

## Review Summary
The LLD outlines a solid backend implementation for the LinkedIn Follower Incentive. However, there is a critical mismatch between the "Full Stack" Requirements/Test Scenarios and the "Backend Only" Scope of implementation. The Test Plan claims to automate browser interactions (clicking buttons) and system-wide effects (balance increases) using only backend Python unit tests, which is technically impossible. Additionally, the storage mechanism for LinkedIn Client credentials is not defined.

## Open Questions Resolved
No open questions found in Section 1.

## Requirement Coverage Analysis (MANDATORY)

**Section 3 Requirements:**
| # | Requirement | Test(s) | Status |
|---|-------------|---------|--------|
| 1 | Extension popup displays CTA... | - | **GAP** (Frontend) |
| 2 | CTA opens `https://www.linkedin.com/...` | T170 | ✓ Covered (Data only) |
| 3 | "I followed" button triggers inline OAuth... | - | **GAP** (Frontend trigger) |
| 4 | `/verify-follow` endpoint verifies status... | T010, T150 | ✓ Covered |
| 5 | Successful verification generates coupon... | T010, T070 | ✓ Covered |
| 6 | Coupon grants exactly +50 bonus requests | T180 | **GAP** (Redemption logic missing) |
| 7 | Coupon code displayed in popup... | T010 | ✓ Covered (API Return) |
| 8 | Email sent to user's registered email... | T100 | ✓ Covered |
| 9 | Duplicate verification requests return original | T030, T090 | ✓ Covered |
| 10 | Rate limiting enforces max 3 attempts... | T040 | ✓ Covered |
| 11 | LinkedIn OAuth tokens are NOT persisted | T160 | ✓ Covered |
| 12 | User_id to LinkedIn_id mapping is stored | T190 | ✓ Covered |
| 13 | All data stored in AWS US-East-1 | T200 | ✓ Covered |

**Coverage Calculation:** 10 requirements covered / 13 total = **76.9%**

**Verdict: BLOCK**

**Missing Scenarios / Scope Mismatch:**
- **REQ-1 & REQ-3:** These are Frontend requirements. Since the LLD explicitly states extension files are "out of scope", these requirements cannot be tested by the proposed `tests/unit/test_verify_follow.py`. Remove these requirements from *this* LLD or scope them to "API provides necessary data for..."
- **REQ-6:** The proposed changes (Section 2) cover *generating* the coupon, not *redeeming* it (applying credits). The test `test_coupon_reward_amount` likely checks the payload, but cannot verify the user's balance actually increases unless the redemption logic is also being implemented here.

## Tier 1: BLOCKING Issues

### Security
- [ ] **Missing Secrets Management:** The `linkedin_client.py` will require a LinkedIn **Client ID** and **Client Secret** to exchange the auth code. The LLD does not specify how these are injected (e.g., `os.environ["LINKEDIN_CLIENT_ID"]`). Hardcoding is forbidden.
    *   **Recommendation:** Add a row to Section 2.2 or a note in 2.6 specifying that Client Credentials will be loaded from secure Environment Variables.

## Tier 2: HIGH PRIORITY Issues

### Quality
- [ ] **Test Plan Realism (Scenario 020 & 060):**
    *   Scenario 020 claims "Input: Click CTA button" and is marked "Auto". This is **impossible** for a Backend Python Unit Test (`tests/unit/test_verify_follow.py`).
    *   Scenario 060 claims "User balance increased". Since the Redemption logic is not in Section 2 (only Verification), a unit test in this repo cannot assert the balance changed.
    *   **Recommendation:** Rename these scenarios to reflect what is actually being tested at the unit level (e.g., "S020: API returns correct LinkedIn URL", "S060: API returns correct Reward Metadata").

### Architecture
- [ ] **Scope Consistency:** The LLD title implies the full feature, but Section 2.1 strictly limits scope to Backend/Auth.
    *   **Recommendation:** Either narrow Section 3 Requirements to "Backend API Requirements" OR accept that full-stack requirements (1, 3) must be marked as "Manual / Out of Scope" for this specific technical implementation plan.

## Tier 3: SUGGESTIONS
- **Observability:** Explicitly log the `reason` when verification fails (e.g., "not_following", "rate_limited") to help support debug user claims.
- **Maintainability:** In `linkedin_client.py`, create a typed `LinkedInConfig` object to hold the credentials/URNs rather than passing them as loose arguments.

## Verdict
[ ] **APPROVED** - Ready for implementation
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision
