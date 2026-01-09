# 1206 - Feature: Firefox LinkedIn OAuth Authentication

## 1. Context & Goal

* **Issue:** #206
* **Objective:** Port LinkedIn OAuth authentication from Chrome to Firefox extension, achieving feature parity.
* **Status:** LLD Draft (Revised per Gemini Review)
* **Related Issues:** #116 (Chrome OAuth implementation), #214 (Firefox test parity)
* **Parent LLD:** `docs/1116-linkedin-oauth.md` (Chrome implementation)

### Background

Issue #116 implemented LinkedIn OAuth for the Chrome extension. The Firefox extension (`extensions/firefox/`) currently lacks authentication, creating a feature gap:

| Feature | Chrome | Firefox |
|---------|--------|---------|
| LinkedIn OAuth | ✅ auth.js (350 lines) | ❌ Missing |
| Login view | ✅ popup.html | ❌ Missing |
| User bar | ✅ popup.html/popup.js | ❌ Missing |
| Age gate | ✅ Integrated | ❌ Missing |
| Restricted view | ✅ popup.html | ❌ Missing |

### Firefox Extension Context

The Firefox extension is **Manifest V3** (like Chrome), which means:
- `browser.storage.session` is available (access token storage)
- `browser.identity.launchWebAuthFlow` is available
- Background scripts syntax differs slightly: `"scripts": ["service-worker.js"]` vs Chrome's `"service_worker"`

## 2. Requirements

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| R1 | OAuth 2.0 flow with LinkedIn | User can authenticate via `browser.identity.launchWebAuthFlow` |
| R2 | Secure token storage | Access token in `browser.storage.session`, refresh token in `browser.storage.local` |
| R3 | Session management | Lazy refresh on action (same as Chrome) |
| R4 | Login UI in popup | Login button visible when not authenticated |
| R5 | Auth status indicator | User bar shows display name when logged in |
| R6 | Logout/disconnect | User can disconnect and clear tokens |
| R7 | Age gate integration | Restricted view for age-gated sites |
| R8 | CSRF protection | Cryptographically random state parameter |
| R9 | Mock mode for testing | `MOCK_MODE` flag for deterministic fake tokens |
| R10 | Feature parity with Chrome | Firefox popup matches Chrome popup behavior |
| R11 | **Unit test coverage (Module E)** | `tests/unit/firefox/auth.test.js` and `tests/unit/firefox/popup.test.js` pass |
| R12 | **Test parity with Chrome** | `npm run test:unit` runs BOTH Chrome and Firefox test suites |

## 3. Alternatives Considered

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| A. Port auth.js with minimal changes | Fast, proven code | API namespace differences (`browser.*` vs `chrome.*`) | **Selected** |
| B. Create abstraction layer | Single codebase | Over-engineering for 2 files | **Rejected** |
| C. Use WebExtension polyfill | Browser-agnostic code | Additional dependency, complexity | **Rejected** |

**Rationale:** Firefox's `browser.*` API is nearly identical to Chrome's `chrome.*` API for identity and storage. A direct port with namespace changes is simplest.

## 4. Data & Fixtures

### 4.1 Data Pipeline

Same as Chrome (LLD 1116 §4.2):
```
User Click ──launchWebAuthFlow──► LinkedIn ──callback──► Extension ──code──► Lambda ──validate──► DynamoDB
```

### 4.2 Firefox-Specific Configuration

| Attribute | Chrome | Firefox |
|-----------|--------|---------|
| API namespace | `chrome.*` | `browser.*` |
| Redirect URL | `https://{id}.chromiumapp.org/` | `https://{id}.extensions.allizom.org/` |
| Identity API | `chrome.identity` | `browser.identity` |
| Session storage | `chrome.storage.session` | `browser.storage.session` (MV3) |

### 4.3 LinkedIn OAuth App Configuration

The existing LinkedIn OAuth app needs an additional redirect URI:

```
Redirect URIs (LinkedIn Developer Portal):
1. https://{chrome-extension-id}.chromiumapp.org/     (existing)
2. https://{firefox-extension-id}.extensions.allizom.org/  (NEW)
```

**Note:** Firefox extension ID is defined in `manifest.json`:
```json
"browser_specific_settings": {
  "gecko": {
    "id": "extension@aletheia.study"
  }
}
```

The redirect URL format for Firefox is: `https://extensions.allizom.org/{gecko-id}/`

