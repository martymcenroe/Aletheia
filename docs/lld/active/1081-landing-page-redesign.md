# 1081 - Feature: Landing Page Redesign

## 1. Context & Goal
* **Issue:** #81
* **Objective:** Replace cyberpunk/retro landing page with modern, professional design that builds trust.
* **Status:** Draft (Revised per Gemini Review 2026-01-06, Branding Update 2026-01-11)
* **Related Issues:** #51 (Chrome Web Store Compliance), #53 (Store Assets)

### Open Questions
*Questions that need clarification before or during implementation. Remove when resolved.*

- [x] ~~What's the brand color palette?~~ **Teal-primary palette (evolved from Lambda green heritage)**
- [x] ~~Do we have a logo asset?~~ **Lambda (λ) icon + Libre Baskerville wordmark lockup**
- [x] ~~Should we use a CSS framework?~~ **Vanilla CSS (single page, no build complexity)**
- [x] ~~What's the hero illustration?~~ **Minimal - CSS shapes or Museum Label screenshot**
- [x] ~~What are the key features to highlight?~~ **Context Awareness, Privacy First, Open Source**
- [x] ~~Should dark mode be supported?~~ **Yes - use @media (prefers-color-scheme: dark)**
- [x] ~~Do we need legal pages?~~ **YES - privacy.html required for Store compliance**

### Resolved Questions (Gemini Review 2026-01-06, Branding 2026-01-11)

| Question | Resolution |
|----------|------------|
| Color Palette | **Teal-primary palette** - Teal primary (evolved from Lambda green), Indigo accent, off-white background |
| Logo | **Lambda + Wordmark lockup** - λ icon + "Aletheia" in Libre Baskerville, multiple lockup variations |
| Typography | **Libre Baskerville + Space Grotesk** - Serif wordmark, sans-serif body (see ADR-0001) |
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
| R3 | Professional typography | Libre Baskerville (wordmark) + Space Grotesk (body) |
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
| Lambda icon | Copy from `extensions/chrome/icons/` → `docs/assets/lambda.svg` | Convert to SVG, match teal palette |
| Wordmark | Libre Baskerville 700 | "Aletheia" or "λletheia" (integrated) |
| Body font | Space Grotesk | Google Fonts, Greek subset |
| Feature icons | **Heroicons v2 Outline** | MIT licensed, consistent stroke widths |
| Screenshots | Museum Label UI (once implemented) | Optional |
| Chrome Store link | Existing URL | Verify live before launch |

### 4.3 File Structure

*Landing page lives in `docs/` folder for clean separation from extension code. GitHub Pages serves from `/docs` on main branch.*

```
docs/                   # Marketing site (GitHub Pages root)
├── index.html          # Main page
├── privacy.html        # Privacy Policy (REQUIRED for Store)
├── assets/
│   ├── lambda.svg      # Lambda icon (COPIED from extensions/, not linked)
│   ├── icon-*.svg      # Feature icons (Heroicons v2 Outline)
│   └── og-image.png    # Social sharing image (1200x630)
└── CNAME               # Custom domain (if applicable)
```

**Note:** Lambda icon must be *copied* to `docs/assets/`, not linked to `../extensions/`. This ensures site remains self-contained.

### 4.4 Deployment Pipeline

Push to `main` branch, GitHub Pages auto-deploys.

## 5. Diagram

### Page Structure (with Lockup Placements)

```
+-------------------------------------------+
|  HEADER (Lockup A: Lambda before)         |
|  [λ] Aletheia      [Features] [GitHub]    |
+-------------------------------------------+
|                                           |
|  HERO (Lockup B: Lambda replaces A)       |
|           λletheia                        |
|  "Understand what you read."              |
|  Privacy-first AI context for any webpage |
|                                           |
|  [Install for Chrome]                     |
|                                           |
+-------------------------------------------+
|                                           |
|  FEATURES (3 cards, Lockup C: stacked)    |
|    λ              λ              λ        |
|  Context       Privacy        Open        |
|   Aware         First        Source       |
|  Analyzes...   ActiveTab...  Audit...     |
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
|  FOOTER (Lockup A: Lambda before)         |
|  [λ] Aletheia                             |
|  [Privacy Policy] [GitHub] [MIT License]  |
|  (c) 2026 Aletheia. Open source.          |
+-------------------------------------------+
```

