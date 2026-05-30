# 10907 — Firefox AMO Publishing (Aletheia)

> **Version:** 2.0.0
> **Last updated:** 2026-05-30 10:49:19 AM Central
> **Applies to:** Aletheia Firefox extension submissions to AMO (`addons.mozilla.org`)

## Aletheia AMO deployment state

| Item | Value |
|---|---|
| Add-on slug | `aletheia-ai` |
| Gecko (add-on) ID | `extension@aletheia.study` |
| Listing URL (public) | `https://addons.mozilla.org/en-US/firefox/addon/aletheia-ai/` |
| Developer Hub | `https://addons.mozilla.org/developers/` |
| Manage Versions URL | `https://addons.mozilla.org/developers/addon/aletheia-ai/versions/` |
| Account | `cto@thrivetech.ai` (forwards to `cto.thrivetech.ai@gmail.com`) |
| Current published version | `1.1.1` (live since 2026-03-06) |
| Pending upload | `1.1.2` (built, release-noted, never published) |
| Minimum Firefox | `140.0` desktop / `142.0` Android |
| License (must be) | `PolyForm Noncommercial 1.0.0` (NOT MIT) |

## Agent invocation phrases (reference)

The operator types one of these to trigger the matching agent action.

| Phrase | What the agent does |
|---|---|
| `Audit 10907` | Audit this runbook for gaps / drift; report findings + current `main` HEAD version line |
| `Run amo prep` | Run §3 verify + §4 build, hand back the Firefox ZIP path |
| `Run amo §3` | Run §3 verify only; report findings |
| `Run amo build` | Run §4 build + verify (assumes §3 already passed) |
| `Run amo sign` | Sign + upload via §14 web-ext API path (optional, automation only) |
| `Submitted amo` | Comment the current Central-time submission timestamp on the release issue (or `at YYYY-MM-DD HH:MM`) |
| `Run amo post-publish` | Run §10 post-publish: tag commit, update release notes, comment + close release issue, update the deployment-state table |

---

# Procedure

## 1. Sign in to AMO Developer Hub

1. Open `https://addons.mozilla.org/developers/` in your browser.
2. Sign in as `cto@thrivetech.ai`. Complete 2FA prompt.
3. Verify the account chip in the top-right reads `cto@thrivetech.ai`. If a different Mozilla identity is active, sign out fully at `https://accounts.google.com/Logout`, close the tab, return to step 1.
4. Confirm the **My Add-ons** list shows **Aletheia** at slug `aletheia-ai`.

## 2. Confirm the new version is not already uploaded

1. Open `https://addons.mozilla.org/developers/addon/aletheia-ai/versions/`.
2. Scan the version history table.
3. Confirm the version you intend to upload (e.g. `1.1.2`) does NOT appear. AMO refuses duplicate version numbers at upload.
4. If the version already exists (typically from a prior partial upload), STOP. Bump both manifests to the next patch version per §13 and rebuild before continuing.

## 3. Agent: verify build prerequisites

Say `Run amo §3`. The agent performs items 1–6 and reports.

1. `extensions/firefox/manifest.json` declares the new `version`, monotonic from the current live version (deployment-state block above). The Chrome manifest matches (`build_release.py` enforces parity on `name`, `version`, `description`, `icons`).
2. Firefox `permissions` is exactly `activeTab`, `tabs`, `scripting`, `contextMenus`, `storage`. `host_permissions` is exactly `["https://api.aletheia.study/*"]`. Every permission has a justification at §11l.
3. `browser_specific_settings.gecko` is intact: `id = "extension@aletheia.study"`, `strict_min_version = "140.0"`, `gecko_android.strict_min_version = "142.0"`. `data_collection_permissions.required = ["authenticationInfo", "websiteContent"]`, `optional = []`.
4. No hardcoded test URLs or dev flags. All API traffic targets `https://api.aletheia.study/*`.
5. `poetry run pytest` passes. `npx playwright test` passes.
6. `docs/releases/firefox-vX.Y.Z.md` exists for the target version.

If any check fails, the agent surfaces it. Fix and re-run `Run amo §3` before proceeding.

## 4. Agent: build and verify the ZIP

Say `Run amo build`. The agent performs items 1–4.