## 5. Diagram

```mermaid
sequenceDiagram
    participant User
    participant Popup as Firefox Popup
    participant Auth as auth.js (Firefox)
    participant Browser as browser.identity
    participant LI as LinkedIn OAuth
    participant Lambda as AWS Lambda

    User->>Popup: Click "Login with LinkedIn"
    Popup->>Auth: AletheiaAuth.initiateLogin()

    Note over Auth: Generate crypto state
    Note over Auth: Store in browser.storage.session

    Auth->>Browser: launchWebAuthFlow(authUrl)
    Browser->>LI: Authorization Request
    LI->>User: LinkedIn Login Page
    User->>LI: Credentials
    LI->>Browser: Redirect with code + state
    Browser->>Auth: Callback URL

    Note over Auth: Validate state (CSRF)
    Auth->>Lambda: POST /auth/token {code}
    Lambda->>Auth: {accessToken, refreshToken, user}

    Note over Auth: Store tokens
    Auth->>Popup: Update UI (logged in)
```

## 6. Technical Approach

### 6.1 Files to Create/Modify

#### Extension Files

| File | Action | Description |
|------|--------|-------------|
| `extensions/firefox/auth.js` | **CREATE** | Port from Chrome with `browser.*` namespace |
| `extensions/firefox/popup.html` | **MODIFY** | Add login-view, user-bar, restricted-view, checking-view |
| `extensions/firefox/popup.js` | **MODIFY** | Add auth integration, age gate logic |
| `extensions/firefox/popup.css` | **MODIFY** | Add auth-related styles (if not present) |
| `extensions/firefox/manifest.json` | **MODIFY** | Add `identity` permission |

#### Test Infrastructure Files (MANDATORY per ADR 0215 Module E)

| File | Action | Description |
|------|--------|-------------|
| `tests/mocks/firefox-api.mock.js` | **CREATE** | Mock `browser.identity`, `browser.storage`, `browser.runtime`, `browser.tabs` |
| `tests/unit/firefox/auth.test.js` | **CREATE** | Unit tests for Firefox auth.js (mirrors Chrome auth tests) |
| `tests/unit/firefox/popup.test.js` | **CREATE** | Unit tests for Firefox popup.js view switching |
| `vitest.config.js` | **MODIFY** | Ensure Firefox tests are included in test suite |

### 6.2 auth.js Port Strategy

The Chrome `auth.js` (350 lines) needs these changes for Firefox:

```javascript
// CHANGE 1: API namespace (global find/replace)
// Chrome: chrome.identity, chrome.storage
// Firefox: browser.identity, browser.storage

// CHANGE 2: Redirect URL helper
// Chrome: chrome.identity.getRedirectURL()
// Firefox: browser.identity.getRedirectURL()
// NOTE: Both return the correct format for their platform

// CHANGE 3: Promise-based APIs (Firefox native)
// Chrome: chrome.* APIs return Promises in MV3
// Firefox: browser.* APIs return Promises natively
// No change needed - both are Promise-based in MV3
```

### 6.3 Manifest Changes

```json
// extensions/firefox/manifest.json - ADD identity permission
{
  "permissions": [
    "activeTab",
    "tabs",
    "scripting",
    "contextMenus",
    "storage",
    "identity"  // NEW - required for launchWebAuthFlow
  ]
}
```

### 6.4 popup.html Changes

Add these views from Chrome popup.html:

1. **Login View** - Lines 13-33 from Chrome popup.html
2. **User Bar** - Lines 38-41 from Chrome popup.html (inside main-view)
3. **Restricted View** - Lines 109-117 from Chrome popup.html
4. **Checking View** - Lines 119-125 from Chrome popup.html
5. **Script tag** - Add `<script src="auth.js"></script>` before popup.js

### 6.5 popup.js Changes

Port auth-related functions from Chrome popup.js:

