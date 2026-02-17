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
