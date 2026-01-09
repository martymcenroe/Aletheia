# 1081 - Feature: Landing Page Redesign

## 1. Context & Goal
* **Issue:** #81
* **Objective:** Replace cyberpunk/retro landing page with modern, professional design that builds trust.
* **Status:** Draft (Revised per Gemini Review 2026-01-06)
* **Related Issues:** #51 (Chrome Web Store Compliance), #53 (Store Assets)

### Open Questions
*Questions that need clarification before or during implementation. Remove when resolved.*

- [x] ~~What's the brand color palette?~~ **Tech Trust: Deep Slate Blue primary, muted teal accent, off-white bg**
- [x] ~~Do we have a logo asset?~~ **Text-only wordmark acceptable for MVP**
- [x] ~~Should we use a CSS framework?~~ **Vanilla CSS (single page, no build complexity)**
- [x] ~~What's the hero illustration?~~ **Minimal - CSS shapes or Museum Label screenshot**
- [x] ~~What are the key features to highlight?~~ **Context Awareness, Privacy First, Open Source**
- [x] ~~Should dark mode be supported?~~ **Yes - use @media (prefers-color-scheme: dark)**
- [x] ~~Do we need legal pages?~~ **YES - privacy.html required for Store compliance**

### Resolved Questions (Gemini Review 2026-01-06)

