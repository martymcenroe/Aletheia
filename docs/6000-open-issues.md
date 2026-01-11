# Aletheia - Open Issues

**Generated:** 2026-01-10 21:58 CT
**Total Open Issues:** 9

---

## Issue #81: Redesign landing page: modern professional aesthetic

**Labels:** feature, post-mvp

**Created:** 2025-12-21
**Updated:** 2026-01-04

### Description

## Objective
Replace the cyberpunk/retro landing page with a modern, professional design that builds trust with potential users.

## Current State
- `index.html` uses monospace font, dark theme, neon green accents
- Aesthetic is "1986 hacker terminal"
- Functional for Chrome Web Store approval but not brand-appropriate

## Requirements

### Design Direction
1. **Clean, modern aesthetic** — Think Linear, Notion, or Stripe
2. **Light theme primary** — Dark mode optional/future
3. **Professional typography** — Inter, SF Pro, or similar sans-serif
4. **Trust signals** — Privacy-first messaging, open source badge, clear value prop

### Technical
- Single `index.html` (keep it simple for GitHub Pages)
- No build step required
- Mobile responsive
- Fast load (<1s)

### Content Sections
1. Hero: Logo, tagline, CTA (Install from Chrome Store)
2. Features: 3-4 key benefits with icons
3. Privacy: Prominent "your data stays local" messaging
4. Footer: Links, copyright

## Out of Scope
- Blog/documentation site
- User accounts
- Analytics

## Acceptance Criteria
- [ ] Page looks professional and trustworthy
- [ ] Mobile responsive
- [ ] Loads in <1 second
- [ ] Privacy policy section retained
- [ ] Chrome Web Store link works

---

## Issue #106: Future: Full article context retrieval

**Labels:** enhancement

**Created:** 2025-12-29
**Updated:** 2026-01-09

### Description

## Summary
Enable retrieval of full article content when surrounding text selection is insufficient for accurate summarization/context.

## Problem
Currently Aletheia captures the user's text selection plus surrounding context. In some cases, understanding the full article may be necessary for accurate interpretation.

## Use Cases
- Academic papers where context spans multiple sections
- News articles where the lede doesn't capture the nuance
- Long-form content where selected passage references earlier material

## Considerations
- Copyright implications (capturing entire articles)
- Storage costs (full articles are large)
- Processing time (more text = more tokens)
- User consent (should user approve full retrieval?)

## Future Work
This is a **future enhancement** - not required for MVP or store submission.

## Related
- 0007-legal-compliance-strategy.md (copyright/fair use)
- Summarizer/Transform layer (would process full article)

---

## Issue #132: Set up support email infrastructure (Cloudflare Email Routing)

**Created:** 2026-01-01
**Updated:** 2026-01-11

### Description

## Context
We need email capability for:
- Firefox Add-ons Store communication (gecko ID: `extension@aletheia.study`)
- Chrome Web Store developer contact
- User support inquiries

## Research Summary

| Option | Cost | Receive | Send | Notes |
|--------|------|---------|------|-------|
| **Cloudflare Email Routing** | **Free** | ✅ | ❌ | Forwards to personal Gmail/etc |
| Cloudflare + Gmail SMTP | Free | ✅ | ✅ | Requires Gmail "send as" config |
| Zoho Mail (free tier) | Free | ✅ | ✅ | 5 users, 5GB, webmail only |
| Forward Email | Free | ✅ | ❌ | Privacy-focused forwarding |
| Namecheap email | ~$1/mo | ✅ | ✅ | Full hosting |

## Recommendation
**Cloudflare Email Routing (free)** - simplest and cheapest.

### Setup Steps
1. Move DNS to Cloudflare (free, keeps Namecheap as registrar)
2. Create `support@aletheia.study` → forwards to personal email
3. Optionally configure Gmail "send as" for replies

### Benefits
- $0/year
- Free CDN/DDoS protection as bonus
- Simple forwarding rules

