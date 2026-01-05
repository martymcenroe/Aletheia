# 1154 - Feature: Add ARIA Attributes for Screen Reader Accessibility

## 1. Context & Goal
* **Issue:** #154
* **Objective:** Add ARIA attributes to extension UI for screen reader compatibility per WCAG 2.1.
* **Status:** Draft
* **Related Issues:** #160 (automated accessibility checks in CI)

### Open Questions
*Questions that need clarification before or during implementation. Remove when resolved.*

- [x] ~~Should we target WCAG 2.1 Level A only, or also Level AA?~~ **Level AA (includes contrast)**
- [x] ~~Do we need to test with actual screen readers?~~ **Yes - automated catches ~30%, manual required**
- [x] ~~Is there a preferred screen reader for testing?~~ **NVDA (Windows) - dev machine is Windows**
- [ ] Should the overlay auto-dismiss be announced, or is it jarring for screen reader users?
- [ ] Should blocked state have a longer announcement, or just "Site blocked"?

### Resolved Questions (Gemini Review 2026-01-05)

1. **Q: What role should the overlay have?**
   **A: `role="dialog"` (or `role="region"`), NOT `role="alert"`.** The overlay contains interactive elements (Close button, "Show More" toggle). Using `role="alert"` on a container with buttons is an accessibility anti-pattern - it implies "read this and don't interact."

2. **Q: Where should `aria-live` go?**
   **A: On the content area inside the dialog, not the container.** This allows users to navigate to interactive buttons while still announcing content updates.

3. **Q: Which screen reader for testing?**
   **A: NVDA on Windows.** Automated tools (axe-core) catch ~30% of issues; manual verification with NVDA is required for the rest.

## 2. Requirements

### Overlay (overlay.js)
1. Add `role="dialog"` to overlay container (supports interactive children)
2. Add `aria-live="polite"` to **content area inside** the dialog
3. Add `aria-label` to describe the dialog purpose
4. Ensure Close button and other controls are keyboard accessible
5. **Focus management:** Do NOT steal focus aggressively (non-modal), but ensure Close button is reachable

### Popup (popup.html, popup.js)
1. Add `aria-label` to icon buttons
2. Add `role="status"` to dynamic status areas
3. Ensure allowlist toggle is keyboard accessible
4. Add `aria-checked` to toggle states

### Blocked State
1. Announce "This site is blocked" to screen readers
2. Provide keyboard-accessible way to understand why

## 3. Alternatives Considered

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| Minimal ARIA (role, aria-live) | Quick implementation | May miss edge cases | **Selected** |
| Full accessibility audit first | Comprehensive | Delays implementation | Rejected |
| Use accessibility library | Consistent patterns | Adds dependency | Rejected |

**Rationale:** Start with essential ARIA attributes per issue requirements, expand based on user feedback.

## 4. Data & Fixtures

N/A - UI/accessibility change, no data.

## 5. Diagram

N/A

## 6. Technical Approach

* **Module:**
  - `extensions/chrome/overlay.js`
  - `extensions/chrome/popup.html`
  - `extensions/chrome/popup.js`
  - (Mirror changes to Firefox extension)
* **Dependencies:** None
* **Pattern:** Standard ARIA attributes

### 6.1 Overlay Implementation (CORRECT PATTERN)

```javascript
// overlay.js - Add ARIA to shadow DOM
// NOTE: role="dialog" NOT role="alert" (overlay has interactive buttons)
shadow.innerHTML = `
  <div class="overlay"
       role="dialog"
       aria-label="Aletheia analysis result"
       aria-modal="false">
    <div class="content" aria-live="polite">
      ${message}
    </div>
    <button class="close-btn" aria-label="Close overlay">×</button>
    <button class="show-more-btn" aria-expanded="false">Show more</button>
  </div>
`;
```

**Why `role="dialog"` not `role="alert"`:**
- `role="alert"` implies "read this text notification, don't interact"
- Our overlay has Close button and "Show More" toggle - interactive elements
- `role="dialog"` (with `aria-modal="false"`) allows navigation to buttons

```html
<!-- popup.html - Add ARIA to buttons -->
<button id="allowlist-toggle"
        aria-label="Toggle site allowlist"
        aria-pressed="false">
  Enable on this site
</button>
```

## 7. Interface Specification

