# Implementation Report — #686, #687

**Issues:** [#686](https://github.com/martymcenroe/Aletheia/issues/686) (§17c secret-in-argv), [#687](https://github.com/martymcenroe/Aletheia/issues/687) (post-publish version drift)
**Date:** 2026-05-29 Central
**Type:** Documentation — applies the `Audit 10907` (§0) findings to `10907-runbook-amo-publish.md` (→ v1.0.3)

## #686 — secret no longer reaches argv

§17c previously ran `npx web-ext sign … --api-key "$WEB_EXT_API_KEY" --api-secret "$WEB_EXT_API_SECRET"`, expanding the secret onto the command line — contradicting §17b ("never as a command-line argument"). Removed both flags; `web-ext` reads `WEB_EXT_API_KEY`/`WEB_EXT_API_SECRET` from the environment. The note now states the secret is never passed on the command line and warns against re-adding the flags.

## #687 — pinned version no longer drifts

The live AMO version was stated in three places (deployment-state, §1 Path B, §3a.1) and nothing refreshed it on publish.
- Added §15a step 5: update the deployment-state **Current published version** to the just-approved version.
- Update trigger now includes "and on each publish (§15a)."
- §1 Path B and §3a.1 now reference the deployment-state block instead of restating the version — single source of truth, one edit per publish.

## Cosmetics (folded in)

- §10b: replaced the two ellipsis rows with the single `data_collection_permissions.required: ["authenticationInfo", "websiteContent"]` array, one row per value.
- §16: commit example uses `Closes #N` and notes `Closes #N` must also be in the PR body (pr-sentinel checks the body).
- §4b: clarified the "10 root files" count (manifest.json + 9 source files).

## Verification

See test-report.md. The §17c command block has no `--api-key`/`--api-secret` lines; version is 1.0.3; §15a step 5 present; no ellipsis rows remain.
