# 0811 - Audit: Accessibility

## 1. Purpose

Ensure Aletheia browser extension is usable by people with disabilities, compliant with accessibility standards, and follows inclusive design principles.

**Aletheia Context:**
- Browser extension popup UI
- Overlay/tooltip UI injected into pages
- Context menu interaction

---

## 2. WCAG 2.1 Compliance

### Level A (Minimum)

| Criterion | Aletheia Applicability | Check | Status |
|-----------|------------------------|-------|--------|
| 1.1.1 Non-text Content | Icons, badges | Alt text for images | |
| 1.3.1 Info and Relationships | Popup structure | Semantic HTML | |
| 1.4.1 Use of Color | Status indicators | Not color-only | |
| 2.1.1 Keyboard | All interactions | Tab-navigable | |
| 2.4.1 Bypass Blocks | N/A (simple UI) | Not applicable | |
| 4.1.1 Parsing | HTML validity | Valid markup | |
| 4.1.2 Name, Role, Value | Interactive elements | ARIA labels | |

### Level AA (Recommended)

| Criterion | Aletheia Applicability | Check | Status |
|-----------|------------------------|-------|--------|
| 1.4.3 Contrast (Minimum) | All text | 4.5:1 ratio | |
| 1.4.4 Resize Text | Popup text | 200% zoom works | |
| 2.4.6 Headings and Labels | Popup sections | Descriptive labels | |
| 2.4.7 Focus Visible | Keyboard nav | Focus indicator visible | |

---

## 3. Extension-Specific Checks

### Popup UI

| Check | Requirement | Status |
|-------|-------------|--------|
| Keyboard navigation | All actions reachable via Tab/Enter | |
| Screen reader | Labels announced correctly | |
| Color contrast | Text readable on all backgrounds | |
| Focus management | Focus trapped in popup | |

### Overlay/Tooltip

| Check | Requirement | Status |
|-------|-------------|--------|
| Not blocking content | Can be dismissed | |
| Timeout configurable | Auto-dismiss timing | |
| Screen reader announcement | ARIA live region | |

### Context Menu

| Check | Requirement | Status |
|-------|-------------|--------|
| Keyboard accessible | Right-click or context key | |
| Clear labeling | "Explain with AI" descriptive | |

---

## 4. Audit Procedure

1. Test with keyboard only (no mouse)
2. Test with screen reader (NVDA/VoiceOver)
3. Test with browser zoom at 200%
4. Check color contrast ratios
5. Document findings in audit record

---

## 5. Audit Record

| Date | Auditor | Findings Summary | Issues Created |
|------|---------|------------------|----------------|
| 2026-01-10 | Claude Opus 4.5 | PASS with gaps: overlay.js has ARIA labels, popup.html missing ARIA labels on interactive buttons (power, logout, manage), images have alt text, lang attribute present | #260 |

---

## 6. References

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Chrome Extension Accessibility](https://developer.chrome.com/docs/extensions/develop/ui/accessibility)