```javascript
// ADD: Auth state management
async function init() {
    // Check authentication first
    const isAuthed = await AletheiaAuth.isAuthenticated();

    if (!isAuthed) {
        showView('login');
        return;
    }

    // Check age gate for current tab
    await checkAgeGate();
}

// ADD: Login handler
async function handleLoginClick() {
    const loginButton = document.getElementById('login-button');
    const loginError = document.getElementById('login-error');

    loginButton.disabled = true;
    loginButton.textContent = 'Signing in...';
    loginError.style.display = 'none';

    try {
        await AletheiaAuth.initiateLogin();
        await checkAgeGate();
    } catch (error) {
        loginError.textContent = `Login failed: ${error.message}`;
        loginError.style.display = 'block';
        // Reset button (use DOM methods, not innerHTML)
        loginButton.disabled = false;
        loginButton.textContent = '';
        const iconSpan = document.createElement('span');
        iconSpan.className = 'linkedin-icon';
        iconSpan.textContent = 'in';
        loginButton.appendChild(iconSpan);
        loginButton.appendChild(document.createTextNode(' Sign in with LinkedIn'));
    }
}

// ADD: Logout handler
async function handleLogoutClick() {
    await AletheiaAuth.logout();
    showView('login');
}

// ADD: User bar update
async function updateUserBar() {
    const authState = await AletheiaAuth.getAuthState();
    const userName = document.getElementById('user-name');
    if (authState && userName) {
        userName.textContent = authState.displayName || 'User';
    }
}

// ADD: Age gate check (simplified - Firefox doesn't have content-safety.js)
async function checkAgeGate() {
    showView('checking');

    // For Firefox MVP: Skip age gate, go directly to main view
    // Age gate requires content-safety.js which is Chrome-only (Issue #104)
    // TODO: Port content-safety.js to Firefox in future issue

    showView('main');
    await renderMainView();
    await updateUserBar();
}
```

### 6.6 API Compatibility Matrix

| API | Chrome | Firefox MV3 | Notes |
|-----|--------|-------------|-------|
| `identity.launchWebAuthFlow` | ✅ | ✅ | Same signature |
| `identity.getRedirectURL` | ✅ | ✅ | Returns platform-specific URL |
| `storage.session` | ✅ | ✅ | Available in MV3 |
| `storage.local` | ✅ | ✅ | Same API |
| `tabs.query` | ✅ | ✅ | Same API |

### 6.7 Test Infrastructure (MANDATORY)

**Per ADR 0215 Module E:** All extension logic must be unit tested via Vitest.

#### 6.7.1 Firefox API Mock (`tests/mocks/firefox-api.mock.js`)

```javascript
// tests/mocks/firefox-api.mock.js
// Mock Firefox browser.* APIs for Vitest

import { vi } from 'vitest';

export function createFirefoxMock(options = {}) {
  const { allowlist = [], tabUrl = 'https://example.com', authenticated = false } = options;

  let storageData = {
    allowlist: [...allowlist],
    ...(authenticated ? {
      refreshToken: 'mock-refresh-token',
      userId: 'mock-user-123',
      displayName: 'Test User'
    } : {})
  };

  let sessionData = authenticated ? {
    accessToken: 'mock-access-token',
    expiresAt: Date.now() + 3600000
  } : {};

  return {
    identity: {
      launchWebAuthFlow: vi.fn().mockImplementation(({ url }) => {
        // Extract state from URL for CSRF testing
        const urlObj = new URL(url);
        const state = urlObj.searchParams.get('state');
        return Promise.resolve(`https://redirect.url/?code=mock-code&state=${state}`);
      }),
      getRedirectURL: vi.fn().mockReturnValue('https://mock-extension-id.extensions.allizom.org/')
    },
    storage: {
      local: {
        get: vi.fn().mockImplementation((keys) => {
          if (typeof keys === 'string') {
            return Promise.resolve({ [keys]: storageData[keys] });
          }
          return Promise.resolve({ ...storageData });
        }),
        set: vi.fn().mockImplementation((items) => {
          Object.assign(storageData, items);
          return Promise.resolve();
        }),
        remove: vi.fn().mockImplementation((keys) => {
          const keysArray = Array.isArray(keys) ? keys : [keys];
          keysArray.forEach(k => delete storageData[k]);
          return Promise.resolve();
        })
      },
      session: {
        get: vi.fn().mockImplementation((keys) => {
          if (typeof keys === 'string') {
            return Promise.resolve({ [keys]: sessionData[keys] });
          }
          return Promise.resolve({ ...sessionData });
        }),
        set: vi.fn().mockImplementation((items) => {
          Object.assign(sessionData, items);
          return Promise.resolve();
        }),
        remove: vi.fn().mockImplementation((keys) => {
          const keysArray = Array.isArray(keys) ? keys : [keys];
          keysArray.forEach(k => delete sessionData[k]);
          return Promise.resolve();
        })
      }
    },
    tabs: {
      query: vi.fn().mockResolvedValue([{ id: 1, url: tabUrl, active: true }])
    },
    runtime: {
      id: 'mock-firefox-extension-id',
      sendMessage: vi.fn().mockResolvedValue({ state: 'allowed' })
    },
    // Test helpers (not part of real API)
    __setStorageData: (data) => { storageData = data; },
    __setSessionData: (data) => { sessionData = data; },
    __getStorageData: () => storageData,
    __getSessionData: () => sessionData
  };
}
```

#### 6.7.2 Firefox auth.test.js Structure

```javascript
// tests/unit/firefox/auth.test.js
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { createFirefoxMock } from '../../mocks/firefox-api.mock.js';

