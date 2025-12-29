# 0112 - Template: Browser Extension Test Script

## Purpose
This template is for creating manual test scripts for browser extensions when the tester has limited knowledge of browser development tools and testing.

## Target Audience
- Non-technical users who can follow detailed step-by-step instructions
- Users unfamiliar with DevTools, browser extension architecture, or testing concepts
- Future you, returning after weeks/months away from the project

## Key Principles
1. **Assume zero prior knowledge** - Explain F12, what DevTools is, etc.
2. **Absolute paths always** - Never use relative paths
3. **Expected outputs** - Show exactly what success looks like after each command
4. **Visual indicators** - Use emoji/symbols for quick scanning (✅ ❌ ⚠️ 🟢 🔴)
5. **Workarounds** - Document alternative approaches when primary method blocked
6. **Quick reference** - Include command cheat sheet at bottom
7. **Cost controls** - Explicitly warn about services that cost money (AWS, etc.)
8. **Browser-agnostic** - Provide instructions for Chrome AND Firefox where applicable

---

## Template Starts Here

```markdown
# {Feature Name} - Complete Test Script
**Feature:** {One-line description}
**Branch:** {branch-name}
**Issue:** #{issue-number}
**Test Reference:** {Link to LLD section, e.g., docs/NNNN-feature-name.md §6.1}

---

## Pre-Test Setup

### 1. Environment Preparation

**Working Directory:**
```bash
# Navigate to correct worktree (replace with actual path)
cd C:\Users\{username}\Projects\{ProjectName}-{IssueNumber}

# Verify you're on the correct branch
git status
# Expected output: "On branch {branch-name}"

# Check for uncommitted changes
git status
# Expected output: "nothing to commit, working tree clean"
```

**Cost Control Verification:** {If applicable}
```bash
# {Service name} should be OFF to prevent unexpected charges
{service_status_command}
# Expected output: {what "OFF" looks like}
```

### 2. Browser Extension Installation

**For Chrome/Chrome Canary:**
1. Open Chrome
2. Type in address bar: `chrome://extensions/` (press Enter)
3. Look for toggle in top-right corner: "Developer mode"
4. Click toggle to turn ON (should turn blue)
5. Click button "Load unpacked"
6. Navigate to folder: `{absolute-path-to-extension-directory}`
7. Click "Select Folder"
8. You should see extension appear with name "{Extension Name}"
9. Click puzzle icon (top-right of browser, near address bar)
10. Find "{Extension Name}" in list
11. Click pin icon to pin to toolbar

**For Firefox:**
1. Open Firefox
2. Type in address bar: `about:debugging#/runtime/this-firefox` (press Enter)
3. Click button "Load Temporary Add-on..."
4. Navigate to: `{absolute-path-to-extension-directory}`
5. Select file: `manifest.json`
6. Click "Open"
7. Extension should appear in list

**Verify Installation:**
- Chrome: Go to `chrome://extensions/` → find "{Extension Name}" → should show "Enabled"
- Firefox: Extension should appear in `about:debugging` with no error messages

### 3. Initial State Verification

**Before any tests:**
- {State requirement 1, e.g., "Allowlist should be EMPTY"}
- {State requirement 2, e.g., "No badge on toolbar icon"}
- {State requirement 3, e.g., "Service worker running (check DevTools)"}

**How to verify:**
1. {Step-by-step verification instructions}
2. {What "correct state" looks like}

### 4. Cost Control / Service Management

{If using AWS, external APIs, or paid services}

**Default State:** {Service} should be OFF to prevent costs

**Commands:**
```bash
{service}_on   # Enable {service}
{service}_off  # Disable {service}
{service}_status  # Check current state
```

**CRITICAL:** Always run `{service}_off` after testing to prevent charges!

---

## Test Execution

{Repeat this section for each test scenario}

### {✅/❌/⏸️} Test {NNN}: {Test Name}
**Status:** {✓ PASSED / ✗ FAILED / ⏸️ READY FOR TEST / ⚠️ BLOCKED} (as of YYYY-MM-DD)
**Priority:** {🔴 Critical / 🟡 Important / 🟢 Nice-to-have}

