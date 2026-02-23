# Implementation Report — Issue #402

## Summary
Fixed missing JWT storage and Authorization headers in extension API calls.

## Root Cause
Two bugs: `storeTokens()` discarded the `jwt` field from token exchange response, and all fetch calls sent no Authorization header.

## Changes (6 files)

| File | Change |
|------|--------|
| `extensions/chrome/auth.js` | `storeTokens()` +jwt param, `getJwt()`, `clearTokens()` +jwt, export, call site |
| `extensions/firefox/auth.js` | Same (browser.* API) |
| `extensions/chrome/service-worker.js` | `getAuthHeaders()` helper, 2 fetch calls |
| `extensions/firefox/service-worker.js` | `getAuthHeaders()` helper, 2 fetch calls, jwt in OAuth flow |
| `extensions/chrome/popup.js` | JWT in full-page, coupon, subscription, upgrade fetches |
| `extensions/firefox/popup.js` | JWT in full-page fetch |

## Graceful Degradation
When no JWT exists (not logged in), requests go without Authorization header. AUTH_ENABLED=false works as before; AUTH_ENABLED=true returns 401 for unauthenticated requests (correct behavior).
