# Implementation Report: Issue #156 - Extension Click-to-Glass Latency Optimization

**Issue:** #156
**Date:** 2026-01-05
**Implementer:** Claude Opus 4.5

## Summary

Optimized extension click-to-glass latency by parallelizing the allowlist check, age gate check (Chrome only), and overlay injection operations using `Promise.all`.

## Problem

The extension had sequential async operations causing 500-1000ms delay:
1. Age gate check (Chrome only) - ~100-200ms
2. Allowlist storage lookup - ~50-100ms
3. Overlay injection - ~200-300ms
4. Show "Saving..." message - ~50-100ms

Total sequential latency: 400-700ms before user sees any feedback.

## Solution

Parallelized independent operations using `Promise.all`:

```javascript
// Chrome: All three in parallel
const [overlayInjected, isAllowlisted] = await Promise.all([
    injectOverlayPromise,    // Inject overlay optimistically
    allowlistPromise,        // Check storage
    ageGatePromise           // Check age restriction
]);

// Firefox: Two in parallel (no age gate)
const [overlayInjected, isAllowlisted] = await Promise.all([
    injectOverlayPromise,
    allowlistPromise
]);
```

**Critical Pattern:** Cleanup (showing error/warning) happens ONLY AFTER `Promise.all` resolves, preventing race conditions.

## Files Modified

| File | Change |
|------|--------|
| `extensions/chrome/service-worker.js` | Parallelized age gate + allowlist + overlay injection |
| `extensions/firefox/service-worker.js` | Parallelized allowlist + overlay injection |

## Technical Details

### Before (Sequential)
```
Click → Age Gate (200ms) → Allowlist (100ms) → Inject Overlay (200ms) → Show "Saving..."
Total: ~500ms before feedback
```

### After (Parallel)
```
Click → [Age Gate | Allowlist | Inject Overlay] (parallel) → Show "Saving..."
Total: ~200ms (limited by slowest operation)
```

### Race Condition Prevention

Per LLD guidance, we do NOT cleanup early:
- ❌ WRONG: `if (!allowed) removeOverlay()` before Promise.all
- ✅ CORRECT: Wait for ALL promises, then check results, then cleanup

### Edge Case Handling

1. **Overlay injection fails (CSP):** Track `overlayInjected` boolean, fall back to `showFeedback()` helper
2. **Age-restricted site:** Show error via already-injected overlay
3. **Non-allowlisted site:** Show warning via already-injected overlay

## Expected Performance Improvement

| Metric | Before | After (Target) |
|--------|--------|----------------|
| Click-to-glass | 500-1000ms | <200ms |
| Age gate delay | Sequential | Parallel |
| Allowlist delay | Sequential | Parallel |

## Alternatives Rejected

1. **Pre-inject on all pages:** Would require `<all_urls>` permission (privacy violation)
2. **Background pre-warming:** Complex, limited benefit
3. **Accept current latency:** Poor UX