describe('Firefox Auth Module', () => {
  let browserMock;

  beforeEach(() => {
    browserMock = createFirefoxMock();
    global.browser = browserMock;
    global.crypto = {
      getRandomValues: (arr) => {
        for (let i = 0; i < arr.length; i++) arr[i] = Math.floor(Math.random() * 256);
        return arr;
      }
    };
    global.fetch = vi.fn();
  });

  describe('generateState', () => {
    it('generates 64-character hex string', () => {
      // Test CSRF state generation
    });

    it('generates unique values', () => {
      // Test uniqueness
    });
  });

  describe('CSRF Protection', () => {
    it('rejects mismatched state parameter', async () => {
      // Test that CSRF mismatch throws error
    });

    it('accepts matching state parameter', async () => {
      // Test valid state flow
    });
  });

  describe('Token Storage', () => {
    it('stores access token in session storage', async () => {
      // Verify browser.storage.session used for access token
    });

    it('stores refresh token in local storage', async () => {
      // Verify browser.storage.local used for refresh token
    });

    it('clears all tokens on logout', async () => {
      // Verify clearTokens() removes from both storages
    });
  });

  describe('Mock Mode', () => {
    it('returns deterministic mock user when MOCK_MODE=true', async () => {
      // Test mock login
    });
  });

  describe('Namespace Verification', () => {
    it('uses browser.identity not chrome.identity', () => {
      // CRITICAL: Verify we call browser.*, not chrome.*
      // This catches the exact bug Gemini warned about
    });

    it('uses browser.storage.session not chrome.storage.session', () => {
      // Verify correct namespace
    });
  });
});
```

#### 6.7.3 Firefox popup.test.js Structure

```javascript
// tests/unit/firefox/popup.test.js
import { describe, it, expect, beforeEach } from 'vitest';
import { JSDOM } from 'jsdom';
import { createFirefoxMock } from '../../mocks/firefox-api.mock.js';

