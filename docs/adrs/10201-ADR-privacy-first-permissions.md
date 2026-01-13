# 0201 - ADR: Privacy-First Extension Permissions

**Status:** Implemented
**Date:** 2025-12-21
**Categories:** Security, Privacy, UX

## 1. Context

Chrome extensions can request broad permissions like `host_permissions: ["<all_urls>"]`, which grants access to all websites. However, this triggers a scary warning: "Read and change all your data on all websites." This warning:

- Erodes user trust before they even try the extension
- Delays Chrome Web Store review (manual security review required)
- Creates liability for data we never intended to access
- Contradicts Aletheia's mission of user safety

We needed to decide how Aletheia would request permissions.

## 2. Decision

**We will NEVER request `host_permissions: ["<all_urls>"]`.**

Instead, we use `activeTab` permission combined with an explicit user-managed allowlist.

## 3. Alternatives Considered

### Option A: activeTab + User Allowlist — SELECTED
**Description:** Request only `activeTab` permission. Users explicitly enable sites via popup UI.

**Pros:**
- No scary permission warning
- Users control exactly which sites Aletheia can access
- Faster Chrome Web Store approval
- Aligns with privacy-first branding

**Cons:**
- Cannot change toolbar icon dynamically per-site
- Cannot inject scripts proactively (requires user action)
- Extra step for users to enable each site

### Option B: All URLs Permission — Rejected
**Description:** Request `host_permissions: ["<all_urls>"]` for seamless access.

**Pros:**
- Simpler UX (works everywhere automatically)
- Can show dynamic toolbar icons per-site

**Cons:**
- Scary Chrome permission warning
- Users may refuse to install
- Slower store review process
- Unnecessary access to sites user never intends to use

### Option C: Predefined Site List — Rejected
**Description:** Hardcode specific domains (e.g., `*://*.linkedin.com/*`)

**Pros:**
- Targeted permissions
- Clear scope

**Cons:**
- Can't add new sites without extension update
- Still requires listing each site in manifest
- Inflexible for users

## 4. Rationale

Privacy is a core value of Aletheia. Requesting minimal permissions:
- Builds user trust from first interaction
- Reduces attack surface (we can't leak what we can't access)
- Demonstrates "Privacy by Design" principle
- Aligns with Chrome's direction toward stricter permission models

The UX trade-offs (no dynamic icons, extra enable step) are acceptable given the trust benefits.

## 5. Security Risk Analysis

| Risk | Impact | Likelihood | Severity | Mitigation |
|------|--------|------------|----------|------------|
| User enables malicious site | Low | Low | 1 | User explicitly chooses; we don't recommend sites |
| Permission creep in future | Med | Low | 2 | ADR documents constraint; code review enforces |
| Bypass via extension update | Med | Low | 2 | Store review catches permission changes |

**Residual Risk:** Low. User has full control over which sites access their data.

## 6. Consequences

### Positive
- Clean Chrome Web Store listing (no warning)
- User trust from day one
- Minimal attack surface
- Faster store approval

### Negative
- Toolbar icon remains static (cannot change color per-site without user action)
- Cannot inject scripts proactively — requires context menu or popup click
- Badge feedback (setBadgeText/setBadgeBackgroundColor) is the only dynamic indicator
- Users must manually enable each site

### Neutral
- Allowlist state stored in `chrome.storage.local`

## 7. Implementation

- **Related Issues:** #77 (Action Feedback), #76 (Allowlist Popup)
- **Related LLDs:** 1076, 1077
- **Status:** Complete

Badge text/color used instead of icon swapping for feedback. Allowlist status shown only inside popup UI.

## 8. References

- [Chrome Extension Permissions](https://developer.chrome.com/docs/extensions/mv3/declare_permissions/)
- [activeTab Permission](https://developer.chrome.com/docs/extensions/mv3/manifest/activeTab/)
- Issue #41: Security Audit

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2025-12-21 | Gemini | Initial decision in 0001 |
| 2025-12-29 | Claude Opus 4.5 | Extracted to ADR format |