{If there are known issues or fixes:}
**Known Issue:** {Description}
**Fix:** {What was done to address it, commit hash if applicable}

#### Setup
**Prerequisites:**
- {Requirement 1 - be specific, e.g., "Visit wsj.com"}
- {Requirement 2 - e.g., "Ensure site is NOT in allowlist"}
- {Requirement 3 - e.g., "Lambda must be OFF: run `aws_off`"}

**How to verify prerequisites met:**
1. {Verification step 1}
   - Expected: {What you should see}
2. {Verification step 2}
   - Expected: {What you should see}

#### Action
**Step-by-step:**
1. {Action 1 - be extremely specific}
   - Example: "Select any single word on the page by double-clicking it"
2. {Action 2}
   - Example: "Right-click on selected text"
3. {Action 3}
   - Example: "In context menu, click 'Explain with AI'"

#### Expected Results
**Visual Feedback:**
- {Visual indicator 1} - e.g., "⚠️ **Overlay appears** near selected text"
  - Message should say: "{exact text}"
  - Background color: {color description or hex code}
- {Visual indicator 2} - e.g., "🟠 **Badge shows:** `!` with amber background"
  - Location: Top-right of browser, on extension icon
- {Visual indicator 3} - e.g., "⏱️ **Overlay disappears** after 5 seconds"

**System Behavior:**
- {Backend behavior 1} - e.g., "📡 **No API call** should be made"
- {Backend behavior 2} - e.g., "🗄️ **Database entry created** with timestamp"

#### Verification
**How to check backend/system state:**

{If checking logs:}
```bash
# Check {service} logs for activity
{log_command} --since 5m
# Expected: {what you should see if test passed}
# If failed: {what error output looks like}
```

{If checking database:}
```bash
# View recent database entries
{db_query_command} --tail 1
# Expected: Entry shows "{expected-data}"
# Timestamp should be recent (within last minute)
```

{If checking browser console:}
**Open DevTools Console:**
1. Press **F12** key (opens DevTools panel at bottom/side of browser)
2. Click **Console** tab at top of DevTools
3. Look for messages that start with `[{Extension Name}]`
4. Should see: `{expected log message}`
5. Should NOT see: Any red error messages

#### Pass Criteria
- [ ] {Criterion 1} - e.g., "Overlay appeared with correct message"
- [ ] {Criterion 2} - e.g., "Badge showed amber exclamation point"
- [ ] {Criterion 3} - e.g., "No API call was made (checked logs)"
- [ ] {Criterion 4} - e.g., "Overlay auto-dismissed after ~5 seconds"

#### If Test Fails
**Common issues and fixes:**

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| {Symptom} | {Root cause} | {Solution with commands/steps} |
| Extension not appearing | Not loaded or disabled | Reload extension: chrome://extensions/ → click reload icon |
| No overlay shows | Content script not injected | Check DevTools Console for errors (F12 → Console tab) |
| {Other common failure} | {Cause} | {Fix} |

**If still stuck:**
1. Reload extension: {browser-specific instructions}
2. Close all tabs and reopen fresh tab to test site
3. Check browser console for errors (F12 → Console tab)
4. Verify prerequisites are actually met
5. Document failure and skip to next test

#### Workarounds
{If primary test method is blocked or difficult}

**Alternative Test Method:**
1. {Alternative approach step 1}
2. {Alternative approach step 2}
3. Achieves same validation but via different path

**Example:** If file:// URLs don't work for testing XSS, use DevTools console injection:
```javascript
// Open DevTools (F12) → Console tab
// Paste this code and press Enter:
const testEl = document.createElement('p');
testEl.textContent = '<script>alert("xss")</script>';
testEl.style.padding = '20px';
testEl.style.background = '#fee';
document.body.insertBefore(testEl, document.body.firstChild);
// Then select the text that appears and test
```

---

## Post-Test Checklist

### 1. Cost Control
{If using paid services}
```bash
# CRITICAL: Turn off paid services
{service}_off
{service}_status  # Verify it's actually off
# Expected: {what "OFF" output looks like}
```

### 2. Test Results Summary
Go back through each test section and update status:
- ✅ **PASSED** - Test succeeded, all criteria met
- ❌ **FAILED** - Test failed (document what went wrong)
- ⏸️ **READY** - Not yet tested
- ⚠️ **BLOCKED** - Cannot test due to dependency/blocker

**Overall Results:**
- Total tests: {N}
- Passed: {N} ✅
- Failed: {N} ❌
- Blocked: {N} ⚠️
- Not tested: {N} ⏸️

### 3. Known Issues / Blockers
**Issues discovered during testing:**
- Issue #{NNN}: {Description}
  - Affects: Test {NNN}
  - Severity: {Critical/Major/Minor}
  - Workaround: {If available}

**Blockers:**
- {Blocker 1} - blocking tests {NNN, NNN}
  - Fix required: {What needs to happen}
  - Tracking: Issue #{NNN} or branch {branch-name}

### 4. File Artifacts
**If saving screenshots or logs:**
- Screenshots: `{absolute-path}/screenshots/test-{NNN}-{description}.png`
- Logs: `{absolute-path}/logs/test-{NNN}-{timestamp}.log`
- Videos: `{absolute-path}/videos/test-{NNN}.mp4`

### 5. Cleanup
**Before closing:**
- [ ] All paid services turned OFF
- [ ] Extension removed/disabled if no longer needed
- [ ] Test data cleaned up (if applicable)
- [ ] This test script updated with results
- [ ] Any new issues filed in GitHub

---

## Quick Reference

### Browser Extension Management

**Chrome:**
```
Load:    chrome://extensions/ → Developer mode ON → Load unpacked
Reload:  chrome://extensions/ → Find extension → Click reload icon
Remove:  chrome://extensions/ → Find extension → Click Remove
Console: F12 → Console tab
```

**Firefox:**
```
Load:    about:debugging → Load Temporary Add-on → select manifest.json
Reload:  about:debugging → Find extension → Click Reload
Remove:  about:debugging → Find extension → Click Remove
Console: F12 → Console tab
```

### DevTools (Browser Developer Tools)

**How to open:**
- Press **F12** key, OR
- Right-click page → "Inspect", OR
- Chrome: Menu → More Tools → Developer Tools
- Firefox: Menu → More Tools → Web Developer Tools

**Useful tabs:**
- **Console:** See JavaScript logs and errors
- **Network:** See API calls and HTTP requests
- **Application/Storage:** See extension storage, cookies
- **Elements/Inspector:** See page HTML/CSS

**Console commands:**
```javascript
// Clear console
clear()

// See extension storage (Chrome)
chrome.storage.local.get(null, console.log)

// Inject test element
document.body.innerHTML += '<p style="background:red">TEST</p>'
```

### Common Commands

**Git:**
```bash
git status                    # Check current branch and changes
git log --oneline -5          # See recent commits
git checkout {branch}         # Switch branches
```

**{Service Name}:**
```bash
{service}_on                  # Enable service
{service}_off                 # Disable service
{service}_status              # Check status
{service}_logs                # View recent logs
```

**Logs/Database:**
```bash
{log_viewer_command}          # View application logs
{db_query_command}            # Query database
```

### File Locations

**Key files:**
- Extension code: `{absolute-path-to-extension}`
- Test data: `{absolute-path-to-test-data}`
- Logs: `{absolute-path-to-logs}`
- Config: `{absolute-path-to-config}`

**Test harnesses:**
- XSS test page: `{absolute-path}/test-xss.html`
- Performance test: `{absolute-path}/test-perf.html`

---

## Notes for 3-Week (or Longer) Return

### Context to Remember
- **Last tested:** {YYYY-MM-DD}
- **Branch:** {branch-name}
- **Issue:** #{issue-number}
- **Status when paused:** {Brief status summary}

