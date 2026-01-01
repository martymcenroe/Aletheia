# Immediate Plan: MVP Decision Point

**Updated:** 2026-01-01 02:30 CT
**Status:** At a fork in the road

---

## The Question

You have TWO viable paths. Choose ONE to focus on:

### Path A: Ship MVP Now (Chrome Store)
Submit current extension to Chrome Web Store. It works, just minimal.

**What's working:**
- ✅ Allowlist popup (domain enable/disable)
- ✅ Context menu "Explain with AI"
- ✅ Overlay feedback (success/error/blocked)
- ✅ Denylist (803 terms from Wikipedia)
- ✅ Semantic guardrails (Bedrock)
- ✅ Lambda deployed and tested

**Remaining for submission:**
| Issue | Task | Est. Effort |
|-------|------|-------------|
| #51 | Store Compliance (manifest, privacy policy) | Small |
| #53 | Store Assets (zip script, screenshots) | Small |

**Pros:** Fast to market, validate with real users
**Cons:** Basic UX, no auth gate, anyone can use

### Path B: Build V2 First (Erudite Suite)
Implement the "Digital Etymologist" features, THEN submit.

**Issues to complete:**
| Issue | Feature | Est. Effort |
|-------|---------|-------------|
| #116 | LinkedIn OAuth (auth gate) | Medium |
| #126 | Hard vs. Soft Blocking | Small |
| #124 | Digital Etymologist Persona | Medium |
| #125 | Museum Label UI | Medium |
| #51/#53 | Store submission | Small |

**Pros:** Polished product, auth prevents abuse
**Cons:** Longer to market, more complexity

---

## Recommendation

**Ship Path A first.** Get in the store, then iterate.

Reasons:
1. Current extension is functional and safe (denylist + semantic)
2. LinkedIn OAuth (#116) adds complexity and may delay
3. Store review takes days - start that clock now
4. V2 features can ship as updates

---

## Tomorrow's TODO (if Path A)

1. **#51: Store Compliance**
   - Review manifest.json for store requirements
   - Verify privacy policy exists (check index.html or separate page)
   - Write store listing description

2. **#53: Store Assets**
   - Run/create `tools/generate_store_assets.py`
   - Create extension zip (EXCLUDE: src/, tests/, docs/)
   - Take screenshots or use placeholders

3. **Submit to Chrome Web Store**
   - Create developer account ($5 one-time)
   - Upload zip and assets
   - Submit for review

---

## Open Issues Summary

| Category | Issues |
|----------|--------|
| **MVP Critical** | #51, #53 |
| **V2 Features** | #116, #124, #125, #126 |
| **Deferred (post-mvp)** | #117, #84 |
| **Process** | #127, #128, #129 |
| **Firefox** | #100 |
| **Nice-to-have** | #104, #106, #99, #94, #95 |
