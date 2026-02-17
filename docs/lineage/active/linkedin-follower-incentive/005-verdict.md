# Issue Review: LinkedIn Follower Incentive (Coupon for Follows)

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Technical Product Manager & Governance Lead.

## Pre-Flight Gate
PASSED

## Review Summary
The proposal is detailed and well-structured, addressing the user story and technical flow clearly. However, there is a **Tier 1 Security/Legal** concern regarding Data Minimization (storage of OAuth tokens without a defined use case for them) that must be addressed before approval. Additionally, architectural details regarding offline development need explicit inclusion.

## Tier 1: BLOCKING Issues

### Security
- [ ] **Data Minimization / Token Storage:** The Security Considerations section states "LinkedIn access tokens encrypted at rest in database". However, the MVP scope explicitly excludes "Follow-back detection" (using the honor system). If the verification is a one-time event and no ongoing monitoring occurs, storing the Access Token creates unnecessary security liability.
    *   **Recommendation:** Remove persistent storage of LinkedIn Access Tokens unless there is a documented requirement for future use. If reuse is required for retries within a session, store temporarily in cache (Redis) with a short TTL, or discard immediately after verification.

### Safety
- [ ] No blocking issues found.

### Cost
- [ ] No blocking issues found.

### Legal
- [ ] No blocking issues found.

## Tier 2: HIGH PRIORITY Issues

### Quality
- [ ] No high-priority issues found.

### Architecture
- [ ] **Offline Development / Static Fixtures:** The "Files to Create" and "Testing Notes" mention mocking but do not explicitly list static fixture files (e.g., `tests/fixtures/linkedin_org_followers_response.json`). To satisfy the requirement for offline development without live API credentials, these assets must be committed to the repo.
    *   **Recommendation:** Add specific JSON fixture files to the "Files to Create/Modify" section.
- [ ] **Dependency Verification:** The document lists "Issue #412 (subscription-model)" as a dependency that "must be completed first".
    *   **Recommendation:** Ensure Issue #412 is in "Done" state before moving this issue to "In Progress".

## Tier 3: SUGGESTIONS
- **Library Dependencies:** Verify if `lambda/auth/linkedin_client.py` requires a new Python package (e.g., a LinkedIn SDK) and ensure it is added to `requirements.txt`.
- **UX Copy:** The error message "Verification temporarily unavailable" is good, but consider distinguishing between "API Error" (our fault/LinkedIn fault) and "Not Found" to reduce user frustration.

## Questions for Orchestrator
1. Does the long-term roadmap definitely include "Unfollow detection"? If so, storing tokens now might be justified, but requires a strict data retention policy. If not, we should strictly avoid storing them.

## Verdict
[ ] **APPROVED** - Ready to enter backlog
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision
