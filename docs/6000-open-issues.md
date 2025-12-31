Print mode: double-sided

Fetching open issues from GitHub...
Fetched 30 open issues
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

## Issue #44: feat: Implement Browser Extension Warning UI

**Labels:** feature

**Created:** 2025-12-09
**Updated:** 2025-12-30

### Description

Implement a 4-tier warning system in the Chrome Extension popup based on backend guardrail scores:

1. **Rejection (Red):** If blocked by Selection Check (Regex) or Denylist (RSDB Hate List). Text: 'Blocked: Invalid format or flagged as potential hate speech (Source: RSDB). Context is not evaluated.'
2. **Warning (Orange):** If Score(Provocative) > 0.0. Text: 'Caution: This term has a {P}% probability of carrying sexual or provocative subtext.'
3. **Advisory (Yellow):** If Score(Provocative) == 0.0 AND (Score(Archaic) > 0 OR Score(Neologism) > 0). Text: 'Note: Term detected as Archaic ({A}%) or Neologism ({N}%). Usage may be obscure or unstable.'
4. **Disclaimer (Footer):** 'AI probability scores are non-deterministic and may fluctuate between checks.'

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
**Updated:** 2025-12-24

### Description

Script to zip extension and gen placeholder images.

---

## Issue #58: chore: Implement SonarQube/SonarLint in VSCode

**Labels:** chore

**Created:** 2025-12-20
**Updated:** 2025-12-24

### Description

Set up static code analysis for consistent code quality across projects.

Tasks:
- [ ] Install SonarLint VSCode extension
- [ ] Configure for Python projects
- [ ] Document setup in Engineering Journal

---

## Issue #79: test: Create static 'Firing Range' web page for manual testing

**Labels:** chore

**Created:** 2025-12-21
**Updated:** 2025-12-30

### Description

## Objective
Create a simple, static HTML page hosted on GitHub Pages (or local) to validate Selection Check, Denylist, and Semantic guardrails without typing.

## Test Cases
- Selection Check: Gibberish/Scripts
- Denylist: Hate terms (mocked)
- Semantic: triggers (Archaic/Provocative)

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

## Issue #84: tool: Create 'Signal Inspector' CLI for compliance verification

**Labels:** chore

**Created:** 2025-12-22
**Updated:** 2025-12-24

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

## Issue #94: Create automated test harness for XSS prevention (Security Test 23)

**Labels:** testing, security

**Created:** 2025-12-24
**Updated:** 2025-12-24

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
**Updated:** 2025-12-24

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

## Issue #99: Feature: Automated testing framework for browser extension

**Labels:** enhancement, testing

**Created:** 2025-12-29
**Updated:** 2025-12-29

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
**Updated:** 2025-12-29

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

## Issue #104: Block age-restricted sites (RTA/adult rating detection)

**Labels:** enhancement, security

**Created:** 2025-12-29
**Updated:** 2025-12-29

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
**Updated:** 2025-12-29

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

**Labels:** documentation, enhancement

**Created:** 2025-12-30
**Updated:** 2025-12-30

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

## Issue #121: feat: integrate official RSDB data source

**Labels:** enhancement

**Created:** 2025-12-31
**Updated:** 2025-12-31

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

## Issue #124: feat: Implement 'Digital Etymologist' Persona & Structured JSON Response

**Labels:** feature, backend

**Created:** 2025-12-31
**Updated:** 2025-12-31

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
**Updated:** 2025-12-31

### Description


## Objective
Differentiate between 'Forbidden' terms (Denylist) and 'Educational' terms (Semantic Analysis).

## The Split
1. **Hard Block (The Denylist):**
   - **Source:** `src/guardrails/resources/denylist.json`
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
