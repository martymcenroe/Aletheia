# Immediate Plan: MVP Path to Store Submission

**Updated:** 2026-01-05 (by Claude Opus 4.5)
**Status:** Store Compliance (#51) → Store Assets (#53) → Submit

---

## Current State

| Component | Status |
|-----------|--------|
| Extension - Chrome MV3 | ✅ Working (`extensions/chrome/`) |
| Extension - Firefox MV2 | ✅ Working (`extensions/firefox/`) |
| Lambda (Bedrock + DynamoDB) | ✅ Deployed |
| Denylist (803 Wikipedia terms) | ✅ Integrated |
| Semantic guardrails | ✅ Active |
| Rate limiting / WAF (#95) | ✅ Deployed (PR #136 merged) |
| Digital Etymologist (#124) | ✅ Deployed (PR #131 merged) |
| Overlay timing | ✅ Fixed (stateful timer management) |
| Test Infrastructure (#105) | ✅ Complete (PR #139 merged) |
| Age-restricted blocking (#104) | ✅ Complete (PR #140 merged) |
| Store assets | ❌ Not created |

---

## Critical Path to Store Submission

### Step 1: Firefox Support (#100) ✅ COMPLETE
**PR:** #138 - merged 2026-01-02
- Separated Chrome and Firefox extensions into distinct directories
- Firefox MV2 manifest with gecko ID
- Fixed first-click timing bug
- Stateful timer management for smooth overlay transitions
- Build script for release ZIPs

### Step 2: Test Infrastructure (#105) ✅ COMPLETE
**PR:** #139 - merged 2026-01-04
- GitHub Pages test site hosting
- Playwright E2E test framework
- 8 test HTML fixtures (age gate + XSS)
- `TEST_BASE_URL` env var for flexibility
- CI pipeline with pytest, coverage, linting

### Step 3: Age-Restricted Blocking (#104) ✅ COMPLETE
**PR:** #140 - merged 2026-01-04
- Blocks `rating="adult"` and RTA pattern
- Allows `rating="mature"`
- Three-state tab management (UNKNOWN/RESTRICTED/ALLOWED)
- "Not Permitted" popup and badge
- 6 E2E tests passing

### Step 4: Store Compliance (#51) ← CURRENT
**LLD:** `docs/1051-store-compliance.md`
**Status:** Needs LLD update

- Review manifest.json for store requirements
- Privacy policy (may need GitHub Pages)
- Store listing description

### Step 5: Store Assets (#53)
**LLD:** `docs/1053-store-assets.md`
**Status:** LLD updated, partially implemented

- Extension zips (created by `tools/build_release.py`)
- Screenshots (1280x800 or 640x400) - NOT DONE
- Promotional tiles (440x280) - NOT DONE

### Step 6: Submit to Chrome Web Store
- Developer account ($5 one-time)
- Upload zip and assets
- Submit for review (takes 1-3 days)

---

## Open Investigation

### Issue #137: Lambda Latency
**Status:** Open - investigation needed

Lambda takes ~5 seconds to respond. Tested with `max_tokens=10` (minimal generation) - still 5 seconds. This rules out LLM generation time as the cause.

**Hypotheses to investigate:**
1. Cold start latency
2. DynamoDB write latency
3. Bedrock API overhead
4. Semantic guardrail check time

---

## Open PRs (0)

No open PRs. All feature work merged.

---

## V2 Features (Post-MVP)

These are deferred until after Chrome Web Store submission:

### High Priority (GDPR Compliance)

Per 0809 security audit and Gemini review (2026-01-05): #116 is a **prerequisite** for #147 because users cannot prove ownership of hash-based `thread_id` without authentication.

**Key Decision (2026-01-05):**
- DynamoDB TTL set to **30 days** (not 24h) - balances privacy with user value
- 30-day retention legally requires on-demand deletion capability
- On-demand deletion requires user identification (OAuth)
- Therefore: **#147 is BLOCKED BY #116**

| Issue | Feature | Status |
|-------|---------|--------|
| #145 | DynamoDB TTL (30 days) | ✅ Ready to implement |
| #116 | LinkedIn OAuth (auth gate) | **HIGH** - enables user identification |
| #147 | GDPR data erasure | ⛔ **BLOCKED BY #116** |

### Standard Priority

| Issue | Feature |
|-------|---------|
| #125 | Museum Label UI |
| #126 | Hard vs. Soft blocking |

---

## Next Action

**Store Compliance (#51):** Review manifest.json, finalize privacy policy, and prepare store listing description. Then proceed to Store Assets (#53) for screenshots and promotional tiles.