### 7.1 ARIA Attributes to Add

| Element | Attribute | Value | Purpose |
|---------|-----------|-------|---------|
| Overlay container | `role` | `"dialog"` | Supports interactive children |
| Overlay container | `aria-modal` | `"false"` | Non-modal (doesn't trap focus) |
| Overlay container | `aria-label` | `"Aletheia analysis result"` | Describes dialog |
| **Content area (inside)** | `aria-live` | `"polite"` | Updates announced |
| Close button | `aria-label` | `"Close overlay"` | Button purpose |
| Show More button | `aria-expanded` | `"true"/"false"` | Expansion state |
| Toggle button | `aria-pressed` | `"true"/"false"` | Toggle state |
| Icon buttons | `aria-label` | Descriptive text | Label for icons |

### 7.2 Contrast Requirements (WCAG AA)

| Element | Foreground | Background | Ratio Required | Status |
|---------|------------|------------|----------------|--------|
| Badge (Amber) | Text | Amber bg | 4.5:1 minimum | TODO: Verify |
| Badge (Red) | Text | Red bg | 4.5:1 minimum | TODO: Verify |
| Overlay text | Black/White | Overlay bg | 4.5:1 minimum | TODO: Verify |

## 8. Security Considerations

| Concern | Mitigation | Status |
|---------|------------|--------|
| N/A | Accessibility-only change | N/A |

**Fail Mode:** N/A

## 9. Performance Considerations

| Metric | Budget | Approach |
|--------|--------|----------|
| DOM size | Negligible increase | Attributes only |

**Bottlenecks:** None.

## 10. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| ARIA announcements too verbose | Med | Low | Test with real screen reader |
| Incomplete coverage | Low | Med | Automated a11y checks (#160) |

## 11. Verification & Testing

### 11.1 Test Scenarios

| ID | Scenario | Type | Input | Expected Output | Pass Criteria |
|----|----------|------|-------|-----------------|---------------|
| 010 | Overlay announced | Manual | Screen reader + extension use | "Aletheia: [message]" | Announced |
| 020 | Toggle state announced | Manual | Toggle allowlist | "Pressed/Not pressed" | State change announced |
| 030 | axe-core passes | Auto | Playwright a11y test | No violations | Zero WCAG A violations |

**Why Manual Tests:** Screen reader behavior cannot be fully automated; requires human verification of announcement quality.

### 11.2 Test Commands

```bash
# Run axe-core via Playwright (after #160)
npx playwright test --grep accessibility

# Manual testing with NVDA (Windows):
# 1. Install NVDA: https://www.nvaccess.org/download/
# 2. Enable NVDA (Ctrl+Alt+N to start)
# 3. Navigate to extension, trigger overlay
# 4. Verify: Dialog is announced, buttons are reachable via Tab
# 5. Verify: Close button has "Close overlay" announcement
```

## 12. Definition of Done

### Code
- [ ] overlay.js has `role="dialog"` with `aria-modal="false"`
- [ ] Content area inside overlay has `aria-live="polite"`
- [ ] Close button has `aria-label="Close overlay"`
- [ ] popup.html has ARIA attributes on all interactive elements
- [ ] popup.js updates `aria-pressed` and `aria-expanded` dynamically
- [ ] Changes mirrored to Firefox extension

### Tests
- [ ] axe-core automated test passes (zero WCAG A/AA violations)
- [ ] Manual NVDA test: dialog announced, buttons reachable via Tab
- [ ] Contrast ratios verified for badge colors

### Documentation
- [ ] Accessibility audit 0811 updated

---

## Appendix: Gemini Review Response

**Review Date:** 2026-01-05
**Reviewer:** Gemini 3 Pro

### Tier 2 Issues (HIGH) - Addressed

| Issue | Resolution |
|-------|------------|
| Role Conflict (`role="alert"` with interactive children) | Changed to `role="dialog"` with `aria-modal="false"` |
| `aria-live` placement | Moved to content area inside dialog, not container |
| Screen reader choice | Standardized on NVDA (Windows) with manual testing required |

### Tier 3 Issues (SUGGESTIONS) - Addressed

| Issue | Resolution |
|-------|------------|
| Focus Management | Added §2 requirement: non-modal, don't steal focus, Close button reachable |
| Contrast Ratios | Added §7.2 table for WCAG AA contrast requirements |
