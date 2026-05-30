# Test Report — Issue #705

## What this PR changes

Two source files, neither executable code:

- `playwright.config.js` — removes a configuration block (the `edge` project). Other Playwright projects (`chromium`, `firefox-overlay`) are unaffected.
- `docs/lld/done/10263-edge-e2e-test-matrix.md` — adds a documentation notice. No executable change.

## Verification

### Static — `playwright.config.js` parses

```bash
cd /c/Users/mcwiz/Projects/Aletheia
node -e "require('./playwright.config.js'); console.log('parsed OK')"
```

Expected: `parsed OK`. Pre-commit ESLint will also run against the file; any syntax regression surfaces there.

### Dynamic — `chromium` and `firefox-overlay` projects still discoverable

```bash
cd /c/Users/mcwiz/Projects/Aletheia
npx playwright test --list --project=chromium | head -3
npx playwright test --list --project=firefox-overlay | head -3
```

Expected: both list tests. Negative check:

```bash
npx playwright test --list --project=edge 2>&1 | grep -i "no project"
```

Expected: Playwright reports the `edge` project is not in the config (because it no longer is).

### No CI procedure changes

`.github/workflows/*.yml` are not touched by this PR. The companion deletion of `e2e-edge.yml` already landed in #698 and is at HEAD of `main` (commit `cdfb828`). This PR neither adds nor modifies any file under `.github/workflows/`.

## Regression scope

The `edge` Playwright project was the only consumer of `tests/e2e/edge/` (which does not exist) and the only target of the deleted CI procedure (gone since #698). No other config block, test spec, doc, or CI procedure references the `edge` project. Removing it cannot regress code that does not call into it.

## What this report does NOT claim

- Does not claim the LLD's design is "wrong" — it was correct for its 2026-01-10 scope. The supersede notice records that the decision was reversed, not that the original design was defective.
- Does not assert anything about future browser support. If Aletheia ever ships to Edge Add-ons, the matrix can be rebuilt; this PR just clears the dead-config state in the meantime.
