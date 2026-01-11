# 0827 Web Assets Audit

**Status:** Active
**Created:** 2026-01-11
**Scope:** Landing pages, marketing sites, extension UI

---

## Overview

This audit defines standards for web assets including icons, buttons, typography, and responsive design. These rules ensure visual consistency and accessibility across Aletheia's web presence.

---

## Icon-as-Character Rules

When placing an icon in lieu of a character (e.g., Lambda replacing L in "Aλetheia"):

### 1. Baseline Alignment
```css
vertical-align: baseline;
```
The icon must sit on the text baseline, not float above or below.

### 2. Size Using `em` Units
```css
height: 0.75em;  /* Inline with text */
```
- Use `em` units relative to font-size
- Typical range: 0.7-0.9em for inline icons
- Never use `px` for text-integrated icons

### 3. Kerning (Letter Spacing)
```css
margin: 0 -0.02em;  /* Tuck into text flow */
```
- Use negative margins to reduce visual gaps
- Test at multiple font sizes

### 4. Display Property
```css
display: inline-block;
```
Ensures consistent rendering across browsers.

### 5. Alt Text
Always provide meaningful alt text:
```html
<img src="lambda.png" alt="λ">
```

---

## Button Consistency Rules

### 1. Equal Prominence for Related Actions
Related actions (e.g., Chrome + Firefox install buttons) must have equal visual weight:

**Correct:**
```css
.cta, .cta-secondary {
  border: 2px solid var(--color-primary);
  background: transparent;
  color: var(--color-primary);
}
```

**Incorrect:**
- One button filled, one button outline only
- Different padding or border-radius
- Different font weights

### 2. Primary vs Secondary Actions
Only use a filled (prominent) style when there is ONE clear primary action.

If both actions are equally valid choices (Chrome vs Firefox), use identical styling.

### 3. Hover States
All interactive elements must have hover feedback:
```css
.button:hover {
  background-color: var(--color-primary);
  color: white;
  transform: translateY(-1px);
}
```

---

## Responsive Design Requirements

### 1. Use `em`/`rem` for Text-Related Sizing
```css
/* Correct */
.logo-lambda { height: 1.2em; width: 1.2em; }
.footer-lambda { height: 1em; width: 1em; }

/* Incorrect */
.logo-lambda { height: 24px; width: 24px; }
```

### 2. Test Browser Zoom
- Ctrl+/Ctrl- should scale everything proportionally
- Icons must scale with surrounding text
- Layout should not break at 200% zoom

### 3. Mobile Breakpoints
Test at these widths:
- 375px (mobile)
- 768px (tablet)
- 1024px (desktop)

### 4. `clamp()` for Fluid Typography
```css
font-size: clamp(3rem, 10vw, 5.5rem);
```
Provides smooth scaling without media query jumps.

---

## Accessibility Checklist

- [ ] All images have alt text
- [ ] Color contrast meets WCAG AA (4.5:1 for text)
- [ ] Interactive elements have focus states
- [ ] Links are distinguishable from body text
- [ ] Page is navigable by keyboard alone

---

## Dark Mode Requirements

Use CSS custom properties with `prefers-color-scheme`:

```css
:root {
  --color-primary: #0D9488;  /* Light mode */
  --color-bg: #F9FAFB;
}

@media (prefers-color-scheme: dark) {
  :root {
    --color-primary: #2DD4BF;  /* Dark mode */
    --color-bg: #111827;
  }
}
```

Test both modes for:
- Sufficient contrast
- Readable text
- Visible borders
- Icon visibility

---

## Audit Checklist

When reviewing web assets:

- [ ] Icons use `em` units, not `px`
- [ ] Icons in text are baseline-aligned with proper kerning
- [ ] Related buttons have equal visual weight
- [ ] All hover states implemented
- [ ] Zoom test passed (100%, 150%, 200%)
- [ ] Mobile breakpoints tested
- [ ] Dark mode verified
- [ ] Accessibility checklist complete

---

## Files in Scope

| File | Type | Notes |
|------|------|-------|
| `docs/index.html` | Landing page | Main marketing page |
| `docs/privacy.html` | Policy page | Legal content |
| `extension/popup.html` | Extension UI | Minimal styling |

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-01-11 | Claude | Initial creation from Issue #81 feedback |
