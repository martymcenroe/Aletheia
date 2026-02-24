# Implementation Report — Issue #433

**Feature:** GitHub OAuth for Admin Dashboard
**Branch:** `433-github-oauth-admin-dashboard`
**Date:** 2026-02-24

## Summary

Replaced the static API key authentication on the admin metrics dashboard with GitHub OAuth. Only collaborators on `martymcenroe/Aletheia` with push access can log in. Uses the GitHub OAuth Web Application flow with HMAC-signed CSRF state tokens.

## Files Changed

| File | Change |
|------|--------|
| `src/auth/github_oauth.py` | New — GitHub OAuth handler (authorize, callback, collaborator check, JWT issuance) |
| `tests/unit/test_github_oauth.py` | New — 25 unit tests covering state tokens, auth flow, access control |
| `src/lambda_auth_function.py` | Added routing for `/auth/github/*` and `/admin/*` static file serving |
| `static/admin/metrics.html` | Added GitHub OAuth login screen, JWT-from-URL extraction |
| `static/admin/metrics.js` | JWT handling: extract from URL, store in localStorage, strip from URL bar |
| `static/admin/metrics.css` | Login screen styles |
| `workers/aletheia-api/worker.js` | CloudFlare Worker: route `/admin/*` and `/auth/*` to Auth Lambda |
| `workers/aletheia-api/wrangler.toml` | Wrangler config for Worker deployment |
| `provision.sh` | Updated Auth Lambda packaging to include `github_oauth.py` and static assets |
| `.gitignore` | Added `.wrangler/` (CloudFlare Workers local cache) |
| `CLAUDE.md` | Removed "Hermes" codename reference |
| `docs/runbooks/10904-runbook-admin-dashboard.md` | Removed "Hermes" codename, documented OAuth flow |

## Security Considerations

- CSRF protection via HMAC-signed state tokens (5-min TTL, using JWT signing secret)
- No access tokens stored server-side — stateless flow
- Collaborator check enforces push-level access (not just read)
- HTML output uses `html.escape()` to prevent XSS in error pages
- JWT in URL is stripped immediately by client-side JS to prevent leakage via Referer/bookmarks
- GitHub credentials stored in AWS Secrets Manager, cached 5 minutes

## Deployment

- Auth Lambda repackaged with new files via `provision.sh`
- CloudFlare Worker deployed via `wrangler deploy` from `workers/aletheia-api/`
- GitHub OAuth App created: "Aletheia Admin Dashboard" at github.com/settings/developers
- Secret `aletheia/github-oauth` created in AWS Secrets Manager