## References
- [Cloudflare Email Routing](https://www.cloudflare.com/developer-platform/products/email-routing/)
- [Free Custom Domain Emails with Gmail and Cloudflare](https://altersquare.medium.com/free-custom-domain-emails-with-gmail-and-cloudflare-a-beginners-guide-84d759b373f7)
- [Cloudflare Email Routing Docs](https://developers.cloudflare.com/email-routing/)

## Definition of Done
- [ ] DNS moved to Cloudflare
- [ ] `support@aletheia.study` forwards to Orchestrator's email
- [ ] Test email received successfully
- [ ] (Optional) Gmail "send as" configured for replies

---

## Issue #246: audit: Add adversarial test logging to 0825 AI Safety

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Problem
0825 AI Safety requires adversarial testing but provides no evidence logging. Agent can claim tests passed without running them.

## Evidence
From 0825 Section 2 Checklist:
- Execute adversarial test cases
- Test prompt injection, jailbreaks, output manipulation

But NO logging mechanism. No evidence of what was attempted.

## Impact
Agent writes 'adversarial tests PASS' with no proof.

## Acceptance Criteria
- [ ] Add CloudWatch logging for adversarial test attempts
- [ ] Log: prompt sent, response received, blocked/passed
- [ ] Audit record must include test case IDs executed
- [ ] Verifiable evidence required, not self-attestation

## Priority
HIGH - AI safety claims are unverifiable

---

## Issue #262: test(unit): Add Lambda OAuth callback endpoint tests

**Labels:** testing

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Summary

The new `/auth/callback` endpoint added in #256 (Firefox OAuth tabs-based flow) lacks unit tests.

## Source

Test Gap Analysis 2026-01-10

## Gap Details

`src/lambda_auth_function.py` has a new `handle_oauth_callback()` function that:
- Handles GET requests to `/auth/callback`
- Receives OAuth redirect from LinkedIn with `?code=...&state=...`
- Returns minimal HTML page for extension to parse

This endpoint is critical to the Firefox OAuth flow but has no automated tests.

## Acceptance Criteria

- [ ] Unit tests for `handle_oauth_callback()` function
- [ ] Test cases cover:
  - Valid code and state parameters
  - Missing code parameter
  - Missing state parameter
  - Error parameter from LinkedIn (user denied)
  - HTML response format validation
- [ ] Tests run in CI

## Effort

Medium - Requires mocking Lambda event structure

## Related

- #256 - Firefox OAuth Tabs-Based Flow (implementation)
- Report: `docs/reports/256/test-report.md`

---

## Issue #263: test(e2e): Add Edge/Chromium browser E2E test matrix

**Labels:** testing, chore

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Summary

E2E tests only run against Chrome. Edge (Chromium-based) is untested despite being a supported browser.

## Source

Test Gap Analysis 2026-01-10 (from Report #116: "Edge (Chromium) | Not tested | Should work")

## Problem

The Chrome extension should work in Edge since Edge uses Chromium, but we have zero automated verification. Users on Edge could encounter issues we never detect.

## Proposed Solution

Add Edge to the Playwright E2E test matrix in playwright.config.js.

## Acceptance Criteria

- [ ] Playwright config includes Edge channel
- [ ] E2E tests run against Edge in CI
- [ ] Extension loads correctly in Edge
- [ ] All existing E2E specs pass in Edge
- [ ] CI workflow updated to include Edge runs

## Considerations

- Edge requires separate browser installation in CI
- May need conditional logic if Edge unavailable
- Consider running Edge tests in separate job to avoid blocking

## Effort

Medium - Requires CI configuration changes

## Related

- Report: docs/reports/116/test-report.md
- Audit: docs/0826-audit-cross-browser-testing.md

---

## Issue #272: test(fix): Apply Shadow DOM patch to Chrome E2E tests

**Labels:** testing, technical-debt

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Problem

The Chrome `museum-label.spec.js` tests are failing (12/16) because they cannot access the closed Shadow DOM. The tests use `host.shadowRoot` which returns `null` for `mode: 'closed'` shadow roots.

## Root Cause

Chrome overlay.js uses closed shadow DOM for security (ADR 0202):
```javascript
const shadow = host.attachShadow({ mode: 'closed' });
```

The test helper `shadowQuery()` tries to access `host.shadowRoot`, which is null for closed shadow roots.

## Solution

We solved this for Firefox in #265 using a helper that patches `attachShadow` to force `mode: 'open'` for testing:

```javascript
await page.evaluate(() => {
    const originalAttachShadow = Element.prototype.attachShadow;
    Element.prototype.attachShadow = function(options) {
        return originalAttachShadow.call(this, { ...options, mode: 'open' });
    };
});
```

## Action Required

Refactor `tests/e2e/museum-label.spec.js` to:
1. Import helpers from `tests/e2e/helpers/overlay-helpers.js`
2. Use `injectOverlay(page, 'chrome')` with the shadow DOM patch
3. Remove duplicate inline helper functions

## Test Evidence

Current state on main:
- Firefox overlay tests: 10/10 pass
- Chrome museum-label tests: 4/16 pass (12 failures)

## Related

- #265 - Firefox overlay E2E tests (implemented the fix)
- #125 - Museum Label UI (original tests)
- ADR 0202 - Shadow DOM isolation decision

---

## Issue #294: feat: Switch to Amazon Nova Micro for sub-second latency

**Created:** 2026-01-10
**Updated:** 2026-01-11

### Description

## Summary

Investigation into Amazon Nova Micro as a replacement for Claude Haiku to achieve sub-second Lambda response times.

## Performance Findings

| Model | Avg Latency | Min | Max |
|-------|-------------|-----|-----|
| Claude Haiku | 1,469ms | 1,194ms | 1,854ms |
| Amazon Nova Micro | 532ms | 498ms | 576ms |

**Speedup: 2.76x faster**

### Projected Full Pipeline Latency

- **Current (Haiku)**: ~500ms guardrail + ~1,500ms etymology = ~2,000ms warm
- **With Nova Micro**: ~200ms guardrail + ~530ms etymology = ~730ms warm

This would comfortably pass the 3.0s smoke test threshold even with cold starts.

## Quality Gap: Prompt Tuning Required

Nova Micro's classifications diverge from our taxonomy in problematic ways:

| Term | Haiku | Nova Micro | Correct? |
|------|-------|------------|----------|
| glamorous | Formal Adjective | Modern Adjective | Both OK |
| cryptocurrency | Technical Financial Term | Modern Technical Term | Both OK |
| **immiserate** | Formal Academic Term | **Archaic Pejorative** | ❌ Nova wrong |
| serendipity | Formal Academic Term | Historical Term | Haiku better |
| hello | Common Greeting | Common Greeting | ✓ |

### The "Immiserate" Problem

Nova classified "immiserate" as "Archaic Pejorative" - this is wrong.

- **Actual usage**: Active in economics ("immiseration thesis"), academic papers, WSJ/Economist
- **Why Nova got it wrong**: Likely pattern-matching "negative-sounding word" → "pejorative"
- **Our WSJ Rule**: If a word appeared in quality journalism in the last 10 years, it's NOT archaic

This suggests Nova needs prompt tuning to understand:
1. The distinction between "rare" and "archaic"
2. That describing negative phenomena (poverty, decline) is not the same as being pejorative
3. Our specific taxonomy definitions

## Work Required

1. **Prompt Engineering**: Adapt system prompts for Nova Micro's response characteristics
   - May need more explicit examples distinguishing formal academic terms from pejoratives
   - Test against our full taxonomy edge cases

2. **Semantic Guardrail**: Test Nova for safety classification (separate from etymology)

3. **JSON Reliability**: Nova produced valid JSON 5/5 times vs Haiku's 4/5 (Haiku had unescaped quote issue on "glamorous")

## API Differences

Nova uses different request schema:
```python
# Claude Haiku
{"anthropic_version": "bedrock-2023-05-31", "max_tokens": 500, "system": "...", "messages": [...]}

# Nova Micro
{"schemaVersion": "messages-v1", "system": [{"text": "..."}], "messages": [...], "inferenceConfig": {"max_new_tokens": 500}}
```

## Test Script

Investigation script at: `tmp/test_nova_micro.py`

## Acceptance Criteria

- [ ] Nova Micro prompts tuned to match Haiku classification accuracy
- [ ] Semantic guardrail tested with Nova Micro
- [ ] Lambda updated to use Nova Micro (configurable via env var)
- [ ] Smoke test passes with <3.0s latency
- [ ] All 5 test terms classified correctly

## References

- [Amazon Nova Models - Bedrock Docs](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-nova.html)
- Model ID: `amazon.nova-micro-v1:0`
- Region: us-east-1 (available)

---

## Issue #295: feat: Display confidence scores instead of single classification label

**Created:** 2026-01-11
**Updated:** 2026-01-11

### Description

## Objective

Display confidence scores across all categories (above threshold) to users instead of a single classification label.

## UX Flow

### Scenario 1: Word with Clear Category
1. User highlights "forsooth" on a webpage
2. Extension calls Lambda → returns confidence scores
3. Popup displays:
   ```
   Archaic: 95%
   General Usage: 5%
   ```
4. User understands this is an archaic term

### Scenario 2: Word with Mixed Signals
1. User highlights "serendipity"
2. Extension calls Lambda → returns confidence scores
3. Popup displays:
   ```
   General Usage: 70%
   Archaic: 15%
   Neologism: 15%
   ```
4. User sees nuanced breakdown, not false precision of single label

### Scenario 3: Provocative Term (Soft Block)
1. User highlights "tupping"
2. Extension calls Lambda → returns scores + warning flag
3. Popup displays:
   ```
   ⚠️ Provocative: 85%
   Archaic: 10%
   General Usage: 5%
   ```
4. Warning icon indicates sensitivity

### Scenario 4: Hate Speech (Hard Block)
1. User highlights a slur
2. Extension calls Lambda → 403 Forbidden
3. Popup displays: "Content blocked"
4. No scores shown (hate filter catches this upstream)

## Requirements

### Display Threshold
1. Show all categories with confidence ≥ 15%
2. Round to nearest 5% for cleaner display (done in Extension, not Lambda)
3. Categories shown in descending order by confidence

### Score Normalization
1. Scores MUST sum to 1.0 (100%) - enforced by LLM prompt
2. Lambda returns raw floats (e.g., 0.70, 0.15)
3. Extension handles display formatting (percentages, rounding)

### Category Taxonomy (Simplified)
1. **General Usage** - Standard, safe language (renamed from "None")
2. **Archaic** - Words that dropped out of common usage before 1950
3. **Provocative** - Sexual slang or double entendres
4. **Neologism** - Newly coined words from last 2 years

### Categories Removed
1. **Hate** - Handled by separate 403 guardrail, never reaches display
2. **Pejorative** - Remove from etymologist prompts (redundant with Hate)
3. **Formal Academic Term** - No longer a label; just show General Usage confidence

### API Response Format
```json
{
  "scores": {
    "general_usage": 0.70,
    "archaic": 0.15,
    "provocative": 0.05,
    "neologism": 0.10
  },
  "gem": "First recorded in 1754, coined by Horace Walpole...",
  "context": "Three sentences of etymological detail...",
  "warning": false
}
```

## Technical Approach

- **Lambda**: Return full `scores` object from semantic guardrail (already calculated)
- **Etymologist**: Remove single-label "signal" output; return only gem+context
- **Extension**: Parse `scores`, filter by threshold, render as list
- **Taxonomy**: Rename "None" → "General Usage" in taxonomy.json

## Files to Create/Modify

- `src/lambda_function.py` — Include scores in response body
- `src/etymologist.py` — Remove "signal" field from prompt/output
- `src/guardrails/resources/taxonomy.json` — Rename "None" to "General Usage"
- `extension/popup.js` — Render score breakdown instead of signal
- `extension/popup.html` — UI for confidence list

## Security Considerations

**Data Exposure Change:**
- Previously: Single label visible to user ("Formal Academic Term")
- Now: Full confidence distribution visible (all 4 categories with percentages)
- Risk: Minimal - categories are non-sensitive (General Usage, Archaic, Provocative, Neologism)
- Hate category scores are NEVER exposed - 403 block occurs before score calculation

**Score Manipulation:**
- Scores come from LLM classification, not user input
- No new attack surface introduced
- Existing XML tag wrapping prevents prompt injection

**Blocked Content:**
- Hate speech still triggers 403 at guardrail layer
- No change to hard block behavior
- Users cannot see scores for blocked content

## Dependencies

- None (foundational change)
- **Blocks:** Issue #294 (Nova Micro switch) — complete this first

## Out of Scope (Future)

- Issue #294 (Nova Micro switch) — do after this is complete
- Confidence calibration — accept model's scores as-is for MVP
- User-configurable threshold — hardcode 15% for now

## Acceptance Criteria

- [ ] Lambda returns `scores` object with all 4 categories
- [ ] Extension displays all categories ≥ 15% confidence
- [ ] "Pejorative" removed from all prompts
- [ ] "None" renamed to "General Usage" in taxonomy
- [ ] No single "signal" label in response
- [ ] Hate speech still returns 403 (no scores shown)
- [ ] Smoke test passes

## Definition of Done

### Implementation
- [ ] Lambda response includes scores
- [ ] Etymologist no longer returns "signal" field
- [ ] Extension renders score breakdown
- [ ] Unit tests for score filtering

### Documentation
- [ ] LLD: `docs/lld/active/XXX-confidence-score-display.md`
- [ ] Update extension wiki if applicable
- [ ] Add new files to `docs/0003-file-inventory.md`

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created

### Verification
- [ ] Run 0809 Security Audit - PASS
- [ ] Run 0817 Wiki Alignment Audit - PASS (if wiki updated)

## Testing Notes

Test with these terms to verify correct score distribution:
- "hello" → General Usage: ~100%
- "forsooth" → Archaic: ~95%
- "cryptocurrency" → General Usage: ~80%, Neologism: ~20%
- "tupping" → Provocative: ~85%, Archaic: ~10%

---
