# Aletheia - Open Issues

**Generated:** 2026-02-25 CT
**Total Open Issues:** 15

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

## Issue #310: feat: Poetic Resonance Detection - Layered Meaning Analysis

**Labels:** enhancement

**Created:** 2026-01-11
**Updated:** 2026-01-11

### Description

## Objective

Enable the Digital Etymologist to detect and explain layered/poetic meanings in word usage, where a term's deeper connotations resonate with the surrounding context.

## UX Flow

### Scenario 1: Poetic Resonance Detected (Happy Path)
1. User highlights "ascension" in an article about elderly people in a nursing home
2. Nova Micro returns etymology + `poetic_potential: 0.78` + `dimensions: ["religious", "architectural"]`
3. Extension displays normal etymology PLUS "Explore Deeper Meaning" button
4. User clicks button
5. Opus analyzes and returns the layered interpretation
6. Result: User gains insight into the layered meaning they might have missed

### Scenario 2: Low Poetic Potential
1. User highlights "hello" in any context
2. Nova Micro returns etymology + `poetic_potential: 0.1` + `dimensions: []`
3. Extension displays normal etymology only
4. No "Explore Deeper Meaning" button appears
5. Result: No unnecessary prompting for common words

### Scenario 3: Novel Dimension Discovered
1. User highlights a word with unusual cultural resonance
2. Nova Micro returns `dimensions: ["novel:internet_culture"]`
3. User clicks "Explore Deeper Meaning"
4. Opus explains the emergent dimension
5. Result: System handles dimensions beyond the pre-defined list

### Scenario 4: Opus Analysis Failure/Timeout (Error Path)
1. User highlights word, sees "Explore Deeper Meaning" button
2. User clicks button
3. Opus fails to respond within 3500ms OR returns error
4. Button shows loading state, then error: "Analysis unavailable - please try again"
5. User can retry or dismiss
6. Result: Graceful degradation, etymology still visible

## Requirements

### Nova Micro Enhancement
1. Output `poetic_potential` score (0.0-1.0) for every analysis
2. Output `potential_dimensions` array (from core list + novel)
3. Maintain backward compatibility with existing response fields
4. Stay within 550ms latency budget (P95)

### Opus Deep Analyzer
1. New module `src/poetic_analyzer.py`
2. Accept word, page context, and initial dimensions
3. Return multi-dimensional analysis with synthesis
4. Return `resonance_strength` score (0.0-1.0) in response
5. Target latency: <3500ms (Lambda processing only, excludes client network RTT)

### Lambda Routing
1. `POETIC_THRESHOLD = 0.6` triggers button visibility
2. New action type: `deep_poetic_analysis`
3. Include `poetic_analysis` in response when available
4. Return error response with `status: "error"` on Opus failure

### Extension UI
1. "Explore Deeper Meaning" button appears when `poetic_potential >= 0.6`
2. Dimension chips with text labels AND color (accessible without color vision)
3. Synthesis paragraph display
4. Resonance strength indicator (sourced from Opus `resonance_strength`, NOT `poetic_potential`)
5. Error state: "Analysis unavailable" with retry button
6. Loading state: Button disabled with spinner during Opus call

### Accessibility (0811 Compliance)
1. Dimension chips MUST have text labels (not color-only)
2. Use icons alongside color to distinguish dimensions (icons use `aria-hidden="true"`)
3. Resonance strength indicator must have text alternative
4. Error messages announced to screen readers (aria-live)

## Technical Approach

- **Nova Micro Prompt:** Add poetic detection instructions to `SYSTEM_PROMPT_NOVA` in `etymologist.py`
- **Opus Analyzer:** New `src/poetic_analyzer.py` with dedicated prompt for deep analysis
- **Lambda:** Conditional routing based on threshold, new action endpoint, timeout handling
- **Extension:** Button in popup, display in overlay, CSS for accessible dimension chips
- **Page Context:** Uses existing `domContext` (body.innerText); synergizes with #106 when implemented

## Security Considerations

- **Prompt injection:** Existing XML tag wrapping protects against injection in page context
- **Cost control:** Deep analysis is user-initiated only (button click), no automatic Opus calls
- **PII:** Opus prompt instructs not to include personal names in synthesis
- **Data handling:** Poetic analysis not persisted to DynamoDB (in-memory only)

