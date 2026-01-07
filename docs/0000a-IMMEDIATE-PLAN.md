# Immediate Plan: MVP Path to Store Submission

**Updated:** 2026-01-06 (by Claude Opus 4.5)
**Status:** Store Compliance (#51) → Submit

---

## Current State

| Component | Status |
|-----------|--------|
| Extension - Chrome MV3 | ✅ Working (`extensions/chrome/`) |
| Extension - Firefox MV2 | ✅ Working (`extensions/firefox/`) |
| Lambda (Bedrock + DynamoDB) | ✅ Deployed |
| Denylist (803 Wikipedia terms) | ✅ Integrated |
| Semantic guardrails | ✅ Active |
| Rate limiting / WAF | ✅ Deployed |
| Digital Etymologist | ✅ Deployed |
| Overlay timing | ✅ Fixed |
| Test Infrastructure | ✅ Complete |
| Age-restricted blocking | ✅ Complete |
| Store assets | ✅ Complete |

---

## Critical Path to Store Submission

### ✅ Completed Steps
- Firefox Support (PR #138)
- Test Infrastructure (PR #139)
- Age-Restricted Blocking (PR #140)
- Store Assets (PR #185)

### Step 1: Store Compliance (#51) ← CURRENT
**LLD:** `docs/1051-store-compliance.md`

- Review manifest.json for store requirements
- Privacy policy (may need GitHub Pages)
- Store listing description

### Step 2: Submit to Chrome Web Store
- Developer account ($5 one-time)
- Upload zip and assets
- Submit for review (takes 1-3 days)

---

## Open PRs (0)

No open PRs. All feature work merged.

---

## V2 Features (Post-MVP)

These are deferred until after Chrome Web Store submission:

### ✅ Completed V2 Features
- LinkedIn OAuth (#116) - auth gate for user identification
- DynamoDB TTL (#145) - 30-day retention
- GDPR data erasure (#147) - on-demand deletion endpoint
- Lambda Latency (#137) - investigated and resolved
- Museum Label UI (#125) - implemented

### Remaining V2

| Issue | Feature |
|-------|---------|
| #126 | Hard vs. Soft blocking |

---

## Next Action

**Store Compliance (#51):** Review manifest.json, finalize privacy policy, and prepare store listing description.
