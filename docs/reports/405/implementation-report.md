# Implementation Report — #405 Auth Readiness Checklist (Items 5-9)

**Date:** 2026-02-24
**Branch:** `405-auth-readiness`
**Issues:** #405 (parent), #442, #443, #444, #404

---

## Changes Made

### 1. E2E Test 060 — Authenticated Analysis Network Verification (#442)

**File:** `tests/e2e/auth-flow.spec.js`

Added test 060 that verifies the complete auth chain at the network level:
- Performs `mockLogin()` via popup page to store JWT in session storage
- Uses `context.route('**/api.aletheia.study/**')` to intercept service worker requests
- Captures the `Authorization` header from the intercepted request
- Asserts the header is `Bearer mock-jwt-for-testing`
- Fulfills with mock JSON response to avoid hitting production

This covers checklist items 5 (E2E authenticated analysis) and 6 (network-level verification).

### 2. Firefox SW Namespace Fix + START_OAUTH Tests (#444)

**File:** `tests/unit/firefox/service-worker.test.js`

**Namespace fix:** Added `global.chrome = browserMock` in `createServiceWorkerEnvironment()`. The Firefox `service-worker.js` uses `chrome.*` namespace (identical source to Chrome). Without this alias, the source evaluation failed silently during tests, resulting in zero coverage of the START_OAUTH handler.

**START_OAUTH test suite:** Added 7 tests covering the complete OAuth flow:
1. Returns true for async response
2. Opens auth tab with correct URL
3. Stores tokens on successful callback (session + local storage)
4. Responds with user info on success
5. Rejects on CSRF state mismatch
6. Handles tab closure (OAuth cancelled)
7. Times out after 5 minutes (fake timers)

### 3. Post-Deploy Smoke Test CI Job (#404)

**File:** `.github/workflows/ci.yml`

Added `post-deploy-smoke` job that runs after `deploy-infra` on pushes to main:
- Health check: `curl` to `/health`, expects 200
- Analysis smoke: `POST` to `/`, accepts 200 (auth off) or 401 (auth on), fails on 5xx
- No checkout or AWS credentials needed (public API only)

### 4. LinkedIn OAuth Manual Testbook (#443)

**File:** `docs/testbooks/10905-testbook-linkedin-oauth.md`

Manual test procedure covering:
- Prerequisites
- Chrome 5-step test procedure
- Firefox 5-step test procedure (with #396 popup-close behavior noted)
- Pass/fail criteria tables per browser
- Evidence recording table

---

## Files Modified

| File | Action |
|------|--------|
| `tests/e2e/auth-flow.spec.js` | Edit — added test 060 |
| `tests/unit/firefox/service-worker.test.js` | Edit — namespace fix + 7 START_OAUTH tests |
| `.github/workflows/ci.yml` | Edit — added post-deploy-smoke job |
| `docs/testbooks/10905-testbook-linkedin-oauth.md` | Create — manual testbook |
| `docs/reports/405/implementation-report.md` | Create — this file |
| `docs/reports/405/test-report.md` | Create — test results |