### Lambda Lockup Variations

| Variation | Format | Usage | Notes |
|-----------|--------|-------|-------|
| **A** | `[λ] Aletheia` | Header, Footer | Lambda separate, easily detachable |
| **B** | `λletheia` | Hero (large) | Lambda replaces A, integrated |
| **C** | `λ` above text | Feature cards | Stacked, square format |

## 6. Technical Approach

* **Module:** `index.html`, `privacy.html` (inline CSS)
* **Dependencies:** None (vanilla HTML/CSS)
* **Pattern:** Static site, single page with separate privacy policy

### 6.1 Color Palette (Teal-Primary)

*Evolved from Lambda icon's green heritage toward professional "Tech Trust" palette.*

```css
/* Google Fonts import */
@import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400;700&family=Space+Grotesk:wght@400;500;700&subset=greek&display=swap');

:root {
  /* Light mode (default) - Teal Primary */
  --color-primary: #0D9488;      /* Teal 600 - evolved from Lambda green */
  --color-primary-light: #14B8A6; /* Teal 500 - hover states */
  --color-accent: #4F46E5;       /* Indigo - secondary accent */
  --color-text: #1F2937;         /* Slate 800 - readable */
  --color-text-muted: #6B7280;   /* Gray 500 - secondary */
  --color-bg: #F9FAFB;           /* Gray 50 - off-white */
  --color-surface: #FFFFFF;      /* White - cards */

  /* Typography */
  --font-serif: 'Libre Baskerville', Georgia, serif;
  --font-sans: 'Space Grotesk', system-ui, sans-serif;
  --max-width: 1200px;
}

/* Dark mode (auto-detect) */
@media (prefers-color-scheme: dark) {
  :root {
    --color-primary: #2DD4BF;    /* Teal 400 */
    --color-primary-light: #5EEAD4; /* Teal 300 */
    --color-accent: #818CF8;     /* Indigo 400 */
    --color-text: #F9FAFB;       /* Gray 50 */
    --color-text-muted: #9CA3AF; /* Gray 400 */
    --color-bg: #111827;         /* Gray 900 */
    --color-surface: #1F2937;    /* Gray 800 */
  }
}
```

**Rationale:** Teal honors the Lambda icon's green heritage while feeling more mature/professional than the original mint. Indigo becomes a secondary accent rather than competing with the Lambda.

### 6.2 Typography System

*See ADR-0001 for full rationale and selection process.*

**Font Pairing:**
| Role | Font | Weight | Notes |
|------|------|--------|-------|
| Wordmark | Libre Baskerville | 700 | Classic serif, complements serifed Lambda |
| Headlines | Libre Baskerville | 700 | Large sizes, tight tracking |
| Body text | Space Grotesk | 400 | Technical sans-serif, screen-optimized |
| UI/Labels | Space Grotesk | 500 | Buttons, navigation |

