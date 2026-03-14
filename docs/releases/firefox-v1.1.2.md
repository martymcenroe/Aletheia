# Firefox AMO — v1.1.2

**Previous store version:** 1.1.1
**Submission date:** 2026-03-10

---

## Public-Facing Notes (for "Release notes")

### What's New in v1.1.2

- **Coupon redemption** — redeem subscription upgrade codes directly from the extension popup
- **Context-aware word disambiguation** — the AI now uses surrounding text to resolve ambiguous words (e.g., "bank" near "river" vs. "bank" near "finance")
- **Focused context window** — sends ~2000 characters around your selection instead of the entire page, improving analysis accuracy and reducing latency

---

## Reviewer Notes (for "Notes to reviewer")

Small incremental update from v1.1.1. Three changes:

1. **Coupon redemption UI** (`popup.js`, `popup.html`) — authenticated users can enter coupon codes to upgrade their subscription tier. Calls `POST /redeem-coupon` on our API.

2. **Context-aware disambiguation** (`service-worker.js`) — instead of sending the entire page DOM to the API, the extension now extracts a ~2000 character window around the user's selection. This improves word sense disambiguation (the API can better resolve ambiguous terms) and reduces payload size.

3. **Version bump** (`manifest.json`) — 1.1.1 → 1.1.2.

**No permission changes from v1.1.1.**

No minified code — all source is readable JavaScript. GitHub repo: https://github.com/martymcenroe/Aletheia

**To test:**
1. Right-click any selected text → "Explain with AI" → overlay appears
2. Click extension icon → log in → enter coupon code (if you have one)
