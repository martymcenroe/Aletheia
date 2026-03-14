# Chrome Web Store — v1.1.2

**Previous store version:** 1.0
**Submission date:** 2026-03-10

---

## Public-Facing Notes (for "Changes in this version")

### What's New in v1.1.2

**Authentication & Accounts**
- Sign in with LinkedIn to access your Aletheia account
- Coupon-based subscription upgrades — redeem codes directly from the extension popup
- Secure OAuth flow delegated to the service worker for reliability

**Smarter Analysis**
- Context-aware word disambiguation — the AI now uses surrounding text to resolve ambiguous words (e.g., "bank" near "river" vs. "bank" near "finance")
- Focused context window — sends ~2000 characters around your selection instead of the entire page, improving accuracy and speed
- Full article context retrieval for deeper analysis
- Confidence scores displayed alongside analysis results
- Poetic resonance detection for literary text

**Security & Privacy**
- All API traffic routed through api.aletheia.study (no direct Lambda URLs)
- Shadow DOM hardened with closed mode
- XSS protections strengthened (innerHTML removed)
- Content safety guardrails improved — fewer false positives on descriptive terms

**Accessibility**
- ARIA labels on all popup buttons
- aria-expanded attribute on context elements
- Improved popup CSS for better readability

**UI Improvements**
- Museum Label progressive disclosure overlay redesign
- Faster click-to-glass response time (parallelized operations)
- NoArchive detection for publisher opt-out signaling

---

## Reviewer Notes (for "Notes to the reviewer")

This is a major update from v1.0, adding authentication (LinkedIn OAuth), subscription management (coupon redemption), and significant analysis improvements.

**Key permission changes since v1.0:**
- Added `tabs` — needed for content script injection and page navigation detection for overlay lifecycle management
- Added `storage` — stores user preferences and auth tokens locally (no remote storage of credentials)
- Added `identity` — required for the LinkedIn OAuth authentication flow (chrome.identity.launchWebAuthFlow)
- Added `notifications` — displays analysis completion notifications
- `host_permissions` narrowed to `https://api.aletheia.study/*` only — all API communication goes through our custom domain

**Security notes:**
- OAuth tokens stored in chrome.storage.session (not localStorage), cleared on browser close
- The `key` field in manifest.json is a public key for stable extension ID during development — not a secret
- No minified code — all source is readable JavaScript
- GitHub repo: https://github.com/martymcenroe/Aletheia

**To test the core flow:**
1. Right-click any selected text on a webpage
2. Choose "Explain with AI"
3. An overlay appears with context-aware analysis

**To test authentication:**
1. Click the extension icon
2. Click "Log in with LinkedIn"
3. Complete OAuth flow
4. Popup should show logged-in state
