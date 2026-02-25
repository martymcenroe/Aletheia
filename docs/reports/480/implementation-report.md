# Implementation Report — Issue #480

## Chrome OAuth: Migrate launchWebAuthFlow to Service Worker

### Problem

`initiateLogin()` in `extensions/chrome/auth.js` called `chrome.identity.launchWebAuthFlow()` from the popup context. In MV3, the popup closes when the user interacts with the auth window, killing the token exchange mid-flow. This is the same class of bug fixed for Firefox in Issue #396.

### Solution

Ported the Firefox #396 persistent state pattern to Chrome:

1. **Popup** sends `START_OAUTH` message to service worker with auth URL, CSRF state, and Lambda URL
2. **Service worker** calls `chrome.identity.launchWebAuthFlow`, validates CSRF state, exchanges code for tokens, and stores them
3. **Popup** handles `{ pending: true }` response and "disconnected" errors gracefully

Chrome's implementation is simpler than Firefox because `launchWebAuthFlow` returns the redirect URL directly (no `tabs.onUpdated` listener needed).

### Files Changed

| File | Change |
|------|--------|
| `extensions/chrome/manifest.json` | Added `host_permissions` for API and auth Lambda URLs |
| `extensions/firefox/manifest.json` | Added `host_permissions` for API and auth Lambda URLs |
| `extensions/chrome/service-worker.js` | Added `START_OAUTH` message handler with full OAuth lifecycle |
| `extensions/chrome/auth.js` | Rewrote `initiateLogin()` to delegate to SW via message passing |
| `extensions/chrome/popup.js` | Updated `handleLoginClick()` to handle `{ pending: true }` and disconnected errors |
| `tests/unit/chrome/service-worker.test.js` | Added 7 new START_OAUTH tests |
| `tests/unit/chrome/auth.test.js` | Rewrote 12 tests for new delegated pattern |

### Design Decisions

- **No `tabs.onUpdated` listener** — Unlike Firefox, Chrome's `launchWebAuthFlow` returns the redirect URL directly to the caller, so no tab monitoring is needed
- **CSRF state passed in message** — Generated in auth.js, sent to SW, validated after `launchWebAuthFlow` returns
- **Immediate `sendResponse`** — SW responds `{ success: true, pending: true }` before launching the auth flow, so popup gets a clean response even if it closes
- **`host_permissions` added to both manifests** — Required for fetch calls to auth Lambda and API from service workers
