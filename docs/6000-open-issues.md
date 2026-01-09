# Aletheia - Open Issues

**Generated:** 2026-01-09 02:45 CT
**Total Open Issues:** 16

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

## Issue #103: Establish standards for log documents to prevent print overflow

**Labels:** documentation, enhancement

**Created:** 2025-12-29
**Updated:** 2025-12-29

### Description

## Problem

Log documents (9000-lessons-learned.md, 9001-open-investigations.md, ENGINEERING-JOURNAL.md) have formatting issues that cause print overflow - lines running off the right edge when printed.

## Audit Findings

Ran audit on all 40 docs/*.md files - **32 have line overflow issues**:

**Worst offenders:**
- 6000-open-issues-2025-12-28.md: 554 chars max (31 long lines)
- 9000-lessons-learned.md: 499 chars max (9 long lines)
- ENGINEERING-JOURNAL.md: 370 chars max (28 long lines)
- 9001-open-investigations.md: 318 chars max (4 long lines)

**Root causes:**
- Long URLs without line breaks
- Wide tables
- Code blocks with long lines
- Lack of markdown line wrapping

## Proposed Solution

Create documentation standards for log files (9xxx and session logs):

1. **Line Length Limit**: Max 100 characters per line
2. **URL Formatting**: Use markdown link syntax `[text](url)` instead of bare URLs
3. **Table Width**: Limit tables to 5-6 columns max, use abbreviations
4. **Code Blocks**: Add manual line breaks in long command examples
5. **Enforcement**: Add to 0002-coding-standards.md Section on Log Files

## Acceptance Criteria

- [ ] Standards documented in 0002-coding-standards.md
- [ ] Template created for log entries (if needed)
- [ ] Existing log files updated to meet standards (or noted as legacy)
- [ ] Print audit passes with <10 files having overflow

## Notes

LaTeX wrapping (`fvextra`, `hyperref`) helps but doesn't fully solve the problem for poorly formatted logs. Prevention is better than fixing during print generation.

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

## Issue #107: Debug VSCode Mermaid diagram preview

**Labels:** documentation, chore

**Created:** 2025-12-29
**Updated:** 2025-12-29

### Description

## Summary
VSCode is not rendering Mermaid diagrams in markdown preview. Need to debug and fix.

## Current State
- Mermaid diagrams render correctly on GitHub
- VSCode markdown preview shows raw mermaid code blocks
- Workaround: Copy/paste to mermaid.live (tedious)

## Potential Solutions
1. Install "Markdown Preview Mermaid Support" extension
2. Install "Mermaid Preview" extension
3. Check VSCode settings for markdown preview extensions
4. Verify mermaid code block syntax (triple backticks + mermaid)

## Priority
**Low** - GitHub works as fallback. Defer until after store submission.

## Acceptance Criteria
- [ ] Mermaid diagrams render in VSCode markdown preview
- [ ] Document working configuration in README or dev setup guide

---

## Issue #108: Printing pipeline: Render Mermaid diagrams to PDF

**Labels:** documentation, chore

**Created:** 2025-12-29
**Updated:** 2025-12-29

### Description

## Summary
The markdown-to-PDF printing pipeline (tools/print/print_markdown.py) does not render Mermaid diagrams. They appear as raw code blocks in printed output.

## Current State
- Pandoc + XeLaTeX converts markdown to PDF
- Mermaid code blocks pass through as-is (not rendered)
- GitHub renders them correctly (web only)

## Potential Solutions

### Option A: Pre-process with mermaid-cli
1. Install `@mermaid-js/mermaid-cli` (mmdc)
2. Before pandoc, extract mermaid blocks and render to PNG/SVG
3. Replace code blocks with image references
4. Run pandoc on modified markdown

### Option B: Pandoc filter
1. Use a Lua filter or pandoc-mermaid-filter
2. Automatically converts mermaid blocks during PDF generation

### Option C: Export from mermaid.live manually
1. When updating docs, export diagrams as images
2. Embed images instead of mermaid code
3. Keep mermaid source in comments for future edits

## Recommendation
**Option A** - cleanest integration with existing pipeline.

## Priority
**Low** - defer until after store submission. GitHub works for viewing.

## Acceptance Criteria
- [ ] Mermaid diagrams render as images in printed PDFs
- [ ] Automated (no manual export step)
- [ ] Update print_markdown.py or create wrapper

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

## Issue #152: Evaluate GitHub Code Scanning (CodeQL) setup

**Labels:** security, chore, post-mvp

**Created:** 2026-01-04
**Updated:** 2026-01-04

### Description

## Context

GitHub offers Code Scanning via CodeQL for static security analysis. Currently shows "Needs setup" in Security tab.

## Evaluation Needed

### Potential Benefits
- Finds security vulnerabilities in Python and JavaScript
- Integrated with GitHub (alerts in Security tab)
- Free for public repositories

### Potential Conflicts
- **Existing linting:** We already have ruff, mypy, ESLint
- **SonarQube:** If we add SonarQube later, may have overlapping coverage
- **CI time:** Adds ~2-5 minutes to workflow runs
- **False positives:** May flag patterns that are intentional

### Languages to Scan
- Python (Lambda, tools)
- JavaScript (browser extensions)

## Decision Points

1. **Do we need CodeQL given existing tooling?**
   - ruff: Python linting + some security rules
   - mypy: Type checking (catches some bugs)
   - ESLint: JavaScript linting
   - gitleaks: Secret scanning (pre-commit)

2. **CodeQL vs SonarQube?**
   - CodeQL: GitHub-native, simpler setup
   - SonarQube: More comprehensive, separate service

3. **When to add?**
   - Now: Get baseline before more code
   - Post-MVP: When we have more complex code

## Setup (If Approved)

```yaml
# .github/workflows/codeql.yml
name: "CodeQL"
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * 1'  # Weekly Monday

jobs:
  analyze:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: python, javascript
      - uses: github/codeql-action/analyze@v3
```

## Acceptance Criteria

- [ ] Decision made: Enable CodeQL or defer
- [ ] If enabled: Workflow added and passing
- [ ] If enabled: Initial scan reviewed, false positives triaged
- [ ] Document decision in ADR if significant

## References

- [GitHub CodeQL docs](https://docs.github.com/en/code-security/code-scanning/introduction-to-code-scanning/about-code-scanning-with-codeql)
- [CodeQL for Python](https://codeql.github.com/docs/codeql-language-guides/codeql-for-python/)

---

## Issue #160: chore: Automate accessibility checks in CI (pa11y/axe-core)

**Labels:** testing, chore

**Created:** 2026-01-05
**Updated:** 2026-01-05

### Description

## Context

0899 Meta-Audit identified that 0811 (Accessibility) is currently a manual procedure with high toil, likely to be skipped during crunch times.

## Proposal

Add automated accessibility scanning to CI pipeline using:
- **pa11y** - CLI accessibility testing
- **axe-core** - Accessibility testing engine (used by Playwright)

## Implementation Options

### Option A: pa11y in CI
\
added 128 packages in 40s

8 packages are looking for funding
  run aletheia@1.0.0
├─┬ https://eslint.org/donate
│ │ └── eslint@9.39.2, @eslint/js@9.39.2
│ ├── https://opencollective.com/eslint
│ │   └── @eslint-community/eslint-utils@4.9.1, eslint-visitor-keys@3.4.3, @eslint/eslintrc@3.3.3, eslint-scope@8.4.0, eslint-visitor-keys@4.2.1, espree@10.4.0
│ ├── https://github.com/sponsors/nzakas
│ │   └── @humanwhocodes/module-importer@1.0.1, @humanwhocodes/retry@0.4.3
│ ├── https://github.com/sponsors/epoberezkin
│ │   └── ajv@6.12.6, ajv@8.12.0
│ └─┬ https://github.com/chalk/chalk?sponsor=1
│   │ └── chalk@4.1.2, chalk@5.0.1
│   └── https://github.com/chalk/ansi-styles?sponsor=1
│       └── ansi-styles@4.3.0, ansi-styles@6.2.3
├── https://github.com/chalk/chalk-template?sponsor=1
│   └── chalk-template@0.4.0
└── https://github.com/sponsors/ljharb
    └── minimist@1.2.8 for details

Welcome to Pa11y

 > Running Pa11y on URL http://localhost:8080/popup.html
### Option B: axe-core with Playwright
\
## Acceptance Criteria

- [ ] CI fails on WCAG Level A violations
- [ ] CI warns on WCAG Level AA violations
- [ ] Popup.html and overlay tested
- [ ] Results logged for audit record

## References

- 0811 Accessibility Audit: - 0899 Meta-Audit recommendation #1
- Issue #154 (ARIA attributes) - manual fixes needed first

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

## Issue #189: Test suite gaps: missing test_build_release.py and orphan test_guardrails.py

**Created:** 2026-01-07
**Updated:** 2026-01-07

### Description

## Summary

During the regression test suite audit (#189 task), the following gaps were identified:

## Missing Tests

### `test_build_release.py`
- **Status:** MISSING
- **Expected location:** `tests/tools/test_build_release.py`
- **Context:** Mentioned in task requirements for consolidating tests. The `tools/build_release.py` script (Issue #53) has no automated tests.
- **Recommendation:** Create unit tests for the build script covering:
  - Icon verification
  - Manifest parity check
  - Version extraction
  - Zip file generation

## Orphan Tests

### `test_guardrails.py`
- **Status:** Present but not mentioned in any `docs/reports/*/test-report.md`
- **Location:** `tests/unit/test_guardrails.py`
- **Questions:**
  - Which issue created this file?
  - Should it be documented in a report?
  - Is it still relevant or can it be merged into another test file?

## Action Items

- [ ] Create `tests/tools/test_build_release.py` for Issue #53
- [ ] Investigate `test_guardrails.py` origin and document or consolidate

---
*Found during test suite reorganization audit*

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

## Issue #205: chore: Strengthen /cleanup to auto-delete orphaned branches

**Created:** 2026-01-09
**Updated:** 2026-01-09

### Description

## Incident Report

**Date:** 2026-01-09
**Symptom:** Branch `126-hard-soft-blocking` found orphaned during `/cleanup`
**Root Cause:** POST-MERGE GATE did not exist; agent removed worktree but forgot to delete local branch

### Timeline

| Time | Event |
|------|-------|
| 08:11 UTC | PR #202 merged via `gh pr merge` |
| 08:11 UTC | GitHub auto-deleted remote branch |
| ~08:12 UTC | Agent removed worktree (assumed) |
| **MISSING** | Agent did NOT delete local branch |
| 10:15 UTC | `/cleanup` flagged orphan branch |

## Immediate Fix (Completed)

- [x] Added POST-MERGE GATE to CLAUDE.md with explicit 4-step checklist
- [x] Added Step 12 Cleanup Checklist to 0004-orchestration-protocol.md
- [x] Documented incident in both files as cautionary example
- [x] Deleted orphan branch `126-hard-soft-blocking`

## Proposed Enhancement

The `/cleanup` skill currently **reports** orphaned branches but does not **delete** them.

### Proposed: Auto-Delete Safe Orphans

Add logic to `.claude/commands/cleanup.md`:

```
For each local branch != main:
  1. Check if remote exists: git branch -vv | grep "origin/.*: gone"
  2. Check if worktree exists: git worktree list | grep branch-name
  3. If remote=gone AND worktree=none:
     → Branch is safely deletable (completed work, merged, cleaned up remotely)
     → Auto-delete: git branch -D {branch-name}
     → Report: "Deleted orphan branch: {branch-name}"
```

### Safety Criteria

Only auto-delete if ALL conditions are met:
- [x] Branch is not `main`
- [x] Remote tracking shows `gone` (was deleted on GitHub)
- [x] No worktree exists for this branch
- [x] Branch has no unpushed commits (implicit: remote existed and was deleted)

### Implementation

1. Update `.claude/commands/cleanup.md` Phase 2 to include auto-delete logic
2. Add `--no-auto-delete` flag for conservative mode
3. Report all deletions in cleanup summary

## Acceptance Criteria

- [ ] `/cleanup` auto-deletes branches where remote is `gone` and no worktree exists
- [ ] Deletions are reported in summary table
- [ ] `--no-auto-delete` flag available for manual control
- [ ] POST-MERGE GATE in CLAUDE.md prevents future orphans

## Labels

`chore`, `process-improvement`, `cleanup`

---