## Files to Create/Modify

- `src/etymologist.py` — Add poetic detection to Nova Micro prompt and response schema
- `src/poetic_analyzer.py` — **NEW** Opus deep analyzer module
- `src/lambda_function.py` — Add routing logic and deep analysis endpoint
- `extensions/chrome/popup.html` — Add "Explore Deeper Meaning" button
- `extensions/chrome/popup.js` — Handle button click, store poetic data, error handling
- `extensions/chrome/overlay.js` — Display poetic analysis section with accessible chips
- `extensions/firefox/*` — Mirror all Chrome changes
- `tests/test_poetic_analyzer.py` — **NEW** Unit tests for analyzer

## Dependencies

- None (can be implemented independently)
- **Synergy with #106:** Full article context would improve Opus analysis quality, but not required
- **Coordinate with #81:** Landing page should highlight poetic resonance as key feature

## Out of Scope (Future)

- Automatic deep analysis without user click (cost concern)
- Confidence calibration for poetic potential
- User-configurable threshold
- Historical tracking of poetic discoveries

## Acceptance Criteria

- [ ] Nova Micro returns `poetic_potential` (0.0-1.0) for all analyses
- [ ] Nova Micro returns `potential_dimensions` array
- [ ] Nova Micro P95 latency remains < 550ms with new prompt
- [ ] "Explore Deeper Meaning" button appears when `poetic_potential >= 0.6`
- [ ] Button does NOT appear when `poetic_potential < 0.6` (test at 0.59)
- [ ] Clicking button triggers Opus analysis
- [ ] Opus returns synthesis explaining layered meaning
- [ ] Opus returns `resonance_strength` (displayed in UI)
- [ ] Dimension chips display with text labels AND colors (accessible)
- [ ] "Ascension" example produces meaningful output with religious + architectural dimensions
- [ ] Normal words like "hello" show low poetic potential (no button)
- [ ] Opus timeout/failure shows error state with retry option
- [ ] Backward compatibility maintained (old clients still work)

## Definition of Done

### Implementation
- [ ] Nova Micro prompt updated with poetic detection
- [ ] `poetic_analyzer.py` module created
- [ ] Lambda routing logic implemented
- [ ] Extension UI changes (both Chrome and Firefox)
- [ ] Unit tests for poetic analyzer
- [ ] E2E tests for button flow
- [ ] E2E test for error/timeout state

### Documentation
- [ ] LLD: `docs/lld/active/1310-poetic-resonance.md`
- [ ] Add new files to `docs/0003-file-inventory.md`
- [ ] Update wiki if user-facing changes
- [ ] **Coordinate with #81:** Update landing page to highlight poetic resonance feature

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created

### Verification
- [ ] Run 0809 Security Audit - PASS
- [ ] Run 0811 Accessibility Audit - PASS (dimension chips)
- [ ] Run 0812 Performance Audit - PASS (verify latency budgets)

## Testing Notes

Test with these terms:
- "hello" in any context → Low poetic potential, no button, **verify no Opus call made**
- "ascension" in elderly care article → High potential, religious + architectural dimensions
- "foundation" in business article about charity → Potential architectural + organizational resonance
- "revolution" in astronomy article → Political + scientific dimensions

**Boundary tests:**
- `poetic_potential: 0.59` → Button does NOT appear
- `poetic_potential: 0.60` → Button DOES appear

**Negative test (cost verification):**
- Highlight word with poetic_potential >= 0.6
- Do NOT click "Explore Deeper Meaning" button
- Verify NO Opus API call in CloudWatch logs

**Error handling test:**
- Simulate Opus timeout (mock 4000ms delay)
- Verify error state displays with retry button

To verify Opus latency: Check `_debug_timings.poetic_analysis_ms` in dev mode response.

## Core Dimensions (Reference)

| Dimension | Icon | Color | Trigger Examples |
|-----------|------|-------|------------------|
| religious | Cross | Purple | ascension, calling, grace, trinity |
| literary | Book | Orange | odyssey, quixotic, kafkaesque |
| architectural | Building | Green | foundation, pillar, threshold |
| artistic | Palette | Blue | composition, canvas, frame |
| political | Scales | Red | revolution, mandate, regime |
| scientific | Microscope | Cyan | catalyst, critical mass, quantum |
| novel:{desc} | Lightbulb | Gray | LLM discovers new dimension |

