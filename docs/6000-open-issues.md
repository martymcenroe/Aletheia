Print mode: double-sided

Fetching open issues from GitHub...
Fetched 28 open issues
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
**Updated:** 2026-01-04

### Description

Prepare assets (Manifest, Privacy Policy, Store Listing) for submission.

---

## Issue #53: Generate Store Assets

**Labels:** chore

**Created:** 2025-12-10
**Updated:** 2026-01-04

### Description

## Status Update (2026-01-04)
**Partially Complete:** `tools/generate_store_assets.py` and `tools/build_release.py` exist but reference old `extension/` path. Need to update for `extension-chrome-V3/` directory structure.

---

## Objective
Create a script (`tools/generate_store_assets.py`) to deterministically generate production-ready assets for the Chrome Web Store submission.

## Requirements

### 1. Icon Generation
- **Input:** `tools/master_lambda.png` (High-res source)
- **Output:** `extension-chrome-V3/icons/` {16, 32, 48, 128}.png
- **Constraint:** Transparent backgrounds, optimized PNGs.

### 2. Promotional Tiles (Placeholders)
- **Small Tile:** 440x280px (Required by Store) - Simple brand color background + Logo.
- **Marquee:** 1400x560px (Required by Store) - "Context, Verified" tagline.

### 3. Zip Packaging
- Script must create `aletheia-chrome-v{version}.zip` and `aletheia-firefox-v{version}.zip`.
- **CRITICAL EXCLUSIONS:** `src/` (Python backend), `.git/`, `docs/`, `tests/`, `.env`.
- **INCLUSIONS:** `manifest.json`, `service-worker.js`, `overlay.js`, `popup.html`, `popup.js`, `popup.css`, `icons/`, content scripts.

## Acceptance Criteria
- [ ] Zip file contains **only** client-side artifacts.
- [ ] No Python code or secrets leaked in the extension zip.
- [ ] Scripts updated for `extension-chrome-V3/` directory structure.

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

## Issue #145: Configure DynamoDB TTL for automatic data expiry

**Labels:** security, backend, audit

**Created:** 2026-01-04
**Updated:** 2026-01-04

### Description

## Problem

Privacy audit (0810) finding P1: DynamoDB stores user input text without TTL expiry.

**Current Behavior:**
- User-selected text is stored in DynamoDB `input` field (`src/lambda_function.py:122`)
- `provision.sh` does not configure `TimeToLiveSpecification`
- Data persists indefinitely

**Expected Behavior:**
- User data should auto-expire after 24-48 hours
- Aligns with ADR 0203 which states "TTL provides automatic data hygiene"

## Impact

- **Privacy:** User text persists longer than necessary
- **Compliance:** May conflict with data minimization principles (GDPR, CCPA)
- **Cost:** Accumulating stale data increases DynamoDB storage costs

## Proposed Solution

1. Add `ttl` attribute to DynamoDB items in `src/lambda_function.py`:
```python
item = {
    ...
    "ttl": {"N": str(int(time.time()) + 86400)},  # 24 hours
}
```

2. Enable TTL in `provision.sh`:
```bash
aws dynamodb update-time-to-live \
    --table-name "$TABLE_NAME" \
    --time-to-live-specification "Enabled=true,AttributeName=ttl"
```

## Acceptance Criteria

- [ ] Lambda adds TTL attribute to all DynamoDB items
- [ ] provision.sh enables TTL on table
- [ ] Existing data cleaned up (or allowed to expire naturally)
- [ ] Privacy audit 0810 updated to mark P1 as resolved

## References

- Privacy Audit: `docs/0810-audit-privacy.md` (P1)
- ADR 0203: Stateful Serverless (mentions TTL)
- Lambda handler: `src/lambda_function.py:119-124`
- Provision script: `provision.sh:16-22`

---

## Issue #147: GDPR: Implement data erasure process (right to be forgotten)

**Labels:** security, backend, audit

**Created:** 2026-01-04
**Updated:** 2026-01-05

### Description

## Context

GDPR Article 17 requires data controllers to have a process to erase personal data on request. As an EU trader/developer, Aletheia must comply.

**Related:** #145 (DynamoDB TTL) - TTL provides automatic erasure after 24-48 hours, but GDPR may require on-demand erasure.

## Current State

- User text stored in DynamoDB `input` field
- No mechanism for users to request data deletion
- No documented data retention policy

## Requirements

