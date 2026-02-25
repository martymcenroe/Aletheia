# Implementation Report — Issue #396: Firefox OAuth Persistent State Fix

## Summary

Replaced closure-based OAuth tab listeners in Firefox service-worker.js with a persistent state pattern using `chrome.storage.session` and top-level event listeners. This fixes the bug where Firefox background script suspension kills dynamic listeners, causing token storage to silently fail after long OAuth flows.

## Root Cause

The START_OAUTH handler registered `chrome.tabs.onUpdated` and `chrome.tabs.onRemoved` listeners **inside** an async closure. These dynamic listeners:
1. Captured `tab.id`, `state`, `callbackUrl`, `sendResponse` in closures
2. Did not survive Firefox background script suspension/restart
3. Silently failed if the user took >30s on the LinkedIn auth page

## Fix: Persistent State Pattern

### Architecture Change

**Before:** Message handler → open tab → register dynamic listeners → wait for callback → exchange tokens → sendResponse
**After:** Message handler → open tab → store `pendingOAuth` in session storage → sendResponse immediately. Top-level `onUpdated` listener → read `pendingOAuth` → detect callback → exchange tokens → store tokens → clear `pendingOAuth`

### Why This Works

- **Top-level listeners** are re-registered every time the SW starts
- **`pendingOAuth`** state persists in `chrome.storage.session` across SW restarts
- **Popup already handles disconnected errors** (`popup.js:346-349`) — user reopens popup to see auth status
- **5-minute stale check** prevents zombie OAuth flows from processing old callbacks
- **`chrome.*` namespace** works identically in Firefox MV3 140+ (returns Promises)

## Files Changed

| File | Change |
|------|--------|
| `extensions/firefox/service-worker.js` | Fixed header comments; added top-level `onUpdated`/`onRemoved` OAuth listeners; rewrote START_OAUTH handler to use persistent state |
| `tests/unit/firefox/service-worker.test.js` | Rewrote 8 START_OAUTH tests for persistent state pattern |

## Files NOT Changed

| File | Why |
|------|-----|
| `extensions/firefox/auth.js` | Already delegates correctly via `browser.runtime.sendMessage` |
| `extensions/firefox/popup.js` | Already handles `disconnected` error and checks `isAuthenticated()` on reopen |
| `extensions/chrome/service-worker.js` | Chrome uses `chrome.identity.launchWebAuthFlow` — no popup closure issue |
| `tests/mocks/firefox-api.mock.js` | Existing mock supports all needed APIs |

## Risk Assessment

- **Blast radius:** Firefox extension only — Chrome unaffected
- **Rollback:** Revert the commit
- **Manual verification:** Requires AUTH_ENABLED=true (deferred to #405)