---

**Gemini Review:** Approved (2026-01-11)

---

## Issue #311: docs: Write Context-Aware explanation page content

**Created:** 2026-01-11
**Updated:** 2026-01-11

### Description

## Summary

The landing page now links to `docs/context.html` from the Context-Aware feature card. A placeholder page has been created but needs real content.

## Current State

- Placeholder page exists at `docs/context.html`
- Basic structure with "Coming Soon" notice
- Links working from landing page

## Content Needed

1. **Why Context Matters** - Explain the problem with traditional dictionaries (static definitions that don't account for context)

2. **How Aletheia Works** - Technical but accessible explanation of:
   - Surrounding text extraction
   - How the AI uses context to disambiguate meaning
   - Why this produces better results than dictionary lookups

3. **Examples** - Real before/after examples showing:
   - A word with multiple meanings (e.g., "bank", "cell", "interest")
   - How Aletheia's context-aware response differs from a dictionary definition
   - Maybe include screenshots of the extension in action

## Design Notes

- Page uses same styling as privacy.html (Libre Baskerville headers, Space Grotesk body)
- Keep it concise - this is marketing content, not documentation
- Target audience: potential users who want to understand the value proposition

## Files

- `docs/context.html` - Edit this file

---

Created from landing page work (Issue #81)

---

## Issue #312: Security: Patch Denial-of-Wallet Vulnerabilities

**Labels:** security, bug

**Created:** 2026-02-25
**Updated:** 2026-02-25

### Description

## Objective
Implement patches for two high-severity Denial-of-Wallet vulnerabilities identified in the rate-limiting and authentication middleware systems.

## UX Flow

### Scenario 1: Database Outage (Fail-Closed)
1. System experiences DynamoDB outage.
2. User from any tier attempts to use the API.
3. System responds with 503 "Service temporarily unavailable".
4. Result: Prevents uncontrolled costs during the outage.

### Scenario 2: Deep Poetic Analysis Rate Limiting
1. User invokes the `deep_poetic_analysis` action (which uses the expensive Opus model).
2. The rate limiter identifies the action and applies a higher token weight (e.g., 5).
3. Result: Quota is accurately consumed based on the cost of the model used, preventing rapid Bedrock credit exhaustion.

## Requirements

### Fail-Closed Architecture
1. The `_handle_dynamo_error` function in `src/auth/token_cap_service.py` must fail closed for all tiers (free, subscriber, admin) during a database error.

### Request Weighting
1. The rate-limiting counter `MultiWindowCounter` must accept a `weight` parameter and decrement the cap limit accordingly.
2. `require_auth` in `src/auth/auth_middleware.py` must inspect the body to determine request weight depending on the action (`deep_poetic_analysis`).

## Technical Approach
- **token_cap_service.py:** Modify `check_and_increment` to accept a `weight` parameter and update the DynamoDB `ConditionExpression` to use `:cap_limit` instead of `:cap`. Modify `_handle_dynamo_error` to fail closed for all tiers.
- **auth_middleware.py:** Parse the request body in `require_auth` to determine the action type. If `deep_poetic_analysis`, pass a weight of 5 to `check_rate_limit`.
- **test_multi_window_counter.py:** Update boundary tests to assert against `:cap_limit` and update the fail-open tests for subscriber/admin tiers to assert fail-closed behavior.

## Security Considerations
These changes directly remediate Denial-of-Wallet vulnerabilities, preventing financial exhaustion via abuse of expensive models or during database outages.

## Files to Modify
- `src/auth/token_cap_service.py` — Implement weighting and fail-closed logic.
- `src/auth/auth_middleware.py` — Pass request weight based on action.
- `tests/unit/test_multi_window_counter.py` — Update tests for new logic.

## Acceptance Criteria
- [ ] `check_and_increment` correctly applies the `weight` parameter to the DynamoDB transaction.
- [ ] Database errors result in a 503 response for all tiers.
- [ ] `deep_poetic_analysis` actions consume 5 tokens instead of 1.
- [ ] All unit tests pass.

---
