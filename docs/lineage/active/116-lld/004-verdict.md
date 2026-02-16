# LLD Review: 116 - Feature: Authenticate users via LinkedIn OAuth

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Software Architect & AI Governance Lead.

## Pre-Flight Gate: PASSED
All required elements are present.

## Review Summary
The LLD is structurally sound but **Architecturally BLOCKED**. There is a fundamental mismatch between the stated Context (Chrome Extension features, Open Questions about `chrome.storage`) and the Proposed Changes (Pure Python implementation using file-system storage). Python code cannot run natively within a Manifest V3 Chrome Extension to interact with `chrome.storage` or handle client-side OAuth redirects.

Either this LLD intends to build a Python CLI/Agent (in which case the Chrome Context is confusing), or it intends to build a Chrome Extension feature (in which case the implementation must be JavaScript/TypeScript).

## Open Questions Resolved
*Reflecting on the confusion in the LLD, these answers assume the target is a Chrome Extension, despite the Python code proposed.*

- [x] ~~Which Chrome extension architecture: Manifest V3 service worker or V2 background page?~~ **RESOLVED: Manifest V3 Service Worker is mandatory for new implementations.**
- [x] ~~Should we use Chrome Identity API (simpler) or manual OAuth flow (more control)?~~ **RESOLVED: Manual flow (matches Section 2.7 decisions), though Identity API is preferred for UX if strictly Chrome-based.**
- [x] ~~What LinkedIn API scopes are needed? (`openid`, `profile`, `email`?)~~ **RESOLVED: `openid`, `profile`, `email` are standard OIDC scopes required for the requested data.**
- [x] ~~Where should tokens be stored: `chrome.storage.local` (encrypted) or `chrome.storage.session`?~~ **RESOLVED: `chrome.storage.session` is preferred for security (tokens cleared on browser close). If persistence is required, `chrome.storage.local` must be used but requires encryption.**
- [x] ~~What is the Lambda endpoint URL for token validation?~~ **RESOLVED: This must be configured via Terraform outputs/Environment Variables, not hardcoded.**

## Requirement Coverage Analysis (MANDATORY)

**Section 3 Requirements:**
| # | Requirement | Test(s) | Status |
|---|-------------|---------|--------|
| 1 | Users can initiate LinkedIn OAuth flow | T010, Scenario 010 | ✓ Covered |
| 2 | Access tokens securely stored (encrypted) | T050, Scenario 050 | ✓ Covered |
| 3 | Token expiration handled gracefully | T060, Scenario 040, 050 | ✓ Covered |
| 4 | Backend Lambda validates tokens | T080, T090, Scenario 070, 080 | ✓ Covered |
| 5 | Auth state is reactive | T100, Scenario 100 | ✓ Covered |
| 6 | Error states returned with codes | Scenario 030, 080, 090, 120 | ✓ Covered |
| 7 | Users can log out | T070, Scenario 060 | ✓ Covered |
| 8 | CSRF protection via state | T030, Scenario 030, 120 | ✓ Covered |

**Coverage Calculation:** 8 requirements covered / 8 total = **100%**

**Verdict:** PASS (However, tests verify Python code that may not be deployable to the target environment).

## Tier 1: BLOCKING Issues

### Architecture
- [ ] **Platform/Language Mismatch (CRITICAL):** The Context (Section 1) and Open Questions describe a **Chrome Extension** (referencing `chrome.storage`, Manifest V3). However, the Proposed Changes (Section 2) implement the logic in **Python** (`src/auth/`, `httpx`, `PyJWT`). Python code cannot run inside a Chrome Extension.
    - **Recommendation:**
        1.  If this is for the Chrome Extension Client: Rewrite Section 2 to use TypeScript/JavaScript, remove Python dependencies (`httpx`, `PyJWT`), and use browser APIs (`fetch`, `chrome.identity`).
        2.  If this is for a Python Backend/CLI: Clarify the Context to remove references to Chrome Extension architecture and `chrome.storage`.
- [ ] **Invalid Storage Mechanism for Lambda:** If `src/auth/token_manager.py` is intended to be used by the Backend (`src/lambda_auth_function.py`), the `store_tokens` function using **local file storage** is invalid. AWS Lambda is ephemeral; local files are lost after execution.
    - **Recommendation:** Backend should verify tokens statelessly or use a database (DynamoDB/Redis) for session management if absolutely necessary (though stateless JWT verification is preferred).

### Safety
- [ ] **Worktree Pollution:** The `store_tokens` implementation (Section 2.4) writes to a `storage_path`. If this defaults to the current working directory in a Python CLI context, it risks committing credentials to git.
    - **Recommendation:** Ensure default storage path is outside the worktree (e.g., `~/.config/app_name/tokens.json`) or strictly git-ignored.

## Tier 2: HIGH PRIORITY Issues

### Architecture
- [ ] **Confusion of Concerns:** The LLD attempts to solve client-side concerns (OAuth redirection, token persistence) and server-side concerns (Token validation) in the same Python module structure without clear separation of execution environments (Client vs Server).

## Tier 3: SUGGESTIONS
- **Testing:** The test plan is excellent for the Python code described, but if the code moves to JS, the test strategy must shift to Jest/Vitest.

## Questions for Orchestrator
1. Is the "Chrome extension" context in Section 1 correct? Or is this actually a Python CLI tool?

## Verdict
[ ] **APPROVED** - Ready for implementation
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision
