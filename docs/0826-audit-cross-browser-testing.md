# 0826 - Cross-Browser Testing Audit

**Status:** CRITICAL FAILURE
**Date:** 2026-01-09
**Triggered by:** Firefox extension completely broken in production

---

## Executive Summary

The Firefox extension shipped with:
1. Missing CSS (178 lines) - login UI broken
2. Missing files (`content-check.js`, `content-safety.js`)
3. Broken OAuth - uses `browser.identity` which doesn't exist in Firefox
4. Zero E2E coverage in actual Firefox browser

**All unit tests passed.** This audit explains why and prescribes fixes.

---

## 1. Root Cause Analysis

### 1.1 Mock Fidelity Lie

**File:** `tests/mocks/firefox-api.mock.js` lines 111-134

```javascript
// THIS IS A LIE - Firefox has NO identity API
identity: {
  launchWebAuthFlow: vi.fn()...
  getRedirectURL: vi.fn()...
}
```

**Reality:** Firefox MV3 does not implement `browser.identity`. The mock claims it does. Tests pass against fictional APIs.

**MDN Compatibility:**
| API | Chrome | Firefox |
|-----|--------|---------|
| `identity.launchWebAuthFlow` | ✅ | ❌ |
| `identity.getRedirectURL` | ✅ | ❌ |
| `storage.session` | ✅ | ✅ (v115+) |

### 1.2 Zero Firefox E2E Coverage

**E2E test files (all Chrome-only):**
- `waf-integration.spec.js`
- `age-gate.spec.js`
- `xss-protection.spec.js`
- `museum-label.spec.js`
- `visual-poc.spec.js`
- `accessibility.spec.js`
- `shadow-dom-security.spec.js`

**Firefox E2E tests:** 0

The extension was NEVER loaded in an actual Firefox browser during CI.

### 1.3 No File Parity Enforcement

Chrome and Firefox extensions should have identical files (except manifest.json). No automation verified this.

**Missing from Firefox on 2026-01-09:**
- `popup.css` - 178 lines of CSS missing (login, restricted, checking views)
- `content-check.js` - entire file missing
- `content-safety.js` - entire file missing

### 1.4 Copy-Paste Without Adaptation

`extensions/firefox/auth.js` was copied from Chrome without adapting for Firefox's different OAuth capabilities.

```javascript
// Line 1-6 of auth.js - THE IRONY
// CRITICAL: Uses browser.* namespace (NOT chrome.*)
// Firefox extension APIs use the WebExtensions browser.* standard
```

The comment claims Firefox compatibility while using Chrome-only APIs.

---

## 2. Testing Philosophy Failures

### 2.1 Over-Reliance on Unit Tests with Mocks

Unit tests verify code works WITH THE MOCK, not with the real browser. When the mock lies, tests are worthless.

**The Illusion of Coverage:**
```
tests/unit/firefox/auth.test.js     - 100% pass (against fake identity API)
tests/unit/firefox/popup.test.js    - 100% pass (never loads actual CSS)
tests/unit/firefox/service-worker.test.js - 100% pass (mocks everything)
```

### 2.2 Missing Test Layers

| Layer | Chrome | Firefox | Purpose |
|-------|--------|---------|---------|
| Unit Tests | ✅ | ✅ | Logic correctness (with mocks) |
| Integration Tests | ✅ | ❌ | Component interaction |
| E2E Tests | ✅ | ❌ | Real browser behavior |
| Visual Tests | ✅ | ❌ | UI rendering |
| API Fidelity Tests | ❌ | ❌ | Mock matches reality |
| File Parity Tests | ❌ | ❌ | Extensions have same files |

### 2.3 False Confidence from CI Green

CI showed all green because:
1. Unit tests use mocks that lie
2. E2E tests only run Chrome
3. No file parity check
4. No mock fidelity check

---

## 3. Specific Bugs Found

### 3.1 `browser.identity` Undefined

**Error:** `can't access property "getRedirectURL", browser.identity is undefined`

**Cause:** Firefox doesn't have `browser.identity` API

**Fix Required:** Implement Firefox OAuth using web-based flow:
- Use `browser.tabs.create()` to open LinkedIn auth page
- Use `browser.webRequest` or URL monitoring to capture redirect
- Or use a popup-based flow with message passing

### 3.2 Missing popup.css Styles

**Symptom:** LinkedIn button shows "in" as text instead of styled icon

**Cause:** Firefox `popup.css` was 178 lines shorter than Chrome version

**Missing styles:**
- `.restricted-view` (age gate)
- `.checking-view` (loading spinner)
- `.login-view` (OAuth)
- `.linkedin-icon` (button icon)
- `.user-bar` (logged-in state)

