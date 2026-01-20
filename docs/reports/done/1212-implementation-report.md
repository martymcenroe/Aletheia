# Implementation Report: Issue #212 - Chrome Service Worker Tests

**Issue:** #212 - Chrome Service Worker Tests
**Date:** 2026-01-09
**Author:** Claude Opus 4.5

## Summary

Created comprehensive unit tests for Chrome extension's `service-worker.js` module, verifying message handlers, installation events, age gate functionality, context menu handling, and API integration.

## What Was Built

### New Test File: `tests/unit/chrome/service-worker.test.js`

23 unit tests organized into 9 test suites:

1. **Service Worker File** (4 tests)
   - File existence verification
   - API_ENDPOINT constant definition
   - CLIENT_VERSION constant definition
   - TabState object definition

2. **Installation Events** (3 tests)
   - onInstalled listener registration
   - Context menu creation on install
   - "Explain with AI" menu item configuration

3. **Message Handlers** (4 tests)
   - onMessage listener registration
   - GET_TAB_STATE message handling
   - RECHECK_TAB async response handling
   - Unknown tab state handling

4. **Security - Sender Validation** (3 tests)
   - Rejects messages from unknown extensions
   - Accepts messages from own extension
   - Accepts messages from content scripts (undefined sender.id)

5. **Age Gate - Tab State Management** (2 tests)
   - tabs.onRemoved listener registration
   - Tab state cleanup on close

6. **Context Menu Click Handler** (3 tests)
   - contextMenus.onClicked listener registration
   - explain-with-ai menu handling
   - Warning badge when site not in allowlist

7. **Badge State** (1 test)
   - Success badge on API response

8. **API Integration** (2 tests)
   - X-Aletheia-Client-Version header
   - NoArchive signal in payload

9. **Error Handling** (1 test)
   - API fetch error handling

### Chrome Mock Extensions: `tests/mocks/chrome-api.mock.js`

Extended the Chrome API mock with service worker APIs:
- `chrome.contextMenus.create()` and `onClicked`
- `chrome.scripting.executeScript()`
- `chrome.action.setBadgeText()` and `setBadgeBackgroundColor()`
- `chrome.tabs.onRemoved`
- `chrome.runtime.onInstalled`

Test utilities added:
- `__simulateMessage()` - Simulate messages to registered listeners
- `__triggerOnInstalled()` - Trigger installation handlers
- `__triggerContextMenuClick()` - Simulate context menu clicks
- `__triggerTabRemoved()` - Simulate tab close events
- `__getBadgeState()` - Inspect badge state per tab
- `__setScriptInjectionResults()` - Configure script injection returns

## Design Decisions

1. **Event-Driven Testing Challenge**: Service workers are event-driven with no direct function exports. Solved by:
   - Capturing registered event listeners in mock
   - Providing `__simulateMessage()` to trigger handlers
   - Providing `__triggerOnInstalled()` for install events

2. **Message Handler Simulation**: The `__simulateMessage()` utility properly handles async responses (when handler returns `true`) by waiting for `sendResponse` callback.

3. **Defensive Test Cleanup**: Used `cleanupEnvironment()` pattern matching auth tests to prevent cross-test pollution.

## Files Changed

| File | Change |
|------|--------|
| `tests/unit/chrome/service-worker.test.js` | Created (23 tests) |
| `tests/mocks/chrome-api.mock.js` | Extended with SW APIs |

## Test Architecture

```
service-worker.js (eval)
        ↓
Registers event listeners
        ↓
Mock captures listeners in arrays:
- messageListeners[]
- contextMenuClickHandlers[]
- installHandlers[]
- tabRemovedHandlers[]
        ↓
Test triggers via __simulate*() methods
        ↓
Assert on responses/side effects
```

## Dependencies

No new dependencies. Uses existing Vitest framework.

## Known Limitations

- Some integration scenarios (like full API round-trip with overlay injection) are simplified in mocks
- Script injection results are pre-configured, not dynamically computed
- Badge state verification is based on mock storage, not visual inspection
