# Firefox AMO — v1.1.1

**Previous store version:** 1.1
**Submission date:** 2026-03-06

---

## Public-Facing Notes

- Fixed: popup no longer displays literal "pending" text during OAuth flow
- Auth routing through custom domain (api.aletheia.study) for all auth endpoints
- Security: rotated internal API URLs, removed exposed URLs from code comments

---

## Reviewer Notes

Bug fix release. Three changes:

1. `popup.js` — `handleLoginClick()` now closes the popup on a pending OAuth response instead of displaying the raw "pending" string
2. `auth.js` — auth endpoint URL updated to route through custom domain
3. `service-worker.js` — removed hardcoded Lambda URL from comments (security hygiene)

No permission changes from v1.1.
