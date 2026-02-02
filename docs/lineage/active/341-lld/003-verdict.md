# LLD Review: 1341 - Feature: Add JWT authentication to analysis endpoint with daily token cap

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Software Architect & AI Governance Lead.

## Pre-Flight Gate
PASSED

## Review Summary
The LLD proposes a solid security enhancement with cost-control mechanisms (daily caps) and standard JWT practices. The Fail-Closed strategy and reliance on AWS Secrets Manager are commended. However, the design requires revision to address potential security risks regarding the placement of administrative tools within the source code directory, missing test dependencies, and incomplete "Open Questions" sections.

## Tier 1: BLOCKING Issues
No blocking issues found. LLD is approved for implementation pending Tier 2 fixes.

### Cost
- [ ] No issues found.

### Safety
- [ ] No issues found.

### Security
- [ ] No issues found.

### Legal
- [ ] No issues found.

## Tier 2: HIGH PRIORITY Issues

### Architecture
- [ ] **Admin Tool Location (Security/Separation of Concerns):** The file `src/admin/adjust_cap.py` is proposed within the `src/` directory. If the deployment pipeline zips the `src/` directory for the Lambda artifact, this inadvertently deploys administrative code/tools to the production runtime.
    - **Recommendation:** Move the admin tool to a separate directory outside the application source, such as `scripts/` or `tools/`.
- [ ] **Unresolved Open Questions:** Section 1 lists "Open Questions" (e.g., "Should token cap be per-user or global?") that are explicitly answered in Section 2.7 ("Global daily").
    - **Recommendation:** Resolve and remove answered questions from Section 1 to avoid ambiguity during implementation.

### Observability
- [ ] No issues found.

### Quality
- [ ] **Missing Test Dependency:** Section 5.3 relies on `moto` for DynamoDB mocking, but `moto` is not listed in Section 2.2 Dependencies.
    - **Recommendation:** Add `moto` (or `pytest-moto`) to the `dev-dependencies` in Section 2.2 to ensure the "Offline Development" requirement is met.
- [ ] **Incomplete Security Spec:** Section 7.1 leaves a `TODO` for Log Injection ("Sanitize user_id before logging").
    - **Recommendation:** Define the sanitization strategy (e.g., "Use structured logging to ensure `user_id` is treated as a field, not a string interpolation target") instead of leaving it as a TODO.

## Tier 3: SUGGESTIONS
- **Secret Caching:** Consider explicitly adding global-scope caching for the Secrets Manager retrieval in `src/lambdas/auth/handler.py` to reduce latency and costs on warm starts.
- **Admin Tool Deps:** Ensure the admin CLI tool has its own dependency definition if it requires libraries not present in the Lambda environment (though it likely shares the project env).

## Questions for Orchestrator
1. None.

## Verdict
[ ] **APPROVED** - Ready for implementation
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision
