# Implementation Report — Issue #446

## Summary

Fixed 3 pre-existing unit test failures blocking auth readiness.

## Changes

### Part A: popup.css Parity Drift

- **File:** `extensions/firefox/popup.css`
- **Problem:** Chrome popup.css had Subscription (Issue #366) and Coupon (Issue #367) section styles (lines 644–815) that Firefox was missing
- **Fix:** Appended identical style blocks to Firefox popup.css

### Part B: Phone Regex Expansion

- **Files:** `extensions/chrome/article-extractor.js`, `extensions/firefox/article-extractor.js`
- **Problem:** Phone regex `\d{3}[-.\s]?\d{3}[-.\s]?\d{4}` failed on `(555) 123-4567` and `+1-555-123-4567`
- **Fix:** Expanded regex to `(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}`
- **ReDoS risk:** Pattern remains linear — no nested quantifiers

## Files Modified

| File | Change |
|------|--------|
| `extensions/firefox/popup.css` | Added subscription + coupon styles |
| `extensions/chrome/article-extractor.js` | Expanded phone regex |
| `extensions/firefox/article-extractor.js` | Expanded phone regex |
