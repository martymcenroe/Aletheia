# Idea: LinkedIn Follower Incentive (Coupon for Follows)

**Status:** Active
**Effort:** Medium (1-2 sessions)
**Value:** Medium
**Blocked by:** subscription-model (need coupon system first)

---

## Problem

Chrome Store launch needs a growth strategy. LinkedIn is the primary distribution channel (Aletheia's target audience is professionals). Offering a coupon for following the creator's LinkedIn profile and/or the ThriveTech.ai company page creates a viral loop:

1. User installs extension (free tier)
2. User wants more requests → follows on LinkedIn for coupon
3. LinkedIn algorithm surfaces content to follower's network
4. Network discovers Aletheia → installs → repeat

---

## Proposal

### User Flow

1. In extension popup, user sees "Get bonus requests: Follow us on LinkedIn"
2. User clicks → opens LinkedIn personal profile linkedin.com/in/martymcenroe page in new tab
3. User follows, then returns to extension and clicks "I followed"
4. Extension calls API to verify follow status Question: Does LinkedIn API allow have this function?
5. If verified → auto-generate coupon → upgrade tier

### LinkedIn API Integration

LinkedIn's API can verify organization followers via the Organizations API (`GET /organizationalEntityFollowerStatistics`). Personal profile follows are harder to verify programmatically — may need to use honor system + manual audit for personal follows.

**ThriveTech.ai verification:** Requires LinkedIn Marketing API access (organization admin must authorize app). Achievable since the user controls both the app and the org.

**Personal profile verification:** LinkedIn doesn't expose a "does user X follow user Y" API. Options:
- Honor system with abuse detection (rate of claims vs actual follower growth)
- Skip personal follows, only incentivize company page follows (verifiable)

### Coupon Delivery

- Auto-generated single-use coupon code unique to user and stored in databse. no time limit but can be refreshed or displayed again
- Delivered in-extension (popup shows code immediately after verification)
- Also sent to collected email (from subscription-model brief)


---

## Implementation

- LinkedIn Marketing API integration for org follower verification
- New Auth Lambda endpoint: `POST /verify-follow` (checks LinkedIn API, generates coupon)
- Extension popup: follow CTA with verification button
- Coupon auto-generation using coupon system from subscription-model
- Rate limiting: one follow incentive per user (deduplicate by user_id)

---

## Next Steps

1. [ ] Run requirements workflow to generate issue
2. [ ] Verify LinkedIn Marketing API access for ThriveTech.ai org
3. [ ] Decide personal follow verification approach
