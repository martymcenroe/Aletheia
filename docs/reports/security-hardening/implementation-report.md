# Implementation Report: Security Audit Remediations

**Issues:** #436, #438, #439, #440
**Branch:** `security-hardening-audit-remediations`
**Audit Source:** `docs/audits/10809-audit-security.md` (2026-02-24)

## Changes

### C-1: Vendor Chart.js Locally (#436)

- **File:** `static/admin/metrics.html`
- **Change:** Replaced CDN `<script>` tag (`cdn.jsdelivr.net/npm/chart.js@4.4.0`) with local `<script src="chart.umd.min.js">`
- **New file:** `static/admin/chart.umd.min.js` (205 KB, Chart.js 4.4.0 UMD bundle)
- **Rationale:** Eliminates third-party CDN dependency for admin dashboard, prevents supply-chain risk

### M-1: Remove python-jose (#438)

- **File:** `provision.sh` (lines 385-386, 408)
- **Change:** Removed `python-jose` from `pip install` command and layer description
- **Verification:** `grep -r "jose" src/` returns no results — no code imports python-jose
- **Rationale:** python-jose is unmaintained and has known CVEs. Project uses PyJWT exclusively.

### H-2: Restrict CORS AllowOrigins (#439)

- **File:** `provision.sh` (lines 538, 559)
- **Change:** `AllowOrigins=['*']` → `AllowOrigins=['https://api.aletheia.study']` on both Agent and Auth Lambda Function URLs
- **Rationale:** All traffic routes through CloudFlare Worker (server-side, no browser CORS needed). Admin dashboard is same-origin. Extension goes through Worker. Direct Lambda URL access blocked by origin secret.

### H-3/H-4: Scope IAM Permissions (#440)

- **File:** `provision.sh` (lines 309-325)
- **Bedrock (H-3):** `"Resource": "*"` → specific model ARNs (`anthropic.claude-3-haiku-20240307-v1:0`, `amazon.nova-micro-v1:0`)
- **DynamoDB (H-4):** `arn:aws:dynamodb:*:*:` → `arn:aws:dynamodb:us-east-1:383687041805:` across all 6 resource ARNs
- **Rationale:** Least-privilege principle. Lambda only needs access to 2 specific models and 4 specific tables in one region/account.

## Risk Assessment

All changes are **provision.sh config** (not deployed until `provision.sh` is run) or **static asset** changes. No runtime code was modified. Zero risk to current production.

## Post-Deploy Verification (when provision.sh is next run)

1. `curl -s https://api.aletheia.study/health` — API still responds
2. Admin dashboard charts render from vendored Chart.js
3. Lambda invocations succeed with scoped Bedrock permissions