### Where You Left Off
1. {What was completed}
2. {What was in progress}
3. {What's next}
4. {Any blockers or decisions needed}

### Important Decisions Made
- {Decision 1}: {Why this approach was chosen}
- {Decision 2}: {Trade-offs considered}

### Tips for Resuming
1. Read this entire test script first
2. Verify all prerequisites still valid
3. Start with a simple test to verify environment
4. Don't assume anything works - verify each step
5. If confused, check session logs: `docs/session-logs/Week-starting-YYYY-MM-DD.md`

---

## Appendix: Browser Extension Testing Primer

{For users completely new to browser extension testing}

### What is a Browser Extension?
A browser extension is a small software program that adds features to your web browser. It runs while you browse and can:
- Read and modify web pages
- Add buttons to the browser toolbar
- Store data locally
- Make network requests

### Key Components
- **manifest.json** - Configuration file (like a recipe for the extension)
- **service-worker.js** - Background script (runs even when not using extension)
- **content scripts** - Scripts injected into web pages you visit
- **popup.html** - UI that appears when you click extension icon

### What Can Go Wrong?
Common issues and how to spot them:
1. **Extension not loading**
   - Symptom: Not in chrome://extensions/ list
   - Check: Manifest.json has errors (look for red error text)

2. **Extension loads but doesn't work**
   - Symptom: Extension appears but clicking does nothing
   - Check: Console for JavaScript errors (F12 → Console → red text)

3. **Works in one browser, not another**
   - Symptom: Chrome works, Firefox doesn't (or vice versa)
   - Cause: Browser-specific APIs or manifest differences

4. **Intermittent failures**
   - Symptom: Sometimes works, sometimes doesn't
   - Check: Race conditions, timing issues, network problems

### How to Debug
1. **Open DevTools** (F12 key)
2. **Check Console tab** for error messages (red text)
3. **Check Network tab** to see if API calls are made
4. **Reload extension** (chrome://extensions/ → reload icon)
5. **Close all tabs** and open fresh tab to test site
6. **Check extension storage** (Application/Storage tab in DevTools)

### Security Concepts

**XSS (Cross-Site Scripting):**
- Attacker injects malicious JavaScript into your extension
- Prevention: Use `textContent` instead of `innerHTML`
- Test: Try to inject `<script>alert('xss')</script>` - should appear as text, not execute

**Shadow DOM:**
- Isolated container for extension UI
- Prevents website CSS from breaking your extension
- Test: Extension UI should look same on all websites

**Content Security Policy (CSP):**
- Rules about what JavaScript can run
- Prevents certain types of attacks
- If violated: Console shows CSP errors

---

**End of Template**
```

---

## Template Usage Instructions

### For LLMs Creating Test Scripts:

1. **Replace ALL placeholders** in curly braces `{like-this}` with actual values
2. **Use absolute paths** everywhere - never relative paths
3. **Write for a non-technical user** - explain F12, DevTools, console, etc.
4. **Include expected outputs** after every command
5. **Add workarounds** for common blockers
6. **Use emoji consistently:**
   - ✅ Test passed
   - ❌ Test failed
   - ⏸️ Test not run yet
   - ⚠️ Test blocked
   - 🔴 Critical priority
   - 🟡 Important priority
   - 🟢 Nice-to-have priority
   - 📡 Network/API activity
   - 🗄️ Database activity
   - ⏱️ Timing-related
   - 🟠/🟢/🔴 Badge colors
7. **Browser-agnostic** - provide Chrome AND Firefox instructions
8. **Quick Reference** section is mandatory
9. **Cost controls** must be explicit and repeated
10. **"If test fails" section** required for each test

### Critical Sections:
- **Pre-Test Setup** - Must verify environment completely
- **Verification** - Must show how to check backend/system state
- **Pass Criteria** - Must be checkboxes, concrete, measurable
- **If Test Fails** - Must include troubleshooting table
- **Quick Reference** - Must have all common commands/paths
- **Notes for 3-Week Return** - Must help user resume after long break

### Quality Checklist:
- [ ] All placeholders replaced with actual values
- [ ] All paths are absolute (no `./` or `../`)
- [ ] Every command has expected output shown
- [ ] DevTools usage explained (not assumed)
- [ ] Browser-specific instructions for Chrome AND Firefox
- [ ] Cost controls mentioned in at least 3 places
- [ ] Quick Reference section complete
- [ ] "If test fails" troubleshooting included
- [ ] Workarounds documented where applicable
- [ ] Appendix included if user is new to browser extension testing