| Question | Resolution |
|----------|------------|
| Color Palette | **Tech Trust palette** - Deep Slate Blue/Indigo primary, muted teal accent, off-white background |
| Logo | **Text-only wordmark** - Use Inter font with tight tracking |
| Framework | **Vanilla CSS** - single page doesn't justify build pipeline |
| Hero | **Minimal** - CSS shapes or Museum Label UI screenshot |
| Features | **3 key features** - Context Awareness, Privacy First, Open Source |
| Dark Mode | **Yes** - @media (prefers-color-scheme: dark), ~10 lines of CSS |
| Legal Pages | **YES** - privacy.html required (blocks #51 Store submission) |

## 2. Requirements

### Design Direction (from issue + Gemini review)
| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| R1 | Clean, modern aesthetic | Similar to Linear, Notion, Stripe |
| R2 | Light theme primary with dark mode | Default light, auto dark via prefers-color-scheme |
| R3 | Professional typography | Inter or system-ui with tight tracking |
| R4 | Trust signals | Privacy-first messaging, open source badge |
| R5 | Mobile responsive | Works on all screen sizes |
| R6 | Fast load | < 1 second load time |

### Technical (from issue + Gemini review)
| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| R7 | Single `index.html` | No build step, GitHub Pages compatible |
| R8 | **Vanilla CSS** | No framework, CSS variables for theming |
| R9 | **privacy.html required** | Linked from footer (Store compliance) |

### Content Sections (from issue)
| Section | Content |
|---------|---------|
| Hero | Wordmark logo, tagline, CTA (Install from Chrome Store) |
| Features | 3 key benefits with icons |
| Privacy | "Your data stays yours" messaging |
| Footer | Privacy Policy link, GitHub, License |

## 3. Alternatives Considered

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| A. Vanilla CSS | Full control, lightweight, no build | More effort | **Selected** |
| B. Tailwind CSS (CDN) | Utility classes, responsive | +30KB, build complexity | Rejected |
| C. Bootstrap | Quick, familiar | Heavy, dated look | Rejected |
| D. Template (Astro, Next.js) | Rich features | Build step required | Rejected |

**Rationale:** Single-page site doesn't justify a build pipeline. Vanilla CSS with CSS variables provides full control and optimal performance.

## 4. Data & Fixtures

### 4.1 Data Sources

| Attribute | Value |
|-----------|-------|
| Source | Static content (hardcoded) |
| Format | HTML |
| Size | < 50KB total |
| Refresh | Manual (redeploy) |
| Copyright/License | Self-authored |

### 4.2 Content Fixtures

| Asset | Source | Notes |
|-------|--------|-------|
| Logo | **Text-only wordmark** | Inter font, tight tracking, SVG optional |
| Feature icons | Heroicons or Feather | MIT licensed |
| Screenshots | Museum Label UI (once implemented) | Optional |
| Chrome Store link | Existing URL | Verify live before launch |

### 4.3 File Structure

```
/
├── index.html          # Main page
├── privacy.html        # Privacy Policy (REQUIRED for Store)
├── assets/
│   ├── icon-*.svg      # Feature icons (Heroicons)
│   └── og-image.png    # Social sharing image (1200x630)
└── CNAME               # Custom domain (if applicable)
```

### 4.4 Deployment Pipeline

Push to `main` branch, GitHub Pages auto-deploys.

## 5. Diagram

### Page Structure

```
+-------------------------------------------+
|  HEADER                                   |
|  Aletheia          [Features] [GitHub]    |
+-------------------------------------------+
|                                           |
|  HERO                                     |
|  "Understand what you read."              |
|  Privacy-first AI context for any webpage |
|                                           |
|  [Install for Chrome]                     |
|                                           |
+-------------------------------------------+
|                                           |
|  FEATURES (3 cards)                       |
|  [Icon] Context-Aware                     |
|  Analyzes text within its paragraph...    |
|                                           |
|  [Icon] Privacy-First                     |
|  Uses ActiveTab: we can't see history...  |
|                                           |
|  [Icon] Open Source                       |
|  Fully transparent. Audit the code...     |
|                                           |
+-------------------------------------------+
|                                           |
|  PRIVACY SECTION                          |
|  "Your data stays yours."                 |
|  - ActiveTab only: we can't see history   |
|  - No analytics, no tracking              |
|  - Open source: verify yourself           |
|                                           |
+-------------------------------------------+
|  FOOTER                                   |
|  [Privacy Policy] [GitHub] [MIT License]  |
|  (c) 2026 Aletheia. Open source.          |
+-------------------------------------------+
```

## 6. Technical Approach

* **Module:** `index.html`, `privacy.html` (inline CSS)
* **Dependencies:** None (vanilla HTML/CSS)
* **Pattern:** Static site, single page with separate privacy policy

### 6.1 Color Palette (Tech Trust)

```css
:root {
  /* Light mode (default) */
  --color-primary: #4F46E5;      /* Indigo - trust, technology */
  --color-accent: #0D9488;       /* Teal - modern, fresh */
  --color-text: #1F2937;         /* Slate 800 - readable */
  --color-text-muted: #6B7280;   /* Gray 500 - secondary */
  --color-bg: #F9FAFB;           /* Gray 50 - off-white */
  --color-surface: #FFFFFF;      /* White - cards */
  --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
  --max-width: 1200px;
}

/* Dark mode (auto-detect) */
@media (prefers-color-scheme: dark) {
  :root {
    --color-primary: #818CF8;    /* Indigo 400 */
    --color-accent: #2DD4BF;     /* Teal 400 */
    --color-text: #F9FAFB;       /* Gray 50 */
    --color-text-muted: #9CA3AF; /* Gray 400 */
    --color-bg: #111827;         /* Gray 900 */
    --color-surface: #1F2937;    /* Gray 800 */
  }
}
```

### 6.2 Typography (Wordmark Logo)

```css
/* Logo as styled text - no image required */
.logo {
  font-family: var(--font-sans);
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.025em;  /* Tight tracking */
  color: var(--color-primary);
}

/* Hero heading */
.hero h1 {
  font-size: clamp(2rem, 5vw, 3.5rem);
  font-weight: 700;
  letter-spacing: -0.025em;
  line-height: 1.1;
}
```

### 6.3 Responsive Layout

```css
/* Mobile-first grid */
.features-grid {
  display: grid;
  gap: 2rem;
  grid-template-columns: 1fr;
}

@media (min-width: 768px) {
  .features-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

/* Container */
.container {
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 0 1.5rem;
}
```

### 6.4 Performance Optimization

| Technique | Implementation |
|-----------|----------------|
| Critical CSS | All CSS inline in `<head>` |
| Font loading | `font-display: swap`, system font fallback |
| No images | SVG icons inline, no photos |
| No JavaScript | Static content only |

## 7. Interface Specification

### 7.1 HTML Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Aletheia - Privacy-First AI Context</title>
  <meta name="description" content="Understand what you read. Privacy-first AI context for any webpage.">
  <style>/* All CSS inline */</style>
</head>
<body>
  <header>
    <span class="logo">Aletheia</span>
    <nav>
      <a href="#features">Features</a>
      <a href="https://github.com/martymcenroe/Aletheia">GitHub</a>
    </nav>
  </header>

  <main>
    <section class="hero">
      <h1>Understand what you read.</h1>
      <p>Privacy-first AI context for any webpage.</p>
      <a href="https://chrome.google.com/webstore/..." class="cta">
        Install for Chrome
      </a>
    </section>

    <section id="features" class="features">
      <div class="features-grid">
        <!-- 3 feature cards -->
      </div>
    </section>

    <section class="privacy">
      <h2>Your data stays yours.</h2>
      <!-- Privacy messaging -->
    </section>
  </main>

  <footer>
    <a href="privacy.html">Privacy Policy</a>
    <a href="https://github.com/martymcenroe/Aletheia">GitHub</a>
    <span>MIT License</span>
    <p>&copy; 2026 Aletheia. Open source.</p>
  </footer>
</body>
</html>
```

### 7.2 Feature Cards (3 Features)

| Feature | Icon | Title | Description |
|---------|------|-------|-------------|
| 1 | `eye` | Context-Aware | Analyzes text within its surrounding paragraph, not just dictionary definitions. |
| 2 | `shield-check` | Privacy-First | Uses ActiveTab: we can't see your browsing history. Ever. |
| 3 | `code-bracket` | Open Source | Fully transparent. Audit the code yourself on GitHub. |

### 7.3 Privacy Policy Page (privacy.html)

**REQUIRED for Chrome Web Store submission (#51).**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <title>Privacy Policy - Aletheia</title>
  <!-- Same styles as index.html -->
</head>
<body>
  <header><!-- Same as index --></header>
  <main class="container">
    <h1>Privacy Policy</h1>
    <p>Last updated: 2026-01-06</p>

    <h2>What We Collect</h2>
    <p>Aletheia only accesses the text you explicitly select...</p>

    <h2>What We Don't Collect</h2>
    <ul>
      <li>Browsing history</li>
      <li>Personal information</li>
      <li>Analytics or tracking data</li>
    </ul>

    <!-- Full policy content -->
  </main>
  <footer><!-- Same as index --></footer>
</body>
</html>
```

## 8. Security Considerations

| Concern | Mitigation | Status |
|---------|------------|--------|
| XSS in static site | No user input | N/A |
| CSP headers | GitHub Pages default | Addressed |
| External resources | All inline, no CDN | Addressed |

**Fail Mode:** N/A - Static site.

## 9. Performance Considerations

| Metric | Budget | Approach |
|--------|--------|----------|
| First Contentful Paint | < 500ms | All CSS inline |
| Total page weight | < 50KB | No frameworks, inline SVG |
| Lighthouse score | > 95 | Follow best practices |
| Time to Interactive | < 1s | No JavaScript |

**Bottlenecks:** Font loading (mitigate with system font fallback + font-display: swap).

## 10. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Design doesn't convey trust | High | Med | Use established "tech trust" palette |
| Looks too generic | Med | Med | Wordmark logo, consistent color system |
| Chrome Store link broken | High | Low | Verify before launch |
| Missing privacy.html | **High** | Low | **Blocks Store submission** |
| Not mobile-friendly | Med | Low | Mobile-first CSS |

## 11. Verification & Testing

### 11.1 Test Scenarios

| ID | Scenario | Type | Input | Expected Output | Pass Criteria |
|----|----------|------|-------|-----------------|---------------|
| 010 | Page loads | Manual | Open index.html | Page renders | Visual inspection |
| 020 | Mobile responsive | Manual | Resize browser | Layout adapts | No horizontal scroll |
| 030 | Dark mode | Manual | Toggle system preference | Colors switch | Readable in both modes |
| 040 | CTA link works | Manual | Click Install | Chrome Store opens | Correct URL |
| 050 | Privacy Policy link | Manual | Click Privacy Policy | privacy.html loads | Page renders |
| 060 | Lighthouse audit | Auto | Run Lighthouse | Score > 95 | Performance, accessibility |
| 070 | Load time | Auto | Measure FCP | < 500ms | Performance budget |

### 11.2 Test Commands

```bash
# Local preview
npx serve .

# Lighthouse audit (requires Chrome)
npx lighthouse https://martymcenroe.github.io/Aletheia/ --output=json

# HTML validation
npx html-validate index.html privacy.html
```

### 11.3 Manual Review Checklist

- [ ] Looks professional and trustworthy
- [ ] Mobile responsive (test on actual device)
- [ ] Dark mode works (toggle system preference)
- [ ] All links work (Chrome Store, GitHub, Privacy Policy)
- [ ] Privacy messaging is prominent
- [ ] No typos in copy
- [ ] Wordmark logo displays correctly
- [ ] Icons are legible in both light/dark modes

## 12. Definition of Done

### Design
- [x] Color palette defined (Tech Trust: Indigo/Teal)
- [x] Typography selected (Inter/system-ui)
- [x] Logo approach decided (Text-only wordmark)
- [ ] Icons selected from Heroicons

### Code
- [ ] `index.html` rewritten with new design
- [ ] `privacy.html` created (REQUIRED for Store)
- [ ] Dark mode via @media (prefers-color-scheme)
- [ ] Responsive on mobile, tablet, desktop
- [ ] All CSS inline (no external files)
- [ ] Loads in < 500ms

### Content
- [ ] Hero copy finalized
- [ ] 3 feature descriptions finalized
- [ ] Privacy section complete
- [ ] Privacy Policy page content written
- [ ] Footer links correct

### Tests
- [ ] Lighthouse score > 95
- [ ] Works on Chrome, Firefox, Safari
- [ ] Mobile tested on real device
- [ ] Dark mode tested

### Review
- [ ] Design review completed
- [ ] Copy review completed
- [ ] User approval before deploying

---

## Appendix: Gemini Review Response

**Review Date:** 2026-01-06
**Reviewer:** Gemini 3 Pro

### Tier 2 Issues (HIGH) - Addressed

| Issue | Resolution |
|-------|------------|
| Legal Pages | **YES** - privacy.html required, linked from footer (blocks #51 Store submission) |

### Tier 3 Issues (SUGGESTIONS) - Incorporated

| Issue | Resolution |
|-------|------------|
| Framework Choice | Selected **Vanilla CSS** - single page doesn't justify build pipeline |
| Dark Mode | **Yes** - @media (prefers-color-scheme: dark), ~10 lines CSS |
| Color Palette | **Tech Trust** - Deep Slate Blue/Indigo primary, muted teal accent |
| Logo | **Text-only wordmark** - Inter font with tight tracking |
| Hero | **Minimal** - CSS shapes or Museum Label screenshot |
| Features | **3 key features** - Context Awareness, Privacy First, Open Source |

**Verdict:** APPROVED
