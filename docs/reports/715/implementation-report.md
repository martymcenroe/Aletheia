# Implementation Report — Issue #715

## Scope

Remove three tracked snapshot files left over from the `edge` Playwright project that was dropped in #706. Pure cruft cleanup; no semantic change.

## Changes

Three `git rm`s, each by exact name, one per command (per fleet hygiene rule: no `-f`, no glob):

```
git rm tests/e2e/__snapshots__/visual-poc.spec.js-snapshots/page-with-extension-edge-win32.png
git rm tests/e2e/__snapshots__/visual-poc.spec.js-snapshots/test-fixture-fullpage-edge-win32.png
git rm tests/e2e/__snapshots__/visual-poc.spec.js-snapshots/test-fixture-header-edge-win32.png
```

These were visual-regression baselines for the `edge` Playwright project. After:

- #698 deleted `.github/workflows/e2e-edge.yml` — the CI job that would have used them is gone
- #706 dropped the `edge` project block from `playwright.config.js` — `npx playwright test --project=edge` now errors with "project not found"
- #706 added a SUPERSEDED notice to `docs/lld/done/10263-edge-e2e-test-matrix.md` — the design doc points operators away from this matrix

Nothing references or generates these files. They are unreachable cruft.

## Not touched

- `docs/lld/done/10263-edge-e2e-test-matrix.md` — preserved as historical record of the removal arc per #706 implementation report.
- `Aletheia.wiki/FAQ.md:20` — the canonical "Edge and other Chromium-based browsers may work but are not officially supported" claim. Out of scope; not in this repo's tracked tree anyway.
- Other `visual-poc.spec.js-snapshots/*.png` baselines for the active `chromium` and `firefox-overlay` projects — untouched, still in use.

## Verification

Pre-merge, in the worktree:

```bash
git ls-files tests/e2e/__snapshots__/visual-poc.spec.js-snapshots/ | grep -i edge
# Expected: empty (grep exits 1)
```

Confirmed: empty. Three `D` entries in `git status`, no other changes.

Post-merge, in the main worktree after FF:

```bash
ls tests/e2e/__snapshots__/visual-poc.spec.js-snapshots/ | grep -i edge
# Expected: empty
```

## Out of scope

- Snapshots for the `edge` project on other OS/platform combinations (`-linux.png`, etc.) — verified absent locally; not a separate cleanup. The three deleted files are the complete set.
- The pre-existing snapshots' Chromium and Firefox baselines are unchanged — visual-regression tests for the active projects continue to operate against the same images.