### 1. Data Inventory
Document all user data storage:
- DynamoDB: thread_id, input (user text), url, safety_score
- CloudWatch: Lambda logs (30 day retention)
- Extension: localStorage (preferences only, no PII)

### 2. Erasure Mechanism
Options to evaluate:
- A) **TTL-only approach**: Short TTL (24h) means data self-erases quickly
- B) **On-demand deletion**: API endpoint to delete by thread_id
- C) **User identification**: Requires auth (#116) to identify "my data"

### 3. Documentation
- Privacy policy must state retention period
- Must explain how users can request erasure

## Acceptance Criteria

- [ ] Data retention policy documented
- [ ] Erasure mechanism implemented (TTL or on-demand)
- [ ] Privacy policy updated with erasure process
- [ ] Privacy audit 0810 updated

## References

- [GDPR Article 17](https://gdpr-info.eu/art-17-gdpr/)
- Privacy Audit: `docs/0810-audit-privacy.md`
- Related: #145 (DynamoDB TTL)
- Related: #116 (LinkedIn Auth - enables user identification)

---

## Issue #148: Document AWS Bedrock no-training commitment

**Labels:** documentation, security, audit

**Created:** 2026-01-04
**Updated:** 2026-01-04

### Description

## Context

Our privacy policy promises we won't train on user data. We need to:
1. Verify AWS Bedrock's commitment to not training on customer prompts
2. Document this in our architecture/privacy docs
3. Ensure our Bedrock configuration enforces this

## AWS Bedrock Data Handling

Per [AWS Bedrock FAQ](https://aws.amazon.com/bedrock/faqs/):
> "Your content is not used to train the base models underlying Amazon Bedrock."

> "Amazon Bedrock does not store or log your prompts and completions."

## Verification Needed

- [ ] Confirm Bedrock model invocation doesn't enable training
- [ ] Verify CloudWatch logging settings for Bedrock calls
- [ ] Check if any Bedrock features opt into training (and avoid them)

## Documentation Updates

- [ ] Update `docs/0810-audit-privacy.md` with Bedrock verification
- [ ] Add to privacy policy: "We use AWS Bedrock which does not train on your data"
- [ ] Reference AWS commitment in `docs/0001-system-architecture.md`

## Acceptance Criteria

- [ ] AWS Bedrock TOS reviewed and documented
- [ ] Privacy audit confirms no-training guarantee
- [ ] Architecture docs updated with data flow privacy guarantees

## References

- [AWS Bedrock Privacy](https://aws.amazon.com/bedrock/faqs/#Security_and_Privacy)
- Privacy Audit: `docs/0810-audit-privacy.md` §6 (AI/LLM Privacy)
- [AWS Shared Responsibility Model](https://aws.amazon.com/compliance/shared-responsibility-model/)

---

## Issue #149: Investigate and possibly remove lambda_harvester_function.py

**Labels:** chore, audit

**Created:** 2026-01-04
**Updated:** 2026-01-04

### Description

## Context

`src/lambda_harvester_function.py` may have been created for testing/data harvesting purposes and might no longer be needed.

## Investigation Needed

- [ ] Determine original purpose of this file
- [ ] Check if it's deployed to AWS (separate Lambda?)
- [ ] Check if anything references it
- [ ] Verify it's not part of production flow

## Current State

- File: `src/lambda_harvester_function.py` (47 lines)
- Coverage: 0% (not unit tested)
- Listed in file inventory as "Data harvester Lambda handler"

## Decision

If no longer needed:
- [ ] Remove file
- [ ] Update `docs/0003-file-inventory.md`
- [ ] Remove any AWS resources if deployed

## References

- Code Quality Audit 0813: Listed as 0% coverage file
- File inventory: `docs/0003-file-inventory.md`

---

## Issue #150: AI-powered DynamoDB data hygiene tool

**Labels:** chore, feature, backend

**Created:** 2026-01-04
**Updated:** 2026-01-04

### Description

## Problem

DynamoDB contains test data from development that should be cleaned up. Manual review is tedious and error-prone. Need an AI-assisted tool to identify and remove low-value entries.

## Proposed Solution

Create a CLI tool (`tools/data_hygiene.py`) that uses AI to screen DynamoDB entries for retention.

### Screening Criteria

1. **Duplicate Detection**
   - Group entries by (word, url, user_id)
   - Flag duplicates of same word on same site by same user
   - Keep only the most recent entry per group

2. **AI-Powered Test Data Detection**
   - Use LLM to evaluate if an entry looks like test data
   - Heuristics for "obvious" lookups a sophisticated user wouldn't need:
     - Common words with no ambiguity ("hello", "the", "test")
     - Developer test patterns ("asdf", "foo", "bar")
     - Single characters or numbers
   - Consider context: same word might be legitimate in one context, test in another

3. **Retention Review Workflow**
   - Interactive mode: Show flagged entries, confirm delete/keep
   - Batch mode: Auto-delete high-confidence test data
   - Mark reviewed entries with `retention_reviewed: true` attribute
   - Skip already-reviewed entries in future runs

### DynamoDB Schema Addition

```python
item = {
    ...existing fields...
    "retention_reviewed": {"BOOL": True},      # Has been reviewed
    "retention_decision": {"S": "keep|delete"} # Decision made
}
```

## CLI Interface

```bash
# Scan and report (dry run)
python tools/data_hygiene.py --scan

# Interactive review
python tools/data_hygiene.py --review

# Auto-delete high-confidence test data
python tools/data_hygiene.py --auto-clean --confidence 0.9

# Show duplicates only
python tools/data_hygiene.py --duplicates
```

## AI Prompt Strategy

```
You are reviewing DynamoDB entries to identify test data.
Given: word, url, timestamp, user context
Determine: Is this likely test data (0.0-1.0 confidence)
Reasoning: Brief explanation

Test data indicators:
- Common words with no ambiguity
- Developer patterns (test, foo, bar, asdf)
- Repeated lookups of same obvious term
- Context suggests debugging, not genuine research

Legitimate data indicators:
- Archaic or unusual terms
- Historical/cultural context
- Terms with controversial etymology
- Words that would benefit from etymology analysis
```

## Acceptance Criteria

- [ ] CLI tool scans DynamoDB for entries
- [ ] Identifies duplicates by (word, url, user)
- [ ] AI screens entries for test data confidence
- [ ] Interactive review mode with keep/delete options
- [ ] Marks reviewed entries to prevent re-review
- [ ] Dry-run mode (no deletes without confirmation)
- [ ] Batch auto-clean mode for high-confidence test data

## Related Issues

- #145 - DynamoDB TTL (automatic expiry)
- #147 - GDPR erasure (right to be forgotten)
- #149 - lambda_harvester investigation

## Security Considerations

- Tool requires AWS credentials with DynamoDB access
- Should log all deletions for audit trail
- Never delete entries with `retention_decision: keep`

---

## Issue #151: GitHub Security Settings: Policy and Private Reporting enabled

**Labels:** documentation, security

**Created:** 2026-01-04
**Updated:** 2026-01-04

### Description

## Completed

The following GitHub security settings have been configured:

### 1. Security Policy ✅
- Created `SECURITY.md` with:
  - Responsible disclosure process
  - Private reporting instructions
  - Response timeline (48h ack, 1 week assessment, 30 day resolution)
  - Scope definition
  - Security measures documentation

### 2. Private Vulnerability Reporting ✅
- Enabled via `gh api repos/martymcenroe/Aletheia/private-vulnerability-reporting --method PUT`
- Researchers can now report vulnerabilities privately through GitHub

### Already Enabled
- Security advisories
- Dependabot alerts
- Secret scanning alerts

## Verification

- [ ] Check Security tab shows "Security policy" as enabled
- [ ] Check "Private vulnerability reporting" shows as enabled
- [ ] Test private reporting flow (optional)

## References

- [GitHub Security Policy docs](https://docs.github.com/en/code-security/getting-started/adding-a-security-policy-to-your-repository)
- [Private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability)

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

## Issue #153: Fix smoke_test.py pytest fixture errors

**Labels:** bug, testing

**Created:** 2026-01-05
**Updated:** 2026-01-05

### Description

## Summary

`tools/smoke_test.py` has 5 test functions that fail when run via `pytest` due to missing `url` fixture.

## Error

```
fixture 'url' not found
```

## Affected Tests

- `test_valid_input`
- `test_blocked_input`
- `test_empty_input`
- `test_prompt_injection`
- `test_tone_neutrality`

## Cause

These functions have a `url: str` parameter expecting a pytest fixture, but no such fixture is defined. The functions appear designed for manual invocation with a URL argument, not as pytest tests.

## Options

1. **Exclude from pytest** - Add `# noqa: PT` or rename functions to not start with `test_`
2. **Create fixture** - Add a `url` fixture in `conftest.py`
3. **Refactor** - Convert to proper pytest tests with fixture or parametrization

## Impact

Currently causes 5 errors in every test run (159 passed, 5 errors).

---
