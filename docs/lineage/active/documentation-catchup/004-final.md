# Issue Filed

URL: https://github.com/martymcenroe/Aletheia/issues/370

---

# Documentation Catchup: ADRs, Lessons Learned, and Blog Drafts

## User Story
As a project maintainer,
I want all architectural decisions and lessons learned from recent feature work formally documented,
So that future sessions have written context instead of relying on tribal knowledge.

## Objective
Capture undocumented decisions from CloudFlare migration, LinkedIn OAuth, JWT auth, and token cap features as ADRs, lessons learned, and blog draft candidates.

## UX Flow

### Scenario 1: Writing ADRs
1. Maintainer identifies implemented feature without formal ADR
2. System provides ADR template and decision context
3. Maintainer creates ADR following established numbering (10217+)
4. Result: Decision rationale preserved in `docs/adr/` directory

### Scenario 2: Compiling Lessons Learned
1. Maintainer reviews recent session transcripts and issue comments
2. System aggregates pain points and integration bugs
3. Maintainer writes retrospective document
4. Result: Operational knowledge captured for future debugging

### Scenario 3: Drafting Blog Posts
1. Maintainer identifies technical topic with broad appeal
2. Drafts markdown in dispatch repo following blog structure
3. Runs blog-review skill for quality check
4. Result: Launch content ready for publication

## Requirements

### ADR Creation
1. Create ADR 10217: JWT Authentication Architecture (HS256, Secrets Manager, dual-secret rotation)
2. Create ADR 10218: Daily Token Cap Implementation (DynamoDB atomic counters, TTL cleanup)
3. Create ADR 10219: Auth Middleware Pattern (decorator-based `@require_auth` on Lambda)
4. Follow template structure from ADR 10200 index
5. Include decision drivers, alternatives considered, and consequences

### Lessons Learned Document
1. Document AssemblyZero workflow bugs encountered (issues #380, #382)
2. Record environment variable quirks (`PYTHONUNBUFFERED=1`, `CLAUDECODE=`)
3. Capture pre-commit hook sequencing requirements (ruff → mypy → gitleaks)
4. Note Lambda packaging directory structure (`src/` requirement)
5. Store in `docs/retrospectives/` or equivalent project location

### Blog Draft Preparation
1. Draft "Building Privacy-First Auth for a Chrome Extension" outline
2. Draft "CloudFlare Workers as a Poor Man's API Gateway" outline
3. Draft "Adversarial Auditing with AI Agents" outline
4. Create markdown files in dispatch repo `drafts/` directory
5. Include code snippets, architecture diagrams, and key takeaways

## Technical Approach
- **ADRs:** Markdown files following MADR template with status, context, decision, consequences
- **Lessons Learned:** Structured retrospective with categories (tooling, environment, packaging)
- **Blog Drafts:** Markdown with frontmatter for dispatch repo blog pipeline

## Risk Checklist
*Quick assessment - details go in LLD. Check all that apply and add brief notes.*

- [ ] **Architecture:** Does this change system structure? No — documentation only
- [ ] **Cost:** Does this add API calls, storage, or compute? No
- [ ] **Legal/PII:** Does this handle personal data or have compliance implications? No
- [ ] **Legal/External Data:** Does this fetch from external sources? No
- [ ] **Safety:** Can this cause data loss or system instability? No

## Security Considerations
- N/A (no security-relevant operations — documentation only)

## Files to Create/Modify
- `docs/adr/10217-jwt-authentication.md` — JWT auth decision record
- `docs/adr/10218-daily-token-cap.md` — Token cap decision record
- `docs/adr/10219-auth-middleware-pattern.md` — Middleware pattern decision record
- `docs/adr/10200-index.md` — Update index with new ADRs
- `docs/retrospectives/2026-02-pre-launch.md` — Lessons learned compilation
- `../dispatch/drafts/privacy-first-auth.md` — Blog draft (dispatch repo)
- `../dispatch/drafts/cloudflare-poor-mans-gateway.md` — Blog draft (dispatch repo)
- `../dispatch/drafts/adversarial-auditing.md` — Blog draft (dispatch repo)

## Dependencies
- None (documentation of already-implemented features)

## Out of Scope (Future)
- Wiki architecture diagrams — deferred to visual documentation issue
- Auth flow sequence diagrams — requires diagramming tooling decision
- Publishing blog posts — drafts only; publication is separate workflow

## Open Questions
- None (all questions resolved)

## Acceptance Criteria
- [ ] ADR 10217 exists at `docs/adr/10217-jwt-authentication.md` with Status, Context, Decision, and Consequences sections
- [ ] ADR 10218 exists at `docs/adr/10218-daily-token-cap.md` with Status, Context, Decision, and Consequences sections
- [ ] ADR 10219 exists at `docs/adr/10219-auth-middleware-pattern.md` with Status, Context, Decision, and Consequences sections
- [ ] ADR index (10200) lists all three new ADRs with titles and status
- [ ] Lessons learned document contains at least 6 categorized items from recent sessions
- [ ] At least one blog draft markdown file exists in dispatch repo with title, intro, and section outline
- [ ] All ADRs pass markdown linting (no syntax errors)

## Reviewer Suggestions

*Non-blocking recommendations from the reviewer.*

- **Taxonomy:** Add `documentation`, `maintenance`, and `blog` labels.
- **Effort Estimate:** T-shirt size appears to be **S** (Small) - mostly writing and compiling existing context.
- **Process:** Verify if `docs/reports/{IssueID}/test-report.md` is strictly necessary for documentation tasks, or if the markdown linting output in the implementation report is sufficient.

## Definition of Done

### Implementation
- [ ] All three ADRs written and committed
- [ ] Lessons learned document written and committed
- [ ] At least one blog draft created in dispatch repo

### Tools
- [ ] N/A (no new tools required)

### Documentation
- [ ] ADR index updated with new entries
- [ ] Blog drafts follow dispatch repo frontmatter format
- [ ] New files added to `docs/0003-file-inventory.md`

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created

### Verification
- [ ] Run 0817 Wiki Alignment Audit - PASS (if wiki content updated)

## Testing Notes
- ADRs are documentation; verification is structural (all required sections present)
- Blog drafts can be previewed with `blog-review` skill for quality feedback
- Lessons learned document should cross-reference issue numbers where bugs were filed (#380, #382)
