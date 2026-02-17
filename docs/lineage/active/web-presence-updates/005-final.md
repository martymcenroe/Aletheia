# Issue Filed

URL: https://github.com/martymcenroe/Aletheia/issues/371

---

# Web Presence Updates for Aletheia Launch

## User Story
As a **product owner preparing for Chrome Store launch**,
I want **all web properties updated with consistent Aletheia messaging**,
So that **potential users encounter professional, accurate product information across all channels**.

## Objective
Update ThriveTech.ai website, LinkedIn, personal website, and Aletheia.study with current product features, screenshots, and launch messaging before Chrome Web Store publication.

## UX Flow

### Scenario 1: Visitor Discovers Aletheia via LinkedIn
1. User sees Aletheia launch post on ThriveTech.ai LinkedIn
2. User clicks through to ThriveTech.ai product page
3. User reviews features, screenshots, pricing
4. User clicks Chrome Web Store badge to install
5. Result: Clear path from discovery to installation

### Scenario 2: Visitor Finds Aletheia.study Directly
1. User lands on Aletheia.study (from search or direct link)
2. User sees feature descriptions with current screenshots
3. User reviews pricing tiers (free vs subscriber)
4. User clicks Chrome Web Store link
5. Result: Landing page converts visitor to user

### Scenario 3: Visitor Checks Personal Website Projects
1. User browses personal website projects section
2. User sees Aletheia entry with description
3. User clicks through to Aletheia.study or Chrome Store
4. Result: Professional portfolio reflects current work

## Requirements

### Content Consistency
1. All properties communicate the same core value proposition
2. Privacy-first messaging present on all properties
3. Multi-browser support (Chrome, Firefox, Edge) mentioned
4. Free tier + subscription model clearly explained
5. Professional/LinkedIn use case emphasized

### Aletheia.study Updates
1. Feature descriptions reflect current capabilities (auth, rate limiting)
2. Fresh screenshots of Chrome extension in action
3. Pricing/tier information with clear differentiation
4. Chrome Web Store badge with proper linking
5. Privacy policy link remains accessible

### ThriveTech.ai Website
1. Aletheia product page with feature list
2. Screenshot gallery showing extension UI
3. Clear CTA to Chrome Web Store
4. Pricing section matching Aletheia.study

### LinkedIn Content
1. Company page description includes Aletheia
2. Launch announcement post draft ready
3. Product screenshot carousel prepared

### Personal Website
1. Projects section entry for Aletheia
2. Brief description with link to Aletheia.study

## Technical Approach
- **Content Drafting:** All marketing copy drafted as markdown in dispatch repo for review
- **Aletheia.study:** Direct HTML/CSS updates in existing repo
- **Screenshots:** Fresh captures of extension showing current UI state
- **Chrome Store:** Listing copy and promotional images prepared
- **External Properties:** LinkedIn and personal website updated manually (documented in implementation report)

## Risk Checklist
*Quick assessment - details go in LLD. Check all that apply and add brief notes.*

- [ ] **Architecture:** Does this change system structure? No — static content only
- [ ] **Cost:** Does this add API calls, storage, or compute? No
- [ ] **Legal/PII:** Does this handle personal data or have compliance implications? No — marketing content only
- [ ] **Legal/External Data:** Does this fetch from external sources? No
- [ ] **Safety:** Can this cause data loss or system instability? No

## Security Considerations
- N/A (no security-relevant operations — static content updates only)

## Files to Create/Modify
- `dispatch/drafts/aletheia-launch-linkedin.md` — LinkedIn launch post draft
- `dispatch/drafts/aletheia-product-copy.md` — Core marketing copy for all properties
- `aletheia-study/index.html` — Updated feature descriptions, screenshots, pricing
- `aletheia-study/assets/screenshots/` — Fresh extension screenshots
- `docs/reports/{IssueID}/implementation-report.md` — Manual update checklist and verification

## Dependencies
- None (can proceed in parallel with other launch tasks)

## Out of Scope (Future)
- Video demo/tutorial — deferred post-launch
- Blog post deep-dive on technology — separate content effort
- Automated cross-property deployment — manual updates acceptable for launch
- A/B testing landing page variants — post-launch optimization

## Open Questions
- None (all questions resolved)

## Acceptance Criteria
- [ ] `dispatch/drafts/aletheia-launch-linkedin.md` exists with launch announcement text
- [ ] `dispatch/drafts/aletheia-product-copy.md` exists with feature list, value prop, pricing copy
- [ ] Aletheia.study index.html contains updated feature descriptions mentioning auth and rate limiting
- [ ] Aletheia.study contains at least 3 fresh screenshots showing current extension UI
- [ ] Aletheia.study displays pricing information for free and subscriber tiers
- [ ] Aletheia.study includes Chrome Web Store badge/link (placeholder URL acceptable pre-launch)
- [ ] Implementation report documents manual updates to LinkedIn and personal website with verification screenshots

## Reviewer Suggestions

*Non-blocking recommendations from the reviewer.*

- **Effort Estimate:** No T-shirt size or story point estimate provided. This appears to be a **Small (S)** or **Medium (M)** task depending on the iteration needed for the copy.
- **Mock Data:** Suggest explicitly stating in the Implementation Plan that screenshots should be generated using a "Clean Profile" or Mock Data to minimize the risk of accidental PII leakage detected during the review phase.

## Definition of Done

### Implementation
- [ ] Core content drafted in dispatch repo
- [ ] Aletheia.study static site updated
- [ ] Screenshots captured and added

### Tools
- N/A (no new tools required)

### Documentation
- [ ] Update wiki pages affected by this change
- [ ] Add new files to `docs/0003-file-inventory.md`

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created

### Verification
- [ ] All four properties reviewed for messaging consistency
- [ ] Chrome Web Store listing copy finalized

## Testing Notes
- **Aletheia.study:** Load in browser, verify all links work, screenshots display, pricing section renders
- **Content review:** Check markdown drafts render correctly, no broken formatting
- **Screenshot quality:** Verify screenshots are high resolution, show relevant UI state, no PII visible
- **Cross-browser:** Verify Aletheia.study renders correctly in Chrome, Firefox, Edge
