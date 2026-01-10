# Aletheia - Closed Issues

**Generated:** 2026-01-09 18:55 CT
**Total Closed Issues:** 118

---

## Issue #1: feat: Migrate to Stateful LangGraph Backend

**Created:** 2025-11-24
**Closed:** 2025-11-24

### Description

Migrate linear Lambda to LangGraph with DynamoDB persistence and Bedrock streaming.

---

## Issue #3: docs: Update README and Cleanup Artifacts

**Created:** 2025-11-24
**Closed:** 2025-11-24

### Description

Reflect LangGraph architecture and remove temporary files.

---

## Issue #5: test: Add Unit Tests for Graph Nodes

**Labels:** chore

**Created:** 2025-11-24
**Closed:** 2025-12-30

### Description

Implement pytest suite to verify agent state transitions and mock Bedrock calls.

---

## Issue #6: feat: Implement RAG Vector Store

**Labels:** feature

**Created:** 2025-11-24
**Closed:** 2026-01-09

### Description

Integrate Pinecone/ChromaDB to enable long-term document recall for the agent.

---

## Issue #7: chore: Add Observability Tracing

**Labels:** chore

**Created:** 2025-11-24
**Closed:** 2026-01-06

### Description

Integrate AWS X-Ray and CloudWatch to trace Lambda execution latency and Bedrock token usage.

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

## Issue #8: chore: Configure Poetry and Python Gitignore

**Created:** 2025-11-24
**Closed:** 2025-12-05

### Description

Initialize pyproject.toml and exclude Python artifacts.

---

## Issue #10: feat: Implement Semantic Maturity Guardrails

**Created:** 2025-11-25
**Closed:** 2025-12-09

### Description

Implement a pre-filter node in LangGraph to detect subtle offensive language.
**User Story:** As a user, I want Aletheia to warn me about archaic, sexually provocative, or offensive terms before I use them, so I can avoid unintentional embarrassment or harm.

**Requirements:**
1. **Not Regex:** Cannot rely on simple word lists (must detect phrases like 'size matters').
2. **Taxonomy:**
   - *Archaic/Outdated:* Terms that are not used widely now but at some point could have been considered pejorative (e.g., 'consumptive').
   - *Provocative:* 'Locker room' talk or sexual double entendres in professional contexts.
   - *Hate/Slur:* Ethnic or racial slurs.
3. **Implementation:**
   - Create a 'guardrails.py' module.
   - Use a lightweight LLM call (e.g., Haiku or Llama Guard) with a specific system prompt.
   - Integrate as a conditional edge in 'agent.py': START -> Guardrail -> Agent.

**Why:** Standard libraries (pydantic, profanity-check) fail on context-dependent phrases.

---

## Issue #11: test: Implement Local Guardrails Test Harness

**Created:** 2025-11-29
**Closed:** 2025-12-05

### Description

Develop a local testing script (manual_test.py) to validate guardrails.py against the safety taxonomy (Archaic, Provocative, Unsafe, Safe) without deploying to AWS. Requires defining ground-truth test cases.

---

## Issue #12: feat: Implement Full Page Context Capture

**Created:** 2025-11-29
**Closed:** 2025-12-05

### Description

Current extension only captures 'selectionText'. To support future RAG and contextual analysis, update the Chrome Extension to capture 'document.body.innerText' (via a content script) and include it in the API payload.

---

## Issue #13: test: Implement Holistic Guardrails Test Harness

**Created:** 2025-11-29
**Closed:** 2025-12-10

### Description

Objective: Develop a comprehensive testing tool 'test_holistic.py' that validates the exact API payload sent by the Chrome Extension.

Requirements:
1. Exact Schema Matching: Test cases must use the production JSON keys:
   * word: The target term (e.g., 'consumptive').
   * context: Surrounding text/paragraph (e.g., 'In La Traviata...').
   * title: Page title (e.g., 'Opera Guide').
   * url: Source domain (e.g., 'wikipedia.org').

2. Validation Logic:
   * Check 'category' (ARCHAIC, PROVOCATIVE, UNSAFE, SAFE).
   * Check 'rationale' (Ensure specific keywords exist in the explanation).

3. Workflow:
   * Load cases from 'test_holistic_data.json'.
   * Mock the API handler.
   * Assert results match expectations.

---

## Issue #14: feat: Implement Compliance Engine

**Labels:** feature

**Created:** 2025-11-29
**Closed:** 2025-12-30

### Description

Objective: Implement a compliance-first context extraction pipeline that respects paywall indicators and ensures zero data retention.

Architecture (The 'Traffic Light' Pattern):
1. Frontend (Extension):
   * Check for 'isAccessibleForFree: False' or 'noai' meta tags.
   * IF DETECTED (Red Light):
       - MVP: Abort transmission. Alert user.
       - Future (v2): Fallback to Client-Side (Edge) Vectorization to keep data local.
   * IF NOT DETECTED (Yellow Light):
       - Transmit payload to AWS (User assumes TOS liability via Terms).

2. Backend (Lambda - The 'Safe Harbor'):
   * Ingest: Accept 'context' via HTTPS.
   * Process: Generate Vector Embedding and Semantic Usage Report.
   * Discard: Explicitly wipe 'context' from memory.
   * Persist: Save only the synthetic report and vector.

Constraints:
* Zero logging of raw text in CloudWatch.
* Strict separation of 'Process' vs 'Store' logic.
* Target Platform: Chrome Desktop (Exclude Mobile/Safari for MVP).

---

## Issue #15: tool: Create DynamoDB Test Data Harvester

**Created:** 2025-11-29
**Closed:** 2025-12-05

### Description

Objective: Create a utility script ('harvest_test_data.py') to generate ground-truth test data from real usage.

Workflow:
1. Connect: Authenticate to AWS DynamoDB (Aletheia Table).
2. Scan: Retrieve the latest N items.
3. Transform: Map DB attributes to the Test Harness Schema ('word', 'url', 'title', 'context').
4. Export: Write to 'test_holistic_data.json'.

Benefit: Allows the developer to 'browse and click' to generate test cases, rather than copy-pasting JSON manually.

---

## Issue #20: chore: Create CLI Deployment Script

**Created:** 2025-11-29
**Closed:** 2025-12-05

### Description

Automate the packaging (Poetry export) and deployment (AWS CLI update) of the Lambda function to remove manual friction.

---

## Issue #21: chore: Cleanup Old AWS Identity Resources

**Labels:** chore

**Created:** 2025-11-29
**Closed:** 2025-12-29

### Description

Identify and remove Aletheia resources (DynamoDB, Lambda, IAM) created under the previous IAM user to prevent cost leakage and confusion.

---

## Issue #22: chore: Provision Greenfield Infrastructure

**Created:** 2025-11-29
**Closed:** 2025-12-05

### Description

Create a bash script (provision.sh) to setup the application stack (DynamoDB Table, IAM Role, Lambda Function) for the 'aletheia-developer' user.

---

## Issue #25: Gate extension features on LinkedIn authentication

**Labels:** security, feature

**Created:** 2025-11-30
**Closed:** 2025-12-30

### Description

Update the MV3 service worker so that the 'Explain with AI' context-menu workflow only runs when the user is logged into LinkedIn. Implement a helper that uses chrome.cookies.getAll({ domain: ".linkedin.com" }) to determine whether any LinkedIn cookies exist; if none are found, show a user-visible 'Not authenticated with LinkedIn' message (via chrome.notifications or equivalent) and abort without calling the webhook. Add the required 'cookies' permission and LinkedIn host_permissions in manifest.json so the service worker can read LinkedIn cookies.

---

## Issue #26: fix: Add host permissions to manifest

**Created:** 2025-12-04
**Closed:** 2025-12-05

### Description

Update manifest.json to include <all_urls> host permissions, resolving the 'Cannot access contents of page' error on complex sites like NYT.

---

## Issue #28: chore: Finalize Greenfield Infrastructure

**Created:** 2025-12-04
**Closed:** 2025-12-05

### Description

Commit the gold-standard provision.sh, deploy.sh, and wired service-worker.js that enables the Data Harvester.

---

## Issue #29: chore: Finalize Greenfield Infrastructure

**Created:** 2025-12-05
**Closed:** 2025-12-05

### Description

Consolidate provision.sh, deploy.sh, and extension wiring into a dedicated branch.

---

## Issue #33: chore: restructure documentation and save test data

**Created:** 2025-12-05
**Closed:** 2025-12-05

### Description

Migrates architecture docs, establishes coding standards (0002), fixes filename spaces, and checkpoints the latest 14-word test dataset.

---

## Issue #38: Cleanup: Quarantine rogue guardrails and update docs

**Created:** 2025-12-08
**Closed:** 2025-12-10

### Description

Moving guardrails.py to legacy and updating lessons learned.

---

## Issue #41: Security Audit: Cull Permissions for Store Compliance

**Created:** 2025-12-09
**Closed:** 2025-12-09

### Description

Objective: Minimize permissions to avoid Manual Review for Jan 15 launch.

  Tasks:
  1. Audit 'manifest.json'.
  2. Remove '<all_urls>' and 'activeTab' if possible.
  3. Replace with specific 'host_permissions' or 'scripting' API.
  4. Ensure Manifest V3 compliance.

---

## Issue #42: Feature: Whitelist Mode & Safety Filters

**Created:** 2025-12-09
**Closed:** 2025-12-09

### Description

Objective: Change default behavior from 'Always On' to 'Default Off'.

  Tasks:
  1. Extension remains inactive on page load.
  2. User must click 'Enable for this site'.
  3. Explore blocking logic for sensitive categories (Medical/Banking/Adult).

---

## Issue #43: Compliance: Publish Privacy Policy

**Created:** 2025-12-09
**Closed:** 2025-12-09

### Description

Objective: Satisfy Google Store requirement for data handling disclosure.

  Tasks:
  1. Create static page at ThriveTech.ai/aletheia/privacy.
  2. Draft policy stating: 'Local-first architecture, no PII collection, no browsing history sales'.
  3. Link URL in Store Listing.

---

## Issue #44: feat: Implement Browser Extension Warning UI

**Labels:** feature

**Created:** 2025-12-09
**Closed:** 2026-01-01

### Description

Implement a 4-tier warning system in the Chrome Extension popup based on backend guardrail scores:

1. **Rejection (Red):** If blocked by Selection Check (Regex) or Denylist (RSDB Hate List). Text: 'Blocked: Invalid format or flagged as potential hate speech (Source: RSDB). Context is not evaluated.'
2. **Warning (Orange):** If Score(Provocative) > 0.0. Text: 'Caution: This term has a {P}% probability of carrying sexual or provocative subtext.'
3. **Advisory (Yellow):** If Score(Provocative) == 0.0 AND (Score(Archaic) > 0 OR Score(Neologism) > 0). Text: 'Note: Term detected as Archaic ({A}%) or Neologism ({N}%). Usage may be obscure or unstable.'
4. **Disclaimer (Footer):** 'AI probability scores are non-deterministic and may fluctuate between checks.'

---

## Issue #45: feat: Implement Deterministic Hate Speech Filter

**Labels:** security, feature

**Created:** 2025-12-09
**Closed:** 2025-12-31

### Description

Implement the Denylist layer of the guardrail funnel: a deterministic, O(1) lookup against a local 'denylist.json' derived from RSDB. This runs *before* the Semantic (LLM) check.

---

## Issue #47: chore: Update Emergency Recovery Protocol

**Created:** 2025-12-09
**Closed:** 2025-12-09

### Description

Explicitly define the Single-Instruction Constraint in docs/0004-orchestration-protocol.md.

---

## Issue #49: chore: Sync Knowledge Base Documents

**Created:** 2025-12-09
**Closed:** 2025-12-09

### Description

Update 9001 with Hate Filter automation tasks, and index 9001 in the Guide (0000) and Inventory (0003).

---

## Issue #53: Generate Store Assets

**Labels:** chore

**Created:** 2025-12-10
**Closed:** 2026-01-07

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

## Issue #56: chore: Audit branch and doc naming for consistency

**Created:** 2025-12-20
**Closed:** 2025-12-20

### Description

Review all open branches and docs/1xxx files to ensure they follow the convention:
- Branch: `{IssueID}-short-description`
- Doc: `1{IssueID}-short-description.md`

Refs: 0002-coding-standards.md (naming convention section to be added)

---

## Issue #57: chore: Resolve Dependabot urllib3 vulnerabilities

**Created:** 2025-12-20
**Closed:** 2025-12-20

### Description

Two high-severity alerts:
1. urllib3 streaming API improperly handles highly compressed data
2. urllib3 allows unbounded decompression chain

Action: Update urllib3 to patched version via poetry.

---

## Issue #58: chore: Implement SonarQube/SonarLint in VSCode

**Labels:** chore

**Created:** 2025-12-20
**Closed:** 2026-01-04

### Description

Set up static code analysis for consistent code quality across projects.

Tasks:
- [ ] Install SonarLint VSCode extension
- [ ] Configure for Python projects
- [ ] Document setup in Engineering Journal

---

## Issue #61: chore: Add testing section to 1041-security-audit.md

**Created:** 2025-12-20
**Closed:** 2025-12-20

### Description

Doc is missing Section 5 (Verification & Testing). Update to match template structure.

---

## Issue #62: chore: Add testing section to 1042-whitelist-mode.md

**Created:** 2025-12-20
**Closed:** 2025-12-20

### Description

Doc is missing Section 5 (Verification & Testing). Update to match template structure.

---

## Issue #63: chore: Add testing section to 1043-privacy-compliance.md

**Created:** 2025-12-20
**Closed:** 2025-12-20

### Description

Doc is missing Section 5 (Verification & Testing). Update to match template structure.

---

## Issue #64: chore: Add testing section to 1045-deterministic-hate-filter.md

**Created:** 2025-12-20
**Closed:** 2025-12-20

### Description

Doc is missing Section 5 (Verification & Testing). Update to match template structure.

---

## Issue #65: chore: Test symlink approach for cross-repo Engineering Journal access

**Created:** 2025-12-20
**Closed:** 2025-12-20

### Description

Test whether Claude Code and other LLM tools can follow the symlink at docs/ENGINEERING-JOURNAL.md to access the global Engineering Journal from martymcenroe repo.

If symlinks don't work:
- Option B: Copy file on session start
- Option C: Git submodule
- Document findings in Engineering Journal.

---

## Issue #69: Feat: CLI Log Inspector Tool

**Created:** 2025-12-20
**Closed:** 2025-12-23

### Description

Create 'tools/log_viewer.py' to inspect DynamoDB telemetry.

  **Requirements:**
  * **Source:** 'AletheiaAgentState' (DynamoDB).
  * **Output:** Stdout (Console only). No file artifacts.
  * **Sort:** Oldest -> Newest (Log style).
  * **Filter:** Default = All. Flag '--tail N'.
  * **Format:**
      * Order: Index, Timestamp, Word, Site.
      * **Dynamic Alignment:** Calculate max width of each column based on content.
      * Padding: Ensure exactly 3 spaces between aligned columns.
      * Index: Zero-padded dynamic width (e.g., '[001/450]').

---

## Issue #71: Chore: Retrofit Inventory with Reliability Status

**Created:** 2025-12-20
**Closed:** 2025-12-23

### Description