1. Delete stale `dist/aletheia-firefox-*.zip` files by exact name. Never glob-delete. If the listing contains anything unrecognized, the agent STOPS and surfaces it.
2. Run `poetry run python tools/build_release.py`. The script runs `web-ext lint` as Step 3; it fails the build on lint errors.
3. Verify the produced `dist/aletheia-firefox-vX.Y.Z.zip`:
   - `manifest.json` at archive root, with `manifest_version: 3` and `browser_specific_settings.gecko.id` present.
   - `icons/` contains the 4 sizes (16, 32, 48, 128).
   - 10 source files at root: `service-worker.js`, `popup.html`, `popup.js`, `popup.css`, `overlay.js`, `content-check.js`, `content-safety.js`, `article-extractor.js`, `auth.js`, `manifest.json`. 14 entries total.
   - All paths use forward slashes. No unexpected files.
4. The agent hands the operator the ZIP path.

**Fallback if `build_release.py` is broken:**

```bash
cd /c/Users/mcwiz/Projects/Aletheia/extensions/firefox
zip -r ../../dist/aletheia-firefox-vX.Y.Z.zip . -x '.*' -x '*/.*' -x 'node_modules/*'
```

Never use PowerShell `Compress-Archive` — AMO rejects backslash separators.

## 5. Diff the live listing against §11 listing content

1. Open the public AMO listing in a **private / incognito** browser window: `https://addons.mozilla.org/en-US/firefox/addon/aletheia-ai/`.
2. For each field below, compare the live listing text against §11. Note any field where the live text differs.

| Live listing field | Compare to | Look for |
|---|---|---|
| Description (the long marketing text) | §11d | Live should contain "We do not enumerate, retain, transmit, or analyze data from tabs..." If it contains "We cannot see your browsing history" or "We use the ActiveTab permission model", the field has drifted. |
| Privacy Policy link | §11i | Click the "Privacy Policy" link. It should resolve to `https://aletheia.study/privacy.html`. If it resolves to `https://martymcenroe.github.io/Aletheia/` or 404s, the field has drifted. |
| Permissions list with justifications | §11l | The listing should show all 5 permissions (`activeTab`, `tabs`, `scripting`, `contextMenus`, `storage`) plus the host permission `https://api.aletheia.study/*`, each with a justification matching §11l. Missing or differing justifications = drift. |
| License | §11k | Should show `PolyForm Noncommercial 1.0.0`. If it shows `MIT` or any other license, the field has drifted. |

Record the list of drifted fields. You'll fix them in §7.

If no fields drifted, skip §7.

## 6. Upload the new ZIP

1. From the Developer Hub, click **Aletheia** → left nav **Manage Status & Versions** (or go to `https://addons.mozilla.org/developers/addon/aletheia-ai/versions/`).
2. Click **Upload a New Version**.
3. Choose the ZIP path the agent handed you in §4 (`dist/aletheia-firefox-vX.Y.Z.zip`). Upload.
4. AMO runs automated validation (seconds). If validation fails, read the error, fix, rebuild, return to step 2.
5. AMO asks "Do you use tools that make your code hard to read?" → answer **No**. Provide the repo as a reviewer reference: `https://github.com/martymcenroe/Aletheia`. Aletheia ships plain readable JavaScript; the ZIP files ARE the source.

The new version now enters review. The previously-approved version stays live until this one is approved.

## 7. Overwrite drifted listing fields (only if §5 found drift)

For each field §5 identified as drifted, navigate to its editor and paste the canonical text from §11.

1. Developer Hub → **Aletheia** → **Edit Product Page** (or **Manage Listing**).
2. For each drifted field:

| Field | Editor location | Paste from |
|---|---|---|
| Description | Listing tab → Description field | §11d |
| Privacy Policy URL | Privacy practices tab → Privacy Policy URL | §11i |
| Permission Justifications | Privacy practices tab → Permission Justification(s) | §11l (one per permission) |
| License | Listing tab → License → "Custom License" → name `PolyForm Noncommercial 1.0.0`, URL `https://polyformproject.org/licenses/noncommercial/1.0.0/` | §11k |

3. Save each tab after editing.
4. Verify in private browsing (`https://addons.mozilla.org/en-US/firefox/addon/aletheia-ai/`) that the updates appear on the public listing.

## 8. Submit for review

1. Click **Submit Version** on the upload flow.
2. Say `Submitted amo` to the agent. The agent comments the current Central-time submission timestamp on the release tracking issue for this version.
3. Wait. AMO automated validation is instant; human review for a listed update typically takes hours to a few days.

## 9. AMO approves — operator action

When AMO emails approval:

1. Say `Run amo post-publish` to the agent.
2. The agent runs §10.
3. Then perform the §11.smoke-test below.

## 10. Agent: post-publish

The agent performs items 1–5 on `Run amo post-publish`:

