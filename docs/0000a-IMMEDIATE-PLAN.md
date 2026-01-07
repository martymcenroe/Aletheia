# Immediate Plan: MVP Path to Store Submission

**Updated:** 2026-01-07 (Cleanup: Full Mode)
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
| LinkedIn OAuth | ✅ Complete |
| DynamoDB TTL | ✅ Complete |
| GDPR data erasure | ✅ Complete |
| Lambda Latency | ✅ Resolved |
| Museum Label UI | ✅ Complete |
| NoArchive Transform | ✅ Complete |

---

## Critical Path to Store Submission

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

## Post-Submission Features

Remaining work after store submission:

| Issue | Feature | Status |
|-------|---------|--------|
| #126 | Hard vs. Soft blocking | Open |

---

## Next Action

**Store Compliance (#51):** Review manifest.json, finalize privacy policy, and prepare store listing description.
