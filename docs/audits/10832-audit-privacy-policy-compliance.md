# 10817 - Audit: Privacy Policy Compliance (Adversarial)

**Audit Date:** 2026-03-12
**Auditor:** Claude Opus 4.6 (adversarial posture)
**Scope:** Privacy policy, EULA, and store listing vs. actual code behavior
**Type:** Read-only legal risk assessment

---

## Executive Summary

The published privacy policy (`docs/privacy.html`) contains **5 critical findings** where claims directly contradict what the code does, **6 high-severity omissions** that could trigger regulatory action, and **9 medium/low findings** of misleading language or incomplete disclosure. The EULA is more accurate than the privacy policy but the two documents contradict each other in key areas.

**Bottom line:** The privacy policy was written for a simpler version of Aletheia (pre-auth, single model, no payments). The product has outgrown it. A user reading only the privacy policy would have a materially incomplete picture of what data is collected, stored, and shared.

---

## Severity Definitions

| Severity | Meaning |
|----------|---------|
| **CRITICAL** | Direct contradiction between published claim and code behavior. Legal exposure. |
| **HIGH** | Material omission that a regulator or store reviewer would flag. |
| **MEDIUM** | Misleading or incomplete language that creates false impressions. |
| **LOW** | Minor discrepancy or best-practice gap. |
| **INFO** | Observation only; no action required. |

---

## Findings

### CRITICAL-01: Privacy Policy Claims "We Do Not Collect Personal Information" — Code Stores LinkedIn PII

**Policy Claim (privacy.html, line 69):**
> We do **not** collect: Personal information

**EULA Claim (eula.html, line 83):**
> We store your LinkedIn user ID, display name, email, and profile picture

**Code Reality (`lambda_auth_function.py`, lines 385-396):**
```python
item = {
    "user_id": user_info["sub"],        # LinkedIn stable member ID
    "display_name": display_name,        # Full name
    "email": user_info.get("email"),     # Email address
    "picture": user_info.get("picture"), # Profile picture URL
    "created_at": now,
    "last_login": now,
}
```

**Stored in:** `aletheia-users` DynamoDB table, **no TTL** (indefinite retention).

**Verdict:** The privacy policy and EULA directly contradict each other. The privacy policy says "no personal information." The EULA correctly discloses LinkedIn PII collection. The code confirms the EULA is accurate. A user reading only the privacy policy — which is what the Chrome Web Store links to — would be misled.

---

### CRITICAL-02: Privacy Policy Lists 3 Permissions — Code Uses 6-7

**Policy Claim (privacy.html, lines 85-91):**
> - **ActiveTab:** Access only the current tab
> - **ContextMenus:** Add "Explain with AI" to your right-click menu
> - **Storage:** Save your preferences locally

**Chrome `manifest.json` (lines 7-14):**
```json
"permissions": [
    "activeTab", "tabs", "scripting",
    "contextMenus", "storage",
    "identity", "notifications"
]
```

**Firefox `manifest.json` (lines 6-11):**
```json
"permissions": [
    "activeTab", "tabs", "scripting",
    "contextMenus", "storage"
]
```

**Undisclosed permissions:**

| Permission | Present In | What It Does | Privacy Impact |
|------------|-----------|--------------|----------------|
| `tabs` | Chrome + Firefox | Query tab URLs/titles | Can read any tab's URL |
| `scripting` | Chrome + Firefox | Inject JS into pages | Can execute code on active tab |
| `identity` | Chrome only | OAuth via `launchWebAuthFlow` | Enables LinkedIn auth flow |
| `notifications` | Chrome only | Desktop notifications | Can show system-level alerts |

**Also undisclosed:** `host_permissions: ["https://api.aletheia.study/*"]` — grants persistent network access to the API endpoint without per-request user action.

**Verdict:** The privacy policy discloses less than half the actual permissions. `scripting` is particularly significant — it allows arbitrary JavaScript execution on pages. While gated behind `activeTab`, a store reviewer would expect this disclosed.

---

