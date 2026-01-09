# Immediate Plan: Store Review & Post-Launch

**Updated:** 2026-01-08
**Status:** Submitted to stores, awaiting review

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

## Post-Launch Features

| Issue | Feature | Status |
|-------|---------|--------|
| #126 | Hard vs. Soft blocking | Open |

---

## Next Action

**Monitor Chrome Web Store review.** Resubmit to Firefox Add-ons when ready.
