# Immediate Plan: MVP Path to Store Submission

**Updated:** 2026-01-01 20:11 CT
**Status:** Implement #105 → merge #104 → then Store Compliance

---

## Current State

| Component | Status |
|-----------|--------|
| Extension - Chrome MV3 | ✅ Working (`extension-chrome-V3/`) |
| Extension - Firefox MV2 | ✅ Working (`extension-firefox-V2/`) |
| Lambda (Bedrock + DynamoDB) | ✅ Deployed |
| Denylist (803 Wikipedia terms) | ✅ Integrated |
| Semantic guardrails | ✅ Active |
| Rate limiting / WAF (#95) | ✅ Deployed |
| Overlay timing | ✅ Fixed (stateful timer management) |
| Store assets | ❌ Not created |

---

## Critical Path to Store Submission

### Step 1: Merge PR #138 (Firefox Support)
**PR:** #138 - feat: Firefox MV2 support and Chrome/Firefox extension separation (ref #100)
**Status:** Ready for orchestrator merge

**What it adds:**
- Separated Chrome and Firefox extensions into distinct directories
- Firefox MV2 manifest with gecko ID
- Fixed first-click timing bug
- Stateful timer management for smooth overlay transitions
- Build script for release ZIPs

### Step 2: Test Infrastructure (#105) ← NEXT
**LLD:** `docs/1105-test-site-infrastructure.md`
**Status:** LLD approved (Gemini reviewed), ready for implementation
**Worktree:** Create `Aletheia-105`

**What it adds:**
- GitHub Pages test site hosting
- Playwright E2E test framework
- 8 test HTML fixtures (age gate + XSS)
- `TEST_BASE_URL` env var for flexibility
- QA Sandbox disclaimers for GitHub ToS compliance

### Step 3: Age-Restricted Blocking (#104)
**LLD:** `docs/1104-age-restricted-blocking.md`
**PR:** #133 (code complete, 33 unit tests passing)
**Status:** Blocked by #105 for E2E test verification
**Worktree:** `Aletheia-104` (active)

**What it adds:**
- Blocks `rating="adult"` and RTA pattern
- Allows `rating="mature"`
- Three-state tab management (UNKNOWN/RESTRICTED/ALLOWED)
- "Not Permitted" popup and badge

### Step 5: Store Compliance (#51)
**LLD:** `docs/1051-store-compliance.md`
**Status:** Needs LLD update

- Review manifest.json for store requirements
- Privacy policy (may need GitHub Pages)
- Store listing description

### Step 6: Store Assets (#53)
**LLD:** `docs/1053-store-assets.md`
**Status:** LLD updated, partially implemented

- Extension zips (created by `tools/build_release.py`)
- Screenshots (1280x800 or 640x400) - NOT DONE
- Promotional tiles (440x280) - NOT DONE

### Step 7: Submit to Chrome Web Store
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

## Open PRs (3)

| PR | Issue | Branch | Status |
|----|-------|--------|--------|
| #138 | #100 Firefox | `53-100-firefox-build` | Ready for merge |
| #133 | #104 Age Block | `104-age-block` | Awaiting review |
| #131 | #124 Etymologist | `124-digital-etymologist` | Awaiting review |

---

## V2 Features (Post-MVP)

These are deferred until after Chrome Web Store submission:

| Issue | Feature |
|-------|---------|
| #116 | LinkedIn OAuth (auth gate) |
| #124 | Digital Etymologist persona |
| #125 | Museum Label UI |
| #126 | Hard vs. Soft blocking |

---

## Next Action

**Orchestrator:** Merge PR #138, then proceed with #51/#53 for store submission.
