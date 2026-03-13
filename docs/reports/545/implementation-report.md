# Implementation Report — Issues #545-#552

**Issues:** Privacy policy remediation (audit 10817 findings C1, C2, C4, C5, H1-H6)
**Date:** 2026-03-13

## Changes

Single file changed: `docs/privacy.html`

### Section 1 — What We Collect (fixes #545 C1+C5, #549 H3, #550 H4)
- Removed false "We do not collect: Personal information" claim
- Added **Account Data** subsection: LinkedIn user ID, display name, email, profile picture
- Added **Full Page Analysis** subsection: 10K char extraction, PII scrubbing disclosure
- Added page title and noarchive metadata signals to selection-based analysis list
- Added **Payment Data** subsection: Stripe customer/subscription IDs
- Added **Local Storage** subsection: auth tokens, user ID, allowlist

### Section 2 — How We Process Your Data (fixes #547 C4)
- Named all three AI models: Amazon Nova Micro, Anthropic Claude Haiku 4.5, Anthropic Claude Opus 4.6
- Disclosed Anthropic as AI provider
- Noted Bedrock no-training guarantee covers all models

### Section 3 — Data Retention (fixes #552 H2)
- Scoped "30 days" to analysis data only
- Added: account data retained until deletion/erasure request
- Added: rate limit counters expire automatically

### Section 4 — Browser Permissions (fixes #546 C2)
- Listed all 7 Chrome permissions and 5 Firefox permissions with justifications
- Split into All Browsers / Chrome Only / Remote Server Access subsections
- Disclosed host_permissions (api.aletheia.study)

### Section 5 — Your Rights (fixes #551 H5+H6)
- Removed data portability claim (no meaningful portable data exists)
- Kept erasure and access rights
- Documented that DELETE /my-data removes from all systems including billing

### Section 6 — Third-Party Services (fixes #548 H1, #551 H5)
- Added LinkedIn (OAuth + profile data)
- Added Stripe (payment processing)
- Added CloudFlare (traffic proxy)
- Updated AWS Bedrock to mention Anthropic Claude models
- Clarified DynamoDB stores accounts/rate limits/coupons, not just "temporary data"
- Changed "no analytics" to accurate "no user analytics; anonymous operational metrics for reliability"
