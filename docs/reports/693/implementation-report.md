# Issue #693 — Implementation Report

## Issue summary

`npm ci` locally on Windows fails partway through because `pa11y` bundles its own `puppeteer`, and that puppeteer's postinstall tries to download `chrome-headless-shell`. The download is unreliable on Windows (anti-virus scanning, file locking on `%LOCALAPPDATA%\Cache\puppeteer\`). When the install fails partway, `node_modules` ends up half-installed and silently drifts from `package-lock.json` — most visibly with `@playwright/test` stuck at an older version. CI does not hit this because `.github/workflows/e2e-firefox.yml` and `.github/workflows/ci.yml` set `PUPPETEER_SKIP_DOWNLOAD: 'true'` as an env var on the `npm ci` step.

## Change set

### `.npmrc` (new file at repo root)

```
; pa11y bundles puppeteer, which auto-downloads chrome-headless-shell on install.
; That download is unreliable on Windows (AV / file-locking) and is not needed
; locally — Aletheia doesn't drive pa11y through that browser.
; CI sets PUPPETEER_SKIP_DOWNLOAD=true via workflow env; this is the local equivalent.
puppeteer_skip_download=true
```

The lowercase `puppeteer_skip_download=true` syntax in `.npmrc` causes npm to set `npm_config_puppeteer_skip_download=true` in the script environment, which puppeteer's postinstall reads as equivalent to `PUPPETEER_SKIP_DOWNLOAD=true`.

## Why this is the right fix

- Matches CI's env-var approach but expressed declaratively at the project level, so a local clone of the repo "just works" without anyone needing to remember the env var.
- Only affects install-time behavior of pa11y's nested puppeteer — does not change puppeteer behavior at runtime, does not change playwright behavior in any way.
- One line of config, trivially reversible.

## Out of scope

- The local playwright + Firefox `newPage` hang surfaced during the same investigation session is a separate problem. Minimal isolation tests (no test framework, no extension, no fixtures) show playwright + Firefox `newPage` hangs >30s on this Windows machine, while playwright + Chromium `newPage` completes in 40ms. This PR does not address that — to be tracked separately if pursued.
- This PR does not retroactively repair an already-stale `node_modules`. After it lands, anyone with a half-installed `node_modules` should run `rm -rf node_modules && npm ci` once to sync to lock.

## Related artifacts

- Issue #693 (this PR closes it).
- `.github/workflows/e2e-firefox.yml`, `.github/workflows/ci.yml` — where CI sets `PUPPETEER_SKIP_DOWNLOAD: 'true'`. Those workflow env vars stay in place; this PR is the local-equivalent expression.
- `package-lock.json` — unchanged by this PR. The version mismatch (locked `@playwright/test@1.60.0` vs locally-installed `1.58.2` before today's session) was a symptom of the failing install, not a separate lock drift.
