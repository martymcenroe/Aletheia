# Implementation Report: Issue #197 - Shadow DOM Security Hardening

## Summary

Changed Shadow DOM from `mode: 'open'` to `mode: 'closed'` per ADR 0202 security requirements. This prevents host page JavaScript from accessing overlay internals.

## LLD Reference

- **LLD:** docs/1197-shadow-dom-hardening.md
- **ADR:** docs/0202-ADR-shadow-dom-isolation.md
- **Issue:** #197

## Changes Made

### Pattern Applied: Module-Level Reference

When using `mode: 'closed'`, `element.shadowRoot` returns `null` to all callers, including our own code. We solve this by capturing the reference at creation time in a module-level variable `activeShadowRoot`.

### Files Modified

#### extensions/chrome/overlay.js

| Location | Change |
|----------|--------|
| Line 35 | Added `let activeShadowRoot = null;` state variable with documentation |
| Line 462 | Added `activeShadowRoot = null;` cleanup in `removeOverlay()` |
| Line 488 | Changed `showLoadingOverlay()` to `mode: 'closed'` + capture reference |
| Line 538 | Changed `showResultOverlay()` to `mode: 'closed'` + capture reference |
| Line 740 | Changed `showAletheiaOverlay()` to `mode: 'closed'` + capture reference |
| Lines 812-813 | Updated `updateAletheiaOverlay()` check to use `activeShadowRoot` |
| Line 829 | Changed `host.shadowRoot.querySelector()` to `activeShadowRoot.querySelector()` |

#### extensions/firefox/overlay.js

Same changes applied at equivalent locations:
- State variable at line 449
- Cleanup at line 462
- Three attachShadow updates at lines 488, 538, 740
- updateAletheiaOverlay fix at lines 812-813, 829

### New Files

| File | Purpose |
|------|---------|
| tests/fixtures/html/test-shadow-access.html | Test fixture with malicious JS attempting shadow access |
| tests/e2e/shadow-dom-security.spec.js | Playwright E2E tests verifying closed mode |

## Security Impact

| Vector | Before | After |
|--------|--------|-------|
| Host page reads shadowRoot | Allowed | Blocked (returns null) |
| Host page manipulates overlay content | Possible | Impossible |
| DOM clobbering attacks | Partially vulnerable | Fully protected |
| Style injection into shadow | Blocked | Blocked (unchanged) |

## Verification

```bash
# Verify no mode: 'open' remains
grep -r "mode: 'open'" extensions/
# Expected: No matches

# Verify all attachShadow calls use 'closed'
grep -rn "mode: 'closed'" extensions/
# Expected: 6 matches (3 Chrome, 3 Firefox)

# Verify activeShadowRoot cleanup
grep -rn "activeShadowRoot = null" extensions/
# Expected: 2 matches (1 Chrome, 1 Firefox in removeOverlay)
```

## Manual Verification Steps

1. Load extension in Chrome/Firefox
2. Visit any allowlisted site
3. Select text to trigger overlay
4. Open DevTools console
5. Run: `document.getElementById('aletheia-overlay-host').shadowRoot`
6. **Expected:** Returns `null`
7. **If returns ShadowRoot object:** Fix not applied correctly

## No Regressions

- Overlay renders correctly (uses internal `activeShadowRoot` reference)
- Overlay updates work (uses `activeShadowRoot.querySelector()`)
- Overlay cleanup works (sets `activeShadowRoot = null`)
- Legacy API `window.updateAletheiaOverlay()` continues to work

## Definition of Done Checklist

- [x] All 3 `attachShadow` calls changed to `mode: 'closed'` in Chrome overlay.js
- [x] All 3 `attachShadow` calls changed to `mode: 'closed'` in Firefox overlay.js
- [x] `activeShadowRoot` variable added to both files
- [x] `activeShadowRoot` assigned after each `attachShadow` call
- [x] `activeShadowRoot = null` added to `removeOverlay()`
- [x] `updateAletheiaOverlay` uses `activeShadowRoot` instead of `host.shadowRoot`
- [x] Code comments reference Issue #197 and ADR 0202
- [x] Security test fixture created
- [x] E2E security tests created
