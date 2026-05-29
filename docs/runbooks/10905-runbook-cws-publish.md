# 10905 — Chrome Web Store Publishing (Aletheia)

> **Version:** 1.0.1
> **Last updated:** 2026-05-29 01:05:10 AM Central
> **Applies to:** Aletheia Chrome extension, every submission to the Chrome Web Store
> **Tracking issue:** [martymcenroe/Aletheia#678](https://github.com/martymcenroe/Aletheia/issues/678)
> **Versioning:** semver per [AssemblyZero#1362](https://github.com/martymcenroe/AssemblyZero/issues/1362) principle 20 — major.minor.patch. See §20 change log.
> **Standard:** built to the AZ#1362 runbook standard. That standard doc is not yet shipped (the issue holds the full spec); [Clio 30002](https://github.com/martymcenroe/Clio/blob/main/docs/runbooks/30002-chrome-web-store-publish.md) is the operator-validated reference implementation.
> **Firefox / AMO:** Mozilla publishing moved to [`10907-runbook-amo-publish.md`](./10907-runbook-amo-publish.md). This runbook is Chrome Web Store only.

## Aletheia CWS deployment state

Durable identifiers for the live Aletheia Chrome listing. Agent commands below (§0) reference these; updating any value here propagates to those commands.

| Item | Value |
|---|---|
| Extension ID | `pfkfdlcdbajamklbneflfbkmnceooijm` |
| Install URL | `https://chromewebstore.google.com/detail/aletheia/pfkfdlcdbajamklbneflfbkmnceooijm` |
| Dashboard listing | `https://chrome.google.com/webstore/devconsole` → Items → Aletheia |
| Publisher | ThriveTech.ai (`cto@thrivetech.ai`) |
| Current published version | `1.1.2` (live; updated 2026-05-25) |
| Stable-ID key | `manifest.json` → `key` field pins the dev-load ID to the published ID — not a secret |
| Submission tracking | per-release issue (see §16); this runbook tracked by [#678](https://github.com/martymcenroe/Aletheia/issues/678) |

Update this table on rebrand, ID change, or republish-from-scratch.

## Throughout this runbook

- **Operator** — the human running the publishing process at the Chrome Web Store dashboard. Can perform any step.
- **Agent** — a Claude Code session with this repo's working tree available. Performs any step marked agent. Invoked by the canonical phrases in §0 below.

## How to verify you have the latest copy

This runbook lives at `docs/runbooks/10905-runbook-cws-publish.md` in [martymcenroe/Aletheia](https://github.com/martymcenroe/Aletheia). The **Version** and **Last updated** lines above identify which revision you're holding.

To compare a printed copy against the canonical:

1. Note the version number on your copy.
2. Say `Run cws pre-flight` or `Audit 10905` (see §0) — the agent reports the current `main` HEAD's runbook version line as part of its output.
3. If your copy's version differs, re-print before continuing.

The §20 Change log at the bottom lists every version with what changed.

## 0. Invoke the agent (canonical phrases)

The operator types one of these phrases into the agent chat to trigger the matching action. The agent recognizes the phrase verbatim or with minor punctuation variation; if a phrase is ambiguous in context, the agent asks for clarification before acting. Phrases are **prefixed `cws`** to disambiguate from the parallel AMO runbook ([10907](./10907-runbook-amo-publish.md)) — `Run cws build` is the Chrome path, `Run amo build` is the Firefox path.

| To make the agent... | Operator says |
|---|---|
| Audit this runbook for gaps / drift | `Audit 10905` |
| Run §3a pre-flight + §4 build, hand back the Chrome ZIP path | `Run cws pre-flight` |
| Run §3a only (no build) and report findings | `Run cws §3a` |
| Run §4 build + verify (pre-flight already passed) | `Run cws build` |
| Comment the submission timestamp on the release issue (current Central time, or pass `at YYYY-MM-DD HH:MM`) | `Submitted cws` |
| After CWS approves: run §15a — tag the commit, update release notes, comment + close the release issue | `Run cws post-publish` (install URL defaults to the deployment-state block; override with `Run cws post-publish <URL>`) |

The agent's reply to any of these includes: (a) a one-line confirmation of what it did, (b) any findings or follow-ups, (c) the current `main` HEAD's runbook version line so the operator can sanity-check a printed copy on every turn.

## 1. Where to start (reading paths)

Pick the path that matches your situation; sections off your path can be skipped on this submission.

| Situation | Read sections |
|-----------|--------------|
| **Path A — First Aletheia submission** (CWS Items list does not show Aletheia) | §2 → §3 → §4 → §5 → §7 → §8 → §9 → §10 → §11 → §12 → §13 → §14 → §15 |
| **Path B — Subsequent Aletheia update** (Aletheia already in the Items list — the normal case; current published version is 1.1.2) | §2 → §3 → §4 → §6 → (review §7–§13 if listing copy changed) → §14 → §15 |
| **Path C — New machine, new Chrome profile, or new publisher account** | Stop. Set up dashboard access first (memory `user-cws-dashboard-access`: dedicated Chrome profile, first bookmark = dev console, saved password, Google Authenticator 2FA), then return here as Path A or Path B. |

§16 Version bump, §17 Troubleshooting, §18 Release notes, §19 Related documents, §20 Change log are reference material — skim once, return as needed.

## 2. Account check (every submission)

Whether this is the first submission or the hundredth, verify the correct identity before any upload:

1. Open the dedicated Chrome profile pre-loaded with `cto@thrivetech.ai` (memory `user-cws-dashboard-access`).
2. Click the first bookmark in the bookmark bar — the Chrome Web Store developer dashboard (`https://chrome.google.com/webstore/devconsole`).
3. Authenticate with the saved password, then approve the Google Authenticator 2FA prompt.
4. The top-right **Publisher** chip must read `ThriveTech.ai`; the avatar email must be `cto@thrivetech.ai`.
5. If it's any other Google identity: sign out fully (`https://accounts.google.com/Logout`), close all Chrome windows, re-open the profile, navigate to the dashboard, choose `cto@thrivetech.ai` from the picker.

This is the same publisher account that hosts Clio. Publisher-level changes (§10) affect both extensions.

## 3. Pre-flight checklist

Split by responsibility. **Agent items** happen in the repo. **Operator items** happen on the publishing machine and dashboard. Each party checks their own before handing off. Items are numbered so they can be referenced as "§3a.N" or "§3b.N".

### 3a. Agent does (in the repo, before producing the ZIP)

1. `extensions/chrome/manifest.json` has the new `version`, monotonically increasing from the last published version (currently `1.1.2`). For Path A first submission, no prior published version exists; auto-pass. The Chrome manifest version is the build's source of truth (`tools/build_release.py` Step 4).
2. `permissions` is exactly `activeTab`, `tabs`, `scripting`, `contextMenus`, `storage`, `identity`, `notifications`. `host_permissions` is exactly `["https://api.aletheia.study/*"]`. **Every permission has a §12 paste-block.** If §12 has fewer entries than the manifest, that's the finding — the 2026-05-26 privacy audit found the dashboard was missing justifications for `tabs`, `storage`, `identity`, and `notifications` (see #670–#672 / `docs/10920-cws-listing-corrections-2026-05-27.md`). Adding a new permission to the manifest requires adding a §12 paste-block in the same change.
3. No live debug-tier console calls in `extensions/chrome/*.js`. **Banned:** live `console.log` / `console.debug` / `console.info` / `console.warn`. **Allowed:** `console.error` inside a `try/catch` that also surfaces the error to the user via the popup/overlay UI; commented-out calls; explanatory comments.
4. No hardcoded test URLs, dev flags, or scratch code. **All API traffic goes through `https://api.aletheia.study/*` — never a raw Lambda Function URL** (this was a v1.1.2 security fix).
5. All tests pass: `poetry run pytest` (backend) and `npx playwright test` (extension e2e).
6. Lint clean: `npm run lint` (or `npx eslint .`).
7. Version bump merged to `main` — build from `main`, never a feature branch.
8. Release notes file `docs/releases/chrome-vX.Y.Z.md` written before the §4 build — see §18.
9. Listing screenshots exist at `screenshots/cws/cws-image-N-<slug>.png`, format **24-bit PNG (no alpha)**, dimensions **1280×800** (or 640×400; 1280×800 is the default). Mechanical check; agent reports file list, sizes, dimensions, and color mode (must be `RGB`, never `RGBA`). **Current state:** only `screenshots/cws/cws-image-1-epocha.png` exists; the live listing carries 4 identical placeholder screenshots. **[#635](https://github.com/martymcenroe/Aletheia/issues/635) tracks producing 4 distinct images** — produce them with [`10906-runbook-cws-image-pad.md`](./10906-runbook-cws-image-pad.md) before the next listing-copy submission.
10. Agent reads each `screenshots/cws/*.png` and pre-describes what's visible (browser chrome, overlay state, page content) so the operator's §3b.3 review is "approve the flag-list," not "review from scratch."
11. Agent reports the current `main` HEAD commit SHA and this runbook's `> **Version:**` line so the operator can sanity-check a printed copy.

### 3b. Operator does (on the publishing machine)

1. §2 Account check passes — Publisher chip `ThriveTech.ai`, avatar `cto@thrivetech.ai`.
2. The version isn't already in the dashboard. For Path B, check the Package tab's version history. For Path A, Aletheia isn't in the Items list yet; auto-pass.
3. Approve the agent's §3a.10 screenshot pre-description, or flag personal info / embarrassing content the agent missed.
4. Review §7–§12 paste-blocks for changes since last submission — these are the canonical source; no second document to open. **The dashboard may still carry pre-audit text** (e.g. the false "cannot see your browsing history" claim, the stale `github.io` privacy URL, missing permission justifications). Where the dashboard disagrees with §7/§11/§12, overwrite the dashboard to match this runbook.
5. Operator's printed-copy version line matches the version the agent reported in §3a.11.

If any §3a item is unchecked, the agent fixes what it can (write missing release notes, regenerate screenshots, etc.) and surfaces the rest before producing the ZIP. If any §3b item is unchecked, the operator pauses before clicking Upload.

## 4. Build & verify the ZIP (agent does this)

**Agent runs §4a + §4b. Operator receives the ZIP path and uploads it at §5 (Path A) or §6 (Path B).**

**CRITICAL:** `build_release.py` uses Python's `ZipFile`, which writes forward-slash separators — safe. If you fall back to manual zipping, use `zip` from MSYS2 / Git Bash, **never** PowerShell `Compress-Archive` (it writes backslash separators that the CWS reviewer flags as malformed).

**CRITICAL:** `extensions/chrome/` must contain only extension files. No `docs/`, `tests/`, `tools/`, `node_modules/`, or session logs. Verify before zipping (an earlier incident packaged a stray `docs/session-logs/` directory into a Firefox build).

### 4a. Build (agent does this)

```bash
cd /c/Users/mcwiz/Projects/Aletheia
# Clear stale artifacts safely — never glob-delete. List first, inspect, then delete by name:
ls -1 dist/aletheia-chrome-*.zip 2>/dev/null || echo "(none present)"
#   If an older-version zip is listed, delete that file BY NAME (e.g. rm dist/aletheia-chrome-v1.1.1.zip).
#   If the list shows anything you do not recognize, STOP and investigate before deleting.
poetry run python tools/build_release.py
```

`tools/build_release.py` verifies all four icons exist and are non-empty in both extension dirs, validates manifest parity (`name`, `version`, `description`, `icons`), runs `web-ext lint` on the Firefox source, reads the version from the Chrome manifest, and produces **both** `dist/aletheia-chrome-v{version}.zip` and `dist/aletheia-firefox-v{version}.zip`. For a CWS submission you use the **chrome** ZIP.

> **Known hardening gap (principle 17):** `build_release.py` does NOT delete stale `dist/*.zip` before building. Until that is fixed, do the list-inspect-delete-by-name step above. Follow-up: add stale-artifact cleanup to `build_release.py` that removes the prior Aletheia zips by exact name (never a glob).

Fallback if `tools/build_release.py` is missing or broken:

```bash
cd /c/Users/mcwiz/Projects/Aletheia
# List, inspect, then delete any stale chrome zip BY NAME (never a glob); STOP if the list is unexpected:
ls -1 dist/aletheia-chrome-*.zip 2>/dev/null || echo "(none present)"
cd extensions/chrome
zip -r ../../dist/aletheia-chrome-vX.Y.Z.zip . -x '.*' -x '*/.*' -x 'node_modules/*'
```

### 4b. Verify (agent does this)

```bash
cd /c/Users/mcwiz/Projects/Aletheia
unzip -l dist/aletheia-chrome-vX.Y.Z.zip
```

Confirm:

- Forward slashes in all paths (no backslashes).
- `manifest.json` at the archive root.
- `icons/` with four icons: 16, 32, 48, 128.
- Expected source files at root: `service-worker.js`, `popup.html`, `popup.js`, `popup.css`, `overlay.js`, `content-check.js`, `content-safety.js`, `article-extractor.js`, `auth.js` (10 root files + 4 icons = 14 entries).
- No unexpected files (docs, session logs, dotfiles, scratch files).

Sanity-check the manifest version inside the ZIP:

```bash
unzip -p dist/aletheia-chrome-vX.Y.Z.zip manifest.json | grep '"version"'
```

The reported version must match the ZIP filename. The agent hands the operator a single line: the path to `dist/aletheia-chrome-vX.Y.Z.zip`.

## 5. First submission upload (Path A — Aletheia not yet in the dashboard)

Use this section only if Aletheia does **not** appear in the dashboard's Items list (historical — Aletheia is already published; this applies only on a republish-from-scratch).

1. From the dashboard, click **+ New item** (top-right of the Items list).
2. The "Upload your item" dialog opens. Click **Choose file** and select `dist/aletheia-chrome-vX.Y.Z.zip`.
3. Click **Upload**. Validation runs (10–60 s). Fix any inline validation errors in source, rebuild, re-upload before proceeding.
4. On success, CWS creates a draft listing and routes you to the **Store listing** tab. Continue §7 → §8 → §9 → §10, then §11 Privacy, §12 Permissions, §13 Pricing.

## 6. Subsequent update upload (Path B — Aletheia already in the dashboard)

Use this section only if Aletheia appears as a row in the Items list (the normal case).

1. From the dashboard, click the **Aletheia** row to open its listing.
2. Left sidebar → **Package**.
3. Click **Upload new package** (top of the Package tab).
4. Choose `dist/aletheia-chrome-vX.Y.Z.zip` and upload.
5. Validation runs. On success, the new version becomes the draft. The previously-published version stays live until this draft is submitted and approved.

## 7. Store listing — product details

Update fields if changed. All text below is paste-ready — copy into the matching CWS form field. These are the top-of-the-form fields on the Store listing tab; §8, §9, §10 are the rest of that tab.

### 7a. Name

```
Aletheia
```

### 7b. Short description

*CWS limit: 132 characters. Current copy: 129 chars.*

```
Instant AI analysis for selected text. Understand context, detect nuance, and verify facts—while maintaining strict data privacy.
```

### 7c. Long description

*CWS limit: 16,000 characters. Plain text. This is the audit-corrected copy (lifted from `docs/lld/done/10051-store-compliance.md` after PRs #670–#672); the "Privacy by Design" line MUST read "we do not enumerate…", never the old "we cannot see your browsing history" claim.*

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

> **Maintainer note:** the LLD's original closing line read "Open Source and transparent." Aletheia is licensed **PolyForm Noncommercial 1.0.0** (source-available, *not* OSI open-source), so this paste-block says "Source-available and transparent" to avoid a license-misrepresentation claim. If you intentionally want the "Open Source" wording back, change the LICENSE first. (Flag for a follow-up issue if the live listing still says "Open Source".)

### 7d. Category

CWS groups categories under uppercase meta-headers (PRODUCTIVITY, LIFESTYLE, etc.). **PRODUCTIVITY is the header, not a selectable value** — the old runbook listed "Productivity," which can't actually be selected (lesson from Clio 30002 v4.2.1). Pick `Tools` from the PRODUCTIVITY group.

```
Tools
```

Confirm against the live listing's current selection before changing it. Rationale (preserved for future maintainers):
- `Tools` (recommended) — single-purpose reading/analysis utility; matches Aletheia's framing.
- `Education` (rejected) — Aletheia aids comprehension but is not a teaching/courseware tool; "Tools" is the closer fit.
- `Developer Tools` (rejected) — not developer-specific; works on any webpage.
- `Communication` (rejected) — Aletheia analyzes content, it doesn't enable communication.

### 7e. Language

```
English (United States)
```

### 7f. Support / contact email

```
cto@thrivetech.ai
```

## 8. Store listing — graphic assets

The **Graphic assets** section of the Store listing tab. Upload in dashboard order; the agent confirmed existence + dimensions + format in §3a.9.

### 8a. Store icon (required)

**CWS requirement:** 128×128 PNG.
**File to upload:** `extensions/chrome/icons/icon128.png`

Same icon ships in the manifest; `build_release.py` Step 1 verifies it exists and is non-empty on every build.

### 8b. Promo video (optional)

YouTube URL input. **Skip** — Aletheia has no promo video. File a follow-up if a featured-listing push needs one.

### 8c. Screenshots (required, at least one)

**CWS requirement:** 1280×800 or 640×400, JPEG or 24-bit PNG (no alpha). Up to 5.
**Files to upload (in order):** `screenshots/cws/cws-image-N-<slug>.png`

**Current state:** only `screenshots/cws/cws-image-1-epocha.png` exists. The live listing shows 4 identical screenshots — that's the bug [#635](https://github.com/martymcenroe/Aletheia/issues/635). Produce 3 more distinct images with [`10906-runbook-cws-image-pad.md`](./10906-runbook-cws-image-pad.md) (`tools/cws_image_pad.py`, brand-blue padding, no cropping of revenue-bearing UI) before submitting listing-copy changes. Drag each into the "Drop image here" target one at a time.

### 8d. Small promo tile (optional)

**CWS requirement:** 440×280, JPEG or 24-bit PNG (no alpha).
`tools/generate_promo_tiles.py` produces this. Required for featured-listing eligibility only; skip for a routine update.

### 8e. Marquee promo tile (optional)

**CWS requirement:** 1400×560, JPEG or 24-bit PNG (no alpha). Same featured-listing posture as §8d. Skip for a routine update.

## 9. Store listing — additional fields

The **Additional fields** section.

### 9a. Official URL (dropdown)

```
thrivetech.ai
```

The publisher domain, already Search-Console-verified under `cto@thrivetech.ai`, so it appears in the dropdown. Official URL represents the **publisher's** identity (ThriveTech.ai); §9b Homepage URL is the **product's** landing page. Two different fields.

### 9b. Homepage URL

```
https://aletheia.study
```

### 9c. Support URL

```
https://github.com/martymcenroe/Aletheia/issues
```

### 9d. Mature content (toggle)

Leave **off**. Aletheia is a reading/analysis utility; no sexual, violent, or substance-related content.

## 10. Account Settings (publisher-level — affects all items)

The Item support setting on the per-item Store listing tab is just a **link** (`Change visibility here`) to the **publisher Account Settings page**, which holds configuration affecting every extension this publisher owns — **Aletheia, Clio, and any future ThriveTech.ai item**. Cover them all in dashboard order so no one-time decision is skipped.

**How to get there:** per-item Store listing tab → Item support → `Change visibility here`; OR main dashboard → left sidebar under PUBLISHER → **Settings**. Both land on `https://chrome.google.com/webstore/devconsole/account`.

### 10a. Profile (one-time, already set)

| Field | Value | Action |
|---|---|---|
| Publisher display name | `ThriveTech.ai` | None |
| Publisher ID | `9f2b248a-0167-40b0-89d5-2ad84348a837` (auto) | None |
| Contact email | `cto@thrivetech.ai` (verified) | None — change only on email rotation |

### 10b. Trader declaration (one-time)

Set to **This is a trader account** (required under EEA consumer-protection law; ThriveTech.ai is a commercial entity). No action for an Aletheia update.

### 10c. Account verification (one-time)

Verified as `Martin McEnroe`, DUNS 119147385. Google-side check; no action unless contact info or DUNS changes.

### 10d. Management — Trusted tester accounts

Email-address input. Leave **empty** for a public release. Populate only during a deliberate Private/beta phase. The **Delete publisher account** button also lives here — **never click it** (destroys Aletheia, Clio, and every item under the publisher).

### 10e. Spotlight item (per-listing decision)

The item highlighted on the publisher's public CWS page. **Current state: Aletheia.** Leave as-is unless deliberately rotating Clio in. Operator decision per launch context.

### 10f. Service account

Google service-account email for CI/API access. Leave **empty** unless automation needs programmatic metadata access.

### 10g. Organization publishing

`Generate approval link` — enterprise-only (domain-restricted) listings. **Skip**; Aletheia is a public listing.

### 10h. Members

Current: Martin McEnroe (`cto.thrivetech.ai@gmail.com`) as Admin. No action unless adding teammates.

### 10i. Item support — Visibility toggle

The single toggle the per-item `Change visibility here` link surfaces. **Recommended: ON** — Aletheia has a public GitHub issue tracker (§9c), so a discoverable support link reduces confused reviews. **All-or-nothing across items:** flipping it OFF also hides Clio's support link; it cannot be set per-item. If the dashboard help text contradicts this, defer to the dashboard and file a runbook-update issue with what it actually said.

## 11. Privacy tab

| Field | Value |
|-------|-------|
| Privacy Policy URL | `https://aletheia.study/privacy.html` |
| Handles user data? | Yes — website content (selected text + ~2,000 chars of surrounding context) and authentication info (LinkedIn OAuth token) |
| Sold to 3rd parties? | No |
| Used for unrelated purposes? | No |
| Used for creditworthiness or lending? | No |

> The Privacy Policy URL was the stale `https://martymcenroe.github.io/Aletheia/` on the live listing; the corrected canonical is `https://aletheia.study/privacy.html` (per `docs/10920-cws-listing-corrections-2026-05-27.md`). Verify the public listing's "Privacy Policy" link resolves there and shows the current policy (no "automatically redacted" claim, no "cannot access browsing history" sentence).

### 11a. Single-purpose description

*CWS asks: "Describe the single purpose of your extension." Paste:*

```
Context-aware analysis of the text the user explicitly selects on a webpage: on a right-click "Explain with AI" action, Aletheia reads the selection plus its surrounding paragraph and returns an explanation that accounts for nuance and usage. It does not act on any tab the user has not explicitly invoked it on.
```

### 11b. Data usage disclosures (Chrome's mandatory checklist)

| Data type | Collected? | Notes |
|-----------|-----------|-------|
| Personally identifiable info | No | — |
| Health info | No | — |
| Financial info | No | — |
| Authentication info | **Yes** | LinkedIn OAuth token, stored in `chrome.storage.session`, cleared on browser close. Matches the Firefox manifest's `data_collection_permissions: authenticationInfo`. |
| Personal communications | No | — |
| Location | No | — |
| Web history | No | — |
| User activity | No | — |
| Website content | **Yes** | The selected text and ~2,000 chars of surrounding context on the active tab, on user-initiated analysis only. Matches `data_collection_permissions: websiteContent`. |

## 12. Permission justifications

CWS requires a written justification for each declared permission and host permission. Each block below is paste-ready. **All seven `permissions` plus the host permission must be filled** — the 2026-05-26 audit found four were missing on the live dashboard (see §3a.2).

### 12a. `activeTab`

```
Used to read the text of the currently active tab only when the user explicitly invokes Aletheia (right-click "Explain with AI"). The extension does not access any other tab. activeTab is granted at invocation time and scoped by Chrome by design. This is the minimum permission required for the extension's stated single purpose.
```

### 12b. `tabs`

```
Used to detect page navigation for overlay lifecycle management (dismissing a stale analysis overlay when the page changes), to inject the content script on the active tab, and to detect the OAuth callback during LinkedIn sign-in. The extension does NOT enumerate, read titles of, or access content from any tab other than the one the user explicitly invokes Aletheia on.
```

### 12c. `scripting`

```
Used to execute the content script (which reads document.body.innerText of the selection's surrounding context) strictly on the active tab during the "Explain with AI" action, and as a recovery path to re-inject the content script into a tab that was open before the extension was installed or reloaded. It is invoked only on the active tab, only with the extension's own bundled scripts, never into any other tab.
```

### 12d. `contextMenus`

```
Provides the primary trigger interface: the right-click "Explain with AI" menu item on selected text. Without it the extension has no entry point.
```

### 12e. `storage`

```
Saves user preferences, the authentication token, and the domain allowlist locally on the user's device. No preferences or credentials are stored on any remote server.
```

### 12f. `identity`

```
Required for the LinkedIn OAuth authentication flow (chrome.identity.launchWebAuthFlow), which signs the user in to their Aletheia account. Used only to complete the OAuth handshake; the resulting token is stored in chrome.storage.session and cleared on browser close.
```

### 12g. `notifications`

```
Displays a brief completion notification when an analysis finishes, so the user knows the result is ready without watching the page. No notification content leaves the device.
```

### 12h. Host permission: `https://api.aletheia.study/*`

```
The single remote endpoint the extension communicates with. The selected text and its surrounding context are sent here for analysis and the result is returned. All traffic is to this custom domain (which fronts the analysis backend through Cloudflare); the extension makes no other network requests and contacts no third-party analytics or tracking host.
```

## 13. Pricing & distribution

| Field | Value |
|-------|-------|
| License | PolyForm Noncommercial 1.0.0 (see [LICENSE](../../LICENSE)) |
| Visibility | Public |
| Regions | All regions |
| Pricing | Free |

## 14. Submit for review

1. Operator clicks **Submit for review**.
2. Chrome review typically takes 1–3 business days.
3. Operator says `Submitted cws`. The agent comments the current Central-time submission timestamp on the release issue (or the time given after `at`).

## 15. Post-publish

After Chrome approves and emails the operator that the version is live, the operator says `Run cws post-publish`. The URL argument is optional — the agent uses the pinned install URL from the deployment-state block unless overridden with `Run cws post-publish <URL>`.

### 15a. Agent does (`Run cws post-publish`)

1. Verify the install link in `docs/index.html` (line ~254) and `docs/demos.html` (line ~153) points at the pinned install URL; fix via the docs-on-main edit flow if stale.
2. Tag the released commit: `git tag chrome-vX.Y.Z-published && git push origin chrome-vX.Y.Z-published` (X.Y.Z from `extensions/chrome/manifest.json`).
3. Comment on the release issue with the approval date and the pinned install URL; close the issue.
4. Update `docs/releases/chrome-vX.Y.Z.md` — fill the `Submission date:` line with the §14.3 timestamp and add an `Approval date:` line for the date Chrome notified the operator.

### 15b. Operator does (clean-profile smoke test)

1. Install Aletheia from the CWS listing on a clean Chrome profile (the agent cannot drive Chrome's profile manager).
2. **Core flow:** select text on any page → right-click → "Explain with AI" → an overlay appears with context-aware analysis.
3. **Auth flow:** click the extension icon → "Log in with LinkedIn" → complete OAuth → popup shows the logged-in state.
4. Verify `chrome://extensions` shows the version that was uploaded.

### 15c. If a smoke test fails

Do **not** delist. File a `launch-blocker` issue, reproduce in dev mode, ship a patch version. A version on the store that mostly works is recoverable; a removed listing has to go through review from scratch.

## 16. Version bump procedure

Aletheia ships Chrome and Firefox from one version line. Bump both manifests together (the Firefox runbook [10907](./10907-runbook-amo-publish.md) §16 is the same procedure).

1. Open a GitHub issue describing the release contents — link the closed work bundled in.
2. Update **both** manifests to the same version:
   - `extensions/chrome/manifest.json` → `"version": "X.Y.Z"`
   - `extensions/firefox/manifest.json` → `"version": "X.Y.Z"`
   (`build_release.py` validates parity and will refuse to build on a mismatch.)
3. Update `docs/releases/chrome-vX.Y.Z.md` and `docs/releases/firefox-vX.Y.Z.md` (§18).
4. Commit: `chore: bump extension versions to X.Y.Z (close #N)`.
5. Merge to `main`.
6. Then §4 Build and §5/§6 Upload.

## 17. Troubleshooting

| Problem | Diagnosis | Action |
|---------|-----------|--------|
| CWS rejects ZIP with "invalid path" / backslash error | ZIP built with PowerShell `Compress-Archive` | Rebuild with `build_release.py` or `zip` (MSYS2 / Git Bash) |
| "Version already exists" | Forgot to bump | Update both manifests, rebuild |
| Reviewer rejection (permission justification) | Reviewer wants more detail | Read the rejection carefully — usually one permission needs a more concrete user-benefit framing; do not dilute the justification just to satisfy them |
| Listing still shows "cannot see your browsing history" | Pre-audit dashboard text | Overwrite §7c Long description; verify in incognito (per `docs/10920`) |
| Privacy Policy link 404s or shows stale policy | Stale `github.io` URL on the dashboard | Set §11 Privacy Policy URL to `https://aletheia.study/privacy.html` |
| ZIP contains unexpected files | Stray dev artifacts under `extensions/chrome/` | Remove; never let a cleanup agent write inside extension dirs |
| Manifest validation fails on icon dimensions | Missing/asymmetric icon | Check `extensions/chrome/icons/` for all four sizes; `tools/generate_icons.py` |
| Screenshot rejected with alpha-channel error | PNG has RGBA, not RGB | Re-export as 24-bit PNG (no alpha); `tools/cws_image_pad.py` outputs RGB |
| Avatar shows wrong account | Multi-account hazard | Sign out fully, close Chrome, re-open profile, choose `cto@thrivetech.ai` |

## 18. Release notes

Per-version notes live in `docs/releases/` as `chrome-vX.Y.Z.md`. Each file contains:

1. **Public-facing notes** — the store listing's "What's New".
2. **Reviewer notes** — permission-justification summary, smoke-test instructions, "no minified code" evidence.
3. The previous version number and the submission date.

Create it **before** §4 Build — it is the source of truth for the dashboard's text fields. Current files: `docs/releases/chrome-v1.1.2.md` (latest), plus `chrome-v1.0.md`.

## 19. Related documents

- [`10907-runbook-amo-publish.md`](./10907-runbook-amo-publish.md) — the parallel Firefox AMO publishing runbook.
- [`10906-runbook-cws-image-pad.md`](./10906-runbook-cws-image-pad.md) — produce 1280×800 store screenshots without cropping.
- [`10903-runbook-lambda-config-change.md`](./10903-runbook-lambda-config-change.md) — backend config changes (the API the extension calls).
- `docs/releases/` — per-version release notes archive.
- `docs/lld/done/10051-store-compliance.md` — original store-listing text and privacy justifications (provenance; the canonical copy now lives inline here).
- `docs/privacy.html` — the published privacy policy (`https://aletheia.study/privacy.html`).
- `docs/legal/eula.html` — End User License Agreement.
- `extensions/chrome/manifest.json` — ground-truth permission declaration.
- Operator memory `user-cws-dashboard-access` — Chrome profile / bookmark / 2FA login pattern.

## 20. Change log

Semver per AZ#1362 principle 20.

| Version | Date | Change |
|---------|------|--------|
| 1.0.1 | 2026-05-29 01:05:10 AM Central | Patch: replaced the `rm -f <glob>` artifact-clean steps in §4a (main + fallback) with a list → inspect → delete-by-name procedure (Closes #681); corrected the deployment-state line to "live; updated 2026-05-25" (CWS is genuinely at 1.1.2). |
| 1.0.0 | 2026-05-28 11:49:42 PM Central | Restructured to the AZ#1362 runbook standard, modeled on [Clio 30002](https://github.com/martymcenroe/Clio/blob/main/docs/runbooks/30002-chrome-web-store-publish.md). Renamed `10905-runbook-extension-store-publish.md` → `10905-runbook-cws-publish.md` and scoped Chrome-only; Firefox/AMO split to new [10907](./10907-runbook-amo-publish.md). Added: semver+timestamp header, deployment-state block (Extension ID `pfkfdlcdbajamklbneflfbkmnceooijm`, install URL, publisher), §0 invoke phrases, §1 reading-path matrix, §3a/§3b split pre-flight, agent-owned `build_release.py` build, dashboard-order §7–§13, publisher-level §10 Account Settings (shared with Clio). Lifted the audit-corrected Long Description, Privacy Policy URL (`aletheia.study/privacy.html`), and all seven permission justifications from `docs/10920-cws-listing-corrections-2026-05-27.md` and `docs/lld/done/10051-store-compliance.md` as inline canonical paste-blocks; flagged the "Open Source" vs PolyForm-Noncommercial wording. Closes #678 (with [10907](./10907-runbook-amo-publish.md)). |