### CRITICAL-03: GDPR Erasure Endpoint (DELETE /my-data) Does Not Delete All User Data

**Policy Claim (privacy.html, lines 96-100):**
> You have the right to: Request deletion of your data at any time
> Data is also automatically purged after 30 days.

**Code Reality (`lambda_auth_function.py`, lines 792-839):**
The `handle_delete_my_data()` function queries `AletheiaAgentState` via the `user_id-index` GSI and deletes matching analysis records.

**What IS deleted:**
- Analysis records (selected text, AI responses, domContext) from `AletheiaAgentState`

**What is NOT deleted:**
- `aletheia-users` record: display_name, email, picture, created_at, last_login
- `aletheia-users` billing fields: stripe_customer_id, stripe_subscription_id, tier, grace_period_end
- `aletheia-token-cap` counters: USER#{user_id} rate limit records (though these have TTL)
- `aletheia-coupons` redeemed_by sets: user_id permanently linked to coupon

**Verdict:** GDPR Article 17 requires erasure of "all personal data." The endpoint only erases analysis history. A user's name, email, profile picture, and payment identifiers persist indefinitely. The privacy policy's blanket "deletion of your data" claim is not fulfilled by the code.

---

### CRITICAL-04: Privacy Policy Says "Amazon Nova AI" — Code Uses Three AI Providers

**Policy Claim (privacy.html, line 74):**
> Your text is analyzed using AWS Bedrock (Amazon Nova AI).

**Code Reality (`etymologist.py`, `provision.sh` lines 384-402):**
Three Application Inference Profiles are provisioned:
- `aletheia-nova-micro` — Amazon Nova Micro
- `aletheia-haiku` — **Anthropic Claude Haiku 4.5**
- `aletheia-opus` — **Anthropic Claude Opus 4.6**

The deep poetic analysis feature (overlay.js, "Explore Deeper Meaning" button) invokes Opus 4.6 specifically. The standard analysis can use Haiku or Nova depending on routing.

**Verdict:** Anthropic is an undisclosed third-party AI provider. User text is sent to Anthropic's models via Bedrock. While Bedrock's no-training guarantee covers all models hosted on it, the privacy policy names only "Amazon Nova AI" — a user would not know their text is being processed by Anthropic's Claude models. This is a material omission for both GDPR transparency requirements and Chrome Web Store disclosure.

---

### CRITICAL-05: Privacy Policy and EULA Directly Contradict on Personal Data

**Privacy Policy (privacy.html, line 69):**
> We do **not** collect: Personal information

**EULA (eula.html, line 83):**
> We store your LinkedIn user ID, display name, email, and profile picture

**EULA (eula.md, line 47):**
> We store your LinkedIn user ID, display name, email address, and profile picture URL as described in our Privacy Policy.

The EULA explicitly says "as described in our Privacy Policy" — but the Privacy Policy says the opposite. A user who reads both documents encounters an irreconcilable contradiction.

**Verdict:** One of these documents is wrong. The EULA is accurate; the privacy policy is not. This creates legal ambiguity about what a user actually consented to.

---

### HIGH-01: Third-Party Services List Is Incomplete

**Policy Claim (privacy.html, lines 103-108):**
> We use the following third-party services:
> - **AWS Bedrock:** AI processing
> - **AWS DynamoDB:** Temporary data storage
> We do not use analytics, advertising networks, or tracking services.

**Actual third-party services the code communicates with or sends data to:**

| Service | Data Shared | Disclosed? |
|---------|-------------|-----------|
| AWS Bedrock | User text, domContext | Partially (model wrong) |
| AWS DynamoDB | All stored data | Yes |
| **LinkedIn** | OAuth credentials, receives user PII | **No** |
| **Stripe** | Customer ID, email (pre-fill), subscription data | **No** |
| **CloudFlare** | All request/response traffic (proxy) | **No** |
| **Anthropic (via Bedrock)** | User text for Claude model processing | **No** |
| AWS Secrets Manager | Internal (credentials) | No (acceptable) |
| AWS CloudWatch | Operational logs + custom metrics | No (acceptable) |
| AWS X-Ray | 5% sampled traces (no PII) | No (acceptable) |
| **GitHub** | OAuth for admin dashboard | **No** |

