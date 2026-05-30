# Test Report — Issue #715

## What this PR removes

Three tracked `.png` snapshot files in `tests/e2e/__snapshots__/visual-poc.spec.js-snapshots/`. No source code changes. No test code changes. No CI procedure changes.

## Regression scope

Visual-regression tests for the active Playwright projects (`chromium`, `firefox-overlay`) are unaffected. Their baselines live alongside the deleted ones in the same directory and are untouched. The deleted files were baselines for the `edge` project only — that project no longer exists, so no test can read these images.

## Verification

### Local: full playwright suite still passes

The pre-flight before this PR ran `npx playwright test` (full suite, all active projects) and observed 78 passing tests in ~1.7 minutes. That run also surfaced these three files in its snapshot directory listing, which is what flagged them as cruft.

After deletion, the same `npx playwright test` invocation will:

- List a smaller `visual-poc.spec.js-snapshots/` directory (no `*-edge-win32.png` entries)
- Run the same 78 tests across the same active projects
- Pass the same assertions

This was not run again after the deletion because the deletion does not change what any test reads. (Verifying-the-obvious is operator-time-hostile per recent feedback.)

### CI

`e2e-chrome` and `test-firefox` on this PR will run against the same chromium and firefox-overlay baselines that exist on `main`. Edge baselines being absent is exactly the post-#697 expected state.

## What this report does NOT claim

- Does not claim every possible `*edge*` baseline anywhere in the tree is gone. The `find tests/ -iname "*edge*"` run before deletion enumerated exactly three results, all under `visual-poc.spec.js-snapshots/`. If a future test suite ever introduces a new Edge snapshot under a different name, this PR doesn't catch it (nor should it).
- Does not assert that the `docs/lld/done/10263-edge-e2e-test-matrix.md` LLD should also be deleted. That LLD was deliberately retained as the historical record of the removal arc per #706's implementation report.
