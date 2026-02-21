# Idea: Web Presence Updates for Launch

**Status:** Active
**Effort:** Medium (1 session)
**Value:** High
**Blocked by:** None (can be done in parallel with everything)

---

## Problem

Multiple web properties need updating before Chrome Store launch to present a consistent, professional message:

1. **ThriveTech.ai LinkedIn page** — company page needs Aletheia product info, launch announcement
2. **ThriveTech.ai website** — needs Aletheia product page or section
3. **Personal website** — needs Aletheia mention/link in projects section
4. **Aletheia.study** — the compliance/landing page, needs feature descriptions, screenshots, pricing info

Currently these properties don't reflect the current state of the product (auth, rate limiting, multi-browser support).

---

## Proposal

### Content Alignment

All properties should communicate:
- What Aletheia does (AI-powered writing analysis for authenticity detection)
- Privacy-first design (no data storage, local processing where possible)
- Multi-browser support (Chrome, Firefox, Edge)
- Professional use case (LinkedIn/professional writing context)
- Free tier available, subscription for power users

### Per-Property Updates

**ThriveTech.ai LinkedIn:**
- Company description update
- Aletheia launch post (draft in dispatch)
- Product screenshot carousel

**ThriveTech.ai website:**
- Aletheia product page with feature list, screenshots, CTA to Chrome Store
- Pricing section (free + subscriber tiers)

**Personal website:**
- Projects section: Aletheia entry with description, link

**Aletheia.study:**
- Updated feature descriptions
- Screenshots of Chrome extension
- Privacy policy link (already exists)
- Pricing/tier information
- Chrome Web Store badge/link

---

## Implementation

- Draft all content as markdown in dispatch repo (blog candidates)
- Update Aletheia.study static content (HTML/CSS in repo)
- LinkedIn and website updates are manual (outside repo)
- Chrome Web Store listing copy and screenshots

---

## Next Steps

1. [ ] Run requirements workflow to generate issue
2. [ ] Draft content in dispatch repo
3. [ ] Take fresh extension screenshots