describe('Firefox Popup', () => {
  describe('View Switching', () => {
    it('shows login view when not authenticated', async () => {
      // Test unauthenticated state
    });

    it('shows main view when authenticated', async () => {
      // Test authenticated state
    });

    it('shows checking view during age gate check', async () => {
      // Test intermediate state
    });
  });

  describe('Auth Integration', () => {
    it('calls AletheiaAuth.initiateLogin on button click', async () => {
      // Test login button handler
    });

    it('shows error on login failure', async () => {
      // Test error handling
    });

    it('updates user bar after successful login', async () => {
      // Test user bar display
    });
  });
});
```

#### 6.7.4 Test Parity Requirement

Update `package.json` to run both Chrome and Firefox tests:

```json
{
  "scripts": {
    "test:unit": "vitest run tests/unit/",
    "test:unit:chrome": "vitest run tests/unit/popup.test.js tests/unit/auth.test.js",
    "test:unit:firefox": "vitest run tests/unit/firefox/",
    "test:unit:all": "vitest run tests/unit/"
  }
}
```

**Requirement:** `npm run test:unit` MUST run both Chrome and Firefox tests. A failure in either blocks the PR.

## 7. Interface Specification

### 7.1 Firefox auth.js Exports

Same as Chrome (LLD 1116 §7.2):

```javascript
window.AletheiaAuth = {
    initiateLogin,      // Start OAuth flow
    logout,             // Clear all tokens
    isAuthenticated,    // Check if user is logged in
    getAuthState,       // Get {userId, displayName} or null
    getAccessToken,     // Get valid token (lazy refresh)
    clearTokens,        // Clear all auth data
    getConfig           // Get config (CLIENT_ID masked)
};
```

### 7.2 View States

| View | Condition | Elements Shown |
|------|-----------|----------------|
| `login` | Not authenticated | Logo, welcome message, LinkedIn button |
| `checking` | Auth OK, checking age gate | Spinner |
| `restricted` | Age-gated site detected | "Not Permitted" message |
| `main` | Auth OK, site allowed | User bar, domain card, power button |
| `manage` | User clicked "Manage Allowlist" | Allowlist management |
| `confirm` | User clicked "Clear All Data" | Confirmation dialog |

## 8. Security Considerations

Same as Chrome (LLD 1116 §8), plus:

| Concern | Firefox-Specific Mitigation |
|---------|----------------------------|
| Extension ID stability | Firefox uses `gecko.id` in manifest - stable across installs |
| Redirect URL security | Firefox validates redirect matches registered extension |
| Storage isolation | `browser.storage` is extension-isolated |

## 9. Performance Considerations

| Metric | Budget | Notes |
|--------|--------|-------|
| Login latency | < 3s | Same as Chrome |
| Token refresh | < 500ms | Same as Chrome |
| Popup load | < 200ms | Auth check is async, doesn't block render |

## 10. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Firefox identity API differences | Med | Low | Test early, fallback to manual flow if needed |
| Redirect URL registration failure | High | Low | Test with LinkedIn app before PR |
| Storage.session unavailable | High | Very Low | Firefox MV3 supports it; fallback to local |
| Age gate not portable | Med | Med | Skip for MVP, document as known limitation |

## 11. Verification & Testing

### 11.1 Test Scenarios

| ID | Scenario | Type | Test File | Expected Output |
|----|----------|------|-----------|-----------------|
| 010 | Mock mode login | **Auto** | `firefox/auth.test.js` | Mock tokens stored in browser.storage |
| 020 | CSRF state generation | **Auto** | `firefox/auth.test.js` | 64-char hex, unique values |
| 030 | CSRF state validation | **Auto** | `firefox/auth.test.js` | Mismatched state rejected with error |
| 040 | Token storage hierarchy | **Auto** | `firefox/auth.test.js` | Access in session, refresh in local |
| 050 | Logout clears all tokens | **Auto** | `firefox/auth.test.js` | Both storages cleared |
| 060 | Namespace verification | **Auto** | `firefox/auth.test.js` | `browser.*` called, not `chrome.*` |
| 070 | Login view on unauthenticated | **Auto** | `firefox/popup.test.js` | Login view displayed |
| 080 | Main view on authenticated | **Auto** | `firefox/popup.test.js` | Main view with user bar |
| 090 | Login button handler | **Auto** | `firefox/popup.test.js` | Calls AletheiaAuth.initiateLogin |
| 100 | Error display on login failure | **Auto** | `firefox/popup.test.js` | Error message shown |
| 110 | Fresh login E2E | Manual | N/A | LinkedIn popup, user bar shows name |
| 120 | Token persists in session | Manual | N/A | Reopen popup, still logged in |
| 130 | Browser close clears access | Manual | N/A | Access token gone, refresh needed |

### 11.2 Manual Smoke Test

1. Load Firefox extension via `about:debugging`
2. Click extension icon - verify login view shown
3. Click "Sign in with LinkedIn"
4. Complete LinkedIn authentication
5. Verify popup shows user name and main view
6. Open DevTools → Storage Inspector - verify:
   - Session Storage has accessToken
   - Local Storage has refreshToken, userId, displayName
7. Click logout - verify login view returns
8. Close Firefox completely, reopen - verify must re-login

### 11.3 LinkedIn App Configuration Test

Before implementation:
1. Get Firefox extension ID: `extension@aletheia.study`
2. Add redirect URI to LinkedIn Developer Portal:
   `https://extensions.allizom.org/extension@aletheia.study/`
3. Test redirect URL in browser to confirm format

## 12. Definition of Done

### Code
- [ ] `extensions/firefox/auth.js` created (port from Chrome)
- [ ] `extensions/firefox/popup.html` updated with auth views
- [ ] `extensions/firefox/popup.js` updated with auth handlers
- [ ] `extensions/firefox/popup.css` has auth styles
- [ ] `extensions/firefox/manifest.json` has `identity` permission
- [ ] LinkedIn app has Firefox redirect URI registered

