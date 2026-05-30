# 10907 — Firefox AMO Publishing (Aletheia)

> **Version:** 1.0.7
> **Last updated:** 2026-05-30 9:15:03 AM Central
> **Applies to:** Aletheia Firefox extension, every submission to Firefox Add-ons (addons.mozilla.org / "AMO")
> **Tracking issue:** [martymcenroe/Aletheia#678](https://github.com/martymcenroe/Aletheia/issues/678)
> **Versioning:** semver per [AssemblyZero#1362](https://github.com/martymcenroe/AssemblyZero/issues/1362) principle 20 — major.minor.patch. See §20 change log.
> **Standard:** built to the AZ#1362 runbook standard. That standard doc is not yet shipped (the issue holds the full spec); [Clio 30002](https://github.com/martymcenroe/Clio/blob/main/docs/runbooks/30002-chrome-web-store-publish.md) is the reference implementation (Chrome), and the companion [`10905-runbook-cws-publish.md`](./10905-runbook-cws-publish.md) is the Aletheia Chrome runbook.
> **Chrome / CWS:** Chrome Web Store publishing is in [`10905-runbook-cws-publish.md`](./10905-runbook-cws-publish.md). This runbook is Firefox AMO only.

## Aletheia AMO deployment state

Durable identifiers for the live Aletheia Firefox listing. Agent commands below (§0) reference these.

| Item | Value |
|---|---|
| Add-on slug | `aletheia-ai` |
| Gecko (add-on) ID | `extension@aletheia.study` |
| Listing URL | `https://addons.mozilla.org/en-US/firefox/addon/aletheia-ai/` |
| Developer Hub | `https://addons.mozilla.org/developers/` |
| Manage Versions | `https://addons.mozilla.org/developers/addon/aletheia-ai/versions/` |
| Account | `cto@thrivetech.ai` (forwards to `cto.thrivetech.ai@gmail.com`) |
| Current published version | `1.1.1` (live on AMO; updated 2026-03-06). `1.1.2` is built + release-noted but never went live — it is the pending upload. |
| Minimum Firefox | `140.0` desktop / `142.0` Android (`browser_specific_settings.gecko`) |
| License (must be) | **PolyForm Noncommercial 1.0.0** — NOT MIT (recurring error; see §11) |

Update this table on rebrand, ID change, slug change, **and on each publish** — §15a refreshes the Current published version after AMO approves. **Do not change the slug** once published — it's baked into the listing URL.

## Throughout this runbook

- **Operator** — the human running the publishing process at the AMO Developer Hub. Can perform any step.
- **Agent** — a Claude Code session with this repo's working tree available. Performs any step marked agent. Invoked by the canonical phrases in §0.

## How to verify you have the latest copy

This runbook lives at `docs/runbooks/10907-runbook-amo-publish.md` in [martymcenroe/Aletheia](https://github.com/martymcenroe/Aletheia). The **Version** and **Last updated** lines identify your revision.

1. Note the version on your copy.
2. Say `Run amo pre-flight` or `Audit 10907` (§0) — the agent reports the current `main` HEAD runbook version line.
3. If your copy differs, re-print before continuing.

## 0. Invoke the agent (canonical phrases)

The operator types one of these to trigger the matching action. The agent recognizes minor punctuation variation and asks for clarification on ambiguity. Phrases are **prefixed `amo`** to disambiguate from the Chrome runbook ([10905](./10905-runbook-cws-publish.md)) — `Run amo build` is Firefox, `Run cws build` is Chrome.

| To make the agent... | Operator says |
|---|---|
| Audit this runbook for gaps / drift | `Audit 10907` |
| Run §3a pre-flight + §4 build, hand back the Firefox ZIP path | `Run amo pre-flight` |
| Run §3a only (no build) and report findings | `Run amo §3a` |
| Run §4 build + verify (pre-flight already passed) | `Run amo build` |
| Sign + upload via the `web-ext` API path (§17, optional) | `Run amo sign` |
| Comment the submission timestamp on the release issue (current Central time, or `at YYYY-MM-DD HH:MM`) | `Submitted amo` |
| After AMO approves: run §15a — tag the commit, update release notes, comment + close the release issue | `Run amo post-publish` (listing URL defaults to the deployment-state block) |

The agent's reply includes (a) a one-line confirmation, (b) findings/follow-ups, (c) the current `main` HEAD runbook version line.

## 1. Where to start (reading paths)

| Situation | Read sections |
|-----------|--------------|
| **Path A — First AMO submission** (add-on not yet in the Developer Hub) | §2 → §3 → §4 → §5 → §7 → §8 → §9 → §10 → §11 → §12 → §13 → §14 → §15 |
| **Path B — Subsequent update** (Aletheia already in My Add-ons — the normal case; for the live vs pending version, see the deployment-state block) | §2 → §3 → §4 → §6 → (review §7–§13 if listing copy changed) → §13 source check → §14 → §15 |
| **Path C — New machine or new AMO account** | Stop. Confirm the `cto@thrivetech.ai` AMO login (2FA) and, if automating, regenerate API credentials (§17). Then return as Path A or Path B. |

§16 Version bump, §17 API/`web-ext` path, §18 Troubleshooting, §19 Related documents, §20 Change log are reference material.

## 2. Account check (every submission)

1. Sign in to `https://addons.mozilla.org/developers/` as `cto@thrivetech.ai` (mail forwards to `cto.thrivetech.ai@gmail.com`); complete 2FA.
2. Confirm the **My Add-ons** list shows **Aletheia** at slug `aletheia-ai`.
3. If a different Mozilla identity is active, sign out and back in as `cto@thrivetech.ai`.

The AMO dashboard access pattern is likely the same Chrome profile used for CWS (memory `user-cws-dashboard-access`) but is **not confirmed** — check that profile's bookmarks first.

## 3. Pre-flight checklist

Split by responsibility, items numbered for "§3a.N" / "§3b.N" reference.

### 3a. Agent does (in the repo, before producing the ZIP)

1. `extensions/firefox/manifest.json` has the new `version`, monotonic from the last published AMO version (see the deployment-state block for the current live and pending versions), and **matching `extensions/chrome/manifest.json`** (`build_release.py` enforces parity on `name`, `version`, `description`, `icons`).
2. Firefox `permissions` is exactly `activeTab`, `tabs`, `scripting`, `contextMenus`, `storage` — **five, not seven**. Firefox does NOT request `identity` (it uses a tabs-based OAuth flow, not `chrome.identity`) or `notifications`. `host_permissions` is exactly `["https://api.aletheia.study/*"]`. Every permission has a §12 paste-block.
3. `browser_specific_settings.gecko` is intact: `id` = `extension@aletheia.study`, `strict_min_version` = `140.0`, `gecko_android.strict_min_version` = `142.0`. The `data_collection_permissions` block declares `required: ["authenticationInfo", "websiteContent"]`, `optional: []` — this must match the §10 data-collection disclosure.
4. No hardcoded test URLs or dev flags; all API traffic goes to `https://api.aletheia.study/*`.
5. All tests pass: `poetry run pytest` + `npx playwright test`. `web-ext lint` is clean — `build_release.py` Step 3 runs it automatically and fails on errors (warnings are reported but non-blocking).
6. Release notes file `docs/releases/firefox-vX.Y.Z.md` written before the §4 build — see §18.
7. Listing screenshots exist at `screenshots/amo/amo-image-N-<slug>.png`. **Current state: directory does not exist; it will be created on first AMO screenshot upload.** AMO accepts up to 10 screenshots with no strict dimension requirement, but use high-resolution images; produce them with [`10906-runbook-cws-image-pad.md`](./10906-runbook-cws-image-pad.md) (it has an AMO output convention and `--width/--height` flags). The CWS 1280×800 images can be reused.
8. Agent reports the current `main` HEAD SHA and this runbook's `> **Version:**` line.

### 3b. Operator does

1. §2 Account check passes.
2. The version isn't already uploaded — check Manage Versions history. (AMO refuses a duplicate version number.)
3. Approve the agent's screenshot set, or flag privacy/embarrassing content.
4. Review §7–§13 paste-blocks for changes — canonical source, no second document. **The live AMO listing may carry the old false "cannot see your browsing history" wording** (the 2026-05-26 audit flagged it on CWS; verify AMO too per `docs/10920`). Where the listing disagrees with §7/§10/§11/§12, overwrite it.
5. Operator's printed-copy version matches §3a.8.

## 4. Build & verify the ZIP (agent does this)

**Agent runs §4a + §4b. Operator receives the ZIP path and uploads it at §5/§6 (or the agent signs via §17).**

**CRITICAL:** use `build_release.py` (Python `ZipFile`, forward slashes) or `zip` from MSYS2 / Git Bash — **never** PowerShell `Compress-Archive` (AMO rejects backslash separators). **CRITICAL:** `extensions/firefox/` must contain only extension files — no `docs/`, session logs, `tests/`. (A cleanup agent once wrote `extensions/firefox/docs/session-logs/` and it got packaged into the ZIP — see memory.)

### 4a. Build (agent does this)

```bash
cd /c/Users/mcwiz/Projects/Aletheia
# Clear stale artifacts safely — never glob-delete. List first, inspect, then delete by name:
ls -1 dist/aletheia-firefox-*.zip 2>/dev/null || echo "(none present)"
#   If an older-version zip is listed, delete that file BY NAME (e.g. rm dist/aletheia-firefox-v1.1.1.zip).
#   If the list shows anything you do not recognize, STOP and investigate before deleting.
poetry run python tools/build_release.py
```

Produces `dist/aletheia-firefox-v{version}.zip` (and the Chrome ZIP). `build_release.py` runs `web-ext lint` on the Firefox source as Step 3.

> **Known hardening gap (principle 17):** `build_release.py` does not auto-clean stale `dist/*.zip`. Do the list-inspect-delete-by-name step above until that is fixed (same gap noted in [10905](./10905-runbook-cws-publish.md) §4a; follow-up: have the script remove prior Aletheia zips by exact name, never a glob).

Fallback if the build tool is broken:

```bash
cd /c/Users/mcwiz/Projects/Aletheia/extensions/firefox
zip -r ../../dist/aletheia-firefox-vX.Y.Z.zip . -x '.*' -x '*/.*' -x 'node_modules/*'
```

### 4b. Verify (agent does this)

```bash
cd /c/Users/mcwiz/Projects/Aletheia
unzip -l dist/aletheia-firefox-vX.Y.Z.zip
```

Confirm:

- Forward slashes in all paths.
- `manifest.json` at the archive root, with `manifest_version: 3` and `browser_specific_settings.gecko.id` present.
- `icons/` with four icons: 16, 32, 48, 128.
- Expected files at root: `manifest.json` plus the 9 source files `service-worker.js`, `popup.html`, `popup.js`, `popup.css`, `overlay.js`, `content-check.js`, `content-safety.js`, `article-extractor.js`, `auth.js` (10 root files total + 4 icons = 14 entries).
- No unexpected files.

Sanity-check the version and gecko ID inside the ZIP:

```bash
unzip -p dist/aletheia-firefox-vX.Y.Z.zip manifest.json | grep -E '"version"|"id"|strict_min_version'
```

The agent hands the operator the path to `dist/aletheia-firefox-vX.Y.Z.zip`.

## 5. First submission upload (Path A — add-on not yet in the Developer Hub)

Historical — Aletheia is already published; this applies only on a from-scratch resubmission.

1. Developer Hub → **Submit a New Add-on**.
2. Distribution channel: **On this site** (listed on AMO). (The other option, "On your own," produces a self-distributed signed XPI — not what we use.)
3. Upload `dist/aletheia-firefox-vX.Y.Z.zip`. Automated validation runs (seconds).
4. Answer the source-code question (§13), then fill listing metadata (§7–§12) and submit.

## 6. Subsequent update upload (Path B — Aletheia already listed)

The normal case.

1. Developer Hub → **My Add-ons** → **Aletheia** → **Manage** → left nav **Manage Status & Versions** (or go straight to the Manage Versions URL in the deployment-state block).
2. Click **Upload a New Version**.
3. Choose `dist/aletheia-firefox-vX.Y.Z.zip` and upload. Automated validation runs.
4. Answer the source-code question (§13). On success the new version enters review; the previously-approved version stays live until this one is approved.

## 7. Listing details

Paste-ready; copy into the matching AMO field. AMO's listing form differs from CWS — fields below are in AMO order.

### 7a. Name

```
Aletheia
```

### 7b. Add-on slug (one-time — do not change)

```
aletheia-ai
```

Baked into the listing URL (`…/addon/aletheia-ai/`). Changing it breaks every existing link. Set once; never edit.

### 7c. Summary

*AMO summary limit: 250 characters. Same copy as the CWS short description (129 characters / 131 bytes UTF-8 — the em-dash is 3 bytes).*

```
Instant AI analysis for selected text. Understand context, detect nuance, and verify facts—while maintaining strict data privacy.
```

### 7d. Description

*AMO listing description. Use the audit-corrected copy — the "Privacy by Design" line MUST read "we do not enumerate…", never "we cannot see your browsing history."*

```
Aletheia: The Privacy-First Context Analyzer

Stop guessing what you are reading. Aletheia brings the power of Large Language Models (LLMs) directly to your browser selection, helping you understand complex terms, detect subtext, and verify claims—without sacrificing your privacy.

How it Works:

1. Select: Highlight any text on any webpage.
2. Click: Right-click and choose "Explain with AI".
3. Understand: Aletheia analyzes the text within its surrounding paragraph to give you a context-aware explanation, not just a dictionary definition.

Why Aletheia?

- Context Matters: Most tools only look at the word. Aletheia looks at the sentence and paragraph to understand nuance, sarcasm, and specific usage.
- Privacy by Design: We do not enumerate, retain, transmit, or analyze data from tabs other than the one you explicitly invoke Aletheia on. We only see the specific text you explicitly select and submit.
- Safe & Secure: Built-in guardrails filter out harmful content before it even reaches the AI.

Source-available and transparent. Your data stays yours.
```

> **Maintainer note:** same "Open Source" → "Source-available" correction as the Chrome runbook §7c, for the same PolyForm-Noncommercial reason.

### 7e. Categories

AMO categories differ from CWS. Aletheia's current listing uses **Other**. Confirm against the live listing before changing. Rationale (preserved):
- `Other` (current) — safe catch-all; what the listing ships with today.
- `Privacy & Security` (candidate) — defensible given the privacy-first framing; consider if deliberately re-categorizing.
- `Language Support` (rejected) — Aletheia analyzes meaning in context, it is not a translation/locale tool.

A category change is a deliberate decision, not a routine-update step.

## 8. Graphic assets

### 8a. Add-on icon

AMO uses the icon from the manifest (`icons.128` → `extensions/firefox/icons/icon128.png`). No separate upload needed unless you want a distinct listing icon.

### 8b. Screenshots

Upload from `screenshots/amo/amo-image-N-<slug>.png` (none exist yet — see §3a.7; produce via [10906](./10906-runbook-cws-image-pad.md)). AMO shows them on the listing page; high-resolution preferred, no hard dimension limit.

## 9. Additional listing fields

### 9a. Homepage URL

```
https://aletheia.study
```

### 9b. Support site / email

```
https://github.com/martymcenroe/Aletheia/issues
```

```
cto@thrivetech.ai
```

### 9c. Tags (optional)

Leave as-is for a routine update. Tags aid discovery; not load-bearing.

## 10. Privacy & data collection

### 10a. Privacy Policy URL

```
https://aletheia.study/privacy.html
```

Confirm it's this, **not** the stale `https://martymcenroe.github.io/Aletheia/` (per `docs/10920-cws-listing-corrections-2026-05-27.md`). Verify in private browsing that the listing's policy link resolves and shows the current policy.

### 10b. Data collection disclosure

Firefox 140+ surfaces data-collection consent from the manifest's `data_collection_permissions`. Aletheia declares `required: ["authenticationInfo", "websiteContent"]` and `optional: []`. Each required value maps to one AMO disclosure:

| `required` array value | AMO disclosure |
|---|---|
| `authenticationInfo` | **Authentication information** — the LinkedIn OAuth token. Stored locally, cleared on browser close. |
| `websiteContent` | **Website content** — the selected text + surrounding context, on user-initiated analysis only. |
| (`optional: []`) | No additional data types. |

The AMO "Manage Data Collection" / data-disclosure form must match this exactly. No "cannot see browsing history" claims; no data type beyond authentication info + website content.

### 10c. Per-permission notes

If AMO requests free-text permission notes, reuse the §12 justifications (the five Firefox permissions + the host).

## 11. License

**CRITICAL — verify every submission.** The license is **PolyForm Noncommercial 1.0.0**, matching the repo [LICENSE](../../LICENSE). It has been wrongly set to **MIT** on AMO before (memory: "AMO listing was incorrectly set to MIT").

AMO's license dropdown does **not** include PolyForm. Choose **"Custom License"** and provide:

- License name: `PolyForm Noncommercial 1.0.0`
- License URL: `https://polyformproject.org/licenses/noncommercial/1.0.0/`
- (Or paste the full text of the repo `LICENSE` file into the custom-license text box.)

Rationale: MIT would (a) misrepresent the project's actual license and (b) silently waive the noncommercial restriction PolyForm exists to assert. Picking a permissive default from the dropdown is the exact mistake to avoid.

## 12. Permission justifications (Firefox — five permissions + host)

Firefox requests **five** permissions (no `identity`, no `notifications`). Paste-ready:

### 12a. `activeTab`

```
Used to read the text of the currently active tab only when the user explicitly invokes Aletheia (right-click "Explain with AI"). The extension does not access any other tab.
```

### 12b. `tabs`

```
Used to detect page navigation for overlay lifecycle management, to inject the content script on the active tab, and — on Firefox specifically — to detect the OAuth callback during the tabs-based LinkedIn sign-in flow. The extension does NOT enumerate or read content from any tab other than the one the user explicitly invokes Aletheia on.
```

### 12c. `scripting`

```
Used to execute the content script (reading the selection's surrounding context) on the active tab during "Explain with AI", and as a recovery path to re-inject the content script into a tab opened before the extension was loaded. Only the active tab, only the extension's own bundled scripts.
```

### 12d. `contextMenus`

```
Provides the primary trigger: the right-click "Explain with AI" menu item on selected text.
```

### 12e. `storage`

```
Saves user preferences, the authentication token, and the domain allowlist locally on the user's device. Nothing is stored on a remote server.
```

### 12f. Host permission: `https://api.aletheia.study/*`

```
The single remote endpoint the extension communicates with: the selected text and its surrounding context are sent here for analysis and the result is returned. No other network requests, no third-party analytics or tracking host.
```

> **Why fewer than Chrome:** the Firefox build authenticates with a tabs-based OAuth flow rather than `chrome.identity`, so it needs neither the `identity` permission nor `notifications`. If AMO shows only these five, that is correct — do not copy the Chrome runbook's seven.

## 13. Source-code submission

AMO requires a source-code upload **only if** the add-on contains minified, concatenated, obfuscated, or transpiled code that the reviewer cannot read directly. **Aletheia ships plain, readable JavaScript with no build/minify step** — the ZIP files *are* the source.

- When AMO asks "Do you use tools that make your code hard to read?" → answer **No**.
- Provide the repository as a reviewer reference: `https://github.com/martymcenroe/Aletheia`.
- If AMO's validator ever flags a specific file as needing source (e.g. a future bundling step), upload a source ZIP plus build instructions (`poetry run python tools/build_release.py`).

## 14. Submit for review

1. Operator clicks **Submit Version** (Path B) or completes the new-add-on flow (Path A).
2. AMO automated validation is instant; human review for a listed update typically takes hours to a few days (a minor update is usually fast; a first submission or a permission change can take longer).
3. Operator says `Submitted amo`. The agent comments the current Central-time submission timestamp on the release issue.

## 15. Post-publish

After AMO approves and emails the operator, the operator says `Run amo post-publish`.

### 15a. Agent does (`Run amo post-publish`)

1. Verify the Firefox install link in `docs/index.html` / `docs/demos.html` points at the AMO listing URL; fix via the docs-on-main edit flow if stale.
2. Tag the released commit: `git tag firefox-vX.Y.Z-published && git push origin firefox-vX.Y.Z-published`.
3. Comment on the release issue with the approval date and the listing URL; close the issue.
4. Update `docs/releases/firefox-vX.Y.Z.md` — fill `Submission date:` and add an `Approval date:` line.
5. Update this runbook's deployment-state **Current published version** row to the just-approved version (e.g. `1.1.2` once it is live), so the live/pending pin does not go stale.

### 15b. Operator does (smoke test)

1. Install/update Aletheia in Firefox from the AMO listing.
2. **Core flow:** select text → right-click → "Explain with AI" → overlay appears with context-aware analysis.
3. **Auth flow:** click the extension icon → "Log in with LinkedIn" → the **tabs-based** OAuth flow completes (a callback tab opens and closes; the `response.pending` state is handled) → popup shows logged-in state.
4. Verify the version in `about:addons`.

### 15c. If a smoke test fails

Do **not** delist. File a `launch-blocker` issue, reproduce in Firefox dev mode (`about:debugging` → Load Temporary Add-on), ship a patch version. A patch must go through AMO review again, so don't pull the working version.

## 16. Version bump procedure

Shared with the Chrome runbook — Aletheia ships both browsers from one version line. See [10905](./10905-runbook-cws-publish.md) §16. In short: bump **both** `extensions/chrome/manifest.json` and `extensions/firefox/manifest.json` to the same `X.Y.Z` (the Chrome manifest is `build_release.py`'s source of truth; parity is enforced), write both release-notes files, commit `chore: bump extension versions to X.Y.Z (Closes #N)`, merge to `main`, then §4 → §6. Put `Closes #N` in the **PR body** too — pr-sentinel validates the body, not the commit message.

## 17. Optional: API-key / `web-ext` signing path

CWS uploads are dashboard-only; AMO additionally supports programmatic upload/signing via API credentials and Mozilla's `web-ext` tool. This is **optional** — the manual §6 dashboard upload is Aletheia's primary path. Use this only when automating.

### 17a. Generate API credentials (operator, one-time)

1. Operator opens `https://addons.mozilla.org/developers/addon/api/key/` while signed in as `cto@thrivetech.ai`.
2. Generate credentials → AMO shows a **JWT issuer** (e.g. `user:12345:67`) and a **JWT secret** (shown once).

### 17b. Secret handling (mandatory — the secret is a credential)

The JWT secret is a long-lived credential that can submit/sign add-ons under this account. Treat it per the root CLAUDE.md secret-handling hygiene:

- **The agent NEVER prints, echoes, logs, or commits the secret**, and never reads it back from a file into chat.
- Operator stores it **outside the repo** as environment variables (`WEB_EXT_API_KEY` = issuer, `WEB_EXT_API_SECRET` = secret) — not in a OneDrive-synced path, not in shell history (use a leading space or a `.env` the agent never cats).
- Pass via **environment**, never as a command-line argument (argv is readable by same-user processes).
- If the secret is ever exposed, the operator revokes it at the same AMO page and regenerates.

### 17c. Sign + upload (agent, `Run amo sign`)

With the env vars exported by the operator in the same shell:

```bash
cd /c/Users/mcwiz/Projects/Aletheia
npx web-ext sign \
  --channel listed \
  --source-dir extensions/firefox \
  --artifacts-dir dist
```

`web-ext` reads `WEB_EXT_API_KEY` and `WEB_EXT_API_SECRET` from the environment directly, so the secret is **never passed on the command line** — do NOT add `--api-key`/`--api-secret` flags, which would put it in argv (the leak §17b forbids). `--channel listed` submits to AMO and queues the public-listing review (equivalent to §6 upload); `--channel unlisted` would instead return a self-distributed signed XPI — not what we publish. The agent confirms `$WEB_EXT_API_KEY`/`$WEB_EXT_API_SECRET` are present in the environment **without printing their values**, and refuses to run if they're unset.

## 18. Troubleshooting

| Problem | Diagnosis | Action |
|---------|-----------|--------|
| AMO rejects ZIP with backslash-path error | Built with PowerShell `Compress-Archive` | Rebuild with `build_release.py` or `zip` (MSYS2 / Git Bash) |
| "Version already exists" | Forgot to bump both manifests | Bump both, rebuild (parity is enforced) |
| License shows MIT on the listing | Recurring AMO default-picker error | Set to Custom License → PolyForm Noncommercial 1.0.0 (§11) |
| AMO asks for source code | Validator flagged code as hard-to-read | Aletheia is not minified — answer No and link the repo; if a specific file is flagged, upload source + build steps (§13) |
| Data-collection disclosure mismatch | AMO form drifted from the manifest | Make the AMO disclosure match `data_collection_permissions` (auth info + website content only) (§10b) |
| `web-ext lint` errors on build | A manifest or file issue | Read the lint output; `build_release.py` fails the build on errors |
| `npx playwright test` hangs on Firefox | Windows sandbox crashes the renderer (Juggler `remoteTab is null`) | Workaround applied in `playwright.config.js` (`MOZ_DISABLE_CONTENT_SANDBOX=1`). If running standalone reproduction scripts, export that env var first. |
| Gecko ID mismatch / "add-on ID changed" | `browser_specific_settings.gecko.id` edited | Restore `extension@aletheia.study` — changing it creates a *new* add-on, orphaning the listing |
| `strict_min_version` rejected | Set below a feature's availability | Keep `140.0` desktop / `142.0` Android unless a feature requires higher |
| Listing still shows "cannot see your browsing history" | Pre-audit text | Overwrite §7d Description; verify in private browsing (per `docs/10920`) |

## 19. Related documents

- [`10905-runbook-cws-publish.md`](./10905-runbook-cws-publish.md) — the parallel Chrome Web Store publishing runbook (shared §16 version bump).
- [`10906-runbook-cws-image-pad.md`](./10906-runbook-cws-image-pad.md) — produce listing screenshots (`screenshots/amo/…`) without cropping.
- `docs/releases/` — per-version release notes (`firefox-vX.Y.Z.md`).
- `docs/lld/done/10051-store-compliance.md` — original store-listing text (provenance; canonical copy now inline here).
- `docs/privacy.html` — published privacy policy (`https://aletheia.study/privacy.html`).
- `docs/legal/eula.html` — End User License Agreement.
- `extensions/firefox/manifest.json` — ground-truth permissions, gecko settings, and `data_collection_permissions`.
- Memory `user-cws-dashboard-access` — login pattern (CWS-confirmed; AMO likely shares the profile).

## 20. Change log

Semver per AZ#1362 principle 20.

| Version | Date | Change |
|---------|------|--------|
| 1.0.7 | 2026-05-30 9:15:03 AM Central | Patch from `Audit 10907`: §3a.7 now states the `screenshots/amo/` directory does not exist (was "none exist" which read as "directory exists, no files"). §7c notes the byte count alongside the visible character count (129 / 131) so a naive `wc -c` reproducibility check does not surface a false discrepancy from the em-dash being 3 UTF-8 bytes (Closes #713). |
| 1.0.6 | 2026-05-30 12:15:15 AM Central | Patch: documented the Windows sandbox Playwright hang in §18 Troubleshooting. The `MOZ_DISABLE_CONTENT_SANDBOX=1` workaround is now permanently applied in `playwright.config.js`. |
| 1.0.5 | 2026-05-29 11:26:54 AM Central | Patch: removed the "no live debug-tier console calls" clause from §3a.4. The §3a.4 item now reads only the kept "no hardcoded test URLs or dev flags" portion. The console-call ban was authored in this runbook's 2026-05-28 v1.0.0 split with no upstream source — not in `docs/privacy.html`, not in any LLD, not in `docs/safety.html`/`docs/threat-model.html`. Local browser-console output never leaves the user's machine, so the rule had no privacy-policy grounding. Removing it eliminates the framing that allowed an agent in a later session to mis-label two existing `service-worker.js` `console.log` calls as "privacy-relevant" and present three "disposition" options to the operator. The cross-reference to the Chrome runbook's deleted §3a.3 went with the deleted clause (Closes #691). |
| 1.0.4 | 2026-05-29 12:57:37 AM Central | Patch: removed a redundant lead-in in §10b — a dangling "Aletheia declares:" the v1.0.3 table rewrite left in front of the new sentence; merged the two into one. Found by the §0 `Audit 10907` self-audit (Closes #689). |
| 1.0.3 | 2026-05-29 12:41:37 AM Central | Patch: applied the §0 `Audit 10907` findings. §17c no longer passes the API secret on the command line — `web-ext` reads `WEB_EXT_API_KEY`/`WEB_EXT_API_SECRET` from the environment, keeping the secret out of argv per §17b (Closes #686). §15a now refreshes the deployment-state Current published version, the update trigger includes "on each publish," and §1 Path B / §3a.1 reference the deployment-state block as the single source so the live/pending version is not duplicated three ways (Closes #687). Cosmetics: §10b shows the single `data_collection_permissions.required` array, §16 notes `Closes #N` belongs in the PR body, §4b clarifies the 10-root-file count. |
| 1.0.2 | 2026-05-29 12:18:55 AM Central | Patch: corrected timestamps that were UTC mislabeled as Central — the v1.0.0/v1.0.1 dates and the header were produced with `TZ='America/Chicago' date`, which Git Bash returns as UTC. Re-derived to true Central (CDT, UTC-5) with plain `date` (Closes #684). |
| 1.0.1 | 2026-05-28 08:05:10 PM Central | Patch: corrected the deployment-state, §1 Path B, and §3a.1 to state the live AMO version is `1.1.1` (1.1.2 was release-noted but never published — it is the pending upload) (Closes #682); replaced the `rm -f <glob>` artifact-clean step in §4a with a list → inspect → delete-by-name procedure (Closes #681). |
| 1.0.0 | 2026-05-28 06:49:42 PM Central | New runbook, built to the AZ#1362 standard, split out of `10905-runbook-extension-store-publish.md` (which became the Chrome-only [10905](./10905-runbook-cws-publish.md)). Firefox-AMO-specific coverage the Chrome runbook lacks: §10b manifest `data_collection_permissions` disclosure (authenticationInfo + websiteContent), §11 PolyForm-Noncommercial custom-license trap (was wrongly MIT), §12 five-permission set (no `identity`/`notifications`; tabs-based OAuth), §13 source-code-submission question, §17 AMO API-key + `web-ext sign` path with secret-handling discipline. Lifted the audit-corrected Description, Privacy Policy URL, and permission justifications from `docs/10920-cws-listing-corrections-2026-05-27.md` and `docs/lld/done/10051-store-compliance.md`. Closes #678 (with [10905](./10905-runbook-cws-publish.md)). |
