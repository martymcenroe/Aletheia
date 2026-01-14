# Immediate Plan: POST-MVP - Store Review Period

**Updated:** 2026-01-14
**Status:** POST-MVP — Submitted to stores, awaiting approval

---

## Project Phase: POST-MVP

**The MVP is complete.** All core features are implemented, tested, and deployed. The extension has been submitted to both Chrome Web Store and Firefox Add-ons.

What "post-MVP" means:
- Product is feature-complete for initial release
- Waiting on external store approvals (out of our hands)
- Extensions not yet public (orchestrator decision)
- Agents are available for new work — **awaiting orchestrator to file issues**

---

## Recent Completions (2026-01-11)

| PR | Feature | Impact |
|----|---------|--------|
| #302 | Nova Micro switch | 2.76x faster (sub-second latency) |
| #297 | Confidence score display | Shows category breakdown instead of single label |
| #298 | Shadow DOM patch | Chrome E2E tests fixed (was 4/16, now passing) |
| #300 | aria-expanded fix | Accessibility compliance |
| #301 | Mixed quote normalization | Bedrock JSON parsing reliability |

**Backlog cleared — 0 open issues.**

---

## Current State

| Component | Status |
|-----------|--------|
| Extension - Chrome MV3 | ✅ Submitted to Chrome Web Store |
| Extension - Firefox MV2 | ⏳ Resubmission pending (fixes merged) |
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
| Security hardening (innerHTML) | ✅ Complete |
| Firefox manifest compliance | ✅ Complete |

---

## Store Submission Status

### Chrome Web Store
- **Status:** ✅ Submitted, awaiting review
- **Expected:** 1-3 days for review

### Firefox Add-ons (AMO)
- **Status:** ⏳ Resubmission pending
- **History:** Initial submission rejected (2026-01-08)
- **Fixes completed:**
  - ✅ Added `data_collection_permissions` + `strict_min_version`
  - ✅ Replaced `innerHTML` with safe DOM methods
- **Next:** Resubmit when ready

---

## Open PRs (0)

No open PRs. All feature work merged.

---

## Open Issues (0)

All issues closed. Backlog is clear.

| Issue | Feature | Closed |
|-------|---------|--------|
| #306 | Chrome E2E tests as CI blocking gate | ✅ |
| #106 | Full article context retrieval | ✅ |
| #81 | Landing page redesign | ✅ |

---

## Next Action

1. **Monitor store reviews** — Chrome and Firefox approvals pending
2. **Orchestrator to file new issues** — Agents standing by
3. **Backlog is clear** — All tracked issues closed
