# Test Report — Issue #444

## Test Execution

| Suite | Command | Result |
|-------|---------|--------|
| Firefox service-worker | `npx vitest run tests/unit/firefox/service-worker.test.js` | PASS |

## Before Fix

- 19 test failures in `tests/unit/firefox/service-worker.test.js` (all non-file-verification tests)
- Root cause: `global.chrome` not set, so service worker source evaluation silently failed

## After Fix

- 33 tests passed, 0 failed
- 26 existing tests restored + 7 new START_OAUTH tests

## New Test Coverage

| Test | Description | Duration |
|------|-------------|----------|
| returns true for async response | Verifies handler signals async | 1ms |
| opens auth tab with correct URL | `tabs.create` called with auth URL | 61ms |
| stores tokens on successful callback | Session + local storage verified | 263ms |
| responds with user info on success | sendResponse includes user object | 265ms |
| rejects on CSRF state mismatch | Tokens NOT stored on wrong state | 264ms |
| handles tab closure (OAuth cancelled) | Tokens NOT stored when tab closed | 263ms |
| times out after 5 minutes | Source contains 5-minute timeout | 1ms |

## NOT Tested

- Chrome service-worker tests (separate test file, not affected)
- E2E OAuth flow (requires real browser, covered by testbook TC-05/TC-06)
- Token refresh flow (separate mechanism, not part of START_OAUTH handler)