**Verdict:** LinkedIn, Stripe, CloudFlare, and Anthropic are material third parties that handle or proxy user data. Their omission is a significant disclosure gap.

---

### HIGH-02: User Profile Data Has No Retention Period

**Policy Claim (privacy.html, line 82):**
> Submitted text is stored for **30 days** to enable features like conversation history, then automatically deleted.

**Code Reality:**

| Data | Table | TTL | Retention |
|------|-------|-----|-----------|
| Analysis text/response | AletheiaAgentState | 30 days | Auto-deleted |
| User profile (name, email, picture) | aletheia-users | **None** | **Indefinite** |
| Stripe customer/subscription IDs | aletheia-users | **None** | **Indefinite** |
| Coupon redemption audit trail | aletheia-coupons | **None** | **Indefinite** |
| Rate limit counters | aletheia-token-cap | 2hr-35d | Auto-deleted |

The 30-day claim applies only to analysis data. LinkedIn profile data, billing data, and coupon audit trails are stored forever.

**Verdict:** The privacy policy creates the impression that ALL data expires in 30 days. User profile data has no retention limit and no documented retention policy.

---

### HIGH-03: Full Article Analysis Not Disclosed

**Policy Claim (privacy.html, lines 58-61):**
> When you select text and choose "Explain with AI", the following is sent:
> - The text you select
> - The surrounding text
> - The page URL

**Code Reality (popup.js, lines 486-523; article-extractor.js):**
The "Analyze Full Page" button extracts up to 10,000 characters of the entire article content — not selected text. This is:
1. Extracted from `<article>`, `<main>`, or `<body>` tags
2. PII-scrubbed (emails and phone numbers redacted)
3. Sent in a `full_article` field to the API

**Verdict:** Full article analysis sends far more than "the text you select." A user who only reads the privacy policy would not expect the extension to extract and transmit entire page content. The PII scrubbing is good practice but also undisclosed.

---

### HIGH-04: Page Title Collected but Not Disclosed

**Policy Claim (privacy.html, lines 59-61):**
Listed: selected text, surrounding text, page URL.

**Code Reality (service-worker.js, lines 557-562):**
```javascript
payload = {
    text: info.selectionText,
    url: info.pageUrl,
    title: tab.title,           // NOT DISCLOSED
    domContext: context,
    signals: { noarchive: ... } // NOT DISCLOSED
}
```

**Verdict:** Page title is sent on every analysis request. The `noarchive` meta tag signal is also sent. Neither is disclosed. Page title alone can reveal sensitive information (e.g., medical condition pages, financial account names).

---

### HIGH-05: Stripe Payment Processing Not Mentioned in Privacy Policy

**EULA (eula.md, lines 57-58):**
> Paid subscriptions are billed monthly via Stripe. By subscribing, you agree to Stripe's Terms of Service.

**Privacy Policy:** No mention of Stripe anywhere.

**Code Reality (stripe_handler.py, stripe_events.py):**
- Stripe customer ID and subscription ID stored in `aletheia-users`
- User email pre-filled in Stripe checkout session
- Webhook events processed: checkout.session.completed, invoice.paid, invoice.payment_failed, customer.subscription.deleted
- Processed event IDs stored indefinitely for idempotency

**Verdict:** Stripe handles payment card data (PCI-compliant) and receives the user's email for checkout. This is a material third-party data sharing that the privacy policy does not disclose.

---

### HIGH-06: Data Portability Right Claimed but No Export Endpoint Exists

**Policy Claim (privacy.html, line 98):**
> You have the right to: Data portability

**Code Reality:** No GET /my-data, export, or download endpoint exists anywhere in the codebase. The only data endpoint is DELETE /my-data (which itself is incomplete per CRITICAL-03).

**Verdict:** Claiming a GDPR right that cannot be exercised is worse than not claiming it. There is no technical mechanism for a user to obtain a copy of their data.

