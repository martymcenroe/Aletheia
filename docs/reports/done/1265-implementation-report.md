# Implementation Report: #265 Firefox Overlay E2E Tests

## Summary

Added E2E tests for Firefox overlay.js to verify rendering and behavior in the Gecko engine. Tests use script injection approach (not full extension loading) matching the existing Chrome test pattern.

## Implementation Approach

### Key Decision: Shadow DOM Access in Firefox

**Problem:** Firefox doesn't expose closed shadow roots like Chrome DevTools does. The existing Chrome tests attempt to access `host.shadowRoot`, which returns `null` for `mode: 'closed'` shadow DOM.

**Solution:** Added shadow DOM patching in `injectOverlay()` helper that forces `mode: 'open'` for testing:

```javascript
if (browser === 'firefox') {
    await page.evaluate(() => {
        const originalAttachShadow = Element.prototype.attachShadow;
        Element.prototype.attachShadow = function(options) {
            return originalAttachShadow.call(this, { ...options, mode: 'open' });
        });
    });
}
```

This allows tests to query shadow DOM contents while preserving production security (closed shadow root).

### Files Created/Modified

| File | Action | Description |
|------|--------|-------------|
| `tests/e2e/helpers/overlay-helpers.js` | Created | Shared test helpers extracted for reuse |
| `tests/e2e/firefox/overlay.spec.js` | Created | 10 Firefox-specific E2E tests |
| `playwright.config.js` | Modified | Added `firefox-overlay` project |

### Test Coverage

| Test ID | Description | Status |
|---------|-------------|--------|
| 010 | Neutral badge renders correctly | PASS |
| 020 | Warning badge renders correctly | PASS |
| 030 | Block badge renders correctly | PASS |
| 040 | Shadow DOM isolation (styles don't bleed) | PASS |
| 050 | Z-index stacking above page elements | PASS |
| 060 | Expand/collapse context | PASS |
| 070 | Close button | PASS |
| 080 | Escape key closes | PASS |
| 090 | Focus management | PASS |
| 100 | XSS prevention | PASS |

### Firefox-Specific Additions

1. **Gecko-specific Shadow DOM tests** (040, 050): Verify style isolation and z-index stacking work correctly in Firefox's rendering engine.

2. **Z-index test improvement**: Test creates high z-index page elements (`z-index: 999999` and `z-index: 9999999`) to verify overlay stays on top at `z-index: 2147483647`.

## Pre-existing Issue Discovered

**Chrome museum-label tests are broken on main branch** (12/16 failing). Root cause: they access `host.shadowRoot` which returns `null` for closed shadow DOM. This is NOT a regression from this PR - tests fail on main too.

The same patching technique used for Firefox tests could fix Chrome tests, but that's out of scope for #265.

## LLD Compliance

Per `docs/lld/active/1265-firefox-overlay-e2e.md`:

- [x] `tests/e2e/firefox/overlay.spec.js` created
- [x] `tests/e2e/helpers/overlay-helpers.js` extracted
- [x] 10 Firefox overlay tests pass (exceeds LLD's 9 target)
- [x] Playwright config updated for Firefox project
- [x] No regression in Firefox tests (Chrome tests have pre-existing failure)

## Out of Scope

- Fixing pre-existing Chrome test failures (separate issue)
- Full Firefox extension loading in Playwright
- Firefox popup.js E2E tests
