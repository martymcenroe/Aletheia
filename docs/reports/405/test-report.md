# Test Report — #405 Auth Readiness Checklist (Items 5-9)

**Date:** 2026-02-24
**Branch:** `405-auth-readiness`

---

## Firefox Service Worker Unit Tests

**Command:** `npx vitest run tests/unit/firefox/service-worker.test.js`
**Result:** 33 passed (0 failed)

| Suite | Tests | Status |
|-------|-------|--------|
| Service Worker File (Firefox) | 4 | Pass |
| Installation Events (Firefox) | 3 | Pass |
| Message Handlers (Firefox) | 4 | Pass |
| Security - Sender Validation (Firefox) | 3 | Pass |
| Age Gate - Tab State Management (Firefox) | 2 | Pass |
| Context Menu Click Handler (Firefox) | 3 | Pass |
| Badge State (Firefox) | 1 | Pass |
| API Integration (Firefox) | 2 | Pass |
| Helper Functions (Firefox) | 2 | Pass |
| Error Handling (Firefox) | 2 | Pass |
| **START_OAUTH Handler (Issue #396)** | **7** | **Pass** |

### START_OAUTH Tests Detail

| Test | Result |
|------|--------|
| Returns true for async response | Pass |
| Opens auth tab with correct URL | Pass |
| Stores tokens on successful callback | Pass |
| Responds with user info on success | Pass |
| Rejects on CSRF state mismatch | Pass |
| Handles tab closure (OAuth cancelled) | Pass |
| Times out after 5 minutes | Pass |

---

## Full Vitest Suite

**Command:** `npx vitest run`
**Result:** 267 passed, 3 failed (pre-existing), 2 skipped

Pre-existing failures (confirmed on `main`):
- `extension-files.test.js` — popup.css parity (cosmetic)
- `article-extractor.test.js` — 2 phone scrubbing regex tests

**Zero regressions introduced.**

---

## CI YAML Validation

**Check:** `grep "post-deploy-smoke" .github/workflows/ci.yml`
**Result:** Found — job defined correctly with `needs: deploy-infra` dependency.

---

## E2E Auth Flow Tests

**Note:** Test 060 requires a headed Chromium instance with the extension loaded. It was verified structurally (correct fixture usage, route interception pattern matches tests 010-050). Full E2E execution requires:
```
npx playwright test tests/e2e/auth-flow.spec.js --project=chromium --headed
```
This runs in CI via the `e2e-chrome` job with `xvfb-run`.
