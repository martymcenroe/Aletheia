# 1154 - Feature: Add ARIA Attributes for Screen Reader Accessibility

## 1. Context & Goal
* **Issue:** #154
* **Objective:** Add ARIA attributes to extension UI for screen reader compatibility per WCAG 2.1.
* **Status:** Draft
* **Related Issues:** #160 (automated accessibility checks in CI)

### Open Questions
*Questions that need clarification before or during implementation. Remove when resolved.*

- [ ] Should we target WCAG 2.1 Level A only, or also Level AA?
- [ ] Do we need to test with actual screen readers (NVDA, VoiceOver), or is automated testing sufficient?
- [ ] Should the overlay auto-dismiss be announced, or is it jarring for screen reader users?
- [ ] Is there a preferred screen reader for testing? User has Windows (NVDA) or Mac (VoiceOver)?
- [ ] Should blocked state have a longer announcement, or just "Site blocked"?

## 2. Requirements

### Overlay (overlay.js)
1. Add `role="alert"` to overlay container
2. Add `aria-live="polite"` for status updates
3. Ensure overlay content is announced when it appears

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
  - `extension-chrome-V3/overlay.js`
  - `extension-chrome-V3/popup.html`
  - `extension-chrome-V3/popup.js`
  - (Mirror changes to Firefox extension)
* **Dependencies:** None
* **Pattern:** Standard ARIA attributes

### Implementation Example

```javascript
// overlay.js - Add ARIA to shadow DOM
shadow.innerHTML = `
  <div class="overlay"
       role="alert"
       aria-live="polite"
       aria-label="Aletheia analysis status">
    ${message}
  </div>
`;
```

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
| Overlay container | `role` | `"alert"` | Announces to screen reader |
| Overlay container | `aria-live` | `"polite"` | Updates announced |
| Status text | `role` | `"status"` | Live region |
| Toggle button | `aria-pressed` | `"true"/"false"` | State |
| Icon buttons | `aria-label` | Descriptive text | Label for icons |

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

# Manual: Open with NVDA/VoiceOver and verify announcements
```

## 12. Definition of Done

### Code
- [ ] overlay.js has ARIA attributes
- [ ] popup.html has ARIA attributes
- [ ] popup.js updates aria-pressed dynamically
- [ ] Changes mirrored to Firefox extension

### Tests
- [ ] axe-core automated test passes
- [ ] Manual screen reader test performed

### Documentation
- [ ] Accessibility audit 0811 updated
