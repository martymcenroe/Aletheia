# Implementation Report — #681, #682

**Issues:** [#681](https://github.com/martymcenroe/Aletheia/issues/681) (rm -f glob in runbooks), [#682](https://github.com/martymcenroe/Aletheia/issues/682) (AMO runbook wrong version fact)
**Date:** 2026-05-29 Central
**Type:** Documentation (runbook corrections to PR #679)

## Why

Two defects in the store-publish runbooks shipped in PR #679, caught in operator review:

1. **#681 — banned deletion pattern.** Both runbooks instructed `rm -f dist/aletheia-*-v*.zip` to clear stale build artifacts. That is a glob force-delete — the "wipe by pattern" hammer the universal CLAUDE.md bans.
2. **#682 — wrong fact.** The AMO runbook (`10907`) claimed "Current published version: 1.1.2". The live AMO version is `1.1.1` (per the AMO public API; 1.1.2 was release-noted but never published).

## Changes

`docs/runbooks/10905-runbook-cws-publish.md` (→ v1.0.1):
- §4a build + fallback: `rm -f <glob>` → list (`ls -1`) → inspect → delete identified file by name → STOP if unexpected.
- Hardening-gap note rewritten (no `rm -f`; future `build_release.py` auto-clean must delete by exact name).
- Deployment-state date corrected to "live; updated 2026-05-25" (CWS version 1.1.2 is correct).
- Changelog row added.

`docs/runbooks/10907-runbook-amo-publish.md` (→ v1.0.1):
- Same `rm -f` → list/inspect/delete-by-name fix in §4a + hardening note.
- Version fact corrected in 3 places: deployment-state, §1 Path B, §3a.1 — now "AMO live 1.1.1; repo/next-upload 1.1.2 (pending, never published)".
- Changelog row added.

## Verification

`grep "rm -f"` over both files returns only the changelog text describing the fix and the safe named-delete example (`rm <file>`), no `rm -f` commands. AMO version reads 1.1.1-live/1.1.2-pending in all three locations. See test-report.md.

## Not in scope (separate follow-ons)

- `build_release.py` stale-artifact auto-clean (a code change; the runbooks flag it).
- CWS listing-copy corrections from `docs/10920` (dashboard edits; CWS was last updated 2026-05-25, before the 2026-05-27 corrections doc).
- Getting Firefox 1.1.2 actually live on AMO (operator publish, pending operator direction).
