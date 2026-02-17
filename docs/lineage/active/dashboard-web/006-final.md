# Issue Filed

URL: https://github.com/martymcenroe/Aletheia/issues/368

---

# Business Metrics Dashboard for Aletheia.study

## User Story
As a **product owner/administrator**,
I want **a web-based business metrics dashboard on Aletheia.study**,
So that **I can track adoption trends, conversion rates, and revenue projections without needing CloudWatch expertise**.

## Objective
Provide a static HTML dashboard on Aletheia.study that visualizes business-level analytics (user adoption, tier conversion, revenue projections) by querying a secure admin-only metrics API endpoint.

## UX Flow

### Scenario 1: Admin Views Dashboard
1. Admin navigates to `https://aletheia.study/admin/metrics`
2. Page prompts for authentication (JWT with admin tier required)
3. Admin authenticates successfully
4. Dashboard loads and displays charts: adoption curve, tier distribution, conversion rates, revenue projections
5. Data auto-refreshes every 5 minutes (configurable)

### Scenario 2: Non-Admin Access Attempt
1. Non-admin user navigates to dashboard URL
2. Page prompts for authentication
3. User authenticates with non-admin credentials
4. System returns 403 Forbidden
5. Page displays "Admin access required" message

### Scenario 3: API Unavailable
1. Admin navigates to dashboard
2. Admin authenticates successfully
3. Metrics API returns 5xx error or times out
4. Dashboard displays "Unable to load metrics. Retrying in 30 seconds..."
5. Dashboard retries automatically

### Scenario 4: Mobile Viewing
1. Admin opens dashboard on mobile device
2. Charts render in responsive single-column layout
3. All data remains readable and interactive

## Requirements

### API Endpoint
1. New `GET /metrics` endpoint in Auth Lambda
2. Requires JWT with `tier: admin` claim
3. Returns JSON with all business metrics in single response
4. Response cached for 5 minutes (CloudWatch rate limits, DynamoDB cost)
5. Timeout: 10 seconds max

### Business Metrics
1. **User Adoption:** Daily new user count for past 90 days
2. **Tier Distribution:** Current count of users per tier (free, subscriber, admin)
3. **Conversion Rate:** Percentage of free users who converted to subscriber (30-day rolling)
4. **Coupon Redemption:** Total coupons redeemed, redemption rate by coupon code
5. **Revenue Projection:** `subscriber_count × monthly_price` (simple calculation)
6. **Retention:** Users with >1 session vs single-session users (30-day window)
7. **Geographic Distribution:** Request counts by country (from CloudFront logs, anonymized)

### Dashboard UI
1. Static HTML page (no build step required)
2. Chart.js for visualizations (CDN-loaded)
3. Auto-refresh interval configurable via query param (default 5 minutes)
4. Mobile-responsive layout (CSS Grid/Flexbox)
5. Loading states and error handling for each chart independently
6. Last-updated timestamp visible

### Offline Development Support
1. `static/admin/mock-metrics.json` fixture file with sample data structure
2. Dashboard detects `?mock=true` query param and loads fixture instead of API
3. Enables frontend development without deployed backend

## Technical Approach
- **Lambda Endpoint:** Add `/metrics` route to existing Auth Lambda, query DynamoDB for user/coupon aggregates, query CloudWatch for operational metrics, return unified JSON
- **DynamoDB Queries:** Use GSI on `tier` attribute for tier counts, scan with filter for date-range adoption data (acceptable for admin-only, low-frequency queries)
- **Static Dashboard:** HTML + vanilla JS, Chart.js via CDN, fetch from `/metrics` endpoint with JWT in Authorization header
- **Authentication:** Reuse existing JWT validation, add `tier === 'admin'` check
- **Caching:** Lambda caches response in memory for 5 minutes to reduce DynamoDB reads
- **Mock Mode:** Static JSON fixture enables offline frontend development

## Risk Checklist
*Quick assessment - details go in LLD. Check all that apply and add brief notes.*

- [x] **Architecture:** Adds new API endpoint and static page. Reuses existing Lambda and hosting.
- [x] **Cost:** DynamoDB scans for metrics (mitigated by 5-minute caching). CloudWatch GetMetricData calls. **Estimated <$5/month** assuming ~100 admin dashboard views/day with 5-minute caching reducing actual API calls to ~12/hour max.
- [ ] **Legal/PII:** No PII exposed. Geographic data derived from CloudFront logs (country only, not IP).
- [ ] **Legal/External Data:** No external data sources.
- [ ] **Safety:** Read-only operations. No data mutation risk.

## Security Considerations
- **Authentication:** JWT required with `tier: admin` claim. Token validation reuses existing Auth Lambda logic.
- **Authorization:** Explicit check that `claims.tier === 'admin'` before returning any data.
- **Data Exposure:** Response contains only aggregate counts. No user IDs, emails, or session data.
- **Input Sanitization:** Query params (refresh interval) validated as positive integers with max cap (3600 seconds).
- **CORS:** Endpoint returns `Access-Control-Allow-Origin: https://aletheia.study` only.

## Files to Create/Modify
- `lambda/auth/handlers/metrics.py` — New handler for `/metrics` endpoint
- `lambda/auth/routes.py` — Add route mapping for `/metrics`
- `static/admin/metrics.html` — Dashboard page
- `static/admin/metrics.js` — Chart rendering and API fetching logic
- `static/admin/metrics.css` — Responsive styling
- `static/admin/mock-metrics.json` — Sample data fixture for offline development
- `terraform/api_gateway.tf` — Add `/metrics` route (if not auto-discovered)
- `docs/wiki/API-Reference.md` — Document `/metrics` endpoint

