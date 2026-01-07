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
| LinkedIn OAuth | ✅ Complete (closed #116) |
| DynamoDB TTL | ✅ Complete (closed #145) |
| GDPR data erasure | ✅ Complete (closed #147) |
| Lambda Latency | ✅ Resolved (closed #137) |
| Museum Label UI | ✅ Complete (closed #125) |

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
| #162 | Transform layer (noarchive summarization) | In Progress (worktree exists) |

---

## Next Action

**Store Compliance (#51):** Review manifest.json, finalize privacy policy, and prepare store listing description.
