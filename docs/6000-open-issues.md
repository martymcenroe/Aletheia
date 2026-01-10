# Aletheia - Open Issues

**Generated:** 2026-01-10 00:05 CT
**Total Open Issues:** 35

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

## Issue #161: chore: Automate performance benchmarks in CI

**Labels:** testing, chore

**Created:** 2026-01-05
**Updated:** 2026-01-05

### Description

## Context

0899 Meta-Audit identified that 0812 (Performance) is currently a manual procedure involving "Check CloudWatch" with high toil.

## Proposal

Add automated performance benchmarks to CI pipeline.

## Implementation Options

### Option A: pytest-benchmark for Lambda
```python
def test_lambda_handler_latency(benchmark):
    result = benchmark(lambda_handler, mock_event, mock_context)
    assert result['statusCode'] == 200
```

### Option B: Playwright performance metrics
```javascript
test('extension load performance', async ({ page }) => {
  const metrics = await page.metrics();
  expect(metrics.TaskDuration).toBeLessThan(100);
});
```

### Option C: Dedicated benchmark workflow
Run on schedule (weekly) rather than every PR to avoid CI slowdown.

## Metrics to Track

| Metric | Target | Source |
|--------|--------|--------|
| Lambda cold start | <500ms | CloudWatch |
| Lambda warm | <100ms | pytest-benchmark |
| Extension load | <100ms | Playwright metrics |
| Click-to-glass | <200ms | Playwright |

## Acceptance Criteria

- [ ] Benchmark tests added to test suite
- [ ] Baseline metrics documented in 0812
- [ ] Regression detection (fail if >20% slower)

## References

- 0812 Performance Audit: `docs/0812-audit-performance.md`
- 0899 Meta-Audit recommendation #1
- Issue #156 (frontend latency optimization)

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

## Issue #214: test(unit): Port popup.test.js and overlay tests to Firefox extension

**Labels:** testing

**Created:** 2026-01-09
**Updated:** 2026-01-09

### Description

## Summary

Firefox extension (`extensions/firefox/`) lacks test parity with Chrome. Chrome has comprehensive tests (`tests/unit/popup.test.js` - 920 lines) but Firefox has none.

## Current State

| File | Chrome Tests | Firefox Tests |
|------|--------------|---------------|
| popup.js | 920 lines in popup.test.js | None |
| overlay.js | E2E tests exist | None |
| service-worker.js | None (separate issue) | None |

- **Source:** Test Gap Analysis 2026-01-09

## Gap Analysis

Firefox extension files with no tests:
- `extensions/firefox/popup.js` (494 lines in Chrome version)
- `extensions/firefox/overlay.js` (871 lines in Chrome version)

## Considerations

