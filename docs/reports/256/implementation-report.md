# Implementation Report: Firefox OAuth Tabs-Based Flow

**Issue:** #256
**Branch:** `256-firefox-oauth-tabs`
**Date:** 2026-01-10

## Summary

Fixed Firefox OAuth authentication by replacing the non-existent `browser.identity` API with a tabs-based OAuth flow. Firefox MV3 does not have `browser.identity` (Chrome-only), causing OAuth to completely fail.

## Problem

The Firefox `auth.js` was using `browser.identity.launchWebAuthFlow()` and `browser.identity.getRedirectURL()`, which don't exist in Firefox's WebExtensions API. This was a silent failure that wasn't caught during development because:

1. Chrome and Firefox extensions shared no unit tests for auth
2. The mock incorrectly provided a fake `browser.identity` API
3. No runtime testing was performed on Firefox

## Solution

Implemented a tabs-based OAuth flow that works in Firefox MV3:

### 1. Lambda Callback Endpoint (`src/lambda_auth_function.py`)

Added `handle_oauth_callback()` function that:
- Handles GET requests to `/auth/callback`
- Receives OAuth redirect from LinkedIn with `?code=...&state=...`
- Returns minimal HTML page with code/state in URL
- Extension monitors tab URL to extract code

```python
def handle_oauth_callback(query_params: dict) -> dict:
    """Handle OAuth callback redirect from LinkedIn."""
    code = query_params.get("code", "")
    state = query_params.get("state", "")
    error = query_params.get("error", "")
    # Returns HTML page (extension monitors URL for code extraction)
```

### 2. Firefox Auth Module (`extensions/firefox/auth.js`)

Replaced identity-based flow with tabs-based flow:

- **`getRedirectURL()`**: Returns Lambda callback URL instead of `browser.identity.getRedirectURL()`
- **`waitForOAuthCallback(tabId, callbackUrl)`**: New function that:
  - Monitors tab URL changes via `browser.tabs.onUpdated`
  - Detects when tab navigates to callback URL
  - Extracts code and state from URL params
  - Handles tab close (user cancellation)
  - 5-minute timeout for login flow
- **`initiateLogin()`**: Rewritten to:
  1. Generate CSRF state
  2. Store state in session storage
  3. Open auth tab with `browser.tabs.create()`
  4. Wait for callback via URL monitoring
  5. Validate state (CSRF protection)
  6. Exchange code for tokens via Lambda

### 3. Firefox Mock (`tests/mocks/firefox-api.mock.js`)

Added tab lifecycle simulation for testing:
- `tabs.create()` - Creates mock tabs with auto-incrementing IDs
- `tabs.remove()` - Removes mock tabs
- `tabs.onUpdated.addListener/removeListener` - Handler registration
- `__simulateTabUpdate(tabId, url, status)` - Test utility to simulate navigation
- `__triggerTabRemoved(tabId, removeInfo)` - Test utility for tab close

### 4. Firefox Auth Tests (`tests/unit/firefox/auth.test.js`)

Updated all tests to work with tabs-based flow:
- **Namespace Verification**: Now verifies NO `browser.identity` usage
- **CSRF Tests**: Simulate OAuth callback via `__simulateTabUpdate()`
- **Token Storage Tests**: Complete OAuth flow simulation
- **Tab Close Handling**: New test for user cancellation

## Files Changed

| File | Changes |
|------|---------|
| `src/lambda_auth_function.py` | Added `/auth/callback` endpoint |
| `extensions/firefox/auth.js` | Tabs-based OAuth flow |
| `tests/mocks/firefox-api.mock.js` | Tab lifecycle mocking |
| `tests/unit/firefox/auth.test.js` | Updated for tabs-based flow |

## Architecture

```
User clicks Login
       │
       ▼
┌─────────────────┐
│ generateState() │  Generate CSRF state
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│ browser.storage.session.set │  Store state for validation
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────┐
│ browser.tabs.create()   │  Open LinkedIn OAuth page
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────────┐
│ browser.tabs.onUpdated      │  Monitor tab URL changes
│ + browser.tabs.onRemoved    │
└────────────┬────────────────┘
             │ (user authenticates)
             ▼
┌──────────────────────────────────────┐
│ Tab navigates to Lambda /auth/callback│
│ ?code=...&state=...                   │
└────────────┬─────────────────────────┘
             │
             ▼
┌─────────────────────────┐
│ Validate state (CSRF)   │  Compare stored vs returned state
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ POST /auth/token        │  Exchange code for tokens
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ storeTokens()           │  Store in session/local storage
└─────────────────────────┘
```

## Security Considerations

1. **CSRF Protection**: State parameter generated with `crypto.getRandomValues()`, validated on callback
2. **Token Hierarchy**: Access token in session storage (cleared on browser close), refresh token in local storage
3. **Lambda Callback**: Only returns HTML page, no token exchange happens at callback URL
4. **Tab Cleanup**: Auth tab automatically closed after callback detection

## Deployment Notes

After merging, the Lambda callback URL must be registered with LinkedIn OAuth app:
- URL: `https://sk33bz56yi5qlbrrwzqnprmeuy0xwhzn.lambda-url.us-east-1.on.aws/auth/callback`
- LinkedIn Developer Portal > App Settings > Auth > Redirect URLs

## Related Documents

- LLD: `docs/lld/active/1206-firefox-oauth.md`
- Audit: `docs/0826-audit-cross-browser-testing.md`
- ADR: `docs/0215-test-first-philosophy.md`