Update 'docs/0003-file-inventory.md' to include a 'Status' column and audit all unlisted files.

  **Taxonomy:**
  * 🟢 **Stable:** Tested & Documented.
  * 🟡 **Beta:** Functional, partial coverage.
  * 🟠 **In-Progress:** Active dev.
  * ⚪ **Placeholder:** Skeleton only.
  * ⚫ **Legacy:** Deprecated.
  * ❓ **Unknown:** Default for audit.

  **Scope:**
  * Add 'Status' column to existing tables.
  * Add 'Core Application' section (agent.py, etc).
  * Add 'Infrastructure' section (deploy.sh, etc).
  * Add 'Extension' section.
  * Audit file tree and assign initial statuses.

---

## Issue #72: Refactor: Standardize Data Harvester Tool

**Created:** 2025-12-20
**Closed:** 2025-12-21

### Description

Refactor 'harvest_test_data.py' to align with project standards.

  **Tasks:**
  1. **Move:** Rename to `tools/harvest.py`.
  2. **Determinism:** Sort output by Timestamp (Oldest -> Newest) to ensure stable Git diffs.
  3. **Features:** Add `--tail N` limit.
  4. **Output:** Ensure JSON output is 'pure' (list of records only) for compatibility with `verify_holistic.py`.
  5. **Inventory:** Update `0003-file-inventory.md` with new location and status.

---

## Issue #73: Refactor: Standardize Data Harvester Tool

**Labels:** chore

**Created:** 2025-12-20
**Closed:** 2025-12-28

### Description

Refactor 'harvest_test_data.py' to align with project standards.

  **Tasks:**
  1. **Move:** Rename to `tools/harvest.py`.
  2. **Determinism:** Sort output by Timestamp (Oldest -> Newest) to ensure stable Git diffs.
  3. **Features:** Add `--tail N` limit.
  4. **Output:** Ensure JSON output is 'pure' (list of records only) for compatibility with `verify_holistic.py`.
  5. **Inventory:** Update `0003-file-inventory.md` with new location and status.

---

## Issue #76: feat: Implement domain allowlist popup with toggle and management

**Created:** 2025-12-21
**Closed:** 2025-12-22

### Description

## Objective
Popup-based domain whitelist control with clear visual state indicator and separate management view.

## UX Flow

### Main Popup (Default View)
1. User clicks extension icon → Popup opens
2. Popup shows:
   - Current domain at top (e.g., `wsj.com`)
   - Large power button toggle (center)
   - Filled/blue = enabled, Outline/gray = disabled
   - "Manage Websites" link/button at bottom
3. User clicks power button → toggles current domain only
4. Toolbar icon badge updates to reflect state

### Management View (Secondary)
1. User clicks "Manage Websites" → View switches
2. Shows scrollable list of all whitelisted domains
3. Checkbox per domain for multi-select
4. "Remove Selected" button
5. "Clear All" button
6. "Back" button to return to main view

## Requirements
1. **Popup always opens on click** (no direct icon toggle)
2. **Main view:** Power button toggles ONLY current domain
3. **Management view:** Accessed via "Manage Websites" link
4. **Visual states:**
   - Enabled: Filled icon (blue/green), badge "✓"
   - Disabled: Outline icon (gray), no badge
5. **Domain header** shows current page's domain
6. **Persistence:** `chrome.storage.local`
7. **Theme:** Dark mode (MVP)

## Files to Create/Modify
- `extension/popup.html` — Popup UI (both views)
- `extension/popup.js` — Popup logic and view switching
- `extension/popup.css` — Styling (dark theme)
- `extension/service-worker.js` — Badge/icon state updates
- `extension/manifest.json` — Add popup config
- `extension/icons/` — Power button states (or CSS/SVG)

## Out of Scope (Future)
- Light mode theming
- Stats display ("Queries sent: N")
- Sensitive site blocking (banking/medical)
- Action feedback notifications (separate issue)
- Whitelist history with re-enable capability
- "Permanently forget" a domain from history

## Acceptance Criteria
- [ ] Click extension icon opens popup (main view)
- [ ] Main view shows current domain at top
- [ ] Power button toggles current domain's whitelist status
- [ ] Icon fill/color changes based on enabled/disabled state
- [ ] Badge shows ✓ when current domain is enabled
- [ ] "Manage Websites" opens management view
- [ ] Management view lists all whitelisted domains
- [ ] Checkboxes allow multi-select removal
- [ ] "Clear All" removes all whitelisted domains
- [ ] "Back" returns to main view
- [ ] Whitelist persists across browser restart

---

## Issue #77: feat: Implement user feedback for context menu actions

**Labels:** feature

**Created:** 2025-12-21
**Closed:** 2025-12-29

### Description

## Objective
Provide immediate visual feedback via selection-anchored overlay and flashing toolbar icon when user clicks "Explain with AI" context menu action.

## UX Flow

### Scenario 1: Domain NOT Allowlisted
1. User right-clicks selected text, chooses "Explain with AI"
2. Extension checks allowlist → domain not found
3. **Overlay appears at selection point:** "⚠️ Enable Aletheia for this site first"
4. **Toolbar icon flashes** (amber/yellow) until user clicks it
5. No API call made

### Scenario 2: Domain Allowlisted, Success
1. User right-clicks selected text, chooses "Explain with AI"
2. Extension checks allowlist → domain found
3. API call to Lambda succeeds
4. **Overlay appears at selection point:** "✓ Saved: [word]" (auto-dismiss 3s)
5. **Toolbar icon flashes green briefly** (2s)

### Scenario 3: Domain Allowlisted, Failure
1. User right-clicks selected text, chooses "Explain with AI"
2. Extension checks allowlist → domain found
3. API call fails (network error, Lambda error, etc.)
4. **Overlay appears at selection point:** "✗ Could not save. Try again."
5. **Toolbar icon flashes red briefly** (2s)

## Requirements

### Selection-Anchored Overlay
1. Appears adjacent to the selected text (using selection bounding rect)
2. Small tooltip-style box with message
3. Dark background, light text (matches extension theme)
4. Success: auto-dismiss after 3 seconds
5. Error: auto-dismiss after 3 seconds
6. Blocked (not allowlisted): persists until icon is clicked OR auto-dismiss after 5 seconds

### Toolbar Badge Feedback
1. **Blocked state:** Badge shows "!" with amber background until user clicks icon (opens popup)
2. **Success:** Badge shows "✓" with green background once, then returns to normal (2s)
3. **Error:** Badge shows "✗" with red background once, then returns to normal (2s)
4. Badge achieved via chrome.action.setBadgeText() and setBadgeBackgroundColor() — no host_permissions required

