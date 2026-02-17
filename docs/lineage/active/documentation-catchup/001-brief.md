# Idea: Documentation Catchup (ADRs, Lessons Learned, Wiki, Blog)

**Status:** Active
**Effort:** Medium (1-2 sessions)
**Value:** High
**Blocked by:** None

---

## Problem

Several sessions of rapid feature work (CloudFlare migration, LinkedIn OAuth, JWT auth, token cap) have outpaced documentation. Before launch, we need to capture:

1. **ADRs** — Architectural decisions made but not formally recorded
2. **Lessons learned** — Workflow bugs, integration pain points
3. **Wiki updates** — If applicable to project wiki
4. **Blog candidates** — Technical posts for dispatch repo (launch content)

Undocumented decisions become tribal knowledge. Agent continuity depends on written records.

---

## Proposal

### ADRs Needed

| Topic | Key Decision | Status |
|-------|-------------|--------|
| JWT Authentication | HS256 with Secrets Manager, dual-secret rotation | Implemented, no ADR |
| Daily Token Cap | DynamoDB atomic counters with TTL cleanup | Implemented, no ADR |
| Auth Middleware Pattern | Decorator-based `@require_auth` on Lambda | Implemented, no ADR |
| CloudFlare Migration | Already has ADR 10216 | Done |

### Lessons Learned

- AssemblyZero LLD workflow: test plan validator only parses Scenario column (filed #382)
- AssemblyZero implementation workflow: scaffold test loop bug (filed #380)
- `PYTHONUNBUFFERED=1` required for background workflow monitoring
- `CLAUDECODE=` (empty, not unset) for nested Claude sessions on MSYS2
- Pre-commit hook sequencing: ruff → mypy → gitleaks order matters
- Auth Lambda packaging must use `src/` directory (not flat file copy)

### Blog Candidates (dispatch repo)

- "Building Privacy-First Auth for a Chrome Extension" — LinkedIn OAuth + JWT architecture
- "CloudFlare Workers as a Poor Man's API Gateway" — migration from CloudFront+WAF
- "Adversarial Auditing with AI Agents" — the audit philosophy and automated verification

### Wiki

- Update project wiki (if exists) with current architecture diagrams
- Auth flow sequence diagram
- Rate limiting architecture

---

## Implementation

- Write ADRs 10217-10219 following template in 10200 index
- Compile lessons learned into a session retrospective doc
- Draft blog posts as markdown in dispatch repo
- Update any wiki pages

---

## Next Steps

1. [ ] Run requirements workflow to generate issue
2. [ ] Write ADRs first (most structured, highest value)
3. [ ] Blog drafts in dispatch