## Dependencies
- Issue #401 (dashboard-cloudwatch) must be completed first — need CloudWatch metrics emitting for operational metrics portion

## Out of Scope (Future)
- **Export to CSV/PDF** — deferred to future issue
- **Custom date range selection** — MVP uses fixed 90-day window
- **Real-time streaming updates** — polling sufficient for business metrics
- **Alerting/thresholds** — CloudWatch Alarms handle operational alerting
- **Historical data archival** — current DynamoDB retention sufficient
- **Copy to Clipboard for raw JSON** — useful debugging feature, deferred

## Open Questions
- None (all questions resolved)
<!-- Resolved:
- [x] Which charting library? → Chart.js (lightweight, no build step, well-documented)
- [x] Caching strategy? → Lambda in-memory cache, 5-minute TTL
- [x] How to get geographic data without PII? → CloudFront/Cloudflare logs provide country-level aggregates
- [x] Offline development? → mock-metrics.json fixture with ?mock=true query param
-->

## Acceptance Criteria
- [ ] `GET /metrics` returns 401 Unauthorized when no JWT provided
- [ ] `GET /metrics` returns 403 Forbidden when JWT has `tier !== 'admin'`
- [ ] `GET /metrics` returns 200 with JSON containing keys: `adoption`, `tiers`, `conversion`, `coupons`, `revenue`, `retention`, `geography`
- [ ] Dashboard page loads at `/admin/metrics` and prompts for authentication
- [ ] Dashboard displays 6 charts after successful authentication
- [ ] Dashboard displays "Unable to load metrics. Retrying in 30 seconds..." when API returns 5xx
- [ ] Dashboard auto-refreshes data every 5 minutes (visible timestamp updates)
- [ ] Dashboard elements do not overlap and horizontal scrolling is not required on viewport width 375px
- [ ] p95 warm response time for `/metrics` endpoint < 1 second; cold start < 3 seconds
- [ ] No PII (email, user ID, IP address) appears in API response
- [ ] Dashboard loads mock data from `mock-metrics.json` when `?mock=true` query param is present

## Reviewer Suggestions

*Non-blocking recommendations from the reviewer.*

- **Visual Validation:** Consider adding a screenshot of the intended layout or the Chart.js prototype to the PR description to speed up the visual review.
- **Labels:** Add `frontend` and `analytics` labels.

## Definition of Done

### Implementation
- [ ] Core feature implemented
- [ ] Unit tests written and passing

### Tools
- [ ] N/A — no CLI tools required for this feature

### Documentation
- [ ] Update wiki pages affected by this change
- [ ] Update README.md if user-facing
- [ ] Update relevant ADRs or create new ones
- [ ] Add new files to `docs/0003-file-inventory.md`

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created

### Verification
- [ ] Run 0809 Security Audit - PASS (admin authentication, no PII exposure)
- [ ] Run 0810 Privacy Audit - PASS (aggregate-only data)
- [ ] Run 0817 Wiki Alignment Audit - PASS (if wiki updated)

## Testing Notes
- **Force 403:** Use valid JWT with `tier: free` or `tier: subscriber`
- **Force 5xx:** Temporarily misconfigure DynamoDB table name in Lambda env
- **Mobile testing:** Chrome DevTools device emulation (iPhone SE, 375px width)
- **Cache validation:** Call endpoint twice within 5 minutes, verify DynamoDB read count unchanged in CloudWatch
- **Geographic data:** Verify response contains country codes (e.g., `"US": 1234`) not IP addresses
- **Mock mode:** Append `?mock=true` to dashboard URL, verify charts render with fixture data

## Sizing
**T-shirt Size: M** (1-2 sessions)

## Original Brief (user's ideation notes)
# Idea: Aletheia.study Business Metrics Dashboard

**Status:** Active
**Effort:** Medium (1-2 sessions)
**Value:** Medium
**Blocked by:** dashboard-cloudwatch (need CloudWatch metrics emitting first)

---

## Problem

CloudWatch is great for real-time ops monitoring but poor for business intelligence: adoption trends, tier conversion rates, cost projections, and metrics to share with non-technical stakeholders. A web dashboard on Aletheia.study fills this gap.

---

## Proposal

Static HTML page on Aletheia.study that queries a metrics API endpoint for business-level analytics. Complements the CloudWatch ops dashboard.

**Business metrics (not available in CloudWatch natively):**
- User adoption curve (new users over time)
- Tier conversion rate (free → subscriber)
- Coupon redemption rates
- Revenue projections (subscriber count × price)
- Retention: returning users vs one-time
- Geographic distribution (derived from CloudFront/Cloudflare logs, not PII)

**Architecture:**
- New Lambda endpoint: `GET /metrics` (admin-authenticated)
- Queries CloudWatch `GetMetricData` for operational metrics
- Queries DynamoDB for business metrics (user counts by tier, coupon stats)
- Returns JSON consumed by static HTML page
- Page hosted on Aletheia.study (existing infrastructure)
- Client-side charting library (Chart.js or similar — lightweight, no build step)

**Privacy:**
- Same privacy constraints as CloudWatch dashboard — aggregate only
- Admin authentication required (JWT with admin tier)
- No user-identifiable data in API response
- Anonymized user ID for moderation same as CloudWatch dashboard

---

## Implementation

- `GET /metrics` endpoint in Auth Lambda (admin-only)
- Static HTML + JS page on Aletheia.study
- Chart.js for visualizations
- Auto-refresh on configurable interval
- Mobile-responsive layout

---

## Next Steps

1. [ ] Run requirements workflow to generate issue
