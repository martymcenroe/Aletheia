# Implementation Report — #689

**Issue:** [#689](https://github.com/martymcenroe/Aletheia/issues/689) — 10907 §10b redundant lead-in
**Date:** 2026-05-29 Central
**Type:** Documentation (cosmetic, → v1.0.4)

## Change

`docs/runbooks/10907-runbook-amo-publish.md` §10b had two consecutive lead-in sentences ("…Aletheia declares:" followed by "The manifest declares `required: [...]` …") — a leftover from the v1.0.3 table rewrite (#686/#687). Merged them into one: "Firefox 140+ surfaces data-collection consent from the manifest's `data_collection_permissions`. Aletheia declares `required: ["authenticationInfo", "websiteContent"]` and `optional: []`. Each required value maps to one AMO disclosure:".

Bumped to v1.0.4 with a changelog row. Surfaced by the §0 `Audit 10907` self-audit.

## Verification

See test-report.md — §10b now has a single lead-in; the disclosure table is unchanged.
