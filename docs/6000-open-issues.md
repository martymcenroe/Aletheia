# Aletheia - Open Issues

**Generated:** 2026-01-10 07:26 CT
**Total Open Issues:** 14

---

## Issue #51: Chrome Web Store Compliance

**Labels:** high-priority, chore

**Created:** 2025-12-10
**Updated:** 2026-01-09

### Description

Prepare assets (Manifest, Privacy Policy, Store Listing) for submission.

---

## Issue #81: Redesign landing page: modern professional aesthetic

**Labels:** feature, post-mvp

**Created:** 2025-12-21
**Updated:** 2026-01-04

### Description

## Objective
Replace the cyberpunk/retro landing page with a modern, professional design that builds trust with potential users.

## Current State
- `index.html` uses monospace font, dark theme, neon green accents
- Aesthetic is "1986 hacker terminal"
- Functional for Chrome Web Store approval but not brand-appropriate

## Requirements

### Design Direction
1. **Clean, modern aesthetic** — Think Linear, Notion, or Stripe
2. **Light theme primary** — Dark mode optional/future
3. **Professional typography** — Inter, SF Pro, or similar sans-serif
4. **Trust signals** — Privacy-first messaging, open source badge, clear value prop

### Technical
- Single `index.html` (keep it simple for GitHub Pages)
- No build step required
- Mobile responsive
- Fast load (<1s)

### Content Sections
1. Hero: Logo, tagline, CTA (Install from Chrome Store)
2. Features: 3-4 key benefits with icons
3. Privacy: Prominent "your data stays local" messaging
4. Footer: Links, copyright

## Out of Scope
- Blog/documentation site
- User accounts
- Analytics

## Acceptance Criteria
- [ ] Page looks professional and trustworthy
- [ ] Mobile responsive
- [ ] Loads in <1 second
- [ ] Privacy policy section retained
- [ ] Chrome Web Store link works

---

## Issue #106: Future: Full article context retrieval

**Labels:** enhancement

**Created:** 2025-12-29
**Updated:** 2026-01-09

### Description

## Summary
Enable retrieval of full article content when surrounding text selection is insufficient for accurate summarization/context.

## Problem
Currently Aletheia captures the user's text selection plus surrounding context. In some cases, understanding the full article may be necessary for accurate interpretation.

## Use Cases
- Academic papers where context spans multiple sections
- News articles where the lede doesn't capture the nuance
- Long-form content where selected passage references earlier material

## Considerations
- Copyright implications (capturing entire articles)
- Storage costs (full articles are large)
- Processing time (more text = more tokens)
- User consent (should user approve full retrieval?)

## Future Work
This is a **future enhancement** - not required for MVP or store submission.

## Related
- 0007-legal-compliance-strategy.md (copyright/fair use)
- Summarizer/Transform layer (would process full article)

---

## Issue #117: spike: Investigate mechanisms to support unauthenticated users while limiting abuse

**Labels:** documentation, enhancement, post-mvp

**Created:** 2025-12-30
**Updated:** 2026-01-01

### Description

