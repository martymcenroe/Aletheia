# Immediate Plan: MVP Path with Security Hardening

**Updated:** 2026-01-01 (morning)
**Status:** LLD for #95 ready for Gemini review

---

## Critical Path to Chrome Web Store

### Step 1: Security Hardening (#95) ← BLOCKING
**LLD:** `docs/1095-security-hardening.md`
**Status:** LLD written, awaiting Gemini review

**What it adds:**
- CloudFront in front of Lambda Function URL
- AWS WAF with rate limiting (100 req/5min/IP)
- Header validation (`X-Aletheia-Client-Version`)
- Denial of Wallet protection

**Why blocking:**
Without rate limiting, a malicious actor could run up AWS costs by hammering the endpoint. This is unacceptable before public release.

### Step 2: Store Compliance (#51)
**LLD:** `docs/1051-store-compliance.md`
**Status:** Needs LLD update

- Review manifest.json for store requirements
- Privacy policy (may need GitHub Pages)
- Store listing description

### Step 3: Store Assets (#53)
**LLD:** `docs/1053-store-assets.md`
**Status:** Needs LLD

- Extension zip (EXCLUDE: src/, tests/, docs/)
- Screenshots (1280x800 or 640x400)
- Promotional tiles (440x280)

### Step 4: Submit to Chrome Web Store
- Developer account ($5 one-time)
- Upload zip and assets
- Submit for review (takes 1-3 days)

---

## Current State

| Component | Status |
|-----------|--------|
| Extension (popup, context menu, overlay) | ✅ Working |
| Lambda (Bedrock + DynamoDB) | ✅ Deployed |
| Denylist (803 Wikipedia terms) | ✅ Integrated |
| Semantic guardrails | ✅ Active |
| Age gate (#104) | ⏳ Code complete, pending E2E tests |
| Rate limiting / WAF | ❌ Not deployed |
| Store assets | ❌ Not created |

---

## Parallel Track: Age Gate Testing (#104 + #105)

**Status:** #104 code complete (PR #133), blocked by #105

| Issue | Description | Status |
|-------|-------------|--------|
| #104 | Age-restricted content blocking | Code complete, 33 unit tests passing |
| #105 | Test site infrastructure | LLD written (`docs/1105-test-site-infrastructure.md`), needs review |

**Why not blocking MVP:** Age gate is a safety enhancement, not a store requirement. Can ship MVP and add age gate verification in parallel.

**Next:** Review `docs/1105-test-site-infrastructure.md`, then implement Playwright E2E tests to unblock #104 merge.

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

**Gemini:** Review `docs/1095-security-hardening.md` using `docs/0109-gemini-lld-review-procedure.md`

After Gemini approval → Opus implements #95 → Then #51/#53 → Submit