```css
/* Wordmark - Libre Baskerville */
.logo, .wordmark {
  font-family: var(--font-serif);
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--color-text);
}

/* Lambda character in wordmark */
.lambda {
  color: var(--color-primary);
}

/* Hero - integrated lockup (λletheia) */
.hero-wordmark {
  font-family: var(--font-serif);
  font-size: clamp(2.5rem, 8vw, 5rem);
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1;
}

/* Body text - Space Grotesk */
body {
  font-family: var(--font-sans);
  font-weight: 400;
  line-height: 1.6;
}

/* UI elements */
.btn, .nav-link {
  font-family: var(--font-sans);
  font-weight: 500;
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

  <!-- Open Graph / Social Sharing -->
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://aletheia.study/">
  <meta property="og:title" content="Aletheia - Privacy-First AI Context">
  <meta property="og:description" content="Understand what you read. Privacy-first AI context for any webpage.">
  <meta property="og:image" content="https://aletheia.study/assets/og-image.png">
  <meta name="twitter:card" content="summary_large_image">

  <!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400;700&family=Space+Grotesk:wght@400;500;700&subset=greek&display=swap" rel="stylesheet">
  <style>/* All CSS inline - see Section 6 */</style>
</head>
<body>
  <header>
    <!-- Lockup A: Lambda before -->
    <div class="logo">
      <span class="lambda">λ</span>
      <span class="wordmark">Aletheia</span>
    </div>
    <nav>
      <a href="#features" class="nav-link">Features</a>
      <a href="https://github.com/martymcenroe/Aletheia" class="nav-link">GitHub</a>
    </nav>
  </header>

  <main>
    <section class="hero">
      <!-- Lockup B: Lambda replaces A (large, integrated) -->
      <h1 class="hero-wordmark"><span class="lambda">λ</span>letheia</h1>
      <p class="hero-tagline">Understand what you read.</p>
      <p class="hero-subtitle">Privacy-first AI context for any webpage.</p>
      <a href="https://chrome.google.com/webstore/..." class="btn cta">
        Install for Chrome
      </a>
    </section>

    <section id="features" class="features">
      <div class="features-grid">
        <!-- 3 feature cards with Lockup C: stacked -->
        <div class="feature-card">
          <span class="feature-lambda">λ</span>
          <h3>Context-Aware</h3>
          <p>Analyzes text within its surrounding paragraph...</p>
        </div>
        <!-- ... more cards -->
      </div>
    </section>

    <section class="privacy">
      <h2>Your data stays yours.</h2>
      <!-- Privacy messaging -->
    </section>
  </main>

  <footer>
    <!-- Lockup A: Lambda before (small) -->
    <div class="footer-logo">
      <span class="lambda">λ</span>
      <span class="wordmark">Aletheia</span>
    </div>
    <nav class="footer-links">
      <a href="privacy.html">Privacy Policy</a>
      <a href="https://github.com/martymcenroe/Aletheia">GitHub</a>
      <span>MIT License</span>
    </nav>
    <p class="copyright">&copy; 2026 Aletheia. Open source.</p>
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

*Ref: [AgentOS:standards/0007-testing-strategy](AgentOS:standards/0007-testing-strategy)*

**Testing Philosophy:** Maximize automated testing. Visual design approval requires human judgment.

### 11.1 Test Scenarios

| ID | Scenario | Type | Input | Expected Output | Pass Criteria |
|----|----------|------|-------|-----------------|---------------|
| 010 | Page loads | Auto | Playwright navigate | 200 status | Page title correct |
| 020 | Mobile responsive | Auto | Playwright viewport 375x667 | No overflow | `overflow-x: hidden` computable |
| 030 | Dark mode | Auto | Playwright emulateMedia dark | CSS vars change | `--color-bg` is dark |
| 040 | CTA link works | Auto | Playwright click | href correct | URL contains chrome.google.com |
| 050 | Privacy Policy link | Auto | Playwright click | privacy.html loads | Page title contains "Privacy" |
| 060 | Lighthouse audit | Auto | lighthouse CLI | Score > 95 | JSON output score |
| 070 | Load time | Auto | Playwright performance | FCP < 500ms | Performance API |
| 080 | HTML validation | Auto | html-validate CLI | 0 errors | Exit code 0 |
| 090 | Links not broken | Auto | Playwright check all anchors | All resolve | No 404s |

### 11.2 Test Commands

```bash
# Run all automated tests
npx playwright test tests/e2e/landing-page.spec.js

# Lighthouse audit (headless)
npx lighthouse https://martymcenroe.github.io/Aletheia/ --output=json --chrome-flags="--headless"

# HTML validation
npx html-validate index.html privacy.html

