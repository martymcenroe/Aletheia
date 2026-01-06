# Implementation Report: Issue #154 - Accessibility Compliance

**Issue:** #154 - ARIA attributes for screen reader accessibility
**Date:** 2026-01-06
**Status:** Complete (Phase 1 - Infrastructure)

## Summary

Implemented automated accessibility testing infrastructure using `@axe-core/playwright` to scan for WCAG 2.0/2.1 AA compliance. The tests provide baseline validation for fixture pages and document extension-specific testing limitations.

## Changes Made

### New Files

| File | Purpose |
|------|---------|
| `tests/e2e/accessibility.spec.js` | 6 accessibility tests using axe-core |

### Modified Files

| File | Changes |
|------|---------|
| `package.json` | Added `@axe-core/playwright` dependency, `test:a11y` script |
| `tests/e2e/utils/test-helpers.js` | Added hardcoded `EXTENSION_ID` constant |

## Test Coverage

### Tests Implemented (6 total)

1. **010: Test fixture page - baseline accessibility**
   - Scans `test-clean.html` for WCAG violations
   - Result: PASS (0 violations)

2. **020: Page with extension loaded - accessibility scan**
   - Scans page after extension injection
   - Result: PASS (0 violations)

3. **030: Adult-restricted page - blocked state accessibility**
   - Scans `test-adult.html` with potential overlay
   - Result: PASS (0 violations, logs impact breakdown)

4. **040: Index page - landing page accessibility**
   - Scans `index.html` fixture
   - Result: PASS (0 violations)

5. **050: Extension popup HTML - direct accessibility scan**
   - Attempts to scan popup via `chrome-extension://` URL
   - Result: SKIP (Chrome blocks direct extension URL access)
   - Documented workaround: manual DevTools audit

6. **060: Museum Label UI - triggered overlay accessibility**
   - Attempts to trigger overlay via text selection
   - Result: SKIP (overlay requires allowlisting)
   - Documents expected behavior

## Technical Decisions

### Extension ID Calculation

The extension ID was calculated from the manifest's public key using Chrome's algorithm:
1. Base64-decode the key from `manifest.json`
2. SHA-256 hash the decoded bytes
3. Map first 32 hex chars (0-9a-f) to alphabet (a-p)

**Result:** `hgkgcicdgpckniojmneapkafkklhnbdj`

This ID is deterministic and stable across installs due to the manifest `key` field.

### Chrome Security Limitation

Chrome blocks navigation to `chrome-extension://` URLs for security reasons. This affects test 050 (popup scan). The test gracefully handles this by catching `ERR_BLOCKED_BY_CLIENT` and documenting the manual testing approach.

### axe-core Configuration

All tests use WCAG 2.0 AA and 2.1 AA tags:
```javascript
.withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
```

## Known Limitations

1. **Popup accessibility** - Cannot be automated via Playwright due to Chrome security. Must be tested manually using Chrome DevTools Lighthouse or standalone accessibility checkers.

2. **Overlay accessibility** - Cannot be triggered in tests because:
   - Extension storage injection via `addInitScript` doesn't affect extension context
   - Context menu actions aren't easily triggerable in Playwright
   - Requires actual site allowlisting which needs user interaction

## Future Work

1. **Phase 2:** Add ARIA attributes to popup.html and museum-label.js based on manual audit findings
2. **Phase 3:** Explore `puppeteer-extra-plugin-stealth` or similar for bypassing extension URL restrictions
3. **CI Integration:** Add accessibility tests to GitHub Actions workflow

## Phase 2: Museum Label ARIA Fix

### Violation Found

Test 070 (Forced Museum Label Scan) detected a **CRITICAL** violation:

- **Rule:** `aria-allowed-attr`
- **Issue:** `aria-expanded` used on plain `<div>` elements without supporting role
- **Affected elements:** `.aletheia-gem`, `.aletheia-context`

### Fix Applied

Modified `extensions/chrome/overlay.js`:

1. Added `role="region"` and `aria-label` to gem/context sections
2. Moved `aria-expanded` to the toggle button (where it belongs)
3. Added `aria-controls` linking button to controlled sections

**Before:**
```html
<div class="aletheia-gem" aria-expanded="false"></div>
<div class="aletheia-context" aria-expanded="false"></div>
<button class="aletheia-toggle">Show More</button>
```

**After:**
```html
<div class="aletheia-gem" id="aletheia-gem-section" role="region" aria-label="Quick summary"></div>
<div class="aletheia-context" id="aletheia-context-section" role="region" aria-label="Full context"></div>
<button class="aletheia-toggle" aria-expanded="false" aria-controls="aletheia-gem-section aletheia-context-section">Show More</button>
```

### Result

All 4 overlay states (WARNING, BLOCK, NEUTRAL, LOADING) now pass WCAG 2.0/2.1 AA with zero violations.

## Files Changed Summary

```
M  package.json
M  tests/e2e/utils/test-helpers.js
M  extensions/chrome/overlay.js      # ARIA fix
A  tests/e2e/accessibility.spec.js
```
