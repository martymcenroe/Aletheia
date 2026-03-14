# 10905 - Extension Store Publishing

## Purpose

Step-by-step instructions for publishing Aletheia extension updates to Chrome Web Store and Firefox AMO. Covers building, uploading, and post-publish verification.

## Accounts

| Store | Account | Dashboard |
|-------|---------|-----------|
| Chrome Web Store | `cto@thrivetech.ai` | https://chrome.google.com/webstore/devconsole |
| Firefox AMO | `cto@thrivetech.ai` (forwards to `cto.thrivetech.ai@gmail.com`) | https://addons.mozilla.org/developers/ |

## Pre-Flight Checklist

Before publishing, verify:

- [ ] Both manifests have the same `version` number
- [ ] `host_permissions` contains ONLY `https://api.aletheia.study/*`
- [ ] No dev/debug code (console.log, hardcoded URLs, test flags)
- [ ] All tests pass (`poetry run pytest` + `npx playwright test`)
- [ ] Version is NOT already published (check dashboards)
- [ ] Changes are merged to main

## Build Zips

**CRITICAL:** Always use `zip` from MSYS2/Git Bash. NEVER use PowerShell `Compress-Archive` — it writes backslash path separators that AMO rejects.

**CRITICAL:** Verify extension directories contain ONLY extension files — no `docs/`, `tests/`, or other non-extension directories.

```bash
# Chrome
cd /c/Users/mcwiz/Projects/Aletheia/extensions/chrome
zip -r ../../dist/aletheia-chrome-vX.Y.Z.zip . -x '.*' -x '*/.*'

# Firefox
cd /c/Users/mcwiz/Projects/Aletheia/extensions/firefox
zip -r ../../dist/aletheia-firefox-vX.Y.Z.zip . -x '.*' -x '*/.*'
```

### Verify Zips

```bash
cd /c/Users/mcwiz/Projects/Aletheia
unzip -l dist/aletheia-chrome-vX.Y.Z.zip
unzip -l dist/aletheia-firefox-vX.Y.Z.zip
```

Confirm:
- Forward slashes in all paths
- 15 files (11 JS/HTML/CSS + manifest.json + 4 icons)
- No unexpected files (docs, session logs, dotfiles)

---

## Chrome Web Store

### Upload

1. Go to https://chrome.google.com/webstore/devconsole
2. Sign in as `cto@thrivetech.ai`
3. Find **Aletheia** in the extension list (or click **New Item** for first publish)
4. Click **Package** → **Upload new package**
5. Upload `dist/aletheia-chrome-vX.Y.Z.zip`
6. Wait for validation — fix any errors before proceeding

### Store Listing

Update if changed (see `docs/lld/done/10051-store-compliance.md` for full text):

| Field | Value |
|-------|-------|
| Name | Aletheia |
| Short Description | Instant AI analysis for selected text. Understand context, detect nuance, and verify facts—while maintaining strict data privacy. |
| Category | Productivity |
| Language | English |

### Privacy Tab

| Field | Value |
|-------|-------|
| Single Purpose | Context analysis of user-selected text |
| Privacy Policy URL | `https://martymcenroe.github.io/Aletheia/` |
| Handles user data? | Yes (page content — selected text only) |
| Sold to 3rd parties? | No |
| Used for unrelated purposes? | No |

### Permission Justifications

| Permission | Justification |
|------------|---------------|
| `activeTab` | Only accesses the current page when the user explicitly interacts (right-click or popup) |
| `tabs` | Required to inject content scripts and detect page navigation for overlay lifecycle |
| `scripting` | Required to execute content scripts on the active tab during analysis |
| `contextMenus` | Primary trigger interface — right-click "Explain with AI" |
| `storage` | Stores user preferences and authentication tokens locally |
| `identity` | Required for LinkedIn OAuth authentication flow |
| `notifications` | Displays analysis completion notifications |
| `host_permissions: api.aletheia.study` | API endpoint for AI analysis — the only remote server the extension communicates with |

