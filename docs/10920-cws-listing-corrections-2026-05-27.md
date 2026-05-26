# 10920 — CWS / AMO Listing Corrections (one-time, 2026-05-27)

## Purpose

One-time corrections to the Chrome Web Store and Firefox AMO dashboard submissions, prompted by the 2026-05-26 adversarial privacy audit (Aletheia#670, #671, #672). The repo-side fixes are committed in **PR closing #670 #671 #672**. Two correction surfaces are operator-only because they live in the dashboards, not the repo.

After all items below are completed, this document can be archived or deleted.

## Why these aren't in the repo PR

The CWS and AMO dashboards each hold three pieces of text/config submitted at listing time:

1. **Store listing → Long Description** (the marketing text shown on the public install page)
2. **Privacy practices → Privacy Policy URL** field
3. **Privacy practices → Permission Justification** fields (per-permission free-text)

Editing the repo source (the LLD at `docs/lld/done/10051-store-compliance.md` and the policy at `docs/privacy.html`) does NOT push to the dashboards. They must be edited manually via the dashboards.

## Access pattern (from memory `user-cws-dashboard-access`)

1. Open your dedicated Chrome profile pre-loaded with `cto@thrivetech.ai`
2. Click the first bookmark in the bookmark bar — Chrome Web Store developer dashboard
3. Authenticate with the saved password
4. Approve the Google Authenticator 2FA prompt on your phone
5. Select the Aletheia item

For AMO: account is also `cto@thrivetech.ai` (forwards to `cto.thrivetech.ai@gmail.com`). Dashboard at https://addons.mozilla.org/developers/. Likely a similar profile/bookmark setup but NOT confirmed — start by checking your Chrome profile's bookmarks.

---

## CWS corrections

### 1. Long Description — remove the false "cannot see browsing history" claim

**Dashboard:** Store listing tab → Listing details → Description (the long-form marketing text)

**Find this paragraph:**

> **Privacy by Design:** We use the "ActiveTab" permission model. We cannot see your browsing history. We only see the specific text you explicitly select and submit.

**Replace with:**

> **Privacy by Design:** We do not enumerate, retain, transmit, or analyze data from tabs other than the one you explicitly invoke Aletheia on. We only see the specific text you explicitly select and submit.

**Why:** The manifest's `tabs` permission technically grants the capability to enumerate other tabs. Claiming "we cannot" is factually wrong. The replacement makes a verifiable behavioral commitment ("we do not") rather than denying a capability that's been granted.

**Verification after save:** Open the public listing in incognito → confirm the paragraph reads the new text.

---

### 2. Privacy practices — fix the Privacy Policy URL

**Dashboard:** Privacy practices tab → Privacy Policy URL field

**Current expected value:** `https://martymcenroe.github.io/Aletheia/` (per stale LLD)

**Change to:** `https://aletheia.study/privacy.html`

**Why:** The policy is hosted at aletheia.study (GitHub Pages); the github.io URL may 404 or serve stale content.

**Verification after save:** Click the "Privacy Policy" link on the public listing in incognito → must load `https://aletheia.study/privacy.html` and show the current policy (no "automatically redacted" claim, no "cannot access browsing history" sentence).

---

### 3. Privacy practices — expand Permission Justification to cover all 7 permissions

**Dashboard:** Privacy practices tab → Permission Justification(s) (one field per permission)

**Current state (per LLD 10051 before today's correction):** Only `activeTab`, `scripting`, `contextMenus` were declared with justifications.

**Manifest actually requests 7 permissions** (`extensions/chrome/manifest.json:7-15`):
- `activeTab` ✓ (declared)
- `tabs` ❌ (not declared)
- `scripting` ✓ (declared)
- `contextMenus` ✓ (declared)
- `storage` ❌ (not declared)
- `identity` ❌ (not declared)
- `notifications` ❌ (not declared)

**Add the missing four justifications:**

- **`tabs`:** Detect page navigation for overlay lifecycle management and content script injection. Also used for OAuth callback detection. The extension does NOT enumerate other tabs.
- **`storage`:** Save preferences, authentication tokens, and domain allowlist locally on the user's device.
- **`identity`:** Required for the LinkedIn OAuth authentication flow.
- **`notifications`:** Display analysis completion notifications.

**Why:** CWS requires justifications for ALL declared permissions, not just the most-used. Submitting with missing justifications is a policy violation; the listing was likely waved through because the reviewer didn't catch the gap, but a future reviewer or an outside investigator would.

**Verification after save:** All seven permission entries should have a justification visible in the Privacy practices view.

---

## AMO corrections (parallel pass)

Likely the same three classes of issue exist on the AMO listing. Verify and apply the same fixes:

1. **AMO listing summary / description** — search for "cannot see your browsing history" and replace with the same updated wording as CWS #1 above.
2. **AMO privacy policy URL** — confirm it's `https://aletheia.study/privacy.html`, not the stale github.io URL.
3. **AMO permission disclosures** — Firefox manifest has the same 7 permissions; if AMO requires per-permission justifications, apply the same four additional justifications.

AMO publishes Firefox extension v1.1.2 already; verify nothing in the public listing carries the old false claims.

---

## Closing checklist

After all CWS items are saved:

- [ ] Public CWS listing in incognito shows the new "do not enumerate" wording (NOT "cannot see")
- [ ] Public CWS listing's "Privacy Policy" link resolves to `https://aletheia.study/privacy.html`
- [ ] CWS Privacy practices shows justifications for all 7 permissions

After all AMO items are saved:

- [ ] Public AMO listing in private browsing shows the new wording (or never had the bad wording)
- [ ] AMO Privacy Policy URL resolves correctly
- [ ] AMO permission disclosures cover all 7 manifest permissions

Then this document can be deleted (or moved to `docs/legacy/` if you want a historical record of the corrections).

## Related

- Repo-side fixes: PR closing #670, #671, #672 (this companion doc).
- Original adversarial audit findings: 2026-05-26 (the day before this doc's intended use).
- Privacy policy now-live (`docs/privacy.html` post-PR #663): no "cannot access browsing history" sentence; no unconditional redaction claim; "Rate limit counters expire automatically within 7 days" (corrected by this PR).
- Operator memory: `user-cws-dashboard-access` for the login pattern.
