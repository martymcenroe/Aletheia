# Implementation Report — Issue #625

**Title:** feat: prompt-injection demo content + Clio-style threat-model wiki
**Date:** 2026-05-23
**Status:** Complete (pending review + merge)
**Branch:** `625-demo-content-and-threat-model`

## Summary

Built a complete demo + documentation suite for Aletheia's prompt-injection defense:

1. Five standalone parody pages, each with an embedded prompt-injection attempt, that visitors can independently invoke Aletheia on to verify the defense works.
2. A Clio-styled threat-model page articulating the "Screen → Verify → Surface" defense posture, what Aletheia commits to defending against, and what it explicitly does not.
3. A demos walkthrough page that links each demo with "what to try" guidance.
4. An update to the existing safety page documenting the Opus verifier layer (shipped in #623).

The demos are transformative parody — recognizable enough to be entertaining, fictional enough to evade DMCA concerns. Names like "Sparx Industries" (not Stark), "Discovery One Systems Corporation" (Discovery One was the ship, not the company), "Tyrenn Corporation" (not Tyrell), and editorial flags everywhere stating that the pages are parody artifacts for testing AI safety tooling.

## Files Created

| File | Genre | Injection Surface |
|------|-------|-------------------|
| `docs/threat-model.html` | Aletheia wiki | n/a — explanatory page |
| `docs/demos.html` | Aletheia wiki | n/a — index page |
| `docs/demos/daily-planet.html` | News article (1990s newspaper) | Reproduced "leaked memo" quoted in body |
| `docs/demos/discovery-one.html` | Technical specification (aerospace corporate) | Example "Configuration Override Block" code snippet |
| `docs/demos/seldon-journal.html` | Academic paper (open-access journal) | "Editor's Note Regarding Automated Summarization" |
| `docs/demos/sparx-linkedin.html` | LinkedIn post (CEO product announcement) | "User testimonial" quote |
| `docs/demos/nexus-wiki.html` | Wikipedia article (encyclopedia entry) | Quote-template citing a fictional leaked design document |

## Files Modified

| File | Change |
|------|--------|
| `docs/safety.html` | Added "Opus Verifier — Post-Classification Sanity Check" section between "Semantic Classifier Error Handling" and "Hallucination Prevention." Corrected stale claim that Nova Micro was the default (production runs on Haiku 4.5; see #620). |
| `docs/index.html` | Added "Demos" nav link and "Threat Model" dropdown entry. |
| `docs/architecture.html` | Same nav update. |
| `docs/observability.html` | Same nav update. |
| `docs/operations.html` | Same nav update. |
| `docs/privacy.html` | Same nav update. |
| `docs/context.html` | Same nav update. |

## Voice and style

The threat model mirrors the Clio wiki's register: measured confidence, commitment language ("load-bearing," "structural enforcement"), explicit scope and limit sections, threat-response pairing. The CIA-triad scaffold becomes "Screen → Verify → Surface" — the same architectural-framework move but specific to Aletheia's threat surface.

Each demo page uses bespoke per-genre styling (newspaper serif, aerospace-corporate sans-serif, academic journal serif, LinkedIn product UI, Wikipedia infobox grid). None inherit the Aletheia chrome — that's intentional. They have to look like genuine artifacts of their respective genres for the demonstration to land.

A small banner at the top of each demo identifies it as a parody artifact and links back to the demos index. This is the minimum needed for ethical disclosure without breaking the demonstration flow.

## DMCA / trademark posture

Each demo page includes a footer disclaimer noting parody intent and that referenced IP belongs to respective owners. Names have been transformed where direct use would create infringement risk:

| Source IP | Parody name used |
|-----------|------------------|
| Stark Industries / Tony Stark | Sparx Industries / Anthony Sparx |
| HAL 9000 (2001: A Space Odyssey) | HAL-3000 (Discovery One Systems Corporation) |
| Tyrell Corporation (Blade Runner) | Tyrenn Corporation |
| Nexus-6 replicants (Blade Runner) | Nexus-7 Synthetic Companion (third generation) |

The Superman/Daily Planet/Lex Luthor demo uses original names because the satirical premise (Superman foiling an AI prompt-injection attack) is inherently transformative — the framing is so absurd no reasonable reader could mistake it for DC content.

The Foundation/psychohistory paper uses Asimov-canonical character names (Hari Seldon, Gaal Dornick, R. Daneel) in an obviously fictional academic-publishing context. Parody under fair use.

## Deploy

This is a docs-only change. No Lambda redeploy required. After merge to `main`:

1. CloudFlare Pages (or whichever static-site host serves `aletheia.study`) auto-publishes the new pages.
2. Verify each new page renders correctly at:
   - `https://aletheia.study/threat-model.html`
   - `https://aletheia.study/demos.html`
   - `https://aletheia.study/demos/daily-planet.html`
   - `https://aletheia.study/demos/discovery-one.html`
   - `https://aletheia.study/demos/seldon-journal.html`
   - `https://aletheia.study/demos/sparx-linkedin.html`
   - `https://aletheia.study/demos/nexus-wiki.html`
3. Manual smoke test: install Aletheia in a browser, visit each demo page, select the highlighted injection text, verify the overlay returns `signal: "Prompt Injection Attempt"` (or the verified Opus downgrade) rather than echoing the attacker's instructions.

## Out of Scope

- Hosting demos on a separate domain (e.g., `dailyplanet.fakenews.martymcenroe.ai`). Files live in this repo; URL routing changes are a future concern.
- Automated end-to-end tests that visit each demo page in a headless browser and assert Aletheia's response. This requires a test JWT (production has `AUTH_ENABLED=true`) and is non-trivial to set up.
- Privacy policy update for content retention. Operational logging of `opus_verifier` events (signal-only, no input text) fits the existing operational-metrics carve-out per `docs/privacy.html` section 6.

## Related

- #618 — gedenken misclassification (the failure mode the demos showcase being correctly handled)
- #623 — Opus verifier (the defense layer demonstrated)
- #620 — model-routing consolidation (production currently runs Haiku, documented in updated safety.html)
- Clio wiki (https://github.com/martymcenroe/Clio/wiki) — style reference for the threat-model voice
