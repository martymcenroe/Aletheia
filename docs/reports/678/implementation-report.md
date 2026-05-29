# Implementation Report — #678

**Issue:** [#678](https://github.com/martymcenroe/Aletheia/issues/678) — docs(runbooks): refresh CWS publishing runbook to AZ#1362 standard; add Mozilla AMO publishing runbook
**Date:** 2026-05-28 Central
**Type:** Documentation (runbooks)

## Objective

Refresh Aletheia's Chrome Web Store publishing runbook to the AssemblyZero#1362 runbook standard, and add a parallel Firefox AMO publishing runbook built to the same standard.

## Dependency finding (the "figure this out")

[AZ#1362](https://github.com/martymcenroe/AssemblyZero/issues/1362) (the runbook standard) is **OPEN / unshipped** — the standard doc `AssemblyZero/docs/standards/00XX-runbook-standard.md` does not exist yet. This does **not** block the work:

- The complete 20-principle spec lives in the AZ#1362 issue body.
- [Clio `30002`](https://github.com/martymcenroe/Clio/blob/main/docs/runbooks/30002-chrome-web-store-publish.md) is the operator-validated reference implementation (iterated v1 → 5.1.0 in one session).

Both Aletheia runbooks were built to the issue-body spec, modeled on Clio 30002. [AZ#1363](https://github.com/martymcenroe/AssemblyZero/issues/1363) (fleet audit dashboard) is also open; updating Aletheia's row there is a follow-on (see Open items).

## Changes

| File | Action |
|---|---|
| `docs/runbooks/10905-runbook-cws-publish.md` | **New** — refreshed CWS runbook (renamed from `10905-runbook-extension-store-publish.md`, scoped Chrome-only) |
| `docs/runbooks/10907-runbook-amo-publish.md` | **New** — Firefox AMO runbook (10906 was taken by the image-pad runbook) |
| `docs/runbooks/10905-runbook-extension-store-publish.md` | **Deleted** — split into the two above |
| `docs/runbooks/10900-runbook-index.md` | Updated index: 10905 → CWS, new 10907 → AMO |
| `docs/runbooks/10906-runbook-cws-image-pad.md` | Updated cross-reference to point at both new runbooks |

## AZ#1362 conformance (20 principles)

Structural: semver+timestamp header (1), "verify latest copy" + "Throughout" stanza (2,3), §0 invoke-phrase table prefixed `cws`/`amo` to disambiguate the two runbooks (4), §1 reading-path matrix Path A/B/C (5), numbered §1–§20 incl. reference sections (6), §3a/§3b agent/operator split with numbered items (7), §20 change log (8), no orphan subsections (9).

Content: agent owns every mechanical task — `build_release.py`, manifest/permission checks, ZIP verify, screenshot dimension checks, `gh issue comment`, `git tag` (10); inline paste-blocks for Name, descriptions, single-purpose, all permission justifications (11); rationale lists for Category/AMO-category (12); dashboard-order parity (13); "where, not just what" dashboard locations (14); cross-page Account Settings coverage shared with Clio (15); historical refs confined to the v1.0.0 change-log entry (16); build-script hardening gap flagged (17).

Process: issue-tracked (18), sub-day Central timestamps (19), semver (20).

## Source material lifted inline

- `docs/10920-cws-listing-corrections-2026-05-27.md` — audit-corrected Long Description ("do not enumerate", not "cannot see browsing history"), corrected Privacy Policy URL (`aletheia.study/privacy.html`, not the stale `github.io`), and all permission justifications. The runbooks now hold this as canonical inline copy, so `10920` can be archived once its dashboard edits are applied.
- `docs/lld/done/10051-store-compliance.md` — store-listing copy provenance.
- `extensions/chrome/manifest.json` + `extensions/firefox/manifest.json` — ground-truth permissions, Extension ID key, gecko settings, `data_collection_permissions`.

## Decisions (operator-confirmed)

1. **"Open Source" → "Source-available"** in the listing Long Description: the license is PolyForm Noncommercial 1.0.0 (source-available, not OSI). Operator confirmed: code is published for privacy/security inspection, not under an open-source grant. Kept.
2. **Worktree + PR** delivery (operator's standing preference) rather than the repo CLAUDE.md's docs-on-main batch rule.

## Open items (follow-on)

- AZ#1363 dashboard: Aletheia's row → "done" with this PR link.
- `build_release.py` does not auto-clean stale `dist/*.zip` (flagged in both runbooks §4a) — candidate hardening issue.
- Screenshots: only `screenshots/cws/cws-image-1-epocha.png` exists; [#635](https://github.com/martymcenroe/Aletheia/issues/635) tracks producing 4 distinct CWS images; no AMO screenshots yet.
