# Implementation Report: Issue #116 - LinkedIn OAuth Authentication

**Issue:** #116
**Title:** feat: Authenticate users via LinkedIn OAuth
**Completed:** 2026-01-06
**Report Generated:** 2026-01-06 (retroactive)

---

## 1. Summary

Implemented LinkedIn OAuth 2.0 authentication to gate extension features and establish user identity. Uses Chrome's `chrome.identity.launchWebAuthFlow` for a compliant OAuth flow with CSRF protection.

## 2. What Was Built

### 2.1 Backend Components

**`src/lambda_auth_function.py`** - Auth Lambda (438 lines)
- Token exchange: Authorization code → access/refresh tokens
- Token refresh: Refresh token → new access token
- Token validation: Verify access token against LinkedIn
- User management: Create/update users in DynamoDB

**Endpoints:**
| Route | Method | Purpose |
|-------|--------|---------|
| `/auth/token` | POST | Exchange auth code for tokens |
| `/auth/refresh` | POST | Refresh access token |
| `/auth/validate` | GET | Validate Bearer token |

### 2.2 Extension Components

**`extensions/chrome/auth.js`** (351 lines)
- OAuth flow initiation with CSRF state
- Token storage hierarchy (session vs local)
- Lazy token refresh
- Mock mode for testing

**Token Storage Hierarchy:**
| Token | Storage | Persistence |
|-------|---------|-------------|
| Access Token | `chrome.storage.session` | Cleared on browser close |
| Refresh Token | `chrome.storage.local` | Persists |
| User Info | `chrome.storage.local` | Persists |

### 2.3 Infrastructure

**DynamoDB Table:** `aletheia-users`
- Primary Key: `user_id` (LinkedIn OIDC `sub` claim)
- Attributes: `display_name`, `created_at`, `last_login`

**Secrets Manager:** `aletheia/linkedin-oauth`
- Stores `client_id` and `client_secret`

## 3. Key Design Decisions

### 3.1 User Identity Strategy
**Decision:** Use LinkedIn OIDC `sub` claim as primary key.
**Rationale:** Stable, immutable identifier that doesn't require additional API permissions. The vanity URL requires `r_basicprofile` (restricted permission).

### 3.2 Token Storage Separation
**Decision:** Access token in session storage, refresh token in local storage.
**Rationale:** Follows security best practices - access tokens are short-lived and shouldn't persist across browser sessions.

### 3.3 CSRF Protection
**Decision:** Cryptographically secure state parameter.
**Rationale:** Required by OAuth 2.0 security best practices. Uses `crypto.getRandomValues()` for 64-character hex state.

## 4. Files Changed

| File | Change Type | Lines |
|------|-------------|-------|
| `src/lambda_auth_function.py` | Created | 438 |
| `extensions/chrome/auth.js` | Created | 351 |
| `extensions/chrome/popup.js` | Modified | +50 (login/logout UI) |
| `extensions/chrome/popup.html` | Modified | +20 (login button) |
| `provision.sh` | Modified | +30 (Users table, auth Lambda) |
| `docs/1116-linkedin-oauth.md` | Created | LLD |

## 5. Security Considerations

1. **CSRF Protection:** State parameter validated on callback
2. **Token Security:** Access tokens in session storage only
3. **Credential Storage:** Client secret in AWS Secrets Manager
4. **Client ID:** Public value (safe to include in extension code)
5. **Scope Minimization:** Only `openid profile` requested

## 6. Known Limitations

1. **Refresh Token:** LinkedIn may not provide refresh tokens for all apps (depends on approval status)
2. **No Vanity URL:** Would require restricted `r_basicprofile` permission
3. **No Email:** Not requested to minimize data collection

## 7. References

- LLD: `docs/1116-linkedin-oauth.md`
- LinkedIn OAuth Docs: https://learn.microsoft.com/en-us/linkedin/shared/authentication/
- Chrome Identity API: https://developer.chrome.com/docs/extensions/reference/identity/