## Context
We want LinkedIn OAuth as primary auth (#116), but would like to offer some level of trial/anonymous access without requiring signup. The challenge: preventing abuse without capturing privacy-sensitive data that Chrome Web Store wouldn't approve.

## Problem Statement
How do we let users "try before they buy" while preventing:
- One person creating unlimited trial accounts
- Bots/scripts abusing free tier
- Denial-of-wallet attacks on our Bedrock costs

## Constraints
- Chrome Web Store privacy requirements
- No IP address logging (likely prohibited)
- No invasive fingerprinting
- Must work across browser profiles/reinstalls (ideally)

## Options to Investigate

### 1. No Trial (Baseline)
- Require LinkedIn OAuth from first use
- **Pros:** Simple, no abuse vector
- **Cons:** High friction, loses casual users

### 2. Extension Install ID
- Use `chrome.runtime.id` or generate UUID on install
- Track usage server-side per ID
- **Pros:** Simple, no PII
- **Cons:** Bypassable via reinstall, cleared on uninstall

### 3. Time-Limited Trial
- "Free for first 24/48 hours after install"
- Store install timestamp locally + server validation
- **Pros:** Natural expiration
- **Cons:** Reinstall resets clock

### 4. Usage-Limited Trial
- "First N requests free"
- Counter stored server-side keyed by install ID
- **Pros:** Fair, predictable cost
- **Cons:** Same bypass as #2

### 5. Rate Limiting Only
- Allow anonymous but heavily rate-limited (e.g., 5 req/day)
- Authenticated users get higher limits
- **Pros:** Always available, natural upgrade path
- **Cons:** Determined abusers can still accumulate

### 6. Hybrid: Generous + Decay
- Start with N free requests
- After exhausted, drop to rate-limited mode
- Auth unlocks full access
- **Pros:** Best UX for legitimate users
- **Cons:** Complex to implement

## Questions to Answer
1. What does Chrome Web Store actually prohibit re: tracking?
2. What's our cost-per-request? (Determines abuse tolerance)
3. What's the conversion funnel goal? (Trial → Auth → Paid?)
4. Can we defer this entirely for MVP and require auth?

## Deliverable
Recommendation document with chosen approach and rationale.

## Related
- #116 - LinkedIn OAuth (primary auth mechanism)

---

## Issue #123: blog: Agent Operating System (AOS) - Beyond CMS for AI Collaboration

**Labels:** blog

**Created:** 2025-12-31
**Updated:** 2026-01-04

### Description

## Concept

The Aletheia documentation system has evolved beyond a Content Management System (CMS) into something more fundamental: an **Agent Operating System (AOS)**—executable documentation that AI agents run as their program.

## The Insight

"CMS" undersells what this is. The docs aren't just reference material—they're the instructions agents execute.

## The AOS Layers

| Layer | What It Does | Examples |
|-------|--------------|----------|
| **Process Automation** | Checklists that execute, not just document | 0009 (Session/Full Closeout) |
| **Context Persistence** | State preserved across sessions and agents | Session logs, IMMEDIATE-PLAN |
| **Agent Orchestration** | Who does what, when, how | CLAUDE.md, GEMINI.md, 0004 |
| **Reality Verification** | Don't trust metadata—verify actual state | 0009 Full Mode |
| **Executable Standards** | Rules that agents can follow literally | 0002, Forbidden Commands |

## The Operating System Metaphor

- **Docs = Programs** — Agents read and execute them
- **Session Logs = Process State** — Preserved across restarts
- **IMMEDIATE-PLAN = Current Task** — The foreground process
- **Checklists = Subroutines** — Called when conditions are met
- **Orchestrator = Scheduler** — Decides which agent runs which task

## What Makes This New

Traditional OS manages hardware resources. AOS manages **cognitive resources** across:
- Multiple agents with different capabilities
- Limited context windows
- No persistent memory within agents
- Varying instruction-following fidelity

## Key Lessons Discovered

1. **Don't trust metadata—verify reality.** Issue status can be wrong. Check if the code actually exists.

2. **Docs are programs.** If you can't execute the instruction literally, it's not clear enough.

3. **Orchestrator is scheduler, not programmer.** The human's job is to route agents to the right docs, not to remember context.

4. **Session logs are process state.** Without them, context dies when the session ends.

## Origin

Discovered during Aletheia development when a session closeout revealed that Issue #45 and #113 were both complete but the IMMEDIATE-PLAN still listed them as pending. The instruction "update IMMEDIATE-PLAN" was insufficient—agents needed to be told to **verify reality, not trust metadata**.

This led to the realization that what we'd built wasn't just documentation—it was an operating system for AI-human collaboration.

## References

- `docs/0000-GUIDE.md` - AOS philosophy section
- `docs/0009-session-closeout-protocol.md` - Full Mode for IMMEDIATE-PLAN verification

## Publication Notes

- Target audience: AI/ML practitioners, developer tooling engineers, anyone working with AI agents
- Angle: Novel framing of documentation as executable infrastructure
- Could include diagrams showing the "OS layers" and agent execution flow

---

## Issue #132: Set up support email infrastructure (Cloudflare Email Routing)

**Created:** 2026-01-01
**Updated:** 2026-01-01

### Description

## Context
We need email capability for:
- Firefox Add-ons Store communication (gecko ID: `extension@aletheia.study`)
- Chrome Web Store developer contact
- User support inquiries

## Research Summary

| Option | Cost | Receive | Send | Notes |
|--------|------|---------|------|-------|
| **Cloudflare Email Routing** | **Free** | ✅ | ❌ | Forwards to personal Gmail/etc |
| Cloudflare + Gmail SMTP | Free | ✅ | ✅ | Requires Gmail "send as" config |
| Zoho Mail (free tier) | Free | ✅ | ✅ | 5 users, 5GB, webmail only |
| Forward Email | Free | ✅ | ❌ | Privacy-focused forwarding |
| Namecheap email | ~$1/mo | ✅ | ✅ | Full hosting |

## Recommendation
**Cloudflare Email Routing (free)** - simplest and cheapest.

### Setup Steps
1. Move DNS to Cloudflare (free, keeps Namecheap as registrar)
2. Create `support@aletheia.study` → forwards to personal email
3. Optionally configure Gmail "send as" for replies

### Benefits
- $0/year
- Free CDN/DDoS protection as bonus
- Simple forwarding rules

## References
- [Cloudflare Email Routing](https://www.cloudflare.com/developer-platform/products/email-routing/)
- [Free Custom Domain Emails with Gmail and Cloudflare](https://altersquare.medium.com/free-custom-domain-emails-with-gmail-and-cloudflare-a-beginners-guide-84d759b373f7)
- [Cloudflare Email Routing Docs](https://developers.cloudflare.com/email-routing/)

## Definition of Done
- [ ] DNS moved to Cloudflare
- [ ] `support@aletheia.study` forwards to Orchestrator's email
- [ ] Test email received successfully
- [ ] (Optional) Gmail "send as" configured for replies

---

## Issue #203: Future: AgentOS Process Improvements (Research-Based)

**Labels:** process, post-mvp

**Created:** 2026-01-09
**Updated:** 2026-01-09

### Description

## Summary

Consolidated backlog item for process improvements derived from academic research (Paper 2512.14012) on expert LLM agent usage patterns.

These ideas are **valid but not urgent** - the current AgentOS workflow successfully shipped Aletheia to the Chrome Web Store. Revisit if evidence of process failures emerges.

---

## Improvement Ideas

### 1. Active Plan & Context Injection (was #127)
- Agents maintain `CURRENT_STATUS.md` in worktrees
- Prompts must reference specific LLD steps, target files, domain objects
- **Goal:** Prevent context loss, provide crash recovery save points

### 2. Scaffolding vs. Logic Split (was #128)
- Two-pass implementation model:
  - **Pass 1 (Skeleton):** Directory structure, function signatures, failing tests (high autonomy)
  - **Pass 2 (Brain):** Business logic implementation (high supervision)
- **Goal:** Match agent autonomy level to task suitability

### 3. Red Team Architecture Challenge (was #129)
- Insert critique phase before LLD approval
- Different model attacks the plan: "Find 3 ways this fails in production"
- **Goal:** Catch hallucinations, over-engineering, security gaps early

---

## Implementation Criteria

Only implement these if:
- [ ] Evidence of repeated process failures (lost context, bad LLDs, etc.)
- [ ] Current review gates prove insufficient
- [ ] Team bandwidth exists after MVP launch

---

## References
- Paper 2512.14012 (arXiv - Expert LLM Agent Usage Patterns)
- Supersedes: #127, #128, #129

---
*Consolidated during backlog cleanup, 2026-01-09*

---

## Issue #204: chore: Repository reorganization - move scripts and test data to proper directories

**Created:** 2026-01-09
**Updated:** 2026-01-09

### Description

## Summary

The repository root has accumulated clutter that should be organized into proper directories. This is a housekeeping task to align with professional Python/JavaScript project standards.

## Current Problems

### Root Directory Clutter

| Category | Count | Files |
|----------|-------|-------|
| Python scripts | 5 | `format-issues.py`, `harvest_test_data.py`, `run_guardrails.py`, `verify_bedrock.py`, `verify_holistic.py` |
| Shell scripts | 6 | `aws-cleanup-old-resources.sh`, `aws-inventory-check.sh`, `batch-pdf.sh`, `print-*.sh`, `run-audit.bat` |
| Test data | 2 | `test_ground_truth.json` (2KB), `test_holistic_data.json` (337KB) |
| Orphan files | 2 | `index.html`, `.print-history.json` |

### Directory Confusion

- `scripts/` is empty (just `.gitkeep`) but `tools/` has all actual tools
- `prompts/` contains stale files including "clean this out later" folder

## Proposed Changes

### 1. Move Python Scripts to `tools/`
```
format-issues.py      → tools/format_issues.py
harvest_test_data.py  → tools/harvest_test_data.py
run_guardrails.py     → tools/run_guardrails.py
verify_bedrock.py     → tools/verify_bedrock.py
verify_holistic.py    → tools/verify_holistic.py
```

### 2. Consolidate Shell Scripts to `tools/aws/`
```
aws-cleanup-old-resources.sh → tools/aws/cleanup_old_resources.sh
aws-inventory-check.sh       → tools/aws/inventory_check.sh
```

### 3. Move Print Scripts to `tools/print/`
```
batch-pdf.sh       → tools/print/batch_pdf.sh
print-all-pdfs.sh  → tools/print/print_all.sh
print-docs.sh      → tools/print/print_docs.sh
```

### 4. Move Test Data to `tests/data/`
```
test_ground_truth.json  → tests/data/ground_truth.json
test_holistic_data.json → tests/data/holistic_data.json
```

### 5. Create `web/` for Landing Page
```
index.html → web/index.html
```

### 6. Cleanup
- [ ] Delete empty `scripts/` directory
- [ ] Add to `.gitignore`: `.print-history.json`, `temp-pdfs/`
- [ ] Move `run-audit.bat` to `tools/`
- [ ] Move `CHATGPT.md`, `GEMINI.md` to `docs/llm-guides/` or delete
- [ ] Clean up `prompts/` directory (archive stale content)

## Post-Move Updates Required

- [ ] Update any import statements referencing moved Python files
- [ ] Update `.claude/settings.local.json` permission paths
- [ ] Update `pyproject.toml` if script entry points exist
- [ ] Update `CLAUDE.md` documentation references
- [ ] Update `docs/0003-file-inventory.md`
- [ ] Run full test suite to verify nothing broke

## Target Structure (Root)

After cleanup, root should contain only:
- Config files: `.gitignore`, `.pre-commit-config.yaml`, `eslint.config.mjs`, `pyproject.toml`, `package.json`, `poetry.lock`, `package-lock.json`, `playwright.config.js`
- Documentation: `README.md`, `LICENSE`, `NOTICE`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `CLAUDE.md`
- Entry points: `deploy.sh`, `provision.sh` (convention to keep in root)
- Directories: `.claude/`, `.github/`, `docs/`, `extensions/`, `src/`, `tests/`, `tools/`, `web/`

## Acceptance Criteria

- [ ] No `.py` files in repository root
- [ ] No utility `.sh` files in repository root (except `deploy.sh`, `provision.sh`)
- [ ] No test data JSON files in repository root
- [ ] Empty `scripts/` directory removed
- [ ] All tests pass after reorganization
- [ ] File inventory updated

## Labels

`chore`, `tech-debt`, `documentation`

---

## Issue #246: audit: Add adversarial test logging to 0825 AI Safety

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Problem
0825 AI Safety requires adversarial testing but provides no evidence logging. Agent can claim tests passed without running them.

## Evidence
From 0825 Section 2 Checklist:
- Execute adversarial test cases
- Test prompt injection, jailbreaks, output manipulation

But NO logging mechanism. No evidence of what was attempted.

## Impact
Agent writes 'adversarial tests PASS' with no proof.

## Acceptance Criteria
- [ ] Add CloudWatch logging for adversarial test attempts
- [ ] Log: prompt sent, response received, blocked/passed
- [ ] Audit record must include test case IDs executed
- [ ] Verifiable evidence required, not self-attestation

## Priority
HIGH - AI safety claims are unverifiable

---

## Issue #248: audit: Add CI job to verify audit execution claims

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Problem
Agents can claim to execute audits with no verification. Session logs may say 'ran 0809 Security - PASS' but nothing validates this.

## Evidence
90% of audits are manual-only. No CI verification that claimed audits were actually run.

## Impact
Audit claims are unverifiable. Trust-based system enables self-excuse.

## Acceptance Criteria
- [ ] CI job scans session logs for audit claims
- [ ] Cross-references against audit record updates
- [ ] Blocks if audit claimed but no record updated
- [ ] Weekly report: audits claimed vs audits evidenced

## Priority
CRITICAL - This is the enforcement gap

---

## Issue #262: test(unit): Add Lambda OAuth callback endpoint tests

**Labels:** testing

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Summary

The new `/auth/callback` endpoint added in #256 (Firefox OAuth tabs-based flow) lacks unit tests.

## Source

Test Gap Analysis 2026-01-10

## Gap Details

`src/lambda_auth_function.py` has a new `handle_oauth_callback()` function that:
- Handles GET requests to `/auth/callback`
- Receives OAuth redirect from LinkedIn with `?code=...&state=...`
- Returns minimal HTML page for extension to parse

This endpoint is critical to the Firefox OAuth flow but has no automated tests.

## Acceptance Criteria

- [ ] Unit tests for `handle_oauth_callback()` function
- [ ] Test cases cover:
  - Valid code and state parameters
  - Missing code parameter
  - Missing state parameter
  - Error parameter from LinkedIn (user denied)
  - HTML response format validation
- [ ] Tests run in CI

## Effort

Medium - Requires mocking Lambda event structure

## Related

- #256 - Firefox OAuth Tabs-Based Flow (implementation)
- Report: `docs/reports/256/test-report.md`

---

## Issue #263: test(e2e): Add Edge/Chromium browser E2E test matrix

**Labels:** testing, chore

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Summary

E2E tests only run against Chrome. Edge (Chromium-based) is untested despite being a supported browser.

## Source

Test Gap Analysis 2026-01-10 (from Report #116: "Edge (Chromium) | Not tested | Should work")

## Problem

The Chrome extension should work in Edge since Edge uses Chromium, but we have zero automated verification. Users on Edge could encounter issues we never detect.

## Proposed Solution

Add Edge to the Playwright E2E test matrix in playwright.config.js.

## Acceptance Criteria

- [ ] Playwright config includes Edge channel
- [ ] E2E tests run against Edge in CI
- [ ] Extension loads correctly in Edge
- [ ] All existing E2E specs pass in Edge
- [ ] CI workflow updated to include Edge runs

## Considerations

- Edge requires separate browser installation in CI
- May need conditional logic if Edge unavailable
- Consider running Edge tests in separate job to avoid blocking

## Effort

Medium - Requires CI configuration changes

## Related

- Report: docs/reports/116/test-report.md
- Audit: docs/0826-audit-cross-browser-testing.md

---

## Issue #264: test(integration): Add DynamoDB integration test fixtures

**Labels:** testing

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Summary

DynamoDB operations are only tested manually via dry-run mode. No automated integration tests exist.

## Source

Test Gap Analysis 2026-01-10 (from Reports #147, #150)

## Problem

Multiple reports note DynamoDB-dependent functionality is "manual only":
- `delete_user_data()` - GDPR compliance function (Report #147)
- TTL backfill logic - Data hygiene (Report #150)
- GSI query performance - User data lookup (Report #147)
- Pagination for tables >1MB - Not tested (Report #150)

## Proposed Solution

Create DynamoDB Local integration test fixtures:

1. **Docker-based DynamoDB Local** for CI
2. **Fixture data** representing production schema
3. **Integration test suite** for Lambda data operations

## Acceptance Criteria

- [ ] DynamoDB Local runs in CI via Docker
- [ ] Test fixtures create tables with GSI
- [ ] Integration tests for `delete_user_data()`
- [ ] Integration tests for TTL operations
- [ ] Pagination tested with >1MB fixture data
- [ ] Tests isolated (no production data access)

## Effort

Medium - Requires Docker setup and fixture design

## Related

- Report: docs/reports/147/test-report.md
- Report: docs/reports/150/implementation-report.md

---

## Issue #272: test(fix): Apply Shadow DOM patch to Chrome E2E tests

**Labels:** testing, technical-debt

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Problem

The Chrome `museum-label.spec.js` tests are failing (12/16) because they cannot access the closed Shadow DOM. The tests use `host.shadowRoot` which returns `null` for `mode: 'closed'` shadow roots.

## Root Cause

Chrome overlay.js uses closed shadow DOM for security (ADR 0202):
```javascript
const shadow = host.attachShadow({ mode: 'closed' });
```

The test helper `shadowQuery()` tries to access `host.shadowRoot`, which is null for closed shadow roots.

## Solution

We solved this for Firefox in #265 using a helper that patches `attachShadow` to force `mode: 'open'` for testing:

```javascript
await page.evaluate(() => {
    const originalAttachShadow = Element.prototype.attachShadow;
    Element.prototype.attachShadow = function(options) {
        return originalAttachShadow.call(this, { ...options, mode: 'open' });
    };
});
```

## Action Required

Refactor `tests/e2e/museum-label.spec.js` to:
1. Import helpers from `tests/e2e/helpers/overlay-helpers.js`
2. Use `injectOverlay(page, 'chrome')` with the shadow DOM patch
3. Remove duplicate inline helper functions

## Test Evidence

Current state on main:
- Firefox overlay tests: 10/10 pass
- Chrome museum-label tests: 4/16 pass (12 failures)

## Related

- #265 - Firefox overlay E2E tests (implemented the fix)
- #125 - Museum Label UI (original tests)
- ADR 0202 - Shadow DOM isolation decision

---