### Allowlist Integration
1. Check `chrome.storage.local` allowlist before API call (depends on Issue #76)
2. No API call if domain not allowlisted

## Technical Approach
- **Overlay positioning:** `window.getSelection().getRangeAt(0).getBoundingClientRect()`
- **Overlay rendering:** Content script inserts self-removing `<div>` with inline styles
- **Icon flashing:** `setInterval` toggling badge text/color, cleared on click or timeout
- **Sandboxed execution:** Uses `chrome.scripting.executeScript()` (isolated world)

## Security Considerations

The selection-anchored overlay uses Chrome's official content script APIs, NOT script injection:

1. **Sandboxed Execution:** Content scripts run in an "isolated world" — they can access the DOM but cannot read or modify the page's JavaScript variables, and the page cannot access the content script's code.

2. **No User Data in DOM:** The overlay displays only static messages ("Saved", "Error") and the selected word. No sensitive data is written to the page.

3. **Permission-Gated:** The `scripting` permission was explicitly granted by the user at install time. This is standard practice for extensions like Grammarly, LastPass, and 1Password.

4. **Self-Removing:** Overlay elements are automatically removed from the DOM after timeout. No persistent modifications to page structure.

5. **No External Scripts:** Overlay styling is inline (no external CSS/JS loaded). No CDN dependencies or network requests from content script.

This approach follows Chrome Extension security best practices and does not introduce XSS or injection vulnerabilities.

## Files to Create/Modify
- `extension/service-worker.js` — Allowlist check, badge animation, orchestration
- `extension/overlay.js` — Content script for selection-anchored overlay
- `extension/manifest.json` — Ensure `scripting` permission (already present)
- `tools/lambda_trace.py` — CLI tool to verify Lambda invocations from CloudWatch

## Dependencies
- Issue #76 (Allowlist popup) must be implemented first

## Out of Scope (Future)
- Chrome system notifications (alternative)
- Sound/vibration feedback
- Detailed error categorization
- Click-to-retry on error overlay

## Acceptance Criteria
- [ ] Overlay appears at selection point (not bottom of screen)
- [ ] Blocked action shows warning overlay + icon flashes until clicked
- [ ] Success shows success overlay (3s) + green icon flash (2s)
- [ ] Error shows error overlay (3s) + red icon flash (2s)
- [ ] No API call made if domain not allowlisted
- [ ] `tools/lambda_trace.py` shows recent Lambda invocations with timestamps
- [ ] Tester can verify no new invocation after blocked action

## Testing: Forcing Network Failure
Use Chrome DevTools → Network tab → "Offline" checkbox to simulate network failure for error state testing.

---

## Issue #78: test: Create static 'Firing Range' web page for manual testing

**Created:** 2025-12-21
**Closed:** 2025-12-21

### Description

## Objective
Create a simple, static HTML page hosted on GitHub Pages (or local) containing specific test cases to validate L1, L2, and L3 guardrails without typing.

## Test Cases (<span> elements)
1. **L1 (Syntax):**
   - Gibberish: 'aighiuagn;ganerw;'
   - Empty: ''
   - Symbols: '!!!???'
2. **L2 (Hate/Denylist):**
   - Known RSDB term (from our mock list).
   - Safe term sharing root with hate term (e.g., 'scunt' vs 'scunthorpe').
3. **L3 (Semantic):**
   - Archaic: 'consumptive'
   - Provocative: 'size matters'
   - Safe: 'hello world'

## Implementation
- File: `docs/test-harness.html`
- Hosting: Enable GitHub Pages for `docs/` folder or open locally.

---

## Issue #79: test: Create static 'Firing Range' web page for manual testing

**Labels:** chore

**Created:** 2025-12-21
**Closed:** 2026-01-04

### Description

## Objective
Create a simple, static HTML page hosted on GitHub Pages (or local) to validate Selection Check, Denylist, and Semantic guardrails without typing.

## Test Cases
- Selection Check: Gibberish/Scripts
- Denylist: Hate terms (mocked)
- Semantic: triggers (Archaic/Provocative)

---

## Issue #80: fix: Wire agent.py to Guardrails and Compliance Engine

**Labels:** bug

**Created:** 2025-12-21
**Closed:** 2025-12-30

### Description

## Context
Ref: `docs/1080-wire-agent-logic.md`
Ref: `docs/0007-legal-compliance-strategy.md`

## Objective
Wire the `agent.py` LangGraph to enforce the security pipeline.
**Note:** We are using the new 'Summarizer' terminology.

## The Pipeline
`Start -> Guardrails (L1-L3) -> Summarizer (No-Op) -> Agent -> End`

## Requirements
1. **Guardrails Node:** Must call `src.guardrails.engine`.
2. **Conditional Edge:** If Guardrails fail, STOP. Do not call Agent.
3. **Summarizer Node:** Create a **Pass-Through** node named `summarizer_node`.
   - **Do NOT** implement summarization logic yet (That is Issue #85).
   - Just return the state as-is for now.
4. **Agent Node:** The existing node, but now downstream of the Summarizer.

## Acceptance Criteria
- [ ] Graph compiles and runs.
- [ ] Blocked input stops execution before the Agent.
- [ ] Valid input flows through the empty Summarizer node to the Agent.

---

## Issue #82: Create Application Identity and Icon Assets

**Created:** 2025-12-22
**Closed:** 2025-12-22

### Description

## 1. Context & Goal
* **Objective:** Establish the visual identity for Aletheia using the new 'Cyber-Gothic Lambda' motif.
* **Goal:** Replace temporary placeholders with production-ready assets that meet Chrome Web Store specifications.

## 2. Requirements
* **Symbol:** A stylistic lowercase Lambda (λ) representing 'Truth' (Aletheia), 'Logic' (Church/Lambda Calculus), and 'Humanity' (Ren).
* **Palette:** Neon Green (approx #22C55E) on Deep Black.
* **Tooling:** A reproducible script to generate assets, avoiding manual image editing.

## 3. Tasks
- [ ] **Design:** Finalize the 'Master' source image (High-res Lambda).
- [ ] **Tooling:** Create tools/generate_icons.py using Pillow.
- [ ] **Assets:** Generate extension/icons/icon*.png (16, 32, 48, 128px).
- [ ] **Manifest:** Update manifest.json to point to the new icon files.
- [ ] **Cleanup:** Commit the tool and the master asset to the repo.

## 4. Definition of Done
* extension/icons/ contains all 4 required PNGs.
* Icons are legible at 16x16px.
* manifest.json correctly references the new files.

---

## Issue #84: tool: Create 'Signal Inspector' CLI for compliance verification

**Labels:** chore, post-mvp

**Created:** 2025-12-22
**Closed:** 2026-01-01

### Description

## Objective
Create a CLI tool (`tools/inspect_signals.py`) to harvest and audit copyright/compliance signals (`noai`, `noarchive`, `robots.txt`) from target URLs. This provides the ground truth data needed to implement the strategy in `docs/0007-legal-compliance-strategy.md`.

## UX Flow

### Scenario 1: Single Site Inspection
1. User runs: `python tools/inspect_signals.py -u https://www.wsj.com`
2. System fetches URL (spoofing standard Chrome User-Agent).
3. System checks `robots.txt`, HTML Meta Tags, and HTTP Headers.
4. System prints color-coded report to console:
   - **ROBOTS.TXT:** Allowed
   - **NOARCHIVE:** TRUE (Meta Tag)
   - **NOAI:** FALSE
5. System appends result to `data/signal_audit.json`.

### Scenario 2: Batch Inspection
1. User runs: `python tools/inspect_signals.py -f docs/test_urls.txt`
2. System iterates through each URL in the file.
3. System prints progress bar or line-by-line status.
4. All results appended to `data/signal_audit.json`.

## Requirements

### Input Handling
1. **`-u / --url <string>`**: Target a single URL.
2. **`-f / --file <path>`**: Target a newline-separated list of URLs.
3. **`-o / --output <path>`**: JSONL output path (Default: `data/signal_audit.json`).

### Signal Detection Logic
The tool must explicitly report the state (True/False/None) of the following signals for each site:
1. **Robots.txt:**
   - Status of `User-agent: *`
   - Status of `User-agent: Aletheia` (if present)
2. **Meta Tags & Headers:**
   - `noindex` (HTML `<meta>` or Header `X-Robots-Tag`)
   - `noarchive` (HTML `<meta>` or Header `X-Robots-Tag`)
   - `nosnippet` (HTML `<meta>` or Header `X-Robots-Tag`)
   - `noai` / `noimageai` (Emerging standards)

### Reporting
1. **Console:** Human-readable summary. Red text for 'Blocking' signals (noai), Yellow for 'Restricted' (noarchive), Green for 'Open'.
2. **JSONL:** Machine-readable record containing:
   - `timestamp`
   - `url`
   - `signals`: { `noarchive`: bool, `noai`: bool, ... }
   - `raw_tags`: (Optional debug data)

## Technical Approach
- **Library:** `requests` for fetching (with custom User-Agent header).
- **Library:** `beautifulsoup4` for parsing HTML meta tags.
- **Library:** `urllib.robotparser` for parsing `robots.txt`.
- **Std Lib:** `argparse` for CLI, `logging` for output.

## Security Considerations
- Tool performs read-only GET requests.
- Must respect request timeouts to prevent hanging on bad URLs.
- User-Agent should identify as "Aletheia Compliance Auditor" (or similar) to be transparent, though we may test with Chrome spoofing to see 'real user' view.

## Files to Create/Modify
- `tools/inspect_signals.py` — New script.
- `data/signal_audit.json` — New output file (gitignored).

## Acceptance Criteria
- [ ] Tool accepts `-u` and `-f` arguments.
- [ ] Output correctly identifies `noarchive` on a known test site (e.g., WSJ or mocked local page).
- [ ] Output correctly parses `X-Robots-Tag` header (not just HTML).
- [ ] Results are persisted to JSONL file.

---

## Issue #85: refactor: Rename 'Compliance' to 'Summarization' and implement Signal Logic

**Labels:** chore

**Created:** 2025-12-22
**Closed:** 2025-12-30

### Description

## Objective
Refactor the codebase to reflect the 'Operation Glass House' strategy (Ref: `docs/0007`). Shift the module's identity from a 'Copyright Shield' to a 'Smart Summarizer' that defaults to transparency but honors 'noarchive' requests.

## UX Flow

### Scenario 1: Open Content (Default)
1. User requests 'Explain this' on a standard blog.
2. Extension detects **no** `noarchive` tags.
3. Summarizer receives `text` + `signals={noarchive: False}`.
4. Summarizer returns **Raw Text** in the `ContextPackage`.
5. Agent receives full context.

### Scenario 2: Restricted Content (No Archive)
1. User requests 'Explain this' on a Paywalled/Private site.
2. Extension detects `noarchive` tag.
3. Summarizer receives `text` + `signals={noarchive: True}`.
4. Summarizer calls LLM to generate 'Fair Use Summary'.
5. Summarizer returns **Summary** (and drops raw text).

## Requirements

### 1. Code Refactoring
1. **Rename File:** `compliance.py` $\rightarrow$ `summarizer.py`.
2. **Rename Type:** `ComplianceReport` $\rightarrow$ `ContextPackage`.
3. **Logic Update:** Implement the 'Switch' logic inside `analyze_context`:
   - IF `signals['noarchive']` is True $\rightarrow$ Summarize.
   - ELSE $\rightarrow$ Pass Raw Text.

### 2. Documentation Updates (Critical)
1. **System Architecture (`docs/0001`):**
   - Update **Component Diagram**: Replace 'Compliance Engine' node with 'Summarizer'.
   - Update **Sequence Diagram**: Reflect the 'Passthrough vs. Summarize' paths.
   - **Constraint:** New diagrams MUST adhere to `docs/0006-mermaid-diagrams.md` (Theme, ClassDefs, Direction).

## Technical Approach
- **Module:** `summarizer.py` (formerly `compliance.py`)
- **Dependencies:** `langchain_core`, `langchain_aws`
- **Search & Replace:** `grep -r 'Compliance' .` to catch all references in comments and docstrings.

## Files to Create/Modify
- `compliance.py` (Delete/Move)
- `summarizer.py` (Create/Refactor)
- `docs/0001-system-architecture.md` (Update Diagrams)
- `tests/test_compliance.py` $\rightarrow$ `tests/test_summarizer.py`

## Acceptance Criteria
- [ ] `summarizer.py` exists and `compliance.py` is gone.
- [ ] `analyze_context` accepts `signals` dict.
- [ ] Unit test confirms: `noarchive=False` returns raw text.
- [ ] Unit test confirms: `noarchive=True` returns summary.
- [ ] Architecture diagrams in `docs/0001` use the new 'Summarizer' terminology and conform to `docs/0006`.

---

## Issue #86: chore: Rewrite LinkedIn auth gate LLD for OAuth flow

**Created:** 2025-12-22
**Closed:** 2025-12-23

### Description

## Objective
Rewrite docs/1025-linkedin-auth-gate.md to use proper OAuth instead of cookie heuristic.

## Context
Current LLD uses cookie presence as auth signal. This is fragile. Need to design proper OAuth flow.

## Tasks
- [ ] Research LinkedIn OAuth requirements
- [ ] Update LLD with OAuth sequence diagram
- [ ] Define token storage strategy

## Blocked By
None (design work)

## Related
Supersedes original approach in #25

---

## Issue #87: chore: Audit 00xx standards docs for coherence and flow

**Created:** 2025-12-22
**Closed:** 2025-12-23

### Description

## Objective
Review all 00xx documents to ensure consistent terminology, clear cross-references, and logical reading order.

## Context
Docs evolved organically. Need a coherence pass now that the system is stabilizing.

## Tasks
- [ ] Verify 0000-GUIDE.md is accurate entry point
- [ ] Check all internal doc links work
- [ ] Ensure no duplicate/conflicting guidance
- [ ] Verify 9000 vs Engineering Journal split is clear
- [ ] Update any stale references

## Files to Review
- 0000-GUIDE.md
- 0001-system-architecture.md
- 0002-coding-standards.md
- 0003-file-inventory.md
- 0004-orchestration-protocol.md
- 0005-testing-strategy-and-protocols.md
- 0006-mermaid-diagrams.md
- 9000-lessons-learned.md

---

## Issue #88: chore: Rewrite LinkedIn auth gate LLD for OAuth flow

**Labels:** chore

**Created:** 2025-12-22
**Closed:** 2025-12-30

### Description

Rewrite docs/1025-linkedin-auth-gate.md to use proper OAuth instead of cookie heuristic. Current approach is fragile.

---

## Issue #89: chore: Audit 00xx standards docs for coherence and flow

**Labels:** chore

**Created:** 2025-12-22
**Closed:** 2025-12-29

### Description

Review all 00xx documents to ensure consistent terminology, clear cross-references, and logical reading order.

---

## Issue #90: fix: Handle duplicate context menu registration error

**Created:** 2025-12-22
**Closed:** 2025-12-23

### Description

## Bug
`Unchecked runtime.lastError: Cannot create item with duplicate id explain-with-ai`

## Cause
`chrome.contextMenus.create` called on extension reload when menu already exists.

## Fix
Wrap in try/catch or check existence before creating:
```javascript
chrome.runtime.onInstalled.addListener(() => {
  try {
    chrome.contextMenus.create({
      id: 'explain-with-ai',
      title: 'Explain with AI',
      contexts: ['selection'],
    });
  } catch (e) {
    console.log('[Aletheia] Context menu already exists');
  }
});
```

## Acceptance Criteria
- [ ] No error on extension reload
- [ ] Context menu still works

---

## Issue #92: chore: Investigate stash with system-architecture changes

**Created:** 2025-12-22
**Closed:** 2025-12-23

### Description

## Context
`git stash show stash@{0}` shows:
- docs/0001-system-architecture.md | 46 +++++++++++++++++++++++++++++++---------

This was stashed from `76-whitelist-popup` branch during logo update work.

## Action
1. `git stash show -p stash@{0}` to view the diff
2. Decide: apply to main, discard, or document what was lost

## Note
Stash index may shift after other stash operations.

---

## Issue #93: bug: Double checkmark in success overlay

**Labels:** bug

**Created:** 2025-12-23
**Closed:** 2025-12-28

### Description

The success overlay shows two checkmarks: one from the icon logic and one in the message text.

**Expected:** ✓ Saved: lawfare
**Actual:** ✓ ✓ Saved: lawfare

**Fix:** Remove the ✓ from the message string in service-worker.js (around line 175), let the overlay type handle the icon.

**Ref:** Issue #77, docs/1077-action-feedback.md

---

## Issue #94: Create automated test harness for XSS prevention (Security Test 23)

**Labels:** testing, security

**Created:** 2025-12-24
**Closed:** 2026-01-04

### Description

## Objective
Automate the XSS prevention smoke test from LLD 1077 §6.2 (steps 23-26) to ensure the overlay always renders malicious text safely using `textContent`.

## UX Flow

### Scenario 1: Malicious Script Tag
1. Test harness injects `<script>alert('xss')</script>` as selected text
2. Overlay renders the text
3. Result: Text appears literally, no script execution

### Scenario 2: Event Handler Injection
1. Test harness injects `<img src=x onerror=alert(1)>` as selected text
2. Overlay renders the text
3. Result: Text appears literally, no alert triggered

### Scenario 3: Encoded Payloads
1. Test harness injects URL-encoded or HTML-encoded XSS payloads
2. Overlay renders the text
3. Result: No script execution, text displayed as-is

## Requirements

### Test Coverage
1. Verify `textContent` is used (never `innerHTML`) for user-supplied text
2. Cover OWASP XSS cheat sheet payloads (script tags, event handlers, SVG, etc.)
3. Test runs headlessly for CI integration

### Automation
1. Harness should be runnable via npm/poetry script
2. Results reported in pass/fail format suitable for CI
3. Clear error messages when XSS protection fails

## Technical Approach
- **Puppeteer/Playwright:** Automate Chrome extension loading and context menu interaction
- **XSS Payload Set:** Curated list from OWASP XSS Filter Evasion cheat sheet
- **Assertion:** Verify no `alert()` dialogs appear; verify overlay `textContent` matches input

## Files to Create/Modify
- `tests/security/xss-overlay-test.js` — Automated test suite
- `tests/security/payloads.json` — XSS payload test vectors
- `package.json` or `pyproject.toml` — Add test script

## Dependencies
- Issue #77 must be completed first (overlay implementation)

## Out of Scope (Future)
- Full penetration testing framework
- CSP header testing (extension context differs from web)

## Acceptance Criteria
- [ ] Test harness runs against loaded extension in headless Chrome
- [ ] Covers minimum 10 distinct XSS payload types
- [ ] All tests pass (no alert dialogs triggered)
- [ ] Integrates with existing test runner (`npm test` or `poetry run pytest`)
- [ ] Documents how to add new payloads

## Testing Notes
Force failure by temporarily changing `textContent` to `innerHTML` in overlay.js — tests should fail.

---

## Issue #95: Security Hardening & Rate Limiting (Anti-DoS)

**Labels:** security, high-priority

**Created:** 2025-12-24
**Closed:** 2026-01-02

### Description

## Objective
Implement immediate "Denial of Wallet" protection via AWS WAF and restrict Lambda access to the Chrome Extension using an API Key/Header strategy.

## UX Flow

### Scenario 1: Standard User (Web Store)
1. User installs extension from Chrome Web Store.
2. Extension makes request including a strict `X-Aletheia-Client-Version` and `X-Api-Key` header.
3. WAF validates headers + Geo-IP + Rate Limit.
4. **Result:** Request processed successfully.

### Scenario 2: Authenticated User (Future State)
1. *Deferred until Feature #25 implementation.*

### Scenario 3: Unauthorized Script / Attacker
1. Script sends `POST` to Lambda URL without valid headers.
2. **Result:** WAF blocks immediately (403 Forbidden).
3. Attacker attempts to "hammer" the endpoint.
4. **Result:** WAF Rate Limiter bans IP (429 Too Many Requests).

## Requirements

### Infrastructure (AWS)
1. **WAF Deployment:** Front the Lambda Function URL (or API Gateway) with AWS WAF.
2. **Rate Limiting:** Cap requests to ~100 per 5 minutes per IP.
3. **Header Inspection:** Block requests missing the specific Extension headers.

### Application (Extension)
1. Inject `X-Api-Key` and `X-Client-Version` into `service-worker.js`.

## Files to Create/Modify
* `extension/service-worker.js`
* `infra/waf-setup.sh` (or AWS Console)
* `docs/security/vulnerability-test.md`

## Acceptance Criteria
- [ ] `curl` without headers returns 403.
- [ ] `curl` with headers returns 200.
- [ ] Sustained high-volume traffic triggers 429.

---

## Issue #96: Bug: Extension shows success feedback on HTTP failure (429/500)

**Labels:** bug

**Created:** 2025-12-25
**Closed:** 2025-12-29

### Description

The extension's fetch logic (service-worker.js) ignores non-200 HTTP status codes, resulting in a 'Success' badge/overlay even when the backend rejects the request (e.g., Throttling/429).

**Reproduction:**
1. Set Lambda concurrency to 0.
2. Trigger extension.
3. Observe Green Checkmark (Success) instead of Red X (Failure).

**Fix Requirement:**
Implement `response.ok` check in fetch handler.

---

## Issue #97: Chore: Establish protocol for syncing documentation infrastructure to active branches

**Labels:** documentation, chore

**Created:** 2025-12-25
**Closed:** 2025-12-28

### Description

## Objective
Prevent 'Documentation Drift' where new tooling (e.g., `docs/session-logs/`) exists on `main` but is missing from long-running feature branches, causing AI session closeouts to fail.

## The Problem
When `main` receives structural updates (new folders, moved scripts), active feature branches (like `77-action-feedback`) become stale. AI agents attempting to run new protocols on old branches fail because the paths don't exist yet.

## Tasks
- [ ] Create a 'Refresh' protocol in `docs/0002-coding-standards.md`.
- [ ] Investigate git hooks or scripts to auto-merge `docs/` changes (optional/future).
- [ ] Immediate action: Merge `main` into all active feature branches.

## Acceptance Criteria
- [ ] `77-action-feedback` has the new `docs/session-logs/` directory.
- [ ] Session closeout scripts run successfully on feature branches.

---

## Issue #98: Bug: Overlay still clips at bottom of viewport despite positioning logic

**Labels:** bug

**Created:** 2025-12-28
**Closed:** 2025-12-30

### Description

## Problem
The overlay continues to appear BELOW the selection even when selected text is at the bottom of the viewport, causing it to be clipped off-screen.

## Expected Behavior
When selection is within 60px of bottom viewport edge, overlay should appear ABOVE the selection (Test 060).

## Current State
- **Branch:** 77-action-feedback
- **Latest commit:** a9dd620
- **File:** extension/overlay.js lines 27-38

## Attempts Made
1. **Commit 552fb7b:** Used `bottom` CSS property with calculation `window.innerHeight - rect.top + 8`
2. **Commit a9dd620:** Switched to `top` property with calculation `rect.top - OVERLAY_HEIGHT - GAP`

Both approaches still result in overlay appearing below and being clipped.

## Testing Details
- **Browser:** Chrome Canary
- **Observable behavior:** Green checkmark flashes, overlay visible if user scrolls down quickly
- **Console logs:** Not appearing (injected script context issue)

## Debug Data Needed
- Actual `rect.top`, `rect.bottom`, `window.innerHeight` values at time of rendering
- Confirmation that `spaceBelow < OVERLAY_HEIGHT` condition is actually triggering
- Verify extension reload is picking up new code

## Next Steps
1. Add visual indicator to show which branch (above/below) triggered
2. Consider using `chrome.debugger` API or alternative logging approach
3. Test in regular Chrome (not Canary) to rule out browser-specific issues

## Related
- Issue #77 (parent feature)
- Test 060 in docs/1077-action-feedback.md
- Section 4.4 in docs/1077-action-feedback.md (positioning spec)

---

## Issue #99: Feature: Automated testing framework for browser extension

**Labels:** enhancement, testing

**Created:** 2025-12-29
**Closed:** 2026-01-04

### Description

## Context
Issue #77 introduced manual smoke tests (docs/1077-action-feedback.md §6.1). These tests are time-consuming and error-prone when done manually.

## Objective
Create automated test framework to replace manual testing where possible.

## Tests to Automate

### High Priority (Core Functionality)
- **Test 010:** Blocked state (not allowlisted)
  - Verify overlay appears with warning message
  - Verify badge shows amber `!`
  - Verify no API call made

- **Test 020:** Badge clearing
  - Verify badge clears when popup opened

- **Test 030:** Success state
  - Verify overlay shows "Saved: [word]"
  - Verify badge shows green ✓
  - Verify API call succeeds (200 status)
  - Verify DynamoDB entry created

- **Test 040:** Error state
  - Verify overlay shows error message
  - Verify badge shows red ✗
  - Test with: network offline, Lambda concurrency=0, API errors

- **Test 080:** XSS prevention
  - Verify malicious HTML displayed as text (not executed)
  - Test multiple XSS payloads (see test-xss.html)

- **Test 090:** Rapid clicks (race condition)
  - Verify badge state remains coherent
  - Verify no stuck badges

### Medium Priority (Visual/UX)
- **Test 070:** Shadow DOM isolation
  - Verify consistent styling across different sites
  - Test on: WSJ, NYT, GitHub

### Low Priority (Blocked by #98)
- **Test 050/060:** Overlay positioning
  - Cannot automate until Issue #98 resolved
  - Requires viewport-aware positioning to work first

## Recommended Approach

### Option 1: Playwright + Chrome Extension Testing
**Pros:**
- Supports Chrome extension testing
- Full browser automation
- Can verify visual elements (screenshots)
- Network mocking for error states

**Cons:**
- Steeper learning curve
- More setup required

**Example:**
```javascript
import { test, expect } from '@playwright/test';

test('blocked state shows warning overlay', async ({ page }) => {
  // Load extension
  const extensionPath = './extension';
  const context = await chromium.launchPersistentContext('', {
    headless: false,
    args: [
      `--disable-extensions-except=${extensionPath}`,
      `--load-extension=${extensionPath}`
    ]
  });

  // Navigate to non-allowlisted site
  await page.goto('https://wsj.com');

  // Select text
  await page.locator('p').first().dblclick();

  // Trigger context menu
  await page.locator('p').first().click({ button: 'right' });
  await page.locator('text=Explain with AI').click();

  // Verify overlay appears
  const overlay = await page.locator('#aletheia-overlay-host');
  await expect(overlay).toBeVisible();
  await expect(overlay).toContainText('Enable Aletheia');

  // Verify badge (requires querying service worker)
  // TODO: Access chrome.action.getBadgeText()
});
```

### Option 2: Puppeteer
**Pros:**
- Simpler API
- Good Chrome extension support
- Can mock network requests

**Cons:**
- Chrome-only (no Firefox)
- Less robust than Playwright

### Option 3: Selenium WebDriver
**Pros:**
- Industry standard
- Multi-browser support
- Mature ecosystem

**Cons:**
- Slower than Playwright/Puppeteer
- More verbose API
- Extension testing can be tricky

## Recommended Stack
```
Playwright + TypeScript
├── Chrome extension context
├── Network mocking (for error states)
├── Screenshot comparison (for Shadow DOM isolation)
└── AWS SDK integration (verify DynamoDB writes)
```

## Test Structure
```
tests/
├── e2e/
│   ├── blocked-state.spec.ts       (Test 010, 020)
│   ├── success-state.spec.ts       (Test 030)
│   ├── error-state.spec.ts         (Test 040)
│   ├── xss-prevention.spec.ts      (Test 080)
│   ├── race-condition.spec.ts      (Test 090)
│   └── shadow-dom.spec.ts          (Test 070)
├── fixtures/
│   ├── test-page.html              (Simple page for testing)
│   ├── xss-payloads.html           (XSS test harness)
│   └── mock-api-responses.json     (Lambda API mocks)
└── helpers/
    ├── extension-loader.ts         (Load extension in test context)
    ├── badge-checker.ts            (Query badge state)
    └── dynamodb-verifier.ts        (Check DB writes)
```

## Implementation Steps
1. Research Playwright Chrome extension testing
2. Create basic test harness (load extension, navigate to page)
3. Implement Test 080 (XSS) - simplest to automate
4. Implement Test 010/020 (blocked state, badge)
5. Implement Test 030 (success) with DynamoDB verification
6. Implement Test 040 (error) with network mocking
7. Implement Test 090 (race condition)
8. Implement Test 070 (Shadow DOM) with screenshot comparison
9. Add CI/CD integration (GitHub Actions)

## Acceptance Criteria
- [ ] All high-priority tests automated
- [ ] Tests run in CI/CD pipeline
- [ ] Test results logged to GitHub Actions
- [ ] Documentation for running tests locally
- [ ] Coverage report showing test pass/fail status
- [ ] Tests complete in < 5 minutes

## Non-Goals
- Visual regression testing (beyond Shadow DOM isolation check)
- Performance testing (separate effort)
- Load testing (not applicable to extension)
- Accessibility testing (future enhancement)

## Dependencies
- None (can start immediately)
- Blocked tests (050, 060) can be added after Issue #98 resolved

## Related Issues
- #77 - Feature that introduced manual tests
- #94 - XSS test harness (manual)
- #98 - Overlay positioning (blocks automation of Tests 050/060)

## References
- Test spec: docs/1077-action-feedback.md §6.1
- Manual test script: TEST-SCRIPT-77.md
- XSS harness: test-xss.html
- Playwright extension testing: https://playwright.dev/docs/chrome-extensions

---

## Issue #100: Feature: Firefox compatibility while maintaining Chrome support

**Labels:** enhancement

**Created:** 2025-12-29
**Closed:** 2026-01-02

### Description

## Context
During Issue #98 debugging, extension was tested in Firefox and required manifest.json changes to load (commit 1cd36c9). These changes were reverted when branch 77 was cleaned up. Extension currently works in Chrome/Chrome Canary but not Firefox.

## Objective
Make Aletheia extension work in both Chrome and Firefox without separate builds or manifests.

## Firefox Error (Current)
When loading extension in Firefox (`about:debugging` → Load Temporary Add-on):

```
Error: background.service_worker is currently disabled. Add background.scripts.
```

## Required Change

### manifest.json - Background Section
**Current (Chrome-only):**
```json
"background": {
  "service_worker": "service-worker.js"
}
```

**Fixed (Chrome + Firefox):**
```json
"background": {
  "service_worker": "service-worker.js",
  "scripts": ["service-worker.js"]
}
```

## Browser Support Matrix

| Browser | Manifest V3 | Service Workers | Background Scripts |
|---------|-------------|-----------------|-------------------|
| Chrome 88+ | ✅ Yes | ✅ Preferred | ⚠️ Deprecated |
| Firefox 109+ | ✅ Yes | ⚠️ Partial | ✅ Required |

**Key Issue:** Firefox Manifest V3 support is incomplete. Firefox still requires `background.scripts` array even though it supports `service_worker`. Chrome ignores `scripts` if `service_worker` is present.

**Solution:** Include BOTH properties. Chrome uses `service_worker`, Firefox uses `scripts`. No conflict.

## Implementation

### 1. Update manifest.json
```json
{
  "manifest_version": 3,
  "name": "Aletheia",
  "version": "1.0",
  "description": "AI-Powered Context Analysis",
  "permissions": [
    "activeTab",
    "scripting",
    "contextMenus",
    "storage"
  ],
  "host_permissions": [],
  "background": {
    "service_worker": "service-worker.js",
    "scripts": ["service-worker.js"]
  },
  "icons": {
    "16": "icons/icon16.png",
    "32": "icons/icon32.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  },
  "action": {
    "default_title": "Aletheia",
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "32": "icons/icon32.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  }
}
```

### 2. Test in Both Browsers

**Chrome:**
1. `chrome://extensions/` → Load unpacked
2. Run smoke tests (TEST-SCRIPT-77.md)
3. Verify all features work

**Firefox:**
1. `about:debugging#/runtime/this-firefox` → Load Temporary Add-on
2. Select `manifest.json` from extension directory
3. Run smoke tests (TEST-SCRIPT-77.md)
4. Verify all features work

## API Compatibility Notes

### Known Compatible APIs (Used by Aletheia)
- ✅ `chrome.contextMenus` → Works in Firefox (via WebExtensions polyfill)
- ✅ `chrome.storage` → Works in Firefox
- ✅ `chrome.scripting.executeScript` → Works in Firefox 101.0+
- ✅ `chrome.action.setBadgeText` → Works in Firefox 109+
- ✅ `chrome.action.setBadgeBackgroundColor` → Works in Firefox 109+

### Potential Issues
- Firefox may require `browser.*` namespace instead of `chrome.*`
- Most modern Firefox versions support `chrome.*` for compatibility
- If issues arise, consider using WebExtensions polyfill: https://github.com/mozilla/webextension-polyfill

## Testing Checklist

Test all features from Issue #77 in BOTH browsers:

- [ ] **Extension loads** without errors
- [ ] **Context menu** appears ("Explain with AI")
- [ ] **Allowlist toggle** in popup works
- [ ] **Test 010:** Blocked state (not allowlisted)
  - [ ] Chrome
  - [ ] Firefox
- [ ] **Test 020:** Badge clearing
  - [ ] Chrome
  - [ ] Firefox
- [ ] **Test 030:** Success state (with Lambda ON)
  - [ ] Chrome
  - [ ] Firefox
- [ ] **Test 040:** Error state (with Lambda OFF)
  - [ ] Chrome
  - [ ] Firefox
- [ ] **Test 070:** Shadow DOM isolation
  - [ ] Chrome
  - [ ] Firefox
- [ ] **Test 080:** XSS prevention
  - [ ] Chrome
  - [ ] Firefox
- [ ] **Test 090:** Rapid clicks
  - [ ] Chrome
  - [ ] Firefox

## Acceptance Criteria

- [ ] Extension loads in Firefox without errors
- [ ] Extension still loads in Chrome without warnings
- [ ] All smoke tests pass in Chrome
- [ ] All smoke tests pass in Firefox
- [ ] No separate builds required (single manifest.json works for both)
- [ ] Documentation updated with Firefox installation instructions

## Future Considerations

**Edge/Brave/Vivaldi:**
- These are Chromium-based, should work like Chrome
- No special handling needed

**Safari:**
- Requires separate build process (Xcode project)
- Out of scope for this issue

## References

- Firefox MV3 docs: https://extensionworkshop.com/documentation/develop/manifest-v3-migration-guide/
- Chrome MV3 docs: https://developer.chrome.com/docs/extensions/mv3/
- WebExtensions polyfill: https://github.com/mozilla/webextension-polyfill
- Test script: TEST-SCRIPT-77.md (branch 77-action-feedback)
- Previous Firefox fix (reverted): commit 1cd36c9

## Related Issues

- #77 - User feedback feature (smoke tests to run in both browsers)
- #98 - Overlay positioning (tested in Firefox during debug)

## Dependencies

None - can be implemented immediately on branch 77-action-feedback.

---

## Issue #102: chore: Reorganize repository structure for professional appearance

**Labels:** chore

**Created:** 2025-12-29
**Closed:** 2026-01-05

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

## Issue #104: Block age-restricted sites (RTA/adult rating detection)

**Labels:** enhancement, security

**Created:** 2025-12-29
**Closed:** 2026-01-04

### Description

## Summary
Prevent users from enabling Aletheia on age-restricted websites. The extension must detect adult content tags and display a permanent blocking state.

## User Story
As a user on an adult-tagged site, I should see a clear "not permitted" message and a red prohibition icon, making it obvious Aletheia will not function here.

## Research Findings

### Authoritative Source: Google Search Central
**Official Documentation:** [SEO Guidelines for Explicit Content](https://developers.google.com/search/docs/crawling-indexing/safesearch)

**Detection methods (per Google):**
```html
<meta name="rating" content="adult">
```
OR
```html
<meta name="rating" content="RTA-5042-1996-1400-1577-RTA">
```

### Decision
**Block on:** `content="adult"` OR RTA pattern
**Allow:** `content="mature"` (movie reviews, medical sites)

## Implementation Details

### Detection (service-worker.js)
1. On tab update/page load, inject content script to check `<meta name="rating">`
2. If `content="adult"` or contains `RTA-5042-1996-1400-1577-RTA` → set tab state to `AGE_RESTRICTED`

### User Feedback - Text Selection Attempt
When user selects text on age-restricted site:
- **DO NOT** show "Enable Aletheia" prompt
- **DO** show message: "Aletheia is not permitted on adult-tagged or age-restricted websites"
- Use amber/warning styling

### User Feedback - Extension Icon
- Show red circle/slash prohibition symbol (🚫) on extension icon
- Icon remains in this state **permanently** until tab is closed
- No timer - state persists for tab lifetime
- No persistence to storage (forget site when tab closes)

### Popup UI (if user clicks extension)
- Display explanatory message
- All controls disabled
- No "enable" option available

### Security Considerations
- Flag set by extension only (not injectable from page)
- Security review needed to prevent bypass
- Document in 0202-DR-content-safety.md

## Testing
- Requires test website with `<meta name="rating" content="adult">` tag
- See Issue #[TEST_INFRA_ISSUE] for test hosting infrastructure
- Manual verification on tagged test page

## Acceptance Criteria
- [ ] Extension detects `rating="adult"` meta tag
- [ ] Extension detects RTA label pattern
- [ ] Text selection shows "not permitted" message (not "enable")
- [ ] Extension icon shows prohibition symbol
- [ ] Icon persists until tab closed (no timer)
- [ ] No site data persisted to storage
- [ ] Popup shows disabled state with explanation
- [ ] Document decision in 0202-DR-content-safety.md

## References
- [Google SafeSearch Guidelines](https://developers.google.com/search/docs/crawling-indexing/safesearch)
- [W3C PICS (Deprecated)](https://www.w3.org/PICS/)

---

## Issue #105: Scriptable test site hosting infrastructure (free/cheap)

**Labels:** enhancement, testing

**Created:** 2025-12-29
**Closed:** 2026-01-04

### Description

## Summary
Create scriptable infrastructure to host test websites for Aletheia extension testing. Must be free or very cheap, and provisioned via script (no manual clicking).

## Problem
- Local file:// URLs don't work (unknown domain, extension restrictions)
- Need real hosted sites with various meta tags for testing
- Manual hosting setup is tedious ("clicky clacky crap")
- User has multiple domain names available

## Requirements
1. **Cost:** Free or near-free
2. **Scriptable:** Provision and deploy via CLI/script
3. **Multiple test pages:** Different meta tags, content types
4. **Domain support:** Can use user's existing domains

## Test Pages Needed
| Page | Purpose | Meta Tags |
|------|---------|-----------|
| `test-adult.html` | Age-restricted blocking (#104) | `<meta name="rating" content="adult">` |
| `test-rta.html` | RTA pattern detection | `<meta name="rating" content="RTA-5042-1996-1400-1577-RTA">` |
| `test-noarchive.html` | Summarizer trigger | `<meta name="robots" content="noarchive">` |
| `test-clean.html` | Happy path baseline | No restrictive tags |
| `test-xss.html` | XSS injection testing | Script tags in content |

## Hosting Options to Evaluate

### Option A: GitHub Pages (Free)
- **Pros:** Free, scriptable via git push, supports custom domains
- **Cons:** HTTPS only, public repo required for free tier
- **Script:** `git push` to gh-pages branch

### Option B: Cloudflare Pages (Free)
- **Pros:** Free, fast, scriptable via Wrangler CLI
- **Cons:** Learning curve
- **Script:** `wrangler pages deploy`

### Option C: AWS S3 + CloudFront (Cheap)
- **Pros:** Already using AWS, full control
- **Cons:** Not free (pennies/month), more setup
- **Script:** `aws s3 sync` + CloudFormation

### Option D: Netlify (Free tier)
- **Pros:** Free, CLI available, instant deploys
- **Cons:** Another account to manage
- **Script:** `netlify deploy`

## Recommendation
**GitHub Pages** - already using GitHub, free, scriptable, custom domain support.

## Deliverables
- [ ] Provisioning script: `tools/provision_test_sites.sh`
- [ ] Test page templates in `tests/fixtures/html/`
- [ ] Documentation of test URLs
- [ ] CI/CD to auto-deploy on change (optional)

## Blocks
- #104 (Age-restricted blocking) - needs test site to verify
- Future manual testing issues

---

## Issue #107: Debug VSCode Mermaid diagram preview

**Labels:** documentation, chore

**Created:** 2025-12-29
**Closed:** 2026-01-10

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

## Issue #109: Rename filter layers and update architecture docs

**Labels:** documentation, chore

**Created:** 2025-12-29
**Closed:** 2025-12-30

### Description

## Summary
Rename the L1/L2/L3/L4 filter layers to functional names and update all documentation to reflect the new architecture.

## Current State (Confusing)
- L1, L2, L3, L4 implies fixed sequential order
- Layers may move between client/server
- "Compliance" is a bad name for the Transform/Summarizer layer
- L2 (Denylist) is not even implemented yet (#45)

## New Naming Convention

### Client-Side (Browser Extension)
| Old | New | Purpose |
|-----|-----|---------|
| (new) | **Age Check** | Block adult-rated sites (#104) |
| (new) | **Robot Meta Check** | Detect noarchive flag, pass to Lambda |
| L1 | **Selection Check** | Entropy, length, XSS detection, user feedback |

### Server-Side (Lambda)
| Old | New | Purpose |
|-----|-----|---------|
| L2 | **Denylist** | Hate term blocking (Issue #45 - stub for now) |
| L3 | **Semantic** | AI-based context analysis (Haiku) |
| L4/Compliance | **Transform** | Summarizer for noarchive content |

## Documents to Update
- [ ] `docs/0001-system-architecture.md` - Main diagram and layer definitions
- [ ] `docs/0007-legal-compliance-strategy.md` - Rename to Signal Handling only
- [ ] `docs/1080-wire-agent-logic.md` - Fix L2 claims, update terminology
- [ ] `docs/0005-testing-strategy-and-protocols.md` - Module names
- [ ] `docs/1010-semantic-guardrails.md` - L3 → Semantic
- [ ] `docs/1011-local-guardrails.md` - L1 → Selection Check
- [ ] `docs/1014-compliance-engine.md` - Rename to Transform
- [ ] `docs/1045-deterministic-hate-filter.md` - L2 → Denylist
- [ ] GitHub Issues referencing old layer names

## New Architecture Diagram
```
┌─────────────────────────────────────────────────────────────┐
│  BROWSER EXTENSION (Client)                                 │
├─────────────────────────────────────────────────────────────┤
│  Age Check → Robot Meta Check → Selection Check             │
│  (block)     (set flags)        (validate input)            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  AWS LAMBDA (Server)                                        │
├─────────────────────────────────────────────────────────────┤
│  Denylist → Semantic → Transform → DynamoDB                 │
│  (stub)     (Haiku)    (if noarchive)                       │
└─────────────────────────────────────────────────────────────┘
```

## Acceptance Criteria
- [ ] All docs use new terminology consistently
- [ ] No references to L1/L2/L3/L4 remain (except historical context)
- [ ] "Compliance" renamed to "Transform" or "Summarizer"
- [ ] Architecture diagram updated with client/server split
- [ ] 0003-file-inventory.md updated if files renamed

---

## Issue #110: Find and recover lost ADR content from web conversations

**Labels:** documentation, chore

**Created:** 2025-12-29
**Closed:** 2025-12-30

### Description

## Summary
Architecture Decision Records (ADR) content was created in previous AI conversations but never committed to the repository. Need to find and recover this content.

## Where to Look

### 1. Gemini Web Conversations
- Search conversation history for "ADR", "decision record", "architecture decision"
- Look for discussions about design choices, trade-offs, alternatives considered
- Check conversations from project inception through December 2025

### 2. Claude Web Conversations
- Same search terms as above
- May have different ADR content than Gemini sessions
- Look for any "why did we choose X over Y" discussions

### 3. Git History (Branches)
- Check for orphaned branches that may contain ADR drafts
- `git branch -a` to list all branches
- `git log --all --oneline | grep -i adr` to search commits

### 4. Local Files
- Check for uncommitted `.md` files mentioning decisions
- Search `docs/` for any partial ADR content

## What to Recover
- **Why LangGraph?** (vs plain Lambda, Step Functions)
- **Why Bedrock?** (vs OpenAI, self-hosted)
- **Why Chrome extension?** (vs bookmarklet, standalone app)
- **Why DynamoDB?** (vs RDS, S3)
- **Guardrail layer decisions** (why 3+ layers?)
- **Any "we decided X because Y" content**

## Deliverables
- [ ] Export relevant conversation excerpts
- [ ] Create `docs/0200-ADR-index.md` as placeholder
- [ ] Draft initial ADR entries from recovered content
- [ ] Reference in new 02xx Decision Record series

## Notes
- Don't need perfect formatting - content recovery is priority
- Can clean up and formalize later
- User will need to search their own conversation histories

---

## Issue #111: Create 02xx Decision Record series (Security, Content Safety, Privacy)

**Labels:** documentation

**Created:** 2025-12-29
**Closed:** 2025-12-29

### Description

## Summary
Create a new 02xx document series for Decision Records, organized by domain for easy reference during interviews and reviews.

## Rationale
When interviewing for positions, being able to point reviewers to specific decision documents relevant to their interests (security, privacy, etc.) demonstrates domain expertise and thoughtful engineering.

## Document Structure

### 0200-DR-index.md
Master index of all decision records with:
- Links to domain-specific documents
- Quick reference of major decisions
- How to read/navigate the DR series

### 0201-DR-security.md
**Audience:** Security engineers, penetration testers, compliance reviewers

| Decision | Alternatives Considered | Rationale |
|----------|------------------------|-----------|
| Rate limiting via WAF | API Gateway throttling, Lambda concurrency | [rationale] |
| API key requirement | Open API, OAuth only | [rationale] |
| XSS prevention approach | CSP, sanitization, both | [rationale] |
| Fail-closed guardrails | Fail-open, configurable | [rationale] |

### 0202-DR-content-safety.md
**Audience:** Trust & Safety, policy reviewers, parents

| Decision | Alternatives Considered | Rationale |
|----------|------------------------|-----------|
| Block adult-rated sites | Warning only, user toggle | See #104 |
| RTA + adult detection | All rating values, manual list | Google SafeSearch guidance |
| Hate speech denylist | AI-only, no filter | Liability shield |
| Semantic context analysis | Keyword only, no AI | Nuance detection |

### 0203-DR-privacy.md
**Audience:** Privacy engineers, GDPR reviewers, data protection officers

| Decision | Alternatives Considered | Rationale |
|----------|------------------------|-----------|
| Ephemeral processing | Persistent storage | Data minimization |
| noarchive → summarize only | Ignore signal, block entirely | Copyright respect |
| No user accounts (MVP) | Required auth, optional auth | Privacy by default |
| DynamoDB TTL | Manual cleanup, no expiry | Automated data hygiene |

### 0204-DR-architecture.md (from recovered ADR)
**Audience:** System architects, backend engineers

| Decision | Alternatives Considered | Rationale |
|----------|------------------------|-----------|
| LangGraph | Plain Lambda, Step Functions | [from ADR recovery] |
| Bedrock (Claude) | OpenAI, self-hosted | [from ADR recovery] |
| Chrome extension | Bookmarklet, standalone app | [from ADR recovery] |
| DynamoDB | RDS, S3, Redis | [from ADR recovery] |

## Dependencies
- #110 (Find lost ADR content) - feeds into 0204
- #109 (Rename layers) - terminology must be consistent

## Deliverables
- [ ] Create docs/0200-DR-index.md
- [ ] Create docs/0201-DR-security.md
- [ ] Create docs/0202-DR-content-safety.md
- [ ] Create docs/0203-DR-privacy.md
- [ ] Create docs/0204-DR-architecture.md (placeholder until #110 complete)
- [ ] Update docs/0003-file-inventory.md
- [ ] Update docs/0000-GUIDE.md to reference DR series

---

## Issue #112: Restructure 0007: Extract content to Decision Records

**Labels:** documentation, chore

**Created:** 2025-12-29
**Closed:** 2025-12-30

### Description

## Summary
Rename and restructure `docs/0007-legal-compliance-strategy.md` - extract decision content to the new 02xx DR series, leaving 0007 as a focused "Signal Handling" reference.

## Current State
0007 contains:
1. Philosophy (Assistant vs Crawler) → **Keep in 0007**
2. Signal Matrix (noai, noarchive, etc.) → **Keep in 0007**
3. "Summarization" Switch logic → **Move to 0203-DR-privacy.md**
4. Implementation notes → **Move to relevant LLDs**

## Issues Found
- Line 15: `noai` / `noimageai` marked as "HARD STOP" but user confirmed these don't apply (Aletheia doesn't train)
- Terminology uses "Compliance" which is being renamed to "Transform"

## Proposed Changes

### Rename
`0007-legal-compliance-strategy.md` → `0007-signal-handling.md`

### Keep in 0007
- Section 1: Philosophy (we are User Agent, not Crawler)
- Section 2: Signal Matrix (updated - see below)
- Brief implementation pointers (which component handles what)

### Updated Signal Matrix
| Signal | Aletheia Action | Reasoning |
|--------|-----------------|-----------|
| `noai` / `noimageai` | **Ignore** | We do inference, not training |
| `noarchive` | **Transform only** | Don't persist raw text |
| `noindex` | **Ignore** | Not a search engine |
| `nosnippet` | **Ignore** | Not a SERP |
| `robots.txt` | **Ignore** | User Agent, not crawler |
| `rating="adult"` | **Block site** | See #104, 0202-DR-content-safety.md |

### Extract to Decision Records
- Why we ignore noai → 0203-DR-privacy.md
- Why Transform on noarchive → 0203-DR-privacy.md
- Summarization approach → 0203-DR-privacy.md or 0204-DR-architecture.md

## Dependencies
- #111 (Create 02xx DR series) - must exist to receive extracted content
- #109 (Rename layers) - terminology consistency

## Acceptance Criteria
- [ ] 0007 renamed to 0007-signal-handling.md
- [ ] Signal matrix updated (noai → Ignore)
- [ ] Decision rationale moved to appropriate DR docs
- [ ] 0003-file-inventory.md updated
- [ ] Cross-references added between 0007 and DR docs

---

## Issue #113: Refactor: Implement "Naked Python" Architecture (Remove LangGraph)

**Created:** 2025-12-30
**Closed:** 2025-12-31

### Description


# Refactor: Implement "Naked Python" Architecture (Remove LangGraph)

**Issue ID:** #113
**Type:** Refactor
**Priority:** High
**Sprint:** "Naked Ridge" Refactor

## 1. Context & Motivation
We currently use **LangGraph** and **LangChain** to orchestrate a simple linear pipeline.
* **The Problem:** This introduces ~200MB of dependencies and increases cold-start latency for a flow that has no cyclic requirements.
* **The Goal:** Pivot to a "Naked Python" architecture. We will use standard Python logic and the native `boto3` library (already present in the Lambda runtime) to handle the flow.
* **The Benefit:** Drastic reduction in deployment size (from ~250MB to <1MB), faster cold starts, and zero dependency hell.

## 2. Technical Requirements

### A. Dependency Cleanup
* **Remove:** `langgraph`, `langchain`, `langchain-aws`, `langchain-core` from `pyproject.toml`.
* **Keep:** `boto3` (for local dev typing), `pytest`.
* **Update:** `deploy.sh` must be simplified. It should no longer export requirements, download binaries, or cross-compile. It should simply zip the `.py` source files.

### B. Logic Refactor (`lambda_function.py`)
Replace the graph invocation with a sequential "Defense Funnel" implemented in pure Python. The Lambda must implement the following server-side layers defined in `docs/1080-wire-agent-logic.md`:

1.  **Denylist:** Execute deterministic blocking of hate terms (Stub: `return False`).
2.  **Semantic:** Call `SemanticGuardrail` to perform AI-based context analysis (using `boto3`).
3.  **Transform:** Execute noarchive handling (Stub: Pass-through).
4.  **Persistence:** Write state/history to DynamoDB (using `boto3`).
5.  **Generation:** Call Bedrock Agent or Model (using `boto3`).

### C. Architecture Updates
* **Remove:** `agent.py` (Graph definition).
* **Remove:** `checkpointer.py` (LangGraph persistence).
* **Update:** `src/guardrails/semantic.py` to ensure it uses `boto3` directly without LangChain wrappers.

## 3. Definition of Done
* [ ] `pyproject.toml` is stripped of LangChain/LangGraph dependencies.
* [ ] `deploy.sh` creates a zip file containing ONLY Python source files (size < 1MB).
* [ ] `lambda_function.py` orchestrates the sequential flow (Denylist -> Semantic -> Transform -> Save -> Bedrock) using only `boto3`.
* [ ] `agent.py` and `checkpointer.py` are deleted.
* [ ] Architecture diagrams in `docs/0001` are updated to reflect the linear flow.
* [ ] **Verification:** Manual test confirms the "Explain" feature works end-to-end with the new lightweight Lambda.

## 4. Documentation Impact
* **Create:** `docs/0211-ADR-naked-python-architecture.md` (Decision record).
* **Deprecate:** `docs/0205-ADR-langgraph-orchestration.md`.
* **Update:** `docs/1080-wire-agent-logic.md` (Update LLD to reflect sequential Python functions).

---

## Issue #114: Restore Overlay Logic and Fix Viewport (Issue 77 + 98)

**Created:** 2025-12-30
**Closed:** 2025-12-30

### Description

Recovery Mission:
1. Restore the lost 'overlay.js' injection logic from Issue #77 (Allowlist Feedback).
2. Implement the V3 positioning math verified in 'tests/manual_overlay_math.html' (Issue #98).
3. Ensure 'service-worker.js' properly triggers the overlay on blocked sites.

---

## Issue #116: feat: Authenticate users via LinkedIn OAuth

**Labels:** security, high-priority, feature

**Created:** 2025-12-30
**Closed:** 2026-01-06

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

## Issue #119: feat: create RSDB download utility for denylist population

**Created:** 2025-12-31
**Closed:** 2025-12-31

### Description

## Context
Issue #45 implemented the denylist filter, but `denylist.json` is empty. We need a utility to populate it from [rsdb.org](http://www.rsdb.org/).

## Requirements

### R1: Download RSDB Data
- Scrape/fetch terms from rsdb.org
- Store in a local directory (NOT in `src/guardrails/resources/`)

### R2: .gitignore Protection
- Create dedicated directory (e.g., `data/rsdb/` or `.rsdb/`)
- Add to `.gitignore` - these terms must NEVER be committed

### R3: Output Format
- Generate JSON matching `denylist.json` schema:
```json
{
    "version": "1.0",
    "source": "rsdb.org",
    "updated": "YYYY-MM-DD",
    "terms": ["term1", "term2", ...]
}
```

### R4: Update Strategy
**Decision needed in LLD:**
- Option A: Full pull each time (simpler, always fresh)
- Option B: Incremental update (check for changes)

Given RSDB is likely small (hundreds to low thousands of terms), **Option A (full pull)** is recommended for simplicity.

## Open Questions for LLD

1. **Storage location:** `.rsdb/` (hidden) vs `data/rsdb/` (visible but ignored)?
2. **Manual vs automated:** Run manually by Orchestrator, or scheduled?
3. **Deployment pipeline:** How does this file get to Lambda? (See integration question below)

## Acceptance Criteria
- [ ] Utility script in `tools/` directory
- [ ] Directory and output file .gitignored
- [ ] Outputs valid JSON matching denylist schema
- [ ] Documented usage in script docstring

## Related
- #45 - Denylist implementation (this populates it)
- #113 - Naked Python Architecture (may affect file paths)

---

## Issue #121: feat: integrate official RSDB data source

**Labels:** enhancement

**Created:** 2025-12-31
**Closed:** 2026-01-01

### Description

## Context
Issue #119 implemented a workaround using a third-party GitHub Gist for RSDB data. This issue tracks the work to get official data from rsdb.org.

**Current State (from #119):**
- Uses Gist: https://gist.github.com/Vizdun/0e9d76834d609dde09842be9bab53db7
- Last updated ~2022 (3+ years stale)
- Unknown collection method
- 2,584 terms (may be incomplete)

## Requirements

### R1: Official Data Source
- Contact rsdb.org maintainers about official API or data export
- If no API: implement web scraper for rsdb.org

### R2: Data Freshness
- Document refresh frequency (monthly? quarterly?)
- Consider automated refresh (GitHub Action or Lambda)

### R3: Validation
- Compare official source against current Gist data
- Document any missing/added terms

## Options to Explore

1. **Email rsdb.org** - Request official export or API access
2. **Web scraper** - Parse rsdb.org HTML directly
3. **Alternative sources** - Wikipedia list of ethnic slurs, HateSonar, etc.

## Priority
**Post-MVP** - Current workaround is sufficient for MVP testing.

## Related
- #119 - RSDB download utility (workaround implementation)
- #45 - Denylist filter (consumer of this data)

## Labels
enhancement, post-mvp, data-source

---

## Issue #124: feat: Implement 'Digital Etymologist' Persona & Structured JSON Response

**Labels:** feature, backend

**Created:** 2025-12-31
**Closed:** 2026-01-02

### Description


## Objective
Transform the Bedrock generation layer to act as an objective 'Digital Etymologist' rather than a generic assistant.

## Requirements
1. **System Prompt:** Update the prompt to enforce a neutral, academic tone (no scolding).
2. **Structured Output:** The Lambda must return a JSON object (not raw string) with three tiers:
   - **Signal:** 2-4 word classification (e.g., 'Archaic Pejorative').
   - **Gem:** Single sentence summary (max 25 words).
   - **Context:** 3-sentence historical detail (max 100 words).
3. **Fail-Safe:** If the LLM produces invalid JSON, fallback to a standard error message.

## Architecture
- **Input:** User text + Context.
- **Processing:** Bedrock (Claude 3 Haiku/Sonnet).
- **Output:** JSON Payload to frontend.

## Acceptance Criteria
- [ ] Returns valid JSON structure.
- [ ] Tone is encyclopedic, not conversational.
- [ ] Latency remains under 3s.

---

## Issue #125: feat: Implement 'Museum Label' Progressive Disclosure UI

**Labels:** feature, frontend

**Created:** 2025-12-31
**Closed:** 2026-01-06

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
**Closed:** 2026-01-09

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
**Closed:** 2026-01-09

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
**Closed:** 2026-01-09

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
**Closed:** 2026-01-09

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

## Issue #134: Bug: Extension/Lambda field name mismatch causes 400 errors

**Created:** 2026-01-01
**Closed:** 2026-01-02

### Description

## Problem
Extension requests return HTTP 400 with `{"error": "Missing required field: text"}`.

## Diagnosis
Field name mismatch between extension and Lambda:

| Extension sends | Lambda expects |
|-----------------|----------------|
| `word` | `text` |
| `context` | `domContext` |

### Extension (`service-worker.js:74-79`)
```javascript
const payload = {
    word: info.selectionText,
    url: info.pageUrl,
    title: tab.title,
    context: fullPageText
};
```

### Lambda (`src/lambda_function.py:69,252,275`)
```python
if "text" not in event:
    return False, "Missing required field: text"
...
text = body["text"]
context_text = body.get("domContext", "")
```

## Evidence
```bash
$ curl -s -X POST "https://sqrqfnypgswudwtcheeasq5xri0aryfx.lambda-url.us-east-1.on.aws/" \
  -H "Content-Type: application/json" \
  -d '{"word":"test","url":"https://example.com","title":"Test","context":"Test"}'

{"error": "Missing required field: text"}
```

## Root Cause
The Lambda was rewritten in Issue #113 (Naked Python) with new field names, but the extension was not updated to match.

## Options
1. **Fix extension** - Update `service-worker.js` to use `text` and `domContext`
2. **Fix Lambda** - Update `lambda_function.py` to accept `word` and `context`

Option 1 is cleaner (semantic field names), but requires extension reload for testing.

## Related
- #113 (Naked Python Architecture) - introduced new Lambda
- Not WAF-related (WAF from #95 was never deployed)

---

## Issue #137: Investigate 5-second Lambda latency

**Created:** 2026-01-02
**Closed:** 2026-01-07

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
**Closed:** 2026-01-06

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

**Labels:** security, high-priority, backend, audit

**Created:** 2026-01-04
**Closed:** 2026-01-07

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
**Closed:** 2026-01-07

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
**Closed:** 2026-01-09

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
**Closed:** 2026-01-06

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
**Closed:** 2026-01-09

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

## Issue #153: Fix smoke_test.py pytest fixture errors

**Labels:** bug, testing

**Created:** 2026-01-05
**Closed:** 2026-01-06

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

## Issue #154: feat: Add ARIA attributes for screen reader accessibility

**Labels:** enhancement, frontend

**Created:** 2026-01-05
**Closed:** 2026-01-06

### Description

## Summary

The extension UI (overlay and popup) lacks ARIA attributes, making it inaccessible to users with screen readers.

## Current State

- Overlay appears/disappears with no announcement to assistive technology
- No `role`, `aria-live`, or `aria-label` attributes on dynamic content
- Keyboard navigation not fully supported (no `tabindex` management)

## Acceptance Criteria

### Overlay (`overlay.js`)
- [ ] Add `role="alert"` to overlay container
- [ ] Add `aria-live="polite"` for status updates
- [ ] Ensure overlay content is announced when it appears

### Popup (`popup.html`, `popup.js`)
- [ ] Add `aria-label` to icon buttons
- [ ] Add `role="status"` to dynamic status areas
- [ ] Ensure allowlist toggle is keyboard accessible
- [ ] Add `aria-checked` to toggle states

### Blocked State
- [ ] Announce "This site is blocked" to screen readers
- [ ] Provide keyboard-accessible way to understand why

## Technical Notes

```javascript
// Example fix for overlay.js
shadow.innerHTML = `
  <div class="overlay"
       role="alert"
       aria-live="polite"
       aria-label="Aletheia status">
    ${message}
  </div>
`;
```

## References

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [MDN ARIA Guide](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA)
- [Chrome Extension Accessibility](https://developer.chrome.com/docs/extensions/mv3/a11y/)

## Labels

accessibility, enhancement, frontend

---

## Issue #155: feat: Skip DynamoDB persistence when 'noarchive' signal present

**Labels:** security, feature, backend

**Created:** 2026-01-05
**Closed:** 2026-01-06

### Description

## Context

`docs/0007-signal-handling.md` states that content with the `noarchive` signal should be transformed/summarized and not persisted. Currently, `src/lambda_function.py` persists all text to DynamoDB regardless of signals.

## Problem

The Lambda handler does not check for `noarchive` signals before persisting user text to DynamoDB, violating the signal handling policy.

## Requirements

Update the Lambda logic to check the `signals` payload and skip the `save_state` call if `noarchive` is present.

### Implementation

**1. Check signals before save:**
```python
# In lambda_handler, before save_state():
signals = event.get('signals', {})
if not signals.get('noarchive', False):
    save_state(thread_id, text, url, safety_score)
```

**2. Extension must pass signals:**
Ensure `extension-chrome-V3/service-worker.js` includes parsed signals in the Lambda request payload.

## Acceptance Criteria

- [ ] Lambda checks for `noarchive` signal before persisting
- [ ] If `noarchive` is true, `save_state()` is skipped
- [ ] Extension passes signals from content script to Lambda
- [ ] Unit tests verify both paths (with/without noarchive)

## References

- Signal Handling Policy: `docs/0007-signal-handling.md`
- Privacy Audit: `docs/0810-audit-privacy.md`
- Related: #145 (DynamoDB TTL)

---

## Issue #156: perf: Optimize extension 'Time to Feedback' latency

**Labels:** enhancement, frontend

**Created:** 2026-01-05
**Closed:** 2026-01-06

### Description

## Context

0812 Performance Audit identified a HIGH severity issue: the time between user clicking "Explain with AI" and the "Saving..." overlay appearing is 500-1000ms (target: <100ms).

## Root Cause

Cumulative latency of sequential asynchronous operations:
1. `contextMenus.onClicked` fires
2. `storage.local.get` (Allowlist Check) - async
3. `scripting.executeScript` (Inject Overlay) - async
4. `scripting.executeScript` (Show Message) - async

## Architectural Trade-off (ADR 0201)

**Privacy wins, Performance loses.**

Because we use `activeTab` permission instead of `host_permissions: ["<all_urls>"]`, we MUST use `scripting.executeScript` at interaction time. This is inherently slower than a pre-loaded content script but protects user privacy.

## Optimization Options

1. **Parallelize Allowlist Check and Script Injection:** Start injecting overlay script while checking allowlist
2. **Pre-inject overlay on allowlisted domains:** After allowlist check passes, inject overlay.js immediately so it's ready for future clicks
3. **Reduce async chain:** Combine multiple scripting.executeScript calls where possible

## Acceptance Criteria

- [ ] Measure current "click-to-glass" time in Chrome DevTools
- [ ] Implement parallelization of allowlist check and script injection
- [ ] Verify improvement (target: <200ms)
- [ ] Apply to both Chrome and Firefox extensions

## References

- docs/GEMINI-HANDOFF-OVERLAY-TIMING.md
- docs/0812-audit-performance.md
- ADR 0201 (Privacy First Architecture)

---

## Issue #157: chore: Migrate ESLint to flat config format

**Labels:** chore

**Created:** 2026-01-05
**Closed:** 2026-01-06

### Description

## Context

0813 Code Quality Audit identified that our ESLint configuration uses the legacy format (`.eslintrc.json`). ESLint 9+ uses "flat config" (`eslint.config.js`).

## Current State

- File: `.eslintrc.json`
- Format: Legacy JSON config
- Works with: ESLint v8 (currently pinned)

## Problem

- ESLint v9+ requires flat config format
- Continuing to use legacy format creates upgrade friction
- Eventually ESLint will drop support for legacy config

## Migration Steps

1. Create `eslint.config.js` with equivalent rules
2. Update any `ESLINT_USE_FLAT_CONFIG` env var usage
3. Test on both Chrome and Firefox extension code
4. Remove `.eslintrc.json`
5. Update CI workflow if needed

## References

- [ESLint Flat Config Migration Guide](https://eslint.org/docs/latest/use/configure/migration-guide)
- [ESLint v9 Release Notes](https://eslint.org/blog/2024/04/eslint-v9.0.0-released/)

## Priority

LOW - Current setup works, this is future-proofing.

---

## Issue #159: docs: Update GitHub Wiki for 0817 audit findings

**Labels:** documentation

**Created:** 2026-01-05
**Closed:** 2026-01-06

### Description

## Context

0817 Wiki Alignment Audit (Gemini 3.0 Pro, 2026-01-05) identified content drift between the GitHub Wiki and actual system behavior.

## Required Updates

### 1. Privacy Page (CRITICAL)

**Current State:** Wiki says "in-memory only"
**Actual State:** Lambda persists data to DynamoDB

**Updates needed:**
- Disclose DynamoDB persistence
- Document 24/48h TTL (once #145 is implemented)
- Note lack of user authentication
- Reference data erasure process (#147)

### 2. Terms of Use Page (HIGH)

**Required:** Create page detailing prohibited content categories enforced by:
- `extension-chrome-V3/content-safety.js` (client-side age gate)
- `src/guardrails/denylist.py` (server-side hate speech filter)

Content categories from `src/guardrails/resources/taxonomy.json`:
- Hate Speech
- Harassment
- Sexual Content
- Age-restricted content

### 3. Architecture Page (MEDIUM)

**Updates needed:**
- Remove references to LangGraph/LangChain (per ADR 0211 Naked Python)
- Add Digital Etymologist persona (#124)
- Document buffered response pattern
- Update data flow diagram

## Wiki Edit Process

Per `docs/0817-audit-wiki-alignment.md` §5:
```bash
git clone https://github.com/martymcenroe/Aletheia.wiki.git
cd Aletheia.wiki
# Edit .md files
git commit -am "docs: update wiki per 0817 audit"
git push
```

## References

- 0817 Audit: `docs/0817-audit-wiki-alignment.md`
- Privacy Audit: `docs/0810-audit-privacy.md`
- Related: #145 (TTL), #147 (GDPR), #148 (Bedrock no-training)

---

## Issue #162: feat: Apply Transform layer (summarization) when 'noarchive' signal present

**Labels:** feature, backend

**Created:** 2026-01-05
**Closed:** 2026-01-07

### Description

## Problem

`docs/0007-signal-handling.md` documents that we respect the `noarchive` signal by routing to the Transform layer (summarization for copyright compliance). However, `lambda_function.py` currently ignores this signal entirely.

**This is a Documentation vs Code drift.**

## Current State

- `docs/0007` states: `noarchive` → Action: TRANSFORM
- `src/lambda_function.py`: No `noarchive` handling exists
- Signal Inspector (`src/signal_inspector/`) can detect `noarchive` but Lambda doesn't use it

## Requirements

1. Lambda should check for `noarchive` signal (via meta tag or X-Robots-Tag header)
2. If present, route response through Transform layer (summarization)
3. If absent, return full context

## Technical Approach

Option A: Client-side detection
- Extension detects `noarchive` and sends flag in request payload
- Lambda checks flag and applies Transform layer

Option B: Server-side detection
- Lambda fetches page headers/meta (adds latency)
- Apply Transform layer if `noarchive` detected

**Recommendation:** Option A (client already has page context)

## References

- Signal handling spec: `docs/0007-signal-handling.md`
- Signal Inspector: `src/signal_inspector/`
- Transform layer: Currently implemented as summarization in etymologist response

## Acceptance Criteria

- [ ] Lambda respects `noarchive` signal per 0007 spec
- [ ] Transform layer applies summarization when signal present
- [ ] Tests verify both paths (with/without `noarchive`)

---

## Issue #173: feat: Visual Regression Testing Infrastructure (Phase 1)

**Labels:** testing, feature

**Created:** 2026-01-06
**Closed:** 2026-01-06

### Description

## Context

To support Issue #53 (Store Assets) and improve testing automation, we need visual regression testing infrastructure. This Phase 1 issue covers the foundational setup.

## Objective

Set up Playwright-based visual regression testing that:
1. Catches UI drift via screenshot comparison
2. Provides deterministic, Lambda-free testing
3. Enables future store asset generation

## Requirements

### Infrastructure
- [ ] Configure Playwright `toHaveScreenshot()` settings
- [ ] Add `npm run test:visual` script
- [ ] Create shared test utilities (`tests/e2e/utils/`)
- [ ] Create mock data modules (`tests/e2e/mocks/`)

### Proof of Concept
- [ ] One visual regression test (`visual-poc.spec.js`)
- [ ] Baseline generation and comparison working
- [ ] Diff detection on intentional changes

## Technical Approach

- Use Playwright's native `toHaveScreenshot()` (v1.40.0+)
- Mock API responses via `page.route()` - no Lambda dependency
- `maxDiffPixels: 100` tolerance for antialiasing
- Serial execution (`workers: 1`) for extension stability
- Baselines committed to git in `__snapshots__/`

## Related

- #53 (Store Assets) - depends on this infrastructure
- #160 (Accessibility automation) - can use same infrastructure
- #161 (Performance benchmarks) - can extend this approach

## Future Phases (Not This Issue)

- Phase 2: Full visual regression suite (popup + overlay)
- Phase 3: Store asset generation
- Phase 4: Expanded E2E coverage
- Phase 5: CI integration

---

## Issue #177: feat: Store surrounding paragraph (domContext) in DynamoDB

**Created:** 2026-01-06
**Closed:** 2026-01-07

### Description

## Summary

The Privacy wiki claims we store "Surrounding paragraph" but the code does NOT store it. The `domContext` is read from the request and sent to Bedrock but never persisted to DynamoDB.

**Current behavior:** Only `text`, `url`, `userId`, `safety_score` stored
**Expected behavior:** Also store `domContext` for analytics and quality monitoring

## Code Evidence

```python
# Line 278-286: save_state call does NOT include domContext
save_state(
    thread_id,
    {
        "text": text,
        "url": body.get("url", ""),
        "userId": body.get("userId"),
        "safety_score": metadata.get("scores", {}),
    },
)

# Line 290: domContext is read but never stored
context_text = body.get("domContext", "")
```

## Definition of Done

### Backend
- [ ] Add `context` field to DynamoDB item in `save_state()`
- [ ] Update DynamoDB table schema if needed (new attribute)
- [ ] Ensure TTL still applies to new field

### Tools
- [ ] Create/update analytics tool with viewing options:
  - View mode: date, word, url only (compact)
  - View mode: full details with surrounding text
  - Export to CSV option
- [ ] Document tool usage

### Documentation
- [ ] Update wiki Privacy.md (should already be accurate after this fix)
- [ ] Update any relevant ADRs
- [ ] Add to 0003-file-inventory.md if new files created

### Verification
- [ ] Run 0809 Security Audit - PASS
- [ ] Run 0810 Privacy Audit - PASS
- [ ] Run 0817 Wiki Alignment Audit - PASS

## Labels
enhancement, privacy, dynamodb

🤖 Generated with [Claude Code](https://claude.com/claude-code)

---

## Issue #178: feat: Store AI etymology response in DynamoDB for quality monitoring

**Created:** 2026-01-06
**Closed:** 2026-01-07

### Description

## Summary

The Privacy wiki claims we store "AI response" for quality monitoring but the code does NOT store it. The etymology response (signal, gem, context) from Bedrock is returned to the client but never persisted.

**Current behavior:** Only `text`, `url`, `userId`, `safety_score` stored
**Expected behavior:** Also store etymology response for quality monitoring and analytics

## Code Evidence

```python
# Line 291: Etymology result generated
result = generate_etymology(text, context_text)

# Line 293-300: Response built and returned, but NOT stored
response_body = {
    "thread_id": thread_id,
    "status": result["status"],
    "signal": result["response"]["signal"],
    "gem": result["response"]["gem"],
    "context": result["response"]["context"],
}

# save_state() was called BEFORE generate_etymology() - response not included
```

## Definition of Done

### Backend
- [ ] Add `response` field to DynamoDB item (store signal, gem, context)
- [ ] Move `save_state()` call to AFTER etymology generation, OR add second save
- [ ] Consider storage size implications (context field can be long)
- [ ] Ensure TTL still applies

### Tools
- [ ] Update analytics tool to display AI responses
- [ ] Add filtering by signal color (green/yellow/orange/red)
- [ ] Export option should include response data

### Documentation
- [ ] Update wiki Privacy.md (should already be accurate after this fix)
- [ ] Update any relevant ADRs
- [ ] Consider privacy implications of storing AI-generated content

### Verification
- [ ] Run 0809 Security Audit - PASS
- [ ] Run 0810 Privacy Audit - PASS
- [ ] Run 0817 Wiki Alignment Audit - PASS

## Notes

This issue is related to but separate from #177 (storing domContext). Both address gaps between wiki claims and code reality discovered during 0810 Privacy Audit.

## Labels
enhancement, privacy, dynamodb

🤖 Generated with [Claude Code](https://claude.com/claude-code)

---

## Issue #179: Retroactive reports for closed issues missing documentation

**Created:** 2026-01-06
**Closed:** 2026-01-06

### Description

## Problem

The 2026-01-06 audit (0802 Reports Completeness) identified ~15+ closed issues that lack required implementation and test reports.

## Affected Issues

| Issue | Title |
|-------|-------|
| #116 | LinkedIn OAuth |
| #119 | RSDB Download |
| #134 | Field Name Mismatch |
| #112 | Restructure 0007 |
| #111 | Decision Records |
| #110 | Recover ADR Content |
| #109 | Rename Filter Layers |
| (and others) |

## Requirements

Per 0004 Orchestration Protocol §8.6, every closed issue should have:
- `docs/reports/{IssueID}/implementation-report.md`
- `docs/reports/{IssueID}/test-report.md`

## Acceptance Criteria

- [ ] Audit all closed issues to identify which need reports
- [ ] Create retroactive reports for issues with significant code changes
- [ ] Mark documentation-only issues as exempt (no code = no report needed)
- [ ] Update 6001-closed-issues.md with report status

## Priority

HIGH - Process compliance gap

## Source

Audit: docs/audit-results/2026-01-06.md (F1)

---

## Issue #180: Update 0809 Security Audit to OWASP Top 10:2025

**Created:** 2026-01-06
**Closed:** 2026-01-06

### Description

## Problem

The 0809 Security Audit currently references OWASP Top 10:2021. OWASP released version 2025 with significant changes.

## Changes in OWASP 2025

### New Categories
- **A03: Software Supply Chain Failures** (expanded from A06:2021 Vulnerable Components)
- **A10: Mishandling of Exceptional Conditions** (new category, 24 CWEs)

### Ranking Shifts
| Category | 2021 | 2025 |
|----------|------|------|
| Security Misconfiguration | #5 | #2 |
| Cryptographic Failures | #2 | #4 |
| Injection | #3 | #5 |
| Insecure Design | #4 | #6 |

### Other Changes
- SSRF absorbed into Broken Access Control
- 589 CWEs analyzed (up from ~400)

## Requirements

- [ ] Update 0809 §2 checklist to OWASP 2025 numbering
- [ ] Add A03 Software Supply Chain section (cross-ref 0819)
- [ ] Add A10 Mishandling of Exceptional Conditions section
- [ ] Update references section with 2025 links
- [ ] Verify Aletheia compliance with new categories

## References

- [OWASP Top 10:2025](https://owasp.org/Top10/2025/)
- [OWASP 2025 Introduction](https://owasp.org/Top10/2025/0x00_2025-Introduction/)

## Priority

MEDIUM - Framework currency

## Source

Audit: docs/audit-results/2026-01-06.md (F2)

---

## Issue #181: Update 0898 Framework Registry with 2025-2026 discoveries

**Created:** 2026-01-06
**Closed:** 2026-01-06

### Description

## Problem

Horizon scanning (deep mode) identified new/updated frameworks that should be tracked in 0898.

## Discovered Frameworks

| Framework | Status | Action |
|-----------|--------|--------|
| **NIST Cyber AI Profile** (IR 8596) | Draft Dec 2025 | Add to registry, monitor |
| **EU AI Act GPAI Obligations** | Effective Aug 2025 | Compliance review |
| **EU AI Act High-Risk** | Effective Aug 2026 | Plan compliance |
| **SPDX 3.0 AI Profile** | Released | Consider for 0819 AIBOM |

## Key Dates

- **Jan 14, 2026:** NIST Cyber AI Profile workshop
- **Jan 30, 2026:** NIST comment period closes
- **Aug 2, 2026:** EU AI Act high-risk obligations

## Requirements

- [ ] Update 0898 §2.1 Active Framework Registry with new entries
- [ ] Add NIST Cyber AI Profile to monitoring list
- [ ] Document EU AI Act compliance status
- [ ] Evaluate SPDX 3.0 AI Profile for 0819 integration
- [ ] Update §5.3 Regulatory Triggers with 2026 dates

## References

- [NIST Cyber AI Profile](https://csrc.nist.gov/News/2025/nist-releases-prelim-draft-cyber-ai-profile)
- [EU AI Act Timeline](https://artificialintelligenceact.eu/implementation-timeline/)
- [SPDX 3.0](https://spdx.dev/)

## Priority

MEDIUM - Proactive compliance

## Source

Audit: docs/audit-results/2026-01-06.md (F3)

---

## Issue #182: Evaluate Claude Code new features (subagents, skills)

**Created:** 2026-01-06
**Closed:** 2026-01-06

### Description

## Opportunity

Claude Code released significant new features in late 2025 that could improve AgentOS workflows.

## New Features Available

| Feature | Description | Potential Use |
|---------|-------------|---------------|
| **Subagents** | Custom specialized agents via `/agents` | Dedicated audit agents |
| **Skills** | Dynamic instruction loading | Skill-based audit execution |
| **Named Sessions** | `/rename`, `/resume` | Session continuity |
| **Status Line** | `/statusline` configuration | Workflow visibility |
| **Thinking Mode** | Default for Opus 4.5 | Already active |

## 2026 Preview (Demo Stage)
- Long-running tasks
- Swarm capabilities

## Requirements

- [ ] Review subagent capabilities for audit automation potential
- [ ] Evaluate skills system for standardized audit execution
- [ ] Consider updating CLAUDE.md to reference new features
- [ ] Test named session workflow for multi-day tasks

## References

- [Claude Code Changelog](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)
- [ClaudeLog](https://claudelog.com/claude-code-changelog/)

## Priority

LOW - Enhancement opportunity

## Source

Audit: docs/audit-results/2026-01-06.md (F4)

---

## Issue #189: Test suite gaps: missing test_build_release.py and orphan test_guardrails.py

**Created:** 2026-01-07
**Closed:** 2026-01-09

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

## Issue #191: refactor: Change session logs from weekly to daily granularity

**Created:** 2026-01-07
**Closed:** 2026-01-07

### Description

## Summary
Change session log files from weekly to daily granularity while preserving the 3:00 AM CT day boundary.

## Current State
- Files: `docs/session-logs/Week-starting-YYYY-MM-DD.md`
- Boundary: Monday 3:00 AM CT to following Monday 2:59 AM CT
- Multiple sessions accumulate in one weekly file

## Proposed State
- Files: `docs/session-logs/YYYY-MM-DD.md`
- Boundary: 3:00 AM CT to following day 2:59 AM CT
- One file per day (calendar day shifted by 3 hours)

## Files to Update
- `CLAUDE.md` - Session logging instructions
- `docs/0000-GUIDE.md` - If session log format is mentioned
- `docs/0009-session-closeout-protocol.md` - Closeout procedure
- `docs/0100-TEMPLATE-GUIDE.md` - Session log template
- `tools/generate_onboard_digest.py` - If it parses session logs

## Rationale
- Easier to locate specific session by date
- Smaller files, faster reads
- Cleaner git history (fewer merge conflicts on same file)

## Migration
Existing weekly files can remain as historical record. New daily format starts immediately.

---

## Issue #192: feat: Add /goodbye command (quick cleanup + exit)

**Created:** 2026-01-07
**Closed:** 2026-01-07

### Description

## Summary
Create a `/goodbye` slash command that bundles quick cleanup with session exit to prevent forgetting cleanup.

## Problem
- Users sometimes forget to run `/cleanup` before ending sessions
- A custom `/exit` command was attempted but overwrote something and never exited
- Need a reliable single command for "I'm done, wrap it up"

## Proposed Behavior
`/goodbye` should:
1. Execute `/cleanup --quick` (session log entry, ~2 min)
2. Exit the session cleanly

## Implementation
Create `.claude/commands/goodbye.md` skill file that:
- Invokes the cleanup skill with --quick flag
- Signals session end after cleanup completes

## Acceptance Criteria
- [ ] `/goodbye` runs quick cleanup
- [ ] Session log entry is created
- [ ] Session exits after cleanup
- [ ] Works reliably (no silent failures)

## Notes
- Do NOT name it `/exit` - that may conflict with built-in behavior
- `/goodbye` is distinctive and clearly indicates "session over"

---

## Issue #193: fix(firefox): add data_collection_permissions and update min version

**Labels:** bug, firefox

**Created:** 2026-01-08
**Closed:** 2026-01-08

### Description

**Context**
Mozilla Linter rejected the v1.0 submission due to missing privacy keys in the manifest (New 2025 Policy).

**Requirements**
1. Add `data_collection_permissions` block to `extensions/firefox/manifest.json` covering:
   - `websiteContent` (for text selection)
   - `personallyIdentifyingInfo` (for LinkedIn OAuth)
2. Add `gecko_android` key with `strict_min_version: '120.0'` to `browser_specific_settings` to silence legacy API warnings.

**Acceptance Criteria**
- `manifest.firefox.json` passes Mozilla Linter without Errors.
- `strict_min_version` warnings regarding Android v57 are gone.

---

## Issue #194: refactor(security): replace unsafe innerHTML with DOM methods

**Labels:** security, refactor

**Created:** 2026-01-08
**Closed:** 2026-01-08

### Description

**Context**
Firefox validation flagged multiple instances of `innerHTML` usage in `overlay.js`. This creates a potential XSS vulnerability if the AI response or selected text contains malicious tags.

**Requirements**
1. Refactor `extensions/chrome/overlay.js` and `extensions/firefox/overlay.js`.
2. Replace all instances of `.innerHTML =` with safe equivalents:
   - Use `.textContent` for plain text.
   - Use `document.createElement()` and `.appendChild()` for structured content.

**Acceptance Criteria**
- Zero instances of `innerHTML` in the codebase.
- Firefox Linter shows 0 Warnings for 'Unsafe assignment'.

---

## Issue #197: fix(security): Change Shadow DOM from mode: 'open' to mode: 'closed' per ADR 0202

**Labels:** security, high-priority

**Created:** 2026-01-09
**Closed:** 2026-01-09

### Description

## Summary

The overlay.js files in both Chrome and Firefox extensions use `attachShadow({ mode: 'open' })` instead of `mode: 'closed'` as mandated by ADR 0202.

## ADR 0202 Requirement

> "We will use Shadow DOM (`element.attachShadow({mode: 'closed'})`) for all UI injected into host pages."

> "Option B: Open Shadow DOM - **Rejected** ... Host page JavaScript can access our shadow tree. Security risk: malicious pages could manipulate our UI. XSS vector if host page is compromised."

## Evidence

```
extensions/chrome/overlay.js:478:    const shadow = host.attachShadow({ mode: 'open' });
extensions/chrome/overlay.js:527:    const shadow = host.attachShadow({ mode: 'open' });
extensions/chrome/overlay.js:728:        const shadow = host.attachShadow({ mode: 'open' });

extensions/firefox/overlay.js:478:    const shadow = host.attachShadow({ mode: 'open' });
extensions/firefox/overlay.js:527:    const shadow = host.attachShadow({ mode: 'open' });
extensions/firefox/overlay.js:728:        const shadow = host.attachShadow({ mode: 'open' });
```

## Risk

A malicious host page could access and manipulate the Aletheia overlay DOM, potentially:
- Injecting malicious content into the overlay
- Stealing user interactions
- Modifying displayed etymology results

## Fix

Change all 6 occurrences from `mode: 'open'` to `mode: 'closed'`.

## Files to Modify

- `extensions/chrome/overlay.js` (3 locations)
- `extensions/firefox/overlay.js` (3 locations)

## Testing

After fix, verify:
1. Overlay still renders correctly on test pages
2. Host page JavaScript cannot access shadow root (`document.querySelector('#aletheia-overlay').shadowRoot` returns `null`)

## References

- ADR 0202: `docs/0202-ADR-shadow-dom-isolation.md`
- Audit finding: `docs/audit-results/2026-01-08.md`

---

## Issue #199: fix: Refine Archaic classification to prevent false positives on formal words

**Created:** 2026-01-09
**Closed:** 2026-01-09

### Description

## Problem

The model is flagging high-register, formal words (like "immiserate", used in the WSJ) as "Archaic." This is incorrect.

## Solution

Refine the "Archaic" classification instructions to be purely chronological, not stylistic.

### Strict Definition for 'Archaic':

**TRUE ARCHAIC (Flag these):** Words that have effectively dropped out of common usage before 1950.
- Examples: "Thou", "Forsooth", "Betwixt", "Swive", "Zounds"
- Criteria: If a modern speaker would only encounter this in a text written 100+ years ago (or a fantasy novel), it is Archaic.

**FORMAL / ACADEMIC (Do NOT Flag):** Words that are rare but currently used in high-level journalism, academia, or economics.
- Examples: "Immiserate", "Ameliorate", "Betoken", "Efficacious"
- The 'WSJ Rule': If the word has appeared in the Wall Street Journal, The Economist, or The New York Times in the last 10 years, it is NOT Archaic. It is merely Formal.

## Implementation

Update the prompt strings in:
- `src/etymologist.py`
- `src/guardrails/` (if applicable)

To explicitly include the "1950 cutoff" and "WSJ Rule."

## Acceptance Criteria

- [ ] System prompt updated with strict chronological definition
- [ ] Tests added for formal vs archaic distinction
- [ ] "Immiserate" and similar formal words no longer flagged as Archaic

---

## Issue #206: feat(firefox): Add LinkedIn OAuth authentication to Firefox extension

**Created:** 2026-01-09
**Closed:** 2026-01-09

### Description

## Summary

Firefox extension is missing LinkedIn OAuth authentication that was added to Chrome in Issue #116. This creates feature parity gap between the two extensions.

## Current State

| Feature | Chrome | Firefox |
|---------|--------|---------|
| LinkedIn OAuth | ✅ Yes (Issue #116) | ❌ Missing |
| Login view | ✅ Yes | ❌ No |
| User bar | ✅ Yes | ❌ No |
| Age gate | ✅ Yes | ❌ No |

## Files to Port

From Chrome to Firefox:
- `extensions/chrome/auth.js` → `extensions/firefox/auth.js`
- `extensions/chrome/popup.js` (auth sections) → `extensions/firefox/popup.js`
- `extensions/chrome/popup.html` (login view, user bar) → `extensions/firefox/popup.html`
- `extensions/chrome/popup.css` (auth styles) → `extensions/firefox/popup.css`

## Considerations

1. **API differences**: Firefox uses `browser.*` APIs vs Chrome's `chrome.*` (mostly compatible via polyfill or direct use)
2. **Identity API**: Firefox's `browser.identity` may have different OAuth flow - needs investigation
3. **Manifest V2**: Firefox extension is MV2, Chrome is MV3 - may affect how auth tokens are handled

## Acceptance Criteria

- [ ] Firefox extension has login view matching Chrome
- [ ] LinkedIn OAuth flow works in Firefox
- [ ] User bar displays after authentication
- [ ] Age gate check works post-authentication
- [ ] Logout functionality works

## References

- Issue #116 - Original Chrome LinkedIn OAuth implementation
- `docs/0002-coding-standards.md` §9.3 - Dual extension parity requirement

---

## Issue #207: feat(testing): Add unit test infrastructure for extension code

**Created:** 2026-01-09
**Closed:** 2026-01-09

### Description

## Summary

Add unit testing framework (Vitest) and Chrome API mocks to enable unit testing of extension code. This is the first phase of implementing ADR 0215 (Test-First Philosophy).

## Motivation

- `popup.js` has 484 lines with **zero unit tests**
- Current E2E tests (Playwright) cannot test error handling, edge cases, or race conditions
- ADR 0215 requires tests before risky changes (e.g., innerHTML removal)
- Chrome API dependencies require mocking for isolation

## Scope

### Add Vitest Framework
- Add `vitest` to devDependencies
- Configure for jsdom environment (DOM simulation)
- Add `npm run test:unit` script

### Create Chrome API Mocks
Create `tests/mocks/chrome-api.mock.js` with mocks for:
- `chrome.tabs.query()`
- `chrome.storage.local.get()` / `set()`
- `chrome.runtime.sendMessage()`
- `chrome.runtime.id`

### Create Auth Mock
Create `tests/mocks/aletheia-auth.mock.js` for:
- `window.AletheiaAuth.isAuthenticated()`
- `window.AletheiaAuth.initiateLogin()`
- `window.AletheiaAuth.logout()`
- `window.AletheiaAuth.getAuthState()`

### Write popup.js Unit Tests
Create `tests/unit/popup.test.js` covering:
- Storage functions (getAllowlist, addToAllowlist, etc.)
- View rendering (showView, renderMainView, etc.)
- Event handlers (handlePowerToggle, handleCheckboxChange, etc.)
- Auth flow (handleLoginClick, handleLogoutClick)
- Age gate (checkAgeGate, polling behavior)

## Acceptance Criteria

- [ ] `npm run test:unit` runs Vitest
- [ ] Chrome API mocks work in jsdom environment
- [ ] popup.js has >80% line coverage
- [ ] Tests verify current behavior (enabling safe refactoring)
- [ ] CI runs unit tests on PR

## Files to Create/Modify

```
package.json                          (add vitest, scripts)
vitest.config.js                      (new)
tests/mocks/chrome-api.mock.js        (new)
tests/mocks/aletheia-auth.mock.js     (new)
tests/unit/popup.test.js              (new)
```

## References

- ADR 0215 - Test-First Philosophy
- Issue #194 - innerHTML removal (blocked on tests)
- Code review findings from `/code-review` (test-coverage agent)

---

## Issue #209: fix(security): Remove innerHTML from popup.js - XSS hardening

**Created:** 2026-01-09
**Closed:** 2026-01-09

### Description

## Summary

Remove remaining innerHTML usage from popup.js in both Chrome and Firefox extensions. This completes the XSS hardening started in Issue #194 (which addressed overlay.js).

**Blocked by:** PR #208 (unit test infrastructure) - tests must exist before refactoring

## Background

Issue #194 removed innerHTML from `overlay.js` but missed `popup.js`. The new `pre-edit-security-warn.sh` hook correctly flagged these during code review.

**Risk Assessment:** Current usage is low-risk (no user input flows into innerHTML), but establishes a dangerous pattern.

## Instances to Fix

| File | Line | Current Code | Risk Level |
|------|------|--------------|------------|
| `extensions/chrome/popup.js` | 187 | `allowlistEl.innerHTML = ''` | Low |
| `extensions/chrome/popup.js` | 417 | `loginButton.innerHTML = '...'` | Low |
| `extensions/firefox/popup.js` | 162 | `allowlistEl.innerHTML = ''` | Low |

## Proposed Fixes

### Fix 1: Clear container safely (Chrome line 187, Firefox line 162)

```javascript
// Before
allowlistEl.innerHTML = '';

// After
while (allowlistEl.firstChild) {
  allowlistEl.removeChild(allowlistEl.firstChild);
}
```

### Fix 2: Reset login button safely (Chrome line 417 only)

```javascript
// Before
loginButton.innerHTML = '<span class="linkedin-icon">in</span> Sign in with LinkedIn';

// After
while (loginButton.firstChild) {
  loginButton.removeChild(loginButton.firstChild);
}
const iconSpan = document.createElement('span');
iconSpan.className = 'linkedin-icon';
iconSpan.textContent = 'in';
loginButton.appendChild(iconSpan);
loginButton.appendChild(document.createTextNode(' Sign in with LinkedIn'));
```

## Test Verification

Per ADR 0215, tests exist to verify current behavior (from PR #208):

- `should clear allowlist element before re-rendering (innerHTML = "" behavior)` - verifies Fix 1
- `should reset button after login failure (innerHTML behavior)` - verifies Fix 2

**Process:**
1. Merge PR #208 (unit tests)
2. Run `npm run test:unit` - verify tests pass
3. Apply fixes
4. Run `npm run test:unit` - verify tests still pass

## Acceptance Criteria

- [ ] PR #208 merged (tests exist)
- [ ] All innerHTML removed from popup.js (Chrome)
- [ ] All innerHTML removed from popup.js (Firefox)
- [ ] `npm run test:unit` passes before AND after changes
- [ ] `npm run lint` passes (no-unsanitized rule)
- [ ] Manual testing: allowlist management works
- [ ] Manual testing: login error recovery works

## References

- Issue #194 - Original innerHTML removal (overlay.js)
- PR #208 - Unit test infrastructure
- ADR 0212 - Unified V3 & Secure DOM
- ADR 0215 - Test-First Philosophy

---

## Issue #211: test(unit): Add tests for auth.js OAuth flow

**Labels:** testing

**Created:** 2026-01-09
**Closed:** 2026-01-10

### Description

## Summary

`extensions/chrome/auth.js` has 350 lines of code with **zero unit tests**. This is the OAuth authentication module handling LinkedIn login, token refresh, and CSRF protection.

## Current State

- **File:** `extensions/chrome/auth.js`
- **Lines:** 350
- **Test coverage:** 0%
- **Source:** Test Gap Analysis 2026-01-09, Report #116

## Why Untested

Report #116 states: "Unit tests for auth module not implemented due to OAuth complexity. Integration and manual testing provide coverage."

## Gap Analysis

The following functions have no automated tests:
- `initiateLogin()` - OAuth flow initiation with CSRF state
- `handleAuthCallback()` - Token exchange
- `refreshAccessToken()` - Token refresh logic
- `validateCsrfState()` - CSRF protection
- Token storage hierarchy (session vs local)

## Proposed Solution

Extract pure functions that can be tested without Chrome API mocks:

1. **CSRF state generation/validation** - Pure crypto functions
2. **Token expiry checking** - Date comparison logic
3. **Storage key management** - Constants and helpers
4. **Error response parsing** - LinkedIn API error handling

Create `tests/unit/auth.test.js` using Vitest (same as popup.test.js).

## Acceptance Criteria

- [ ] Extract testable pure functions from auth.js
- [ ] Create `tests/unit/auth.test.js`
- [ ] Test CSRF state generation (cryptographically random, correct length)
- [ ] Test CSRF state validation (match/mismatch scenarios)
- [ ] Test token expiry logic
- [ ] Test error handling for common OAuth failures
- [ ] Minimum 50% line coverage for auth.js

## References

- Report #116: `docs/reports/116/test-report.md`
- LLD: `docs/1116-linkedin-oauth.md`
- Existing JS test pattern: `tests/unit/popup.test.js`

---

## Issue #212: test(unit): Add tests for service-worker.js

**Labels:** testing

**Created:** 2026-01-09
**Closed:** 2026-01-10

### Description

## Summary

`extensions/chrome/service-worker.js` has 395 lines of code with **zero unit tests**. This is the extension's background script handling context menus, tab state management, and message routing.

## Current State

- **File:** `extensions/chrome/service-worker.js`
- **Lines:** 395
- **Test coverage:** 0%
- **Source:** Test Gap Analysis 2026-01-09

## Gap Analysis

The following functionality has no automated tests:

### Context Menu Management
- `chrome.contextMenus.create()` - Menu item creation
- `handleContextMenuClick()` - Click handler routing
- Menu item enable/disable based on allowlist

### Tab State Management
- `tabStates` Map - Age gate state tracking
- `GET_TAB_STATE` message handler
- Tab state transitions (checking → allowed/restricted)

### Message Routing
- `chrome.runtime.onMessage` handler
- Response formatting
- Error handling

## Proposed Solution

1. Create `tests/unit/service-worker.test.js` using Vitest
2. Mock Chrome APIs (contextMenus, tabs, runtime, storage)
3. Test each message type handler independently
4. Test tab state transitions

## Acceptance Criteria

- [ ] Create `tests/unit/service-worker.test.js`
- [ ] Test context menu creation on install
- [ ] Test context menu click handling
- [ ] Test tab state management (GET_TAB_STATE)
- [ ] Test message routing for all message types
- [ ] Test error handling for invalid messages
- [ ] Minimum 50% line coverage

## References

- Chrome mocks pattern: `tests/mocks/chrome-api.mock.js`
- Existing JS test pattern: `tests/unit/popup.test.js`

---

## Issue #213: test(unit): Add mocked tests for lambda_auth_function.py delete_user_data()

**Labels:** testing

**Created:** 2026-01-09
**Closed:** 2026-01-09

### Description

## Summary

`src/lambda_auth_function.py` has 550 lines with the `delete_user_data()` function only tested manually. This is the GDPR data erasure implementation.

## Current State

- **File:** `src/lambda_auth_function.py`
- **Lines:** 550
- **Function:** `delete_user_data(user_id)`
- **Test coverage:** Manual only
- **Source:** Test Gap Analysis 2026-01-09, Report #147

## Why Untested

Report #147 states: "Coverage Gap Analysis - delete_user_data(): Manual only - Requires DynamoDB + GSI"

The manual test plan includes:
- M1: GSI Creation verification
- M2: Unauthenticated request rejection
- M3: Invalid token rejection
- M4: Valid deletion flow
- M5: No data to delete scenario
- M6: Verify deletion in DynamoDB

## Proposed Solution

Add unit tests with mocked DynamoDB client:

```python
# tests/unit/test_lambda_auth.py
from unittest.mock import MagicMock, patch
import pytest

@patch('src.lambda_auth_function.dynamodb')
def test_delete_user_data_success(mock_dynamodb):
    mock_dynamodb.Table.return_value.query.return_value = {
        'Items': [{'pk': 'user123', 'sk': 'item1'}]
    }
    # ... test deletion logic
```

## Acceptance Criteria

- [ ] Create `tests/unit/test_lambda_auth.py`
- [ ] Mock DynamoDB client and GSI query
- [ ] Test successful deletion (items found and deleted)
- [ ] Test no items to delete scenario
- [ ] Test batch delete pagination (>25 items)
- [ ] Test GSI query error handling
- [ ] Test batch write error handling

## Test Scenarios

| ID | Scenario | Mock Setup | Expected |
|----|----------|------------|----------|
| 010 | Delete with items | Query returns 3 items | batch_write called, returns count=3 |
| 020 | Delete with no items | Query returns empty | No batch_write, returns count=0 |
| 030 | Delete with pagination | Query returns 30 items | Two batch_write calls |
| 040 | GSI query fails | Query raises exception | Error propagated |
| 050 | Batch write fails | batch_write raises | Error propagated |

## References

- Report #147: `docs/reports/147/test-report.md`
- Existing Lambda tests: `tests/unit/test_lambda_handler.py`

---

## Issue #218: test(firefox): Add unit tests for Service Worker (Parity)

**Labels:** testing, technical-debt

**Created:** 2026-01-10
**Closed:** 2026-01-10

### Description

## Context
  We implemented Chrome Service Worker tests in #212. We must achieve parity for Firefox.

  ## Requirements
  1. Create `tests/unit/firefox/service-worker.test.js`
  2. Port logic from `tests/unit/chrome/service-worker.test.js`
  3. Use `browser.*` mocks via `firefox-api.mock.js`
  4. Ensure `npm run test:unit` runs both suites.

---