1. **API Differences:** Firefox uses `browser.*` APIs vs Chrome's `chrome.*`
2. **Manifest Version:** Firefox is MV2, Chrome is MV3
3. **Auth Module:** Firefox lacks auth.js (Issue #206 tracks adding it)

## Proposed Solution

### Option A: Shared Test Suite (Recommended)
Create parameterized tests that run against both extensions:

```javascript
const extensions = ['chrome', 'firefox'];
extensions.forEach(browser => {
  describe(`popup.js (${browser})`, () => {
    // Load browser-specific popup.js
    // Use browser-specific API mocks
  });
});
```

### Option B: Separate Test Files
- `tests/unit/popup-firefox.test.js`
- Mirror Chrome tests with Firefox API mocks

## Acceptance Criteria

- [ ] Firefox popup.js has unit tests
- [ ] Tests cover storage functions (getAllowlist, addToAllowlist, etc.)
- [ ] Tests cover view rendering
- [ ] Tests cover event handlers
- [ ] Firefox overlay.js has E2E coverage
- [ ] Test parity documented in test report

## References

- Chrome popup tests: `tests/unit/popup.test.js`
- Firefox auth gap: Issue #206
- Coding standards: Dual extension parity requirement

---

## Issue #222: Implement Claude-Gemini Dual Review Automation System

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

**Objective:**
Automate the coordination between Claude Code (Sonnet 4.5) and Gemini CLI (3 Pro) to create a dual-AI review system for LLD design, implementation review, and issue filing.

**UX Flow:**

**Happy Path:**
1. User writes LLD → Claude auto-invokes Gemini for review → Feedback incorporated → User approves implementation
2. User implements feature → Claude auto-invokes Gemini for code review → Dual approval (Gemini + User) → Merge
3. User drafts issue → Claude auto-invokes Gemini for completeness check → User files issue

**Error/Edge Cases:**
- Gemini quota exhausted → Abort review, notify user with reset time, log event
- Model downgrade detected → Abort review, prevent wrong model usage
- Network timeout → Retry once, then abort if fails
- Invalid Gemini response → Parse best-effort, flag to user

**Requirements:**
1. **Model Detection:** JSON output parsing detects Gemini 3 Pro vs downgrade to Flash
2. **Automatic Triggers:** LLD save, implementation complete, issue draft → auto-invoke Gemini
3. **Prompt Library:** Versioned prompts in `gemini-prompts/` directory
4. **Dual Approval Gate:** Implementation merge requires both Gemini + User approval
5. **Session Logging:** Gemini writes directly to session logs (Claude validates)
6. **Quota Handling:** Abort on exhaustion, log events, notify user
7. **Feedback Parsing:** Extract [BLOCKING], [HIGH], [SUGGESTION] markers, ignore implementation offers

**Technical Approach:**

**Module:** AI Workflow Coordination
**Dependencies:**
- Gemini CLI v0.23.0+
- jq (JSON parsing)
- Existing Aletheia workflow (0004-orchestration-protocol.md)

**Design Pattern:** Event-driven automation with model verification

**Components:**
1. `tools/gemini-model-check.sh` - Bash wrapper for model detection
2. `gemini-prompts/*.txt` - Prompt library (lld-review, implementation-review, issue-review, session-log)
3. `.claude/workflow-state.json` - Track current workflow phase
4. `tmp/gemini-quota-events.jsonl` - Quota event logging
5. `docs/0602-skill-gemini-dual-review.md` - Master skill documentation

**Security Considerations:**
- Gemini session log writes validated by Claude before commit
- Model detection prevents using wrong model tier
- Quota logs stored locally (no PII)
- Prompt library versioned in git for audit trail

**Files to Create:**
- `gemini-prompts/README.md`
- `gemini-prompts/lld-review.txt`
- `gemini-prompts/implementation-review.txt`
- `gemini-prompts/issue-review.txt`
- `gemini-prompts/session-log.txt`
- `tools/gemini-model-check.sh`
- `.claude/workflow-state.json`
- `tmp/gemini-quota-events.jsonl`
- `docs/0602-skill-gemini-dual-review.md` ← Master skill doc

**Files to Modify:**
- `CLAUDE.md` - Add "Gemini Dual-Review Integration" section
- `docs/0004-orchestration-protocol.md` - Update review gates
- `docs/0600-skill-instructions-index.md` - Add 0602 reference
- `.claude/settings.local.json` - Add Gemini CLI permissions

**Acceptance Criteria:**
- [ ] LLD save auto-triggers Gemini review
- [ ] Model downgrade detected 100% of the time (unit tests pass)
- [ ] Implementation review requires dual approval (Gemini + User)
- [ ] Quota exhaustion aborts gracefully with user notification
- [ ] Session logs written by Gemini validated by Claude
- [ ] All 7 integration tests pass
- [ ] Prompt library versioned and documented

**Definition of Done:**
- [ ] All files created per "Files to Create" section
- [ ] All files modified per "Files to Modify" section
- [ ] Implementation report: `docs/reports/{IssueID}/implementation-report.md`
- [ ] Test report: `docs/reports/{IssueID}/test-report.md`
- [ ] Unit tests for model detection pass
- [ ] Integration tests for all 3 phases pass
- [ ] Documentation: `docs/0602-skill-gemini-dual-review.md` complete
- [ ] CLAUDE.md updated with dual-review section
- [ ] 0600 index updated to reference 0602
- [ ] Pre-commit hooks pass
- [ ] Gemini reviewed and approved
- [ ] User tested and approved
- [ ] Session log entry written

---

## Issue #232: audit: Create 0899 Meta-Audit Validation (CRITICAL)

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Problem
The meta-audit (0899) is referenced in the audit index but **does not exist**. This audit is supposed to verify that other audits were actually executed.

## Evidence
From 0800-audit-index.md: '0899 Meta-Audit Validation' is listed but no file exists at docs/0899-*.md

## Impact
Without this, agents can claim to execute audits with no verification. The entire audit system lacks a validation layer.

## Acceptance Criteria
- [ ] Create docs/0899-meta-audit-validation.md
- [ ] Scan all audit records for execution history
- [ ] List missing/overdue audits
- [ ] Add CI job that blocks if any quarterly audit is overdue
- [ ] Add CI job that verifies audit records were filled when claimed

## Priority
CRITICAL - This is the audit-of-audits. Everything else depends on it.

---

## Issue #233: audit: Create 0898 Horizon Scanning Protocol

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Problem
The horizon scanning audit (0898) is referenced in the audit index but **does not exist**. This audit is supposed to detect when referenced frameworks/standards are updated.

## Evidence
From 0800-audit-index.md: '0898 Horizon Scanning Protocol' is listed but no file exists at docs/0898-*.md

## Impact
Audits reference external standards (OWASP Top 10:2025, ISO 42001:2023, EU AI Act). When these standards update, we have no process to detect the change. Audits become stale.

## Acceptance Criteria
- [ ] Create docs/0898-horizon-scanning-protocol.md
- [ ] Track all external framework references
- [ ] Quarterly check if frameworks have new versions
- [ ] Update audits when frameworks change

## Priority
HIGH - Framework drift undermines audit validity

---

## Issue #234: audit: Remove Exception Registry self-excuse mechanism (0825)

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Problem
0825 AI Safety audit contains an 'Exception Registry' (§7) that allows agents to formally excuse audit failures with a 'budget of 2'.

## Evidence
From 0825-audit-ai-safety.md:
```
## 7. Exception Registry (ADR 0213)
**Exception Budget:** 2 (exceeding budget = automatic FAIL)
```

## Impact
This is **institutionalized self-excuse**. An agent can:
1. Fail an audit item
2. Add 'Justification' text they write themselves
3. Move on with work

No human approval required. No escalation.

## Acceptance Criteria
- [ ] Remove Exception Registry section from 0825
- [ ] Convert to 'Known Limitations' (advisory, not excusable)
- [ ] Require human (orchestrator) approval for any excused failure
- [ ] Create GitHub issue for ANY audit failure (no internal exceptions)

## Priority
CRITICAL - This undermines the entire audit system

---

## Issue #235: audit: Remove 'Justified Miss' self-excuse language (0812)

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Problem
0812 Performance audit contains 'Justified Miss' classification that allows agents to excuse any failure as an 'architectural trade-off'.

## Evidence
From 0812-audit-performance.md:
\
Actual audit record shows:
> **Status:** FAIL (500-1000ms vs 100ms target)
> **Excuse:** 'This is a Justified Miss because ADR 0201 prohibits \ permission'

## Impact
Agent writes justification AND accepts it. No oversight.

## Acceptance Criteria
- [ ] Remove 'Justified Miss' classification
- [ ] FAIL = FAIL (open issue)
- [ ] Trade-offs documented in ADR, not in audit
- [ ] Audit reflects reality, not excuses

## Priority
HIGH - This pattern appears in multiple audits

---

## Issue #236: audit: Enforce calendar schedule for 'as needed' audits (0811, 0817)

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Problem
Audits marked 'as needed' have no enforcement mechanism. Agents can defer indefinitely by claiming 'not needed now'.

## Evidence
0811 Accessibility - marked 'as needed' - **NEVER EXECUTED** (audit record completely empty)
0817 Wiki Alignment - marked 'on user-facing changes' - no calendar enforcement

## Impact
0811 has literally never been run. The entire audit exists but has zero execution history.

## Acceptance Criteria
- [ ] Replace 'as needed' with monthly minimum
- [ ] Replace 'on change' with monthly minimum + on change
- [ ] Add CI check: block if any audit > 30 days since last execution
- [ ] Run 0811 Accessibility immediately (it's never been run)

## Priority
HIGH - 0811 has NEVER been executed

---

## Issue #237: audit: Execute 0811 Accessibility audit (NEVER RUN)

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Problem
0811 Accessibility audit has **never been executed**. The audit record section is completely empty.

## Evidence
From 0811-audit-accessibility.md audit record:
```
| Date | Auditor | Findings Summary |
|------|---------|------------------|
| | | |
```

## Impact
We have accessibility requirements but no verification they are met. pa11y runs in CI but the formal audit has never been conducted.

## Acceptance Criteria
- [ ] Execute 0811 audit manually
- [ ] Fill in audit record with findings
- [ ] Create issues for any failures found
- [ ] Schedule recurring execution

## Priority
MEDIUM - Audit exists but has never been run

---

## Issue #238: audit: Execute 0818 AI Management/ISO 42001 audit (NEVER RUN)

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Problem
0818 AI Management System audit has **never been executed**. Audit record is empty.

## Evidence
Audit file exists with comprehensive checklist but no execution history.

## Acceptance Criteria
- [ ] Execute 0818 audit
- [ ] Fill in audit record
- [ ] Create issues for any failures

## Priority
MEDIUM - AI governance audit never run

---

## Issue #239: audit: Execute 0819 AI Supply Chain audit (NEVER RUN)

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Problem
0819 AI Supply Chain / OWASP LLM03 audit has **never been executed**. Audit record is empty.

## Evidence
Audit file exists with comprehensive checklist but no execution history.

## Acceptance Criteria
- [ ] Execute 0819 audit
- [ ] Fill in audit record
- [ ] Create issues for any failures

## Priority
MEDIUM - Supply chain security audit never run

---

## Issue #240: audit: Execute 0820 Explainability/XAI audit (NEVER RUN)

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Problem
0820 Explainability / XAI audit has **never been executed**. Audit record is empty.

## Evidence
Audit file exists with comprehensive checklist but no execution history.

## Acceptance Criteria
- [ ] Execute 0820 audit
- [ ] Fill in audit record
- [ ] Create issues for any failures

## Priority
MEDIUM - Explainability audit never run

---

## Issue #241: audit: Execute 0821 Agentic AI Governance audit (NEVER RUN)

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Problem
0821 Agentic AI Governance / OWASP Agentic 2026 audit has **never been executed**. Audit record is empty.

## Evidence
Audit file exists with comprehensive checklist but no execution history.

## Acceptance Criteria
- [ ] Execute 0821 audit
- [ ] Fill in audit record
- [ ] Create issues for any failures

## Priority
HIGH - This governs our agent behavior, never verified

---

## Issue #242: audit: Execute 0822 Bias and Fairness audit (NEVER RUN)

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Problem
0822 Bias and Fairness / ISO 24027 audit has **never been executed**. Audit record is empty.

## Evidence
Audit file exists with comprehensive checklist but no execution history.

## Acceptance Criteria
- [ ] Execute 0822 audit
- [ ] Fill in audit record
- [ ] Create issues for any failures

## Priority
MEDIUM - Bias audit never run

---

## Issue #243: audit: Execute 0823 AI Incident Post-Mortem (NEVER RUN)

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Problem
0823 AI Incident Post-Mortem audit framework exists but has **never been triggered**. No incident records.

## Evidence
Audit file exists with comprehensive framework but incident log is empty.

## Acceptance Criteria
- [ ] Review if any past incidents should have triggered 0823
- [ ] Document the incident history (even if retroactive)
- [ ] Ensure incident classification is not agent-discretionary

## Priority
MEDIUM - Incident audit framework never used

---

## Issue #244: audit: Remove N/A bypass mechanism from all audits

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Problem
Multiple audits allow entire sections to be skipped with 'N/A (not applicable)' without verification that the condition still holds.

## Evidence
From 0825 AI Safety:
- LLM04: Data Poisoning - N/A (no fine-tuning)
- LLM08: Vector/Embedding - N/A (no RAG)
- AA02: Rogue Agents - N/A (no agent persistence)
- AA03: Memory Poisoning - N/A (no memory)

## Impact
If code changes (e.g., fine-tuning added), agent could fail to notice the N/A is now wrong.

## Acceptance Criteria
- [ ] Replace N/A with explicit verification check
- [ ] 'N/A because X' must verify X is still true
- [ ] Add re-verification dates to N/A items
- [ ] Quarterly review of all N/A items

## Priority
HIGH - N/A is a stealth bypass

---

## Issue #245: audit: Add tool integrity verification to CI

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Problem
Silent tool failures are treated as passes. If ESLint crashes, agent sees '0 errors' and moves on.

## Evidence
From 0813 Code Quality Audit:
> On 2026-01-08, ESLint security plugins were declared in package.json but never installed. ESLint crashed with ERR_MODULE_NOT_FOUND. The audit noted 'NPM unmet dependencies' as MEDIUM priority without realizing this meant zero security linting.

## Impact
A crashed tool produces no output. No output looks like 'passed'. This is invisible failure.

## Acceptance Criteria
- [ ] CI job verifies ESLint actually ran (check for expected output pattern)
- [ ] CI job verifies pytest collected > 0 test items
- [ ] CI job verifies ruff processed files (not empty run)
- [ ] Fail-loud if any tool appears broken
- [ ] No silent failures treated as pass

## Priority
CRITICAL - Silent failures undermine all tooling

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

## Issue #247: audit: Add severity classification verification to 0823

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Problem
0823 Incident Post-Mortem allows agent to self-classify incident severity. An agent could classify a security breach as SEV-4 (minor) to reduce urgency.

## Evidence
From 0823:
- SEV-1: Critical - safety/security breach - Immediate
- SEV-4: Low - minor issues - < 1 week

Classification is entirely discretionary.

## Impact
Incident severity determines response time. Self-classification enables downgrading.

## Acceptance Criteria
- [ ] Add automated severity indicators
- [ ] Security keywords auto-classify as SEV-1
- [ ] User data exposure auto-classifies as SEV-1
- [ ] Agent classification is suggestion, human confirms

## Priority
HIGH - Self-classification is a loophole

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

## Issue #249: audit: Require auditor identity in all audit records

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Problem
Audit records do not consistently require auditor identity. Agent could fill in record anonymously.

## Evidence
Multiple audit records have 'Auditor' column but many entries are blank or generic.

## Impact
No accountability for audit quality. Can not trace who approved what.

## Acceptance Criteria
- [ ] All audit records require Auditor name
- [ ] Auditor must be commit author
- [ ] No anonymous audit entries
- [ ] Audit record validation in pre-commit

## Priority
MEDIUM - Accountability gap

---

## Issue #250: audit: Create audit overdue blocking in CI

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Problem
No CI mechanism blocks work when audits are overdue. Quarterly audits can be indefinitely deferred.

## Evidence
- 0818 ISO 42001: marked quarterly, never run
- 0819 Supply Chain: marked quarterly, never run
- No CI enforcement

## Impact
Scheduled audits are suggestions, not requirements.

## Acceptance Criteria
- [ ] CI job tracks last audit execution dates
- [ ] Blocks merge if any quarterly audit > 90 days overdue
- [ ] Blocks merge if any monthly audit > 30 days overdue
- [ ] Warning at 75% threshold

## Priority
HIGH - Schedule enforcement is missing

---

## Issue #251: audit: Fix ESLint security plugin installation (0813 finding)

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Problem
0813 Code Quality audit found ESLint security plugins were declared but never installed. ESLint crashed silently.

## Evidence
From 0813 audit record 2026-01-08:
> ESLint security plugins declared in package.json but never installed
> ESLint crashed with ERR_MODULE_NOT_FOUND

## Impact
Zero JavaScript security linting. Silent failure treated as pass.

## Acceptance Criteria
- [ ] Run npm install to install declared dependencies
- [ ] Verify eslint-plugin-security is working
- [ ] Add CI check that ESLint actually produces output
- [ ] No silent ESLint failures

## Priority
HIGH - Security linting is broken

---

## Issue #252: audit: Add external framework version tracking (drift detection)

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Problem
Audits reference external frameworks (OWASP Top 10, ISO 42001, EU AI Act) but have no process to detect when frameworks update.

## Evidence
- 0809 references 'OWASP Top 10:2025'
- 0818 references 'ISO/IEC 42001:2023'
- 0821 references 'OWASP Agentic 2026'
- No tracking of when these are superseded

## Impact
Audits against outdated frameworks give false compliance.

## Acceptance Criteria
- [ ] Create framework version registry
- [ ] Track publication dates
- [ ] Quarterly check for new versions
- [ ] Alert when framework updates detected

## Priority
MEDIUM - Long-term staleness risk

---

## Issue #253: audit: Document all audit failures as GitHub issues (policy)

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Problem
Current policy allows audit findings to be documented internally without creating tracking issues. Findings can be hidden in audit records.

## Proposal
ALL audit findings must create GitHub issues:
- FAIL → Issue created immediately
- WARN → Issue created with 'low-priority' label
- INFO → Optional issue

## Rationale
GitHub issues are visible, trackable, and cannot be quietly dismissed. Internal audit records can be edited or forgotten.

## Acceptance Criteria
- [ ] Update CLAUDE.md with issue creation requirement
- [ ] Update 0800-audit-index with policy
- [ ] Pre-commit hook: block if audit record shows FAIL but no issue link
- [ ] No internal-only failures

## Priority
HIGH - Visibility and accountability

---

## Issue #254: audit: Create missing system integration audits

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Problem
Multiple system integration areas have no audit coverage:
- Bedrock guardrails configuration
- DynamoDB schema compliance
- Lambda environment variable security
- Claude Code model versions

## Evidence
No 08xx file covers these areas. Audit index has no entries.

## Impact
Critical infrastructure configurations are unverified.

## Acceptance Criteria
- [ ] Create 0826 Model Version Audit (Claude/Bedrock tracking)
- [ ] Create 0827 Guardrails Configuration Audit
- [ ] Create 0828 Infrastructure Security Audit
- [ ] Add to audit schedule

## Priority
MEDIUM - Coverage gaps

---

## Issue #256: Fix Firefox OAuth - implement tabs-based flow

**Created:** 2026-01-10
**Updated:** 2026-01-10

### Description

## Problem

Firefox MV3 does not have `browser.identity` API. The current `auth.js` uses:
- `browser.identity.getRedirectURL()`
- `browser.identity.launchWebAuthFlow()`

These don't exist in Firefox, causing: `can't access property "getRedirectURL", browser.identity is undefined`

## Solution

Implement tabs-based OAuth flow for Firefox:
1. Use `browser.tabs.create()` to open LinkedIn auth page
2. Monitor for OAuth callback redirect
3. Extract auth code from callback URL
4. Complete token exchange

## References

- Audit: docs/0826-audit-cross-browser-testing.md
- Related: #206, #216, #231

---