# Local preview for manual review
npx serve .
```

### 11.3 Manual Tests (Only If Unavoidable)

| ID | Scenario | Why Not Automated | Steps |
|----|----------|-------------------|-------|
| M010 | Visual design approval | Subjective "professional" judgment | 1. Open in browser 2. Screenshot desktop/mobile 3. Present to stakeholder |
| M020 | Typography readability | Human perception required | 1. Read full page 2. Check font rendering 3. Verify line height comfortable |
| M030 | Icon clarity | Subjective visual assessment | 1. View icons at 100% 2. Check both light/dark modes |

**Justification:** These tests require human aesthetic judgment that cannot be reliably automated. Design approval is inherently subjective.

## 12. Definition of Done

### Design
- [x] Color palette defined (Teal-primary, evolved from Lambda green - see Section 6.1)
- [x] Typography selected (Libre Baskerville + Space Grotesk - see ADR-0001)
- [x] Logo approach decided (Lambda + Wordmark lockup system - see Section 5)
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

## Appendix: Review Log

*Track all review feedback with timestamps and implementation status.*

### Gemini Review #1 (APPROVED)

**Timestamp:** 2026-01-06
**Reviewer:** Gemini 3 Pro
**Verdict:** APPROVED

#### Comments

| ID | Comment | Implemented? |
|----|---------|--------------|
| G1.1 | "Legal pages required - privacy.html blocks Store submission" | ✅ YES - Section 7.3 added |
| G1.2 | "Framework choice should be explicit" | ✅ YES - Vanilla CSS selected in Section 3 |
| G1.3 | "Dark mode support recommended" | ✅ YES - @media prefers-color-scheme in Section 6.1 |
| G1.4 | "Color palette should convey trust" | ✅ YES - Tech Trust palette in Section 6.1 |
| G1.5 | "Logo approach unclear" | ✅ YES - Text-only wordmark in Section 6.2 |
| G1.6 | "Hero illustration needed" | ✅ YES - Minimal CSS shapes in Section 5 |
| G1.7 | "Features should be specific" | ✅ YES - 3 key features in Section 7.2 |

### Branding Update (2026-01-11)

**Participants:** Marty (Product), Claude Opus 4.5 (Implementation)
**Process:** Iterative visual font comparison via local HTML preview pages

#### Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Primary Color | Teal (#0D9488) | Evolved from Lambda's mint green heritage |
| Wordmark Font | Libre Baskerville | Serif complements serifed Lambda icon |
| Body Font | Space Grotesk | Technical sans-serif, pairs well with serif |
| Logo System | Lambda + Wordmark lockup | Three variations (A, B, C) for different contexts |

#### Artifacts Created

- `docs/adr/0001-typography-system.md` - Full ADR with reusable prompt
- `tmp/font-preview*.html` - Visual comparison pages (dev artifacts)

### Gemini Review #2 (APPROVED with fixes)

**Timestamp:** 2026-01-11
**Reviewer:** Gemini 3 Pro
**Verdict:** APPROVED (after addressing HIGH issues)

#### Feedback Received

| Priority | Issue | Resolution |
|----------|-------|------------|
| [BLOCKING] | Corrupted font URL | **FALSE POSITIVE** - URLs verified correct |
| [HIGH] | Files in repo root | ✅ FIXED - Moved to `docs/` folder |
| [HIGH] | Icon not self-contained | ✅ FIXED - Copy to `docs/assets/lambda.svg` |
| [SUGGESTION] | Missing OG meta tags | ✅ ADDED - Open Graph + Twitter Card |
| [SUGGESTION] | Icon set unspecified | ✅ FIXED - Heroicons v2 Outline |

### Review Summary

| Review | Date | Verdict | Key Issue |
|--------|------|---------|-----------|
| Gemini #1 | 2026-01-06 | APPROVED | privacy.html required |
| Branding Update | 2026-01-11 | UPDATED | Typography + color + lockups defined |
| Gemini #2 | 2026-01-11 | APPROVED | Structure + self-containment |

**Final Status:** APPROVED - Ready for implementation
