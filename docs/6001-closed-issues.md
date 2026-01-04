# Aletheia - Closed Issues

**Generated:** 2026-01-01 10:26 CT
**Total Closed Issues:** 61

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