1. Verify the Firefox install link in `docs/index.html` and `docs/demos.html` points at the AMO listing URL. Fix via the docs-on-main edit flow if stale.
2. Tag the released commit: `git tag firefox-vX.Y.Z-published && git push origin firefox-vX.Y.Z-published`.
3. Comment on the release tracking issue with the approval date and the listing URL. Close the issue.
4. Update `docs/releases/firefox-vX.Y.Z.md` — fill `Submission date:` and add an `Approval date:` line.
5. Update the deployment-state table at the top of this runbook: set **Current published version** to the just-approved version; clear **Pending upload** unless another version is already in flight.

---

# 11. Listing field content (paste-ready)

Canonical text for every AMO form field. When the operator overwrites a drifted field at §7, paste from here.

### 11a. Name

```
Aletheia
```

### 11b. Add-on slug (one-time — never change)

```
aletheia-ai
```

Baked into the listing URL. Changing it breaks every existing link.

### 11c. Summary (250 char limit)

129 characters / 131 bytes UTF-8 (the em-dash is 3 bytes):

```
Instant AI analysis for selected text. Understand context, detect nuance, and verify facts—while maintaining strict data privacy.
```

### 11d. Description

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

### 11e. Category

```
Other
```

### 11f. Screenshots

If you are NOT changing screenshots this submission (the typical case for an update), no action — existing AMO screenshots remain.

If you are changing screenshots: produce per `docs/runbooks/10906-runbook-cws-image-pad.md` (CWS 1280×800 images can be reused). Output to `screenshots/amo/amo-image-N-<slug>.png`. Upload at §6 step 5 alongside the ZIP, or via the Listing tab after submission.

### 11g. Homepage URL

```
https://aletheia.study
```

### 11h. Support site / email

Support site:
```
https://github.com/martymcenroe/Aletheia/issues
```

Support email:
```
cto@thrivetech.ai
```

### 11i. Privacy Policy URL

```
https://aletheia.study/privacy.html
```

NOT `https://martymcenroe.github.io/Aletheia/` (stale; may 404).

### 11j. Data collection disclosure (Firefox 140+ Manage Data Collection form)

Match these to the manifest's `data_collection_permissions`:

| Disclosed type | Detail |
|---|---|
| Authentication information | LinkedIn OAuth token. Stored locally, cleared on browser close. |
| Website content | The selected text + surrounding context, on user-initiated analysis only. |
| (none other) | — |

No "cannot see browsing history" claims. No data type beyond these two.

### 11k. License (Custom — AMO does not have PolyForm in its dropdown)

Choose **"Custom License"** in the AMO dropdown.

License name:
```
PolyForm Noncommercial 1.0.0
```

License URL:
```
https://polyformproject.org/licenses/noncommercial/1.0.0/
```

Or paste the full text of the repo `LICENSE` file into the custom-license text box.

### 11l. Permission justifications (5 permissions + host)

**`activeTab`:**
```
Used to read the text of the currently active tab only when the user explicitly invokes Aletheia (right-click "Explain with AI"). The extension does not access any other tab.
```

**`tabs`:**
```
Used to detect page navigation for overlay lifecycle management, to inject the content script on the active tab, and — on Firefox specifically — to detect the OAuth callback during the tabs-based LinkedIn sign-in flow. The extension does NOT enumerate or read content from any tab other than the one the user explicitly invokes Aletheia on.
```

**`scripting`:**
```
Used to execute the content script (reading the selection's surrounding context) on the active tab during "Explain with AI", and as a recovery path to re-inject the content script into a tab opened before the extension was loaded. Only the active tab, only the extension's own bundled scripts.
```

**`contextMenus`:**
```
Provides the primary trigger: the right-click "Explain with AI" menu item on selected text.
```

**`storage`:**
```
Saves user preferences, the authentication token, and the domain allowlist locally on the user's device. Nothing is stored on a remote server.
```

**Host permission `https://api.aletheia.study/*`:**
```
The single remote endpoint the extension communicates with: the selected text and its surrounding context are sent here for analysis and the result is returned. No other network requests, no third-party analytics or tracking host.
```

### 11.smoke-test (operator does after AMO approves)

1. Install / update Aletheia in Firefox from the AMO listing.
2. **Core flow:** select text on any page → right-click → "Explain with AI" → overlay appears with context-aware analysis.
3. **Auth flow:** click extension icon → "Log in with LinkedIn" → tabs-based OAuth completes (a callback tab opens and closes) → popup shows logged-in state.
4. Verify the version in `about:addons` matches what was uploaded.