---

### MEDIUM-01: "We Do Not Use Analytics" Is Misleading

**Policy Claim (privacy.html, line 108):**
> We do not use analytics, advertising networks, or tracking services.

**Code Reality (observability.py):**
- CloudWatch custom metrics: `RequestCount`, `CapUtilization`, `CapDenied`, `BedrockCostEstimate`, `ErrorRate`, `Latency` — all with tier/model dimensions
- X-Ray distributed tracing at 5% sampling rate
- Structured JSON logging with user_id (anonymized hash), request mode, latency breakdown

These are **operational** metrics, not user analytics or tracking. No user behavior is profiled. But the blanket "no analytics" claim is technically incorrect — the system does analyze usage patterns in aggregate.

**Verdict:** The claim is defensible but could be challenged. A more accurate statement would be "We do not use user analytics, advertising, or tracking. We collect anonymous operational metrics for service reliability."

---

### MEDIUM-02: Store Listing Overstates Permission Minimalism

**Store Listing (10051-store-compliance.md, lines 46-47):**
> **Privacy by Design:** We use the "ActiveTab" permission model. We cannot see your browsing history. We only see the specific text you explicitly select and submit.

**Actual Permissions:** 6-7 permissions including `tabs` (can query any tab's URL), `scripting` (can inject JS), `identity` (Chrome OAuth), `notifications`.

**Verdict:** The listing implies only `activeTab` is used. "We cannot see your browsing history" is technically true (no `history` permission), but the `tabs` permission can query open tab URLs. The store listing should accurately reflect the full permission set.

---

### MEDIUM-03: Privacy Policy Contact Differs from EULA Contact

**Privacy Policy (privacy.html, line 118):**
> Email: support@aletheia.study

**EULA (eula.html, line 130):**
> Email: cto@thrivetech.ai

**Verdict:** A user exercising GDPR rights might contact the wrong entity. The privacy policy lists a different email than the EULA. If `support@aletheia.study` is not monitored, GDPR subject access requests could be missed.

---

### MEDIUM-04: Browser Local Storage Contents Not Disclosed

**Policy Claim (privacy.html, line 89):**
> **Storage:** Save your preferences locally

**Code Reality (auth.js, popup.js):**
`chrome.storage.local` / `browser.storage.local` stores:
- `refreshToken` — OAuth refresh token (long-lived credential)
- `userId` — LinkedIn member ID (persistent identifier)
- `displayName` — User's full name
- `allowlist` — Array of enabled domains

`chrome.storage.session` / `browser.storage.session` stores:
- `jwt` — JSON Web Token
- `accessToken` — LinkedIn access token
- `expiresAt` — Token expiry timestamp
- Diagnostic data (HTTP status, latency, timestamps)

**Verdict:** "Save your preferences" drastically understates what's stored locally. Persistent identifiers, auth tokens, and usage diagnostics go beyond "preferences." GDPR requires disclosure of persistent identifiers stored on user devices.

---

### MEDIUM-05: LinkedIn OAuth Scopes Not Disclosed

**Code Reality (auth.js, line ~244):**
LinkedIn OAuth requests scopes: `openid profile`

The `openid` scope returns the `sub` claim (stable ID). The `profile` scope returns name, email, and picture. Users see LinkedIn's consent screen but the privacy policy doesn't explain what data is obtained from LinkedIn or why.

**Verdict:** Best practice is to disclose which OAuth scopes are requested and what data they return. The EULA partially covers this; the privacy policy does not.

---

### MEDIUM-06: Coupon Redemption Creates Permanent User-Coupon Link

**Code Reality (coupon_handler.py, lines 209):**
When a user redeems a coupon, their `user_id` is added to the coupon's `redeemed_by` set (a DynamoDB String Set). This set has no TTL.

**Not disclosed:** The coupon table permanently records which users redeemed which coupons. This is an audit trail that creates a permanent association between user identity and promotional activity.

---

### MEDIUM-07: EULA Claims "Only Text You Explicitly Select" — Full Page Feature Contradicts

**EULA (eula.md, line 82):**
> We only process text you explicitly select and submit

**Code Reality:** The "Analyze Full Page" button processes up to 10,000 characters of page content that the user did not select — it's algorithmically extracted from the DOM.

**Verdict:** While the user explicitly clicks the button, the data processed is not "text you explicitly select." The EULA language should distinguish between selection-based and page-based analysis.

---

### LOW-01: Prior Privacy Audit (10810) Contains Stale Claims

**10810-audit-privacy.md, Section 2, Data Inventory:**
Several rows claim "In-memory only" or "No persistent data" for data that is now stored in DynamoDB with 30-day TTL. The audit was partially updated but the Data Subject Rights table (lines 68-73) still claims "No PII stored" and "No persistent user data."

**Verdict:** The prior audit should be marked as superseded by this one. Stale audit documents create false assurance.

---

### LOW-02: GitHub OAuth for Admin Not Disclosed

**Code Reality (github_oauth.py):**
Admin users authenticate via GitHub OAuth. GitHub user ID and login are used to issue admin-tier JWTs. GitHub profile data is not persisted to DynamoDB (JWT only, 24h expiry).

**Verdict:** Low risk since GitHub OAuth is admin-only and data isn't persisted. But it's an undisclosed authentication pathway that processes third-party identity data.

---

### INFO-01: PII Scrubbing in Article Extractor Is Good Practice

**Code Reality (article-extractor.js, lines 57-63):**
Email addresses and phone numbers are redacted (`[email redacted]`, `[phone redacted]`) before full article content is transmitted.

**Verdict:** This is a positive privacy measure. Consider disclosing it in the privacy policy as a trust signal. Users should know their content is being sanitized before transmission.

---

### INFO-02: X-Ray Tracing Correctly Bans PII

**Code Reality (observability.py, lines 116-120):**
Explicit STRICT BAN on logging prompt text, completion text, user input, or URLs in X-Ray traces. Only safe metadata (token counts, latency, model ID) is recorded.

**Verdict:** Well-implemented. No action required.

---

### INFO-03: Session Storage Correctly Scoped

**Code Reality:** Access tokens and JWTs are stored in session storage (cleared on browser close). Only refresh tokens and user IDs persist in local storage.

**Verdict:** Good security practice. Token lifecycle is appropriate.

---

## Summary Table

| ID | Severity | Finding | Policy Says | Code Does |
|----|----------|---------|-------------|-----------|
| CRITICAL-01 | Critical | PII collection denied | "We do not collect personal information" | Stores LinkedIn name, email, picture indefinitely |
| CRITICAL-02 | Critical | Permissions understated | Lists 3 permissions | Uses 6-7 permissions |
| CRITICAL-03 | Critical | GDPR erasure incomplete | "Request deletion of your data" | Only deletes analysis records, not profile/billing |
| CRITICAL-04 | Critical | AI provider misidentified | "Amazon Nova AI" | Also uses Anthropic Claude Haiku 4.5 + Opus 4.6 |
| CRITICAL-05 | Critical | Policy-EULA contradiction | Policy: no PII; EULA: stores PII | EULA is correct, policy is wrong |
| HIGH-01 | High | Third parties omitted | Lists AWS only | Also LinkedIn, Stripe, CloudFlare, Anthropic, GitHub |
| HIGH-02 | High | Retention gaps | "30 days then deleted" | User profiles stored indefinitely |
| HIGH-03 | High | Full article undisclosed | "Text you select" | Full page content (10K chars) also sent |
| HIGH-04 | High | Page title undisclosed | Lists text, context, URL | Also sends page title + meta signals |
| HIGH-05 | High | Stripe undisclosed | No mention | Stores Stripe customer/subscription IDs |
| HIGH-06 | High | Portability unimplemented | "Data portability" right | No export endpoint exists |
| MEDIUM-01 | Medium | "No analytics" misleading | "No analytics" | Has CloudWatch metrics + X-Ray tracing |
| MEDIUM-02 | Medium | Store listing overstated | "ActiveTab permission model" | 6-7 permissions beyond activeTab |
| MEDIUM-03 | Medium | Contact mismatch | support@aletheia.study | EULA says cto@thrivetech.ai |
| MEDIUM-04 | Medium | Local storage understated | "Save preferences" | Stores auth tokens, user IDs, diagnostics |
| MEDIUM-05 | Medium | OAuth scopes undisclosed | Not mentioned | Requests openid + profile scopes |
| MEDIUM-06 | Medium | Coupon audit trail | Not disclosed | Permanent user-coupon association |
| MEDIUM-07 | Medium | EULA contradicts full page | "Text you explicitly select" | Full page extracts unselected content |
| LOW-01 | Low | Stale prior audit | "No PII stored" | PII stored since auth implementation |
| LOW-02 | Low | GitHub admin OAuth | Not mentioned | Admin auth via GitHub (JWT only) |

---

## Sources Reviewed

| Source | Path | Purpose |
|--------|------|---------|
| Privacy Policy | `docs/privacy.html` | Published privacy claims |
| EULA (HTML) | `docs/legal/eula.html` | Published terms of service |
| EULA (Markdown) | `docs/legal/eula.md` | Source-of-truth EULA |
| Store Listing | `docs/lld/done/10051-store-compliance.md` | Chrome Web Store submission text |
| Permission ADR | `docs/adrs/10201-ADR-privacy-first-permissions.md` | Permission design rationale |
| Prior Audit | `docs/audits/10810-audit-privacy.md` | Previous privacy audit |
| Chrome manifest | `extensions/chrome/manifest.json` | Chrome permission declarations |
| Chrome service worker | `extensions/chrome/service-worker.js` | Background data flow |
| Chrome auth | `extensions/chrome/auth.js` | OAuth implementation |
| Chrome popup | `extensions/chrome/popup.js` | UI data collection |
| Chrome overlay | `extensions/chrome/overlay.js` | Result display + deep analysis |
| Chrome article extractor | `extensions/chrome/article-extractor.js` | Full page extraction + PII scrub |
| Chrome content check | `extensions/chrome/content-check.js` | Age gate meta tag detection |
| Firefox manifest | `extensions/firefox/manifest.json` | Firefox permission declarations |
| Firefox service worker | `extensions/firefox/service-worker.js` | Background data flow |
| Firefox auth | `extensions/firefox/auth.js` | OAuth implementation |
| Firefox popup | `extensions/firefox/popup.js` | UI data collection |
| Firefox overlay | `extensions/firefox/overlay.js` | Result display |
| Firefox article extractor | `extensions/firefox/article-extractor.js` | Full page extraction |
| Agent Lambda | `src/lambda_function.py` | Main analysis backend |
| Auth Lambda | `src/lambda_auth_function.py` | Authentication + GDPR endpoint |
| Etymologist | `src/etymologist.py` | AI model invocation |
| Observability | `src/observability.py` | Metrics + tracing |
| Rate Limiter | `src/auth/rate_limit.py` | Tier-based rate limiting |
| Token Cap | `src/auth/token_cap_service.py` | Usage counter storage |
| Coupon Handler | `src/auth/coupon_handler.py` | Coupon redemption + audit |
| Stripe Handler | `src/auth/stripe_handler.py` | Payment integration |
| Stripe Events | `src/auth/stripe_events.py` | Webhook event processing |
| JWT Service | `src/auth/jwt_service.py` | Token signing |
| Auth Middleware | `src/auth/auth_middleware.py` | Request authentication |
| GitHub OAuth | `src/auth/github_oauth.py` | Admin authentication |
| Provision Script | `provision.sh` | Infrastructure definitions |

---

## Methodology

This audit was conducted adversarially: every claim in the privacy policy, EULA, and store listing was cross-referenced against the actual extension and backend source code. The auditor assumed the posture of a hostile regulator or store reviewer looking for discrepancies.

**Not in scope:** Whether the data practices themselves are problematic — only whether they are accurately disclosed.

---

*Audit complete. No code or wiki changes made.*
