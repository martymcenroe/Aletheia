Print mode: double-sided

Fetching open issues from GitHub...
Fetched 20 open issues
Saving to docs\6000-open-issues.md...
Saved docs\6000-open-issues.md
Generating PDF with pandoc...
Generated temp-pdfs\6000-open-issues.pdf
Printing temp-pdfs\6000-open-issues.pdf...
Double-sided printing requested.
Sent to printer: Brother HL-L6300DW series Printer (double-sided)

Complete!
   Markdown: docs\6000-open-issues.md
   PDF: temp-pdfs\6000-open-issues.pdf (deleted after print)
   Printed to: Brother HL-L6300DW series Printer (double-sided)
en usage.

## Updated Context
LangSmith removed from scope (LangChain-specific, we're using Naked Python per ADR 0211).

## Goals
- End-to-end request tracing via X-Ray
- Bedrock token usage metrics in CloudWatch
- Cold start latency monitoring
- Error rate dashboards

## Technical Approach
- Enable X-Ray tracing on Lambda
- Use `boto3` X-Ray SDK for custom subsegments (Guardrails, Bedrock calls)
- CloudWatch custom metrics for token counts
- CloudWatch Logs Insights for query patterns

---

## Issue #51: Chrome Web Store Compliance

**Labels:** high-priority, chore

**Created:** 2025-12-10
**Updated:** 2025-12-24

### Description

Prepare assets (Manifest, Privacy Policy, Store Listing) for submission.

---

## Issue #53: Generate Store Assets

**Labels:** chore

**Created:** 2025-12-10
**Updated:** 2026-01-02

### Description

## Objective
Create a script (`tools/generate_store_assets.py`) to deterministically generate production-ready assets for the Chrome Web Store submission.

## Requirements

### 1. Icon Generation
- **Input:** `tools/master_lambda.png` (High-res source)
- **Output:** `extension/icons/` {16, 32, 48, 128}.png
- **Constraint:** Transparent backgrounds, optimized PNGs.

### 2. Promotional Tiles (Placeholders)
- **Small Tile:** 440x280px (Required by Store) - Simple brand color background + Logo.
- **Marquee:** 1400x560px (Required by Store) - "Context, Verified" tagline.

### 3. Zip Packaging
- Script must create `aletheia-v{version}.zip`.
- **CRITICAL EXCLUSIONS:** `src/` (Python backend), `.git/`, `docs/`, `tests/`, `.env`.
- **INCLUSIONS:** `manifest.json`, `service-worker.js`, `overlay.js`, `popup.html`, `popup.js`, `popup.css`, `icons/`.

## Acceptance Criteria
- [ ] Zip file contains **only** client-side artifacts.
- [ ] No Python code or secrets leaked in the extension zip.

---

## Issue #81: Redesign landing page: modern professional aesthetic

**Labels:** feature

**Created:** 2025-12-21
**Updated:** 2025-12-24

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

## Issue #102: chore: Reorganize repository structure for professional appearance

**Labels:** chore

**Created:** 2025-12-29
**Updated:** 2025-12-29

### Description

## Problem
Repository root has 24 tracked files (vs professional standard of ~10-15 config files). This looks disorganized to visitors on GitHub.

## Current Root (24 files)
**Config (8):** .gitignore, LICENSE, README.md, pyproject.toml, poetry.lock, CLAUDE.md, GEMINI.md, CHATGPT.md ✅
**App Code (5):** agent.py, checkpointer.py, compliance.py, lambda_function.py, lambda_harvester_function.py
**Scripts (4):** aws-cleanup-old-resources.sh, aws-inventory-check.sh, deploy.sh, provision.sh
**Tools (4):** harvest_test_data.py, run_guardrails.py, verify_bedrock.py, verify_holistic.py
**Test Data (2):** test_ground_truth.json, test_holistic_data.json
**Legacy (1):** index.html (KEEP - has privacy policy for Chrome Store)

## Proposed Structure
```
aletheia/
├── [8 config files in root] ✅
├── src/                        # Move 5 app code files here
├── scripts/aws/                # Move 4 AWS scripts here
├── tools/                      # Move 4 tools here + print scripts
└── tests/data/                 # Move 2 test data files here
```

## Migration Plan

### Phase 1: Application Code (CRITICAL - Test First!)
Move to `src/`:
- agent.py
- checkpointer.py
- compliance.py
- lambda_function.py
- lambda_harvester_function.py

**⚠️ BLOCKER:** Lambda deployment may break. Test:
1. Update deploy.sh to handle new paths
2. Test provision.sh still works
3. Verify Lambda functions deploy correctly
4. Check all import paths in Python code

### Phase 2: Scripts (Safe)
Move to `scripts/aws/`:
- aws-cleanup-old-resources.sh
- aws-inventory-check.sh
- deploy.sh
- provision.sh

### Phase 3: Tools (Safe)
Move to `tools/`:
- harvest_test_data.py
- run_guardrails.py
- verify_bedrock.py
- verify_holistic.py
- [Print scripts from local .gitignored files]

### Phase 4: Test Data (Safe)
Move to `tests/data/`:
- test_ground_truth.json
- test_holistic_data.json

## Testing Requirements
- [ ] All Python imports still resolve
- [ ] deploy.sh successfully deploys Lambda
- [ ] provision.sh still provisions infrastructure
- [ ] Local tools (log_viewer.py, etc.) still work
- [ ] pytest runs successfully
- [ ] Lambda functions execute in AWS

## Acceptance Criteria
- [ ] Root directory has ≤15 files (only config)
- [ ] All files in logical directories
- [ ] No broken imports
- [ ] Deployment pipeline still works
- [ ] All tests pass

## Priority
Medium - Improves professionalism but not user-facing. Complete before going public or seeking contributors.

## Prep Work Done
- Created directory structure (scripts/aws/, tests/data/, tools/print/)
- Deleted legacy/ directory (only contained .py_bak files)

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
**Updated:** 2025-12-29

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

## Issue #116: feat: Authenticate users via LinkedIn OAuth

**Labels:** security, feature

**Created:** 2025-12-30
**Updated:** 2025-12-30

### Description

## Summary
Implement LinkedIn OAuth authentication to gate extension features and enable user identification.

## Why LinkedIn?
- LinkedIn enforces one account per person (reduces abuse vs. disposable email signups)
- Professional identity signal
- Foundation for future tiered access (free/paid)

## Requirements
1. **OAuth Flow:** Standard OAuth 2.0 with LinkedIn API
2. **Token Storage:** Secure storage of access/refresh tokens
3. **Session Management:** Handle token expiration and refresh
4. **UI:** Login button in popup, auth status indicator

## Technical Considerations
- Chrome Identity API vs. manual OAuth flow
- LinkedIn API scopes needed (profile, email?)
- Backend token validation (Lambda)
- Logout/disconnect functionality

## Out of Scope (Future Issues)
- Tiered access (free/paid)
- Other OAuth providers (Google, GitHub)
- Trial/anonymous access

## Related
- Supersedes #25 (cookie heuristic - closed)
- Supersedes #88 (LLD rewrite - closed)
- Legacy doc: `docs/1025-linkedin-auth-gate.md`

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
**Updated:** 2025-12-31

### Description

## Concept

The Aletheia documentation system has evolved beyond a Content Management System (CMS) into something more fundamental: an **Agent Operating System (AOS)**—executable documentation that AI agents run as their program.

## The Insight

"CMS" undersells what this is. The docs aren't just reference material—they're the instructions agents execute.

## The AOS Layers

| Layer | What It Does | Examples |
|-------|--------------|----------|
| **Process Automation** | Checklists that execute, not just document | 0009 (Closeout), 0011 (Cleanup) |
| **Context Persistence** | State preserved across sessions and agents | Session logs, IMMEDIATE-PLAN |
| **Agent Orchestration** | Who does what, when, how | CLAUDE.md, GEMINI.md, 0004 |
| **Reality Verification** | Don't trust metadata—verify actual state | 0011 Section 6 |
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
- `docs/0011-environment-cleanup-checklist.md` - Section 6 (IMMEDIATE-PLAN verification)
- `docs/0009-session-closeout-protocol.md` - Escalation to 0011

## Publication Notes

- Target audience: AI/ML practitioners, developer tooling engineers, anyone working with AI agents
- Angle: Novel framing of documentation as executable infrastructure
- Could include diagrams showing the "OS layers" and agent execution flow

---

## Issue #125: feat: Implement 'Museum Label' Progressive Disclosure UI

**Labels:** feature, frontend

**Created:** 2025-12-31
**Updated:** 2025-12-31

### Description


## Objective
Update the overlay UI to support the 'Signal -> Gem -> Context' progressive disclosure flow.

## The 'Museum Label' Concept
Users should not be overwhelmed. They should see the artifact (Signal) and a brief description (Gem). The deep history (Context) is opt-in.

## UX Flow
1. **Tier 1 (Glance):** Show the Amber/Red Badge + The 'Signal' (Category).
2. **Tier 2 (Hover):** Show The 'Gem' (1-sentence summary).
3. **Tier 3 (Click/Expand):** Reveal The 'Context' (Full historical detail).

## Technical Changes
- Update `overlay.js` to parse the new JSON response.
- Create CSS animations for the expansion (smooth slide-down).
- Ensure the 'Close' button is always accessible.

## Acceptance Criteria
- [ ] UI defaults to compact view (Signal + Gem).
- [ ] 'Expand' action reveals full context.
- [ ] Visual hierarchy clearly distinguishes the three tiers.


---

## Issue #126: feat: Implement Hard vs. Soft Blocking Logic

**Labels:** feature, core-logic

**Created:** 2025-12-31
**Updated:** 2026-01-01

### Description


## Objective
Differentiate between 'Forbidden' terms (Denylist) and 'Educational' terms (Semantic Analysis).

## The Split
1. **Hard Block (The Denylist):**
   - **Source:** `src/guardrails/resources/denylist.json` (Wikipedia-sourced via Issue #121)
   - **Action:** Immediate 403 Forbidden.
   - **UX:** 'Blocked: Hate Speech detected.' (No further interaction allowed).
   - **Target:** Well-known slurs, severe hate speech (e.g., words that a writer replaces with just one letter and -word e.g. Z-word).

2. **Soft Block (The Semantic Warning):**
   - **Source:** Bedrock Semantic Analysis.
   - **Action:** 200 OK (with Warning payload).
   - **UX:** Show 'Potential Issue' Amber Badge. User *can* read the 'Erudite' explanation and choose to dismiss/ignore.
   - **Target:** Nuanced terms, archaic phrases, dogwhistles.

## Implementation
- Update `lambda_function.py` to ensure Denylist remains 'Fail Closed'.
- Update Semantic layer to return a 'Warning' classification instead of a hard block, passing the context to the frontend.

## Acceptance Criteria
- [ ] Denylist terms trigger immediate blocking (Green tests).
- [ ] Semantic 'gray area' terms allow the user to see the explanation.

---

## Issue #127: process: Implement 'Active Plan' and 'Context Injection' Protocols

**Labels:** process, workflow

**Created:** 2025-12-31
**Updated:** 2025-12-31

### Description


## Context (From Paper 2512.14012)
Research indicates that expert developers do not 'vibe'; they control. Two specific techniques identified for maintaining control are **Plan Files** (externalizing state) and **Context Injection** (referencing specific domain objects/files).

## Objective
Update our Orchestration Protocols (0004/0008) to force agents to explicitly track state and reference context, rather than relying on implicit context window retention.

## Requirements

### 1. The 'Active Plan' File
During a Mini-Sprint, the working Agent must maintain a temporary file in the worktree (e.g., `CURRENT_STATUS.md`).
- **Content:** The specific steps from the LLD being executed.
- **Update Frequency:** Must be updated *before* claiming a step is done.
- **Goal:** Prevents the agent from 'claiming victory so soon' and provides a save point if the session crashes.

### 2. 'Context Type' Injection in Prompts
Update `docs/0008-orchestrator-instructions.md` to require **Plan-Referenced Prompting**.
- **Forbidden:** 'Fix the validation function.'
- **Required:** 'Implement **Step 3** of `docs/1113-naked-python.md`. Modify **only** `lambda_function.py`. The input is the **Event Object** defined in Section 6.2.'
- **Key Context Types to Reference:**
    - Reference to Step in Plan
    - Reference to Output File (Target)
    - Domain Object (Specific terminology)

## Definition of Done
- [ ] `docs/0004-orchestration-protocol.md` updated with 'Active Plan' requirement.
- [ ] `docs/0008-orchestrator-instructions.md` updated with Prompting Templates.


---

## Issue #128: process: Formalize 'Scaffolding vs. Logic' Task Splitting

**Labels:** core-logic, process

**Created:** 2025-12-31
**Updated:** 2025-12-31

### Description


## Context (From Paper 2512.14012)
The paper identifies a distinct split in Agent Suitability:
- **Highly Suitable:** Scaffolding, Boilerplate, Writing Tests.
- **Unsuitable/Risky:** Complex Business Logic, Core Decision Making.

## Objective
Update our Issue Template and LLD process to split complex features into two distinct passes. We should not ask the agent to do both simultaneously.

## The Protocol Change
Modify `docs/0102-TEMPLATE-feature-lld.md` or `docs/0004-orchestration-protocol.md` to define the **Two-Pass Implementation**:

### Pass 1: The Skeleton (High Agent Autonomy)
- Create directory structures.
- Define function signatures (with type hints and docstrings).
- Create **Failing Tests** (The Test Harness).
- *Agent Mode:* Fast, high-autonomy.

### Pass 2: The Brain (High Human Control)
- Implement the specific business rules inside the signatures.
- Connect the actual logic.
- Verify against the Test Harness.
- *Agent Mode:* Step-by-step, high-supervision.

## Definition of Done
- [ ] Documentation updated to reflect the Two-Pass workflow.
- [ ] Example provided in `0004-orchestration-protocol.md`.


---

## Issue #129: audit: Integrate 'Red Team' Architecture Challenge

**Labels:** process, audit

**Created:** 2025-12-31
**Updated:** 2025-12-31

### Description


## Context (From Paper 2512.14012)
Experts use agents not just for code, but to 'collaboratively talk out problems' and challenge assumptions. The current workflow moves from LLD to Code too quickly without a critique phase.

## Objective
Insert a **'Red Team Challenge'** step into the Feature Lifecycle (`docs/0004`) before the LLD is marked 'Approved'.

## The Protocol
Before coding begins, a separate Model (e.g., Gemini if Claude wrote the LLD) must perform a hostile critique of the plan.

### The 'Critic' Persona
- **Goal:** Find hallucinations, over-engineering, and security gaps.
- **Prompt:** 'You are the Red Team. Attack this LLD. Find 3 ways it will fail in production. Find 1 dependency that doesn't exist.'

## Definition of Done
- [ ] `docs/0004-orchestration-protocol.md` updated with the Red Team step.
- [ ] `docs/0109-gemini-lld-review-procedure.md` updated to include specific 'Red Team' attack vectors.


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

## Issue #137: Investigate 5-second Lambda latency

**Created:** 2026-01-02
**Updated:** 2026-01-02

### Description

## Problem

The extension shows "Saving..." for ~5 seconds before transitioning to "Context Saved". This delay persists even with `max_tokens=10`, disproving the hypothesis that Sonnet generation time is the cause.

## Tested

- `max_tokens=10` in `src/lambda_function.py` - still 5 second delay
- Timer/gap bugs fixed in extension overlay (separate issue #100)

## Likely Causes to Investigate

1. **Lambda Cold Start** - First invocation after idle period spins up container
2. **Semantic Guardrail** - `SemanticGuardrail.check_safety()` makes an LLM call before generation
3. **DynamoDB Write** - `save_state()` is in the critical path
4. **Network Latency** - Round trip to AWS us-east-1

## Proposed Investigation

1. Add timing logs to each stage of `lambda_handler`:
   - Validation
   - Guardrails (denylist + semantic)
   - DynamoDB save
   - Bedrock generation
2. Identify the bottleneck
3. Consider:
   - Provisioned concurrency for cold starts
   - Caching semantic guardrail results
   - Moving DynamoDB write out of critical path (async)

## References

- Extension timing fixes: #100
- Gemini handoff doc: `docs/GEMINI-HANDOFF-OVERLAY-TIMING.md`

---