If a smoke test fails: do NOT delist. File a `launch-blocker` issue, reproduce in Firefox dev mode (`about:debugging` → Load Temporary Add-on), ship a patch version. A patch must go through AMO review again; do not pull the working version.

---

# 12. First submission (Path A — historical)

Aletheia is already published. This applies only to a from-scratch resubmission (new add-on entry).

1. Developer Hub → **Submit a New Add-on**.
2. Distribution channel: **On this site** (listed on AMO).
3. Upload `dist/aletheia-firefox-vX.Y.Z.zip`.
4. Answer the source-code question per §6 step 5. Fill listing metadata from §11 (Name, Slug, Summary, Description, Category, Homepage URL, Support URL/email, Privacy Policy URL, Permission Justifications, License). Submit.

---

# 13. Version bump procedure

Shared with the Chrome runbook 10905. Aletheia ships both browsers from one version line.

1. Open a tracking issue for the release.
2. Bump both manifests to the same `X.Y.Z`:
   - `extensions/chrome/manifest.json`
   - `extensions/firefox/manifest.json`
3. Write `docs/releases/chrome-vX.Y.Z.md` and `docs/releases/firefox-vX.Y.Z.md`.
4. Commit + PR: `chore: bump extension versions to X.Y.Z (Closes #N)`. Put `Closes #N` in the PR body too — pr-sentinel validates the body, not the commit message.
5. Merge to `main`.
6. Then proceed with §4 → §6 of this runbook for AMO; parallel work for CWS in 10905.

# 14. Web-ext API signing (optional, automation only)

The manual §6 dashboard upload is Aletheia's primary path. Use this only when automating.

### 14a. Generate API credentials (one-time)

1. Open `https://addons.mozilla.org/developers/addon/api/key/` while signed in as `cto@thrivetech.ai`.
2. Generate credentials. AMO shows a **JWT issuer** and a **JWT secret** (shown once).

### 14b. Secret handling

The JWT secret is a long-lived credential:

- Operator stores the issuer and secret as environment variables `WEB_EXT_API_KEY` and `WEB_EXT_API_SECRET`. Not in a OneDrive-synced path. Not in shell history (leading space, or a `.env` the agent never reads).
- Pass via environment, never as a command-line argument (argv is readable by same-user processes).
- The agent NEVER prints, echoes, logs, or commits the secret.
- If exposed: revoke at the AMO API key page and regenerate.

### 14c. Sign + upload (`Run amo sign`)

With env vars exported in the same shell:

```bash
cd /c/Users/mcwiz/Projects/Aletheia
npx web-ext sign \
  --channel listed \
  --source-dir extensions/firefox \
  --artifacts-dir dist
```

`web-ext` reads `WEB_EXT_API_KEY` / `WEB_EXT_API_SECRET` from the environment. Do NOT add `--api-key`/`--api-secret` flags — that puts the secret in argv. `--channel listed` queues the public-listing review (equivalent to §6 upload).

The agent verifies the env vars are set without printing their values; refuses to run if unset.

# 15. Troubleshooting

| Problem | Diagnosis | Action |
|---|---|---|
| AMO rejects ZIP with backslash-path error | Built with PowerShell `Compress-Archive` | Rebuild with `build_release.py` or `zip` from MSYS2 / Git Bash |
| "Version already exists" at upload | Forgot to bump one or both manifests | Bump both per §13, rebuild |
| License shows MIT on the listing | AMO default-picker error | Set to Custom License → PolyForm Noncommercial 1.0.0 (§11k) |
| AMO asks for source code | Validator flagged code as hard-to-read | Aletheia is not minified — answer No and link the repo. If a specific file is flagged, upload the repo as a source ZIP with build instructions |
| Data-collection disclosure mismatch | AMO form drifted from the manifest | Make the AMO form match §11j |
| `web-ext lint` errors on build | Manifest or file issue | Read the lint output; `build_release.py` fails the build on errors |
| `npx playwright test` hangs on Firefox | Windows sandbox crashes the renderer (Juggler `remoteTab is null`) | `MOZ_DISABLE_CONTENT_SANDBOX=1` workaround is permanently applied in `playwright.config.js`. Export it manually if running standalone reproduction scripts. |
| Gecko ID mismatch / "add-on ID changed" | `browser_specific_settings.gecko.id` was edited | Restore `extension@aletheia.study`. Changing it creates a new add-on, orphaning the listing. |
| `strict_min_version` rejected | Set below a Firefox feature's availability | Keep `140.0` desktop / `142.0` Android unless a feature requires higher |
| Listing still shows "cannot see your browsing history" | Pre-audit text | Overwrite §11d at §7. Verify in private browsing. |

