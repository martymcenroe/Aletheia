# Implementation Report: #926

**Issue:** [#926](https://github.com/martymcenroe/Aletheia/issues/926), runbook 10907: add the unlisted signing path and fix what #925 will hit
**Type:** Documentation only. No code, configuration or infrastructure changes.

## Changes

| File | Change |
|---|---|
| `docs/runbooks/10907-runbook-amo-publish.md` | 2.0.0 → 2.1.0. Deployment state names `1.1.3` as pending and `1.1.2` as skipped. §2 says a number spent by an unlisted upload is taken for the listing. §6 gains the distribution-channel step. New §15, unlisted signing, with a URL or path, a click, a success sign and a failure path on every operator step. §11j and §11l carry review warnings citing `extensions/firefox/auth.js:92`, `:111` and `src/auth/refresh_token_service.py`; their paste-ready text is unchanged. §11.smoke-test signs in first, enables the site, and adds a restart check. Troubleshooting gains four rows. Troubleshooting, Related documents and Change log move to §16, §17 and §18. |
| `docs/runbooks/10905-runbook-cws-publish.md` | Its pointer to 10907's version-bump section read §16 and now reads §13. |

## Facts checked before writing

- AMO public versions: 1.0, 1.1, 1.1.1 (AMO API, 2026-10-23).
- `dist/aletheia-firefox-v1.1.3.zip`: 14 entries, forward slashes, matching §4. No file under `extensions/` has changed on `main` since the zip was built.
- 1.1.3 keeps `aletheiaRefreshToken` in `storage.local` (`extensions/firefox/auth.js:111`), and the JWT and LinkedIn access token in `storage.session` (`:92`).
- Mozilla documents that version numbers are unique across the listed and unlisted channels, and that an "On your own" upload is signed and offered as a `.xpi` download.

## Not changed

The §11j and §11l paste-ready text is public listing copy, so its wording is the operator's to approve (see #875). This change only flags it.