### Test Infrastructure (MANDATORY - Blocks PR)
- [ ] `tests/mocks/firefox-api.mock.js` created with full browser.* mock
- [ ] `tests/unit/firefox/auth.test.js` created and passing
- [ ] `tests/unit/firefox/popup.test.js` created and passing
- [ ] `npm run test:unit` runs BOTH Chrome and Firefox tests
- [ ] All automated tests pass (010-100 in §11.1)

### Manual Verification
- [ ] Manual OAuth flow works in Firefox (110-130 in §11.1)
- [ ] Storage hierarchy verified via DevTools

### Documentation
- [ ] Implementation report created
- [ ] Test report created
- [ ] Known limitations documented (age gate deferred)

### Review
- [ ] Code review completed
- [ ] Pre-merge gate passed
- [ ] Firefox Add-ons compatibility verified
- [ ] **Gemini sign-off on test coverage**

---

## Appendix A: Chrome vs Firefox auth.js Diff

The port requires only namespace changes. Key search/replace:

| Search | Replace | Count (approx) |
|--------|---------|----------------|
| `chrome.identity` | `browser.identity` | 3 |
| `chrome.storage` | `browser.storage` | 8 |
| `chrome.runtime` | `browser.runtime` | 1 |

No logic changes required - APIs are compatible.

## Appendix B: Known Limitations

### Age Gate (Deferred)

Chrome's age gate relies on:
- `content-safety.js` - Content script for age detection
- `content-check.js` - Page signal inspection
- Service worker tab state management

These are Chrome-specific (Issue #104). For Firefox MVP:
- **Skip age gate** - Go directly to main view after auth
- **Future issue** - Port content-safety.js to Firefox

### Manifest V2 Fallback (Not Needed)

Firefox extension is already MV3, so `browser.storage.session` is available. No MV2 fallback needed.

## Appendix C: File Sizes (Effort Estimate)

### Extension Files

| File | Chrome Lines | Firefox Changes |
|------|--------------|-----------------|
| auth.js | 350 | ~10 lines changed (namespace) |
| popup.html | 132 | ~50 lines added (views) |
| popup.js | 494 → 317 (Firefox simpler) | ~100 lines added (auth) |
| popup.css | Same | ~20 lines added (auth styles) |

### Test Files (NEW)

| File | Estimated Lines | Description |
|------|-----------------|-------------|
| `tests/mocks/firefox-api.mock.js` | ~80 | Full browser.* mock |
| `tests/unit/firefox/auth.test.js` | ~200 | Auth module tests |
| `tests/unit/firefox/popup.test.js` | ~150 | Popup view tests |

**Total Effort:** ~180 lines (extension) + ~430 lines (tests) = **~610 lines**

### Why Tests Add 2.4x Effort

The test infrastructure is essential:
1. **Namespace verification tests** catch the exact bug Gemini warned about (using `chrome.*` instead of `browser.*`)
2. **CSRF tests** verify security-critical state handling
3. **Storage tests** ensure token hierarchy is correct
4. **Mock infrastructure** enables future Firefox tests without duplication

This is the "Warrior" standard: tests prove the code works, not just that it was written.

---

## Appendix D: Gemini Review Response

**Review Date:** 2026-01-09
**Reviewer:** Gemini (Security Architect / Strategist)
**Initial Verdict:** REJECTED

### Issue Identified

> "The LLD completely ignores Module E: Frontend Logic Testing. It proposes writing critical authentication code (`auth.js`) without a single line of automated verification."

### Risk Called Out

> "If `auth.js` has a typo in the `browser.*` namespace (e.g., `browser.storage.local` vs `browser.storage.session`), it will crash silently in production."

### Fix Applied

1. Added R11 (Unit test coverage) and R12 (Test parity) to Requirements
2. Added §6.7 Test Infrastructure section with:
   - Firefox API mock specification
   - auth.test.js structure with namespace verification tests
   - popup.test.js structure
   - package.json script requirements
3. Updated §11.1 Test Scenarios: 10 automated tests, 3 manual
4. Updated §12 Definition of Done with mandatory test infrastructure checklist
5. Updated Appendix C with test file effort estimates

### Key Addition: Namespace Verification Tests

```javascript
describe('Namespace Verification', () => {
  it('uses browser.identity not chrome.identity', () => {
    // CRITICAL: Verify we call browser.*, not chrome.*
    // This catches the exact bug Gemini warned about
  });
});
```

**Revised Status:** Ready for re-review
