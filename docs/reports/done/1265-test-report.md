# Test Report: #265 Firefox Overlay E2E Tests

## Test Execution Summary

| Metric | Value |
|--------|-------|
| Total Tests | 10 |
| Passed | 10 |
| Failed | 0 |
| Duration | 10.1s |
| Browser | Firefox (Playwright) |
| Mode | Headless |

## Test Results

```
Running 10 tests using 1 worker

  ✓  1 [firefox-overlay] › firefox/overlay.spec.js:31:9 › Firefox Overlay (#265) › Rendering (Gecko) › 010: Neutral badge renders correctly in Firefox (1.0s)
  ✓  2 [firefox-overlay] › firefox/overlay.spec.js:54:9 › Firefox Overlay (#265) › Rendering (Gecko) › 020: Warning badge renders correctly in Firefox (730ms)
  ✓  3 [firefox-overlay] › firefox/overlay.spec.js:69:9 › Firefox Overlay (#265) › Rendering (Gecko) › 030: Block badge renders correctly in Firefox (771ms)
  ✓  4 [firefox-overlay] › firefox/overlay.spec.js:89:9 › Firefox Overlay (#265) › Shadow DOM Isolation (Gecko-specific) › 040: Styles do not bleed in or out in Firefox (883ms)
  ✓  5 [firefox-overlay] › firefox/overlay.spec.js:120:9 › Firefox Overlay (#265) › Shadow DOM Isolation (Gecko-specific) › 050: Z-index stacking above complex page elements (981ms)
  ✓  6 [firefox-overlay] › firefox/overlay.spec.js:160:9 › Firefox Overlay (#265) › Interaction › 060: Expand/collapse context works in Firefox (1.3s)
  ✓  7 [firefox-overlay] › firefox/overlay.spec.js:185:9 › Firefox Overlay (#265) › Interaction › 070: Close button works in Firefox (767ms)
  ✓  8 [firefox-overlay] › firefox/overlay.spec.js:205:9 › Firefox Overlay (#265) › Interaction › 080: Escape key closes overlay in Firefox (754ms)
  ✓  9 [firefox-overlay] › firefox/overlay.spec.js:229:9 › Firefox Overlay (#265) › Accessibility › 090: Focus management works in Firefox (762ms)
  ✓ 10 [firefox-overlay] › firefox/overlay.spec.js:248:9 › Firefox Overlay (#265) › Security › 100: XSS prevention works in Firefox (1.2s)

  10 passed (10.1s)
```

## Test Categories

### Rendering (Gecko) - 3 tests
Verifies badge rendering for all severity levels in Firefox's rendering engine:
- Neutral (blue) badge
- Warning (amber) badge
- Block (red) badge with hard-block card class

### Shadow DOM Isolation - 2 tests
Firefox-specific tests for Shadow DOM behavior:
- **040**: Page styles (Comic Sans, pink background, hidden badges) don't leak into shadow DOM
- **050**: Overlay maintains `z-index: 2147483647` above competing high-z elements

### Interaction - 3 tests
Standard interaction tests validated in Firefox:
- Expand/collapse context via Show More/Less toggle
- Close button removes overlay
- Escape key closes overlay

### Accessibility - 1 test
Focus management: Close button receives focus on overlay open

### Security - 1 test
XSS prevention: Script tags in signal/gem/context are escaped, not executed

## Known Issues

### Chrome Tests Failing (Pre-existing)

Chrome `museum-label.spec.js` tests fail on **main branch** (12/16 failures). This is NOT caused by this PR:

```
Main branch: 12 failed, 4 passed
Worktree: 12 failed, 4 passed (identical)
```

Root cause: Tests access `host.shadowRoot` which returns `null` for closed shadow DOM. The same fix applied to Firefox tests (patching `attachShadow` to `mode: 'open'`) would fix Chrome tests, but that's a separate issue.

## Artifacts

- Test results: `test-results/`
- Playwright report: `playwright-report/` (run `npx playwright show-report`)
- Traces available for failed tests (none in this run)

## Acceptance Criteria Verification

| Criteria | Status |
|----------|--------|
| Firefox overlay tests created | PASS |
| Museum label rendering tested | PASS |
| Shadow DOM isolation verified | PASS |
| Overlay dismiss behavior tested | PASS |
| No regression introduced | PASS (Chrome failures pre-existing) |
