# ADR-0001: Typography System

**Status:** Accepted
**Date:** 2026-01-11
**Deciders:** Marty (Product), Claude Opus 4.5 (Implementation)

---

## Context

Aletheia needed a typography system for its landing page and brand identity. The existing LLD (1081) specified Inter as the wordmark font, but this felt generic and didn't complement the Lambda (λ) icon—which has serif-like qualities with its elegant curved terminals.

Key constraints:
- Must support Greek characters (λ for Lambda)
- Must work well at multiple sizes (hero wordmark → body text)
- Should complement the serifed Lambda icon
- Free fonts preferred (Google Fonts or Fontshare)
- Must render well on screens

## Decision

**Wordmark Font:** Libre Baskerville (Google Fonts)
**Body Font:** Space Grotesk (Google Fonts)

### Font Pairing

| Context | Font | Weight | Notes |
|---------|------|--------|-------|
| Logo/Wordmark | Libre Baskerville | 700 | Serif, classic literary authority |
| Hero headlines | Libre Baskerville | 700 | Large sizes, tight tracking |
| Body text | Space Grotesk | 400 | Sans-serif, technical character |
| UI elements | Space Grotesk | 500 | Buttons, labels, navigation |
| Feature headings | Space Grotesk | 700 | Card titles, section headers |

### CSS Implementation

```css
/* Google Fonts import */
@import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400;700&family=Space+Grotesk:wght@400;500;700&subset=greek&display=swap');

:root {
  --font-serif: 'Libre Baskerville', Georgia, serif;
  --font-sans: 'Space Grotesk', system-ui, sans-serif;
}

/* Wordmark */
.logo, .wordmark {
  font-family: var(--font-serif);
  font-weight: 700;
  letter-spacing: -0.01em;
}

/* Body and UI */
body {
  font-family: var(--font-sans);
  font-weight: 400;
}
```

## Rationale

### Why Libre Baskerville for Wordmark

1. **Serif harmony** — The Lambda icon has serif-like terminal curves; a serif wordmark creates visual cohesion
2. **Literary authority** — Aletheia reveals meaning in text; a classic book typeface reinforces this scholarly positioning
3. **Greek support** — Full Greek character set including λ (U+03BB)
4. **Distinctiveness** — Stands out from the Inter/system-ui monotony of modern SaaS

### Why Space Grotesk for Body

1. **Technical character** — Geometric with personality; feels modern without being cold
2. **Contrast with serif** — Classic serif + geometric sans is a proven pairing
3. **Screen optimized** — Designed for digital interfaces
4. **Greek support** — Full Greek character set
5. **User preference** — Ranked in "liked" tier during evaluation

### Alternatives Considered

| Font | Role | Verdict | Reason |
|------|------|---------|--------|
| Inter | Body | Rejected | Too generic, doesn't add character |
| Satoshi | Body | Runner-up | Excellent but Fontshare adds dependency |
| Manrope | Body | Considered | Good but less distinctive than Space Grotesk |
| Merriweather | Wordmark | Runner-up | Screen-optimized but less authoritative |
| Lora | Wordmark | Considered | Modern warmth but less classic feel |

## Selection Process

The typography was selected through an **iterative visual comparison process** using local HTML preview pages.

### Process Steps

1. **Initial exploration** — 10 sans-serif fonts in a grid layout
2. **Pivot to serifs** — Recognized Lambda icon has serif qualities; explored 6 serif options
3. **Second serif round** — 6 more serifs based on emerging preferences
4. **Finals** — Top 6 across all rounds for direct comparison
5. **Pairing exploration** — Locked serif wordmark, tested 6 sans-serif body pairings
6. **Final selection** — Libre Baskerville + Space Grotesk

### Evaluation Criteria

- Visual harmony with Lambda (λ) icon
- Readability at body sizes
- Character/personality (avoiding generic)
- Bold weight not too crowded
- Greek character support

### User Rankings (Abbreviated)

**Serif Round 1:** Libre Baskerville > Lora > EB Garamond
**Serif Round 2:** Merriweather > Spectral > Fraunces
**Body Pairings:** Space Grotesk selected from 6 candidates

---

## Appendix: Reusable Prompt for Future Projects

Use this prompt to replicate the typography selection process on other projects (e.g., Talos):

```
I need to select typography for [PROJECT NAME]. Here's the context:

**Brand/Product:**
- [Describe what the product does]
- [Describe the brand personality: technical, friendly, authoritative, playful, etc.]
- [Any existing visual assets to complement, e.g., logo, icon]

**Constraints:**
- Must support [character sets needed, e.g., Greek, Cyrillic]
- Free fonts preferred (Google Fonts, Fontshare, etc.)
- [Any specific requirements: screen optimization, print, variable fonts, etc.]

**Process I want to follow:**
1. Show me 10 candidate fonts in a local HTML preview page (6-up grid so I can see them all at once)
2. I'll rank them by preference
3. Based on my preferences, show me another round of 6 candidates
4. Continue iterating until we have a winner
5. If using font pairing (e.g., serif headlines + sans body), repeat the process for the secondary font
6. Document the final choice in an ADR

**For the preview pages:**
- Use a representative sentence from the project's copy
- Show the font at multiple weights (regular, medium, bold)
- Show it in context (headline size, body size)
- Include the project name rendered as a wordmark
- Make cards hoverable so I can focus on each one

Start by asking any clarifying questions, then generate the first preview page.
```

### Example for Talos

```
I need to select typography for Talos (a CLI orchestration tool). Here's the context:

**Brand/Product:**
- Talos orchestrates multiple AI agents across projects
- Brand personality: Technical, powerful, precise, slightly intimidating (named after the Greek automaton)
- Existing asset: Talos uses terminal/CLI aesthetic, monospace for code

**Constraints:**
- Must support Greek (Τάλως)
- Free fonts (Google Fonts preferred)
- Should pair well with monospace code blocks

**Process:** [same as above]

**Preview text:** "Talos coordinates your agents with precision—one command to orchestrate them all."
```

---

## Consequences

### Positive
- Typography now complements the Lambda icon
- Clear hierarchy between wordmark (serif) and body (sans)
- Both fonts are free and well-supported
- Greek characters render correctly

### Negative
- Two font families = slightly larger page weight (~50KB combined)
- Libre Baskerville has limited weights (400, 700 only—no 500)

### Mitigations
- Use `font-display: swap` for performance
- Subset fonts to Latin + Greek if size becomes an issue

---

## References

- Preview pages: `tmp/font-preview*.html` (local development artifacts)
- LLD: `docs/lld/active/1081-landing-page-redesign.md`
- Lambda icon: `extensions/chrome/icons/icon128.png`
