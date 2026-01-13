# 0202 - ADR: Shadow DOM for Injected UI

**Status:** Implemented
**Date:** 2025-12-22
**Categories:** Security, UX

## 1. Context

Aletheia's content scripts inject UI elements (overlays, feedback messages) into host web pages. Without isolation:

- Host page CSS can break our UI (resets, overrides)
- Our CSS can break host page layout
- Host page JavaScript can access/manipulate our DOM
- Results in "broken UI" reports and unprofessional appearance

We needed a strategy for isolating injected UI from host pages.

## 2. Decision

**We will use Shadow DOM (`element.attachShadow({mode: 'closed'})`) for all UI injected into host pages.**

## 3. Alternatives Considered

### Option A: Closed Shadow DOM — SELECTED
**Description:** Create shadow root with `mode: 'closed'` before appending styled content.

**Pros:**
- Complete CSS isolation (bidirectional)
- Host JavaScript cannot access our shadow tree
- Professional appearance on any site (WSJ, NYT, etc.)
- Required for Chrome Web Store approval on complex sites

**Cons:**
- Slightly more complex code
- Cannot easily debug shadow content in DevTools
- Must include all styles within shadow root

### Option B: Open Shadow DOM — Rejected
**Description:** Use `mode: 'open'` for easier debugging.

**Pros:**
- Easier to debug in DevTools
- Still provides CSS isolation

**Cons:**
- Host page JavaScript can access our shadow tree
- Security risk: malicious pages could manipulate our UI
- XSS vector if host page is compromised

### Option C: iframe Injection — Rejected
**Description:** Inject UI in an iframe for complete isolation.

**Pros:**
- Complete isolation (CSS, JS, DOM)
- Familiar pattern

**Cons:**
- Cross-origin restrictions complicate communication
- Heavier resource usage
- Sizing/positioning challenges
- Feels "hacky" compared to Shadow DOM

### Option D: No Isolation (Inline Styles) — Rejected
**Description:** Use inline styles with high specificity.

**Pros:**
- Simplest implementation
- No Shadow DOM complexity

**Cons:**
- CSS specificity wars with host page
- No protection from host JS
- Breaks on sites with aggressive CSS resets
- Unprofessional results

## 4. Rationale

Shadow DOM is the modern web standard for component isolation. `mode: 'closed'` provides:
- Security: Host page cannot manipulate our UI
- Reliability: Consistent appearance across all sites
- Professionalism: Required for enterprise sites (news, finance)

The debugging inconvenience is minor compared to security benefits.

## 5. Security Risk Analysis

| Risk | Impact | Likelihood | Severity | Mitigation |
|------|--------|------------|----------|------------|
| XSS via shadow DOM bypass | High | Low | 3 | Use closed mode; sanitize all content |
| CSS injection into shadow | Med | Low | 2 | Shadow DOM blocks external CSS |
| Host JS manipulating our UI | High | Med | 6 | Closed mode prevents access |

**Residual Risk:** Low with closed mode. Open mode would be Medium risk.

## 6. Consequences

### Positive
- Consistent UI across all websites
- Protected from host page interference
- Professional appearance on enterprise sites
- Security against UI manipulation attacks

### Negative
- More complex implementation code
- Harder to debug in DevTools
- All styles must be included in shadow root
- Cannot use external stylesheets easily

### Neutral
- Standard modern web practice
- Well-documented pattern

## 7. Implementation

- **Related Issues:** #77 (Action Feedback), #94 (XSS Test Harness)
- **Related LLDs:** 1077
- **Status:** Complete

Overlay implementation creates shadow root before appending styled content. All CSS defined inline within shadow root.

## 8. References

- [MDN: Using Shadow DOM](https://developer.mozilla.org/en-US/docs/Web/API/Web_components/Using_shadow_DOM)
- [Chrome Extension Content Scripts](https://developer.chrome.com/docs/extensions/mv3/content_scripts/)

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2025-12-22 | Gemini | Initial decision in 0001 |
| 2025-12-29 | Claude Opus 4.5 | Extracted to ADR format |