# 16. Related documents

- `docs/runbooks/10905-runbook-cws-publish.md` — parallel Chrome Web Store publishing runbook.
- `docs/runbooks/10906-runbook-cws-image-pad.md` — produce listing screenshots without cropping.
- `docs/releases/firefox-vX.Y.Z.md` — per-version release notes.
- `docs/privacy.html` — published privacy policy at `https://aletheia.study/privacy.html`.
- `docs/legal/eula.html` — End User License Agreement.
- `extensions/firefox/manifest.json` — ground-truth permissions, gecko settings, data collection.

# 17. Change log

| Version | Date | Change |
|---------|------|--------|
| 2.0.0 | 2026-05-30 10:49:19 AM Central | **Major restructure** per operator end-to-end test (#726). The runbook was a checklist wrapped in maintainer commentary, redundant steps, and nebulous directions; this version is a flat numbered procedure (§1–§10 for the update path) with explicit URLs, clicks, what-to-look-for, and what-to-do-if-it-fails on every step. Major changes: dropped redundant `§2 Account check passes` operator item (§2 happens once, in §1); separated `web-ext lint` from §3 verify (it runs during §4 build, can't be verified pre-build); split the §3b.4 "review §7–§13 for changes" lump into §5 ("Diff the live listing") with a per-field comparison table; added §7 "Overwrite drifted listing fields" with explicit dashboard surfaces (the prior runbook directed operators to "overwrite at §6 upload" without saying how); made screenshots a no-op for updates by default (§11f); moved first-submission flow to §12 with a "historical" label; removed front-matter padding (Tracking issue, Versioning, Standard reference, Chrome cross-reference); removed §4 anecdote about a cleanup-agent incident; removed §4a "Known hardening gap" bug-commentary; removed §7e category-rationale history, §11 license-rationale restating its own warning, §12 "Why fewer than Chrome" cross-runbook commentary. Listing paste-blocks (now §11) are unchanged in content; only their position and numbering moved (Closes #726). |
| 1.0.10 | 2026-05-30 10:28:40 AM Central | Patch: dropped the §0 section number. The agent-invocation-phrases table read as "step 0, do this first" when it is reference material, not a procedure step (Closes #721). |
| 1.0.9 | 2026-05-30 10:05:57 AM Central | Patch: dropped "pre-flight" framing throughout. §3 retitled "Verification (before §4 build)"; `Run amo pre-flight` → `Run amo prep` (Closes #719). |
| 1.0.8 | 2026-05-30 9:50:00 AM Central | Patch from `Audit 10907`: removed three references to `docs/10920-cws-listing-corrections-2026-05-27.md` (at §3b.4, §10a, §18) (Closes #717). |
| 1.0.7 | 2026-05-30 9:15:03 AM Central | Patch from `Audit 10907`: §3a.7 says directory does not exist; §7c notes byte/char count (Closes #713). |
| 1.0.6 | 2026-05-30 12:15:15 AM Central | Patch: documented the Windows sandbox Playwright hang in §18 Troubleshooting. `MOZ_DISABLE_CONTENT_SANDBOX=1` workaround applied in `playwright.config.js`. |
| 1.0.5 | 2026-05-29 11:26:54 AM Central | Patch: removed the "no live debug-tier console calls" clause from §3a.4 (Closes #691). |
| 1.0.4 | 2026-05-29 12:57:37 AM Central | Patch: removed a redundant lead-in in §10b (Closes #689). |
| 1.0.3 | 2026-05-29 12:41:37 AM Central | Patch: applied `Audit 10907` findings. §17c no longer passes the API secret on the command line. §15a refreshes the deployment-state version. §1 Path B / §3a.1 reference the deployment-state block (Closes #686, #687). |
| 1.0.2 | 2026-05-29 12:18:55 AM Central | Patch: corrected timestamps that were UTC mislabeled as Central (Closes #684). |
| 1.0.1 | 2026-05-28 08:05:10 PM Central | Patch: corrected deployment-state to state the live AMO version is `1.1.1`. Replaced `rm -f <glob>` artifact-clean with list-inspect-delete-by-name (Closes #682, #681). |
| 1.0.0 | 2026-05-28 06:49:42 PM Central | New runbook, built to the AZ#1362 standard, split out of `10905-runbook-extension-store-publish.md` (Closes #678). |