### 3.3 Missing Content Scripts

**Files missing from Firefox:**
- `content-check.js` - age restriction detection
- `content-safety.js` - content safety checks

**Consequence:** Age gate and content safety features completely non-functional

---

## 4. Prescribed Fixes

### 4.1 Immediate (P0)

1. **Fix Firefox OAuth** - Implement without `browser.identity`
2. **Sync all files** - Ensure Firefox has all Chrome files
3. **Add file parity test** - Automated check in CI

### 4.2 Short-term (P1)

4. **Add mock fidelity test** - Verify mocked APIs exist in real browser
5. **Add Firefox E2E tests** - Load extension in actual Firefox
6. **Add visual regression tests** - Screenshot comparison

### 4.3 Long-term (P2)

7. **Refactor to shared codebase** - Single source, build for both
8. **Add pre-commit hooks** - Block commits that break parity
9. **Documentation** - Document Firefox API differences

---

## 5. New Tests Required

### 5.1 File Parity Test

```javascript
// tests/parity/extension-files.test.js
test('Firefox has all Chrome files except manifest', () => {
  const chromeFiles = glob('extensions/chrome/**/*');
  const firefoxFiles = glob('extensions/firefox/**/*');

  for (const file of chromeFiles) {
    if (file === 'manifest.json') continue;
    expect(firefoxFiles).toContain(file);
  }
});

test('Shared files are identical', () => {
  const sharedFiles = ['popup.css', 'popup.html', 'overlay.js', ...];
  for (const file of sharedFiles) {
    const chrome = read(`extensions/chrome/${file}`);
    const firefox = read(`extensions/firefox/${file}`);
    expect(firefox).toEqual(chrome);
  }
});
```

### 5.2 Mock Fidelity Test

```javascript
// tests/mocks/mock-fidelity.test.js
test('Firefox mock only includes real Firefox APIs', () => {
  const FIREFOX_UNSUPPORTED = [
    'identity.launchWebAuthFlow',
    'identity.getRedirectURL',
    // Add others as discovered
  ];

  const mock = createFirefoxMock();

  for (const api of FIREFOX_UNSUPPORTED) {
    const [namespace, method] = api.split('.');
    expect(mock[namespace]?.[method]).toBeUndefined();
  }
});
```

### 5.3 Firefox E2E Test

```javascript
// tests/e2e/firefox/popup.spec.js
test('Firefox popup renders correctly', async ({ browser }) => {
  // Load Firefox with extension
  const context = await firefox.launchPersistentContext('', {
    headless: false,
    args: [`--load-extension=${firefoxExtPath}`]
  });

  // Open popup
  const popup = await openExtensionPopup(context);

  // Visual comparison
  await expect(popup).toHaveScreenshot('firefox-popup.png');
});
```

---

## 6. Process Failures

### 6.1 No Manual Firefox Testing

The PR that added Firefox OAuth (#216) was merged without anyone actually testing it in Firefox.

**New Rule:** PRs touching Firefox extension MUST include screenshot of working feature in Firefox.

### 6.2 No Cross-Browser CI Job

CI only tests Chrome. There should be a Firefox job that:
1. Loads extension in Firefox
2. Runs E2E tests
3. Captures screenshots

### 6.3 No File Sync Automation

When Chrome files change, Firefox files should automatically be flagged for update.

**New Rule:** Pre-commit hook that fails if Chrome extension files are modified without corresponding Firefox changes.

---

## 7. Lessons Learned

1. **Mocks can lie** - A passing unit test only proves code works with the mock
2. **E2E is not optional** - Must test in real browser
3. **Dual codebases are dangerous** - Files drift without automation
4. **CI green ≠ working software** - Test the right things
5. **Manual testing still matters** - Someone should have tried Firefox

---

## 8. Action Items

| # | Action | Owner | Priority | Issue |
|---|--------|-------|----------|-------|
| 1 | Fix Firefox OAuth (no identity API) | TBD | P0 | #TBD |
| 2 | Create file parity test | TBD | P0 | #TBD |
| 3 | Remove identity from Firefox mock | TBD | P0 | #TBD |
| 4 | Add Firefox E2E test suite | TBD | P1 | #TBD |
| 5 | Add visual regression tests | TBD | P1 | #TBD |
| 6 | Add pre-commit hook for parity | TBD | P2 | #TBD |
| 7 | Document Firefox API differences | TBD | P2 | #TBD |

---

## 9. References

- MDN browser.identity: https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/identity
- Firefox MV3 Migration: https://extensionworkshop.com/documentation/develop/manifest-v3-migration-guide/
- Issue #206: Firefox OAuth (introduced the bug)
- Issue #216: Firefox OAuth PR (merged without testing)
