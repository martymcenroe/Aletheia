# LLD Review: 116 - Feature: Authenticate users via LinkedIn OAuth

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Software Architect & AI Governance Lead.

## Pre-Flight Gate
PASSED

## Review Summary
The LLD provides a solid foundation for a Python CLI OAuth flow, with clear separation of concerns between the client (CLI) and the backend (Lambda). The transition from a Chrome Extension to a CLI context is well-handled. However, a critical Safety issue exists regarding test isolation: the design allows the application to write to `~/.config`, but the test plan does not explicitly enforce using temporary directories during automated testing, creating a risk of polluting the developer's or CI environment's actual configuration files. This must be addressed before implementation.

## Open Questions Resolved
No open questions found in Section 1.

## Requirement Coverage Analysis (MANDATORY)

**Section 3 Requirements:**
| # | Requirement | Test(s) | Status |
|---|-------------|---------|--------|
| 1 | Users can initiate LinkedIn OAuth flow from CLI and receive valid tokens | 010, 130 | ✓ Covered |
| 2 | Access tokens are securely stored in encrypted format at `~/.config/...` | 010, 055 | ✓ Covered |
| 3 | Token expiration is handled gracefully (refresh or re-auth prompt) | 040, 050 | ✓ Covered |
| 4 | Backend Lambda validates tokens statelessly by calling LinkedIn API | 070, 080 | ✓ Covered |
| 5 | Auth state is reactive (callbacks invoked when state changes) | 100 | ✓ Covered |
| 6 | Error states are returned with actionable error codes | 030, 090, 120 | ✓ Covered |
| 7 | Users can log out, clearing all stored credentials | 060 | ✓ Covered |
| 8 | CSRF protection via state parameter validation | 120 | ✓ Covered |

**Coverage Calculation:** 8 requirements covered / 8 total = **100%**

**Verdict:** PASS

## Tier 1: BLOCKING Issues

### Safety
- [ ] **Test Isolation / Worktree Scope (CRITICAL):** While the CLI application is correctly designed to store tokens in `~/.config/assemblyzero/`, the Test Plan (Section 10) does not explicitly mandate that tests must use a temporary directory or mock storage.
    *   **Risk:** Tests like `T050` (`test_store_tokens_persists`) and `T055` may write to the developer's *actual* `~/.config` directory if not properly isolated, violating the safety rule against side effects outside the worktree during development.
    *   **Recommendation:** Update Section 10 (Test Plan/Strategies) to explicitly state: "All unit and integration tests involving file storage MUST use the `tmp_path` fixture or mock the storage path to prevent writing to the user's actual home directory."

### Cost
- [ ] No issues found.

### Security
- [ ] No issues found.

### Legal
- [ ] No issues found.

## Tier 2: HIGH PRIORITY Issues

### Architecture
- [ ] **Path Structure:** The LLD modifies `src/lambda_auth_function.py`. While this passes mechanical checks, having a Lambda handler in the root of `src/` is a minor architectural smell (vs `src/handlers/`). Since the file already exists, this is acceptable, but ensure the new imports for `src.auth` work correctly within the Lambda runtime environment (packaging considerations).

### Observability
- [ ] No issues found.

### Quality
- [ ] **Port Conflict Testing:** The Risks section mentions "Local server port conflict", but there is no specific test scenario for this.
    *   **Recommendation:** Add a test scenario (e.g., `015`) to verify behavior when port 8585 is in use (e.g., fail gracefully or try next port).

## Tier 3: SUGGESTIONS
- **Mermaid Auto-Inspection:** The "Auto-Inspection Results" in Section 6.1 were left blank. Ensure these are verified.
- **Dependency Pinning:** `PyJWT = "^2.8.0"`. Ensure the exact version used in Lambda matches the dev environment to avoid "works on my machine" issues with crypto libraries.

## Questions for Orchestrator
1. None.

## Verdict
[ ] **APPROVED** - Ready for implementation
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision
