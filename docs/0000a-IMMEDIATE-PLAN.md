# Immediate Plan: Store Review & Post-Launch

**Updated:** 2026-01-10
**Status:** Submitted to stores, awaiting review

---

## Backlog Cleanup (2026-01-09 - 2026-01-10)

Reviewed all open issues. Closed/consolidated 9 issues:

| Issue | Action |
|-------|--------|
| #6 | Closed - RAG Vector Store was resume fluff, no clear use case |
| #127, #128, #129 | Consolidated into #203 (Future: AgentOS Process Improvements) |
| #151 | Closed - GitHub Security Settings already complete |
| #149 | Closed - lambda_harvester_function.py already removed |
| #161 | Closed - CI Performance benchmarks completed |
| #160 | Closed - CI Accessibility checks completed |
| #126 | Closed - Hard vs. Soft blocking completed |

**Backlog reduced to 14 open issues.**

### Ready to Implement (LLD + Gemini Review)
- **#132** - Support email infrastructure (needs Cloudflare access)

### Updated /onboard Skill
- `--full` now regenerates digest before reading docs
- `--quick` reports digest age
- Digest is now gitignored (auto-generated, local-only)

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
| #81 | Landing page redesign | post-mvp |
| #117 | Unauthenticated users | post-mvp |

---

## Next Action

**Monitor Chrome Web Store review.** Resubmit to Firefox Add-ons when ready.
