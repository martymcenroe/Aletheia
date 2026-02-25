# Test Report — Issue #396: Firefox OAuth Persistent State Fix

## Test Results

### Firefox Service Worker Tests
```
35 passed | 0 failed
```

### Full Unit Suite
```
15 test files | 368 passed | 4 skipped | 0 failed
```

## START_OAUTH Test Coverage (8 tests)

| Test | Verifies |
|------|----------|
| opens auth tab with correct URL | `chrome.tabs.create` called with authUrl |
| stores pendingOAuth in session storage | `chrome.storage.session.set` called with `{ pendingOAuth: { tabId, state, callbackUrl, lambdaAuthUrl, startedAt } }` |
| top-level listener detects callback and stores tokens | Simulate tab update → fetch token exchange → session/local storage set → pendingOAuth cleared |
| validates CSRF state | Mismatched state → no fetch, pendingOAuth cleared |
| clears pendingOAuth when tab closed | Simulate tab removed → `storage.session.remove('pendingOAuth')` called |
| detects stale OAuth (>5 min) | Old `startedAt` → no fetch, pendingOAuth cleared |
| handles token exchange failure | Mock fetch 500 → pendingOAuth cleared, no tokens stored |
| ignores tab updates with no pendingOAuth | Tab update without START_OAUTH → no errors, no fetch |
| stale check uses 5-minute threshold from source | Source code contains timeout constant |

## Verification Checklist

- [x] Firefox SW tests: 35/35 pass
- [x] Full unit suite: 368 pass, 0 fail
- [x] No mock changes needed
- [x] Chrome tests unaffected
- [ ] Manual Firefox testbook TC-05 (requires AUTH_ENABLED=true, deferred to #405)
