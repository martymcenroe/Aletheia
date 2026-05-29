# Issue #691 — Implementation Report

## Issue summary

Delete the fabricated runbook rule that banned live `console.log` / `console.debug` / `console.info` / `console.warn` calls in extension JavaScript. The rule was framed as a privacy-policy concern by the agent in the 2026-05-29 onboard, but had no grounding in `docs/privacy.html` or any other source document.

## Change set

### `docs/runbooks/10907-runbook-amo-publish.md`

- Version: 1.0.4 → 1.0.5.
- Last updated: 2026-05-29 11:26:54 AM Central.
- **§3a.4**: removed the *"No live debug-tier console calls in `extensions/firefox/*.js` (same banned/allowed rule as the Chrome runbook §3a.3)"* clause. The item now reads only the kept *"No hardcoded test URLs or dev flags"* portion. No renumbering needed — items 5–8 keep their numbers, and the §3b.5 + §8b cross-references to §3a.7 and §3a.8 remain accurate.
- Change-log entry added at v1.0.5.

### `docs/runbooks/10905-runbook-cws-publish.md`

- Version: 1.0.2 → 1.0.3.
- Last updated: 2026-05-29 11:26:54 AM Central.
- **§3a.3 deleted in full.** Remaining §3a items 4–11 renumbered to 3–10.
- §3b.3 cross-reference updated: §3a.10 → §3a.9.
- §3b.5 cross-reference updated: §3a.11 → §3a.10.
- §8 (Graphic assets) cross-reference updated: §3a.9 → §3a.8.
- Change-log entry added at v1.0.3.

## Grounding (why the rule had to go)

`docs/privacy.html` (last updated March 2026):

- Commits to what is sent to servers, stored for 30 days, not used for training, not sold.
- No mention of console output. No mention of local browser-state behavior.

Grep across `docs/*.html`, `docs/lld/done/10051-store-compliance.md`, and the broader `docs/` tree for `console\.|local.{0,10}log|browser.{0,10}console` (case-insensitive): no matches outside the two runbooks themselves.

`console.log(...)` writes to the user's own browser DevTools panel on the user's own machine. It is not transmitted, not stored on a remote server, not shared with a third party. The privacy policy makes no commitment that prohibits it.

## Out of scope

- The two `extensions/firefox/service-worker.js` lines (`:566`, `:585`) flagged in the original handoff are **not** modified by this PR. With the rule removed, they are a code-hygiene matter, not a publishing blocker. A future decision about removing them belongs in its own issue if anyone chooses to pursue it.
- The other ~28 mundane `console.log` calls across `extensions/firefox/{auth.js, popup.js, service-worker.js}` are also unaffected.
- The blog draft at `C:/Users/mcwiz/Projects/dispatch/drafts/2026-05-29-vigilance-is-the-eternal-price-of-freedom-from-Aletheia.md` is in a separate repo and uncommitted.
- The lessons-learned entry on `main` is uncommitted on main and will batch with `/cleanup` per project rule.

## Related artifacts

- Issue body of #691 was rewritten before opening this PR; the "Decision pending" section now reads "Decision: delete the rule."
- `data/pickup-read-log.md` entry 2026-05-29 08:11:30 contains the grep results that established the rule had no upstream source.
- `docs/lessons-learned.md` entry dated 2026-05-29 captures the broader lesson (agent-authored rule + agent-applied privacy framing = self-confirming false constraint).