### Pricing & Distribution

| Field | Value |
|-------|-------|
| License | PolyForm Noncommercial 1.0.0 |
| Visibility | Public |
| Regions | All regions |

### Submit

1. Click **Submit for review**
2. Chrome review typically takes 1-3 business days
3. Note the submission date in the GitHub issue

### Post-Publish Verification

After the extension is approved and live:

1. Install from the Chrome Web Store listing
2. Core flow test: select text on any page → right-click → "Explain with AI" → overlay appears
3. Auth flow test: click extension icon → Log in with LinkedIn → verify login succeeds
4. Check version number in `chrome://extensions`

---

## Firefox AMO

### Upload

1. Go to https://addons.mozilla.org/developers/
2. Sign in as `cto@thrivetech.ai`
3. Find **Aletheia** → **Manage Versions** (or **Submit a New Add-on** for first publish)
4. Click **Upload a New Version**
5. Upload `dist/aletheia-firefox-vX.Y.Z.zip`
6. AMO runs automated validation — fix any errors before proceeding

### Listing Details

| Field | Value |
|-------|-------|
| Name | Aletheia |
| Slug | `aletheia-ai` |
| Summary | Instant AI analysis for selected text. Understand context, detect nuance, and verify facts—while maintaining strict data privacy. |
| Category | Other |
| License | PolyForm Noncommercial 1.0.0 (**NOT MIT** — check this every time, it was incorrectly set to MIT previously) |
| Gecko ID | `extension@aletheia.study` |

### Source Code

AMO may ask for source code if minification is detected. Our code is NOT minified — select "No" or provide the GitHub repo link if asked: `https://github.com/martymcenroe/Aletheia`

### Submit

1. Click **Submit Version**
2. AMO review is typically fast (minutes to hours)
3. Note the submission date in the GitHub issue

### Post-Publish Verification

After the version is approved and live:

1. Check the listing: https://addons.mozilla.org/addon/aletheia-ai/
2. Verify the version number matches
3. Install/update in Firefox
4. Core flow test: select text → right-click → "Explain with AI" → overlay appears
5. Auth flow test: click extension icon → Log in with LinkedIn → verify login succeeds

---

## Version Bump Procedure

When bumping versions for a new release:

1. Create a GitHub issue for the version bump
2. Update both manifests:
   - `extensions/chrome/manifest.json` → `"version": "X.Y.Z"`
   - `extensions/firefox/manifest.json` → `"version": "X.Y.Z"`
3. Commit: `chore: bump extension versions to X.Y.Z (close #N)`
4. Then follow the build and upload steps above

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| AMO rejects zip with backslash paths | Rebuild with `zip` command, not PowerShell `Compress-Archive` |
| "Version already exists" | Bump version in manifests first |
| Chrome review rejection | Read the rejection email carefully — usually permission justification issues |
| AMO asks for source code | Link to GitHub repo — our code is not minified |
| pr-sentinel blocks version bump PR | Ensure PR body has `Closes #N` referencing an OPEN issue |
| Extension zip contains unexpected files | Check that no agent created docs/logs inside extension directories |

## Release Notes

Store release notes in `docs/releases/` with the naming convention:
- `chrome-vX.Y.Z.md` — Chrome Web Store release
- `firefox-vX.Y.Z.md` — Firefox AMO release

Each file should contain:
1. **Public-facing notes** — what users see in the store listing
2. **Reviewer notes** — what the store reviewer sees (permission justifications, testing instructions)
3. Previous version and submission date

Create the release notes file BEFORE uploading — it serves as the source of truth for what you paste into the dashboard.

## Related Documents

- `docs/releases/` — release notes archive
- `docs/lld/done/10051-store-compliance.md` — original store listing text and privacy justifications
- `docs/legal/eula.html` — End User License Agreement
- `docs/privacy.html` — Privacy Policy
