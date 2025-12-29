# Issue #77 - Complete Test Script
**Feature:** User Feedback for Context Menu Actions
**Branch:** 77-action-feedback
**Test Reference:** docs/1077-action-feedback.md §6.1

---

## Pre-Test Setup

### 1. Environment Preparation
```bash
# Navigate to worktree
cd C:\Users\mcwiz\Projects\Aletheia-77

# Verify on correct branch
git status
# Should show: On branch 77-action-feedback

# Check for uncommitted changes
git status
# Should be clean (no changes)

# Verify AWS Lambda is OFF (prevent denial of wallet)
aws_status
# Expected: reservedConcurrentExecutions: 0
```

### 2. Extension Installation (Chrome)
1. Open Chrome (or Chrome Canary)
2. Go to `chrome://extensions/`
3. Enable "Developer mode" (top right)
4. Click "Load unpacked"
5. Select folder: `C:\Users\mcwiz\Projects\Aletheia-77\extension`
6. Pin Aletheia to toolbar (puzzle icon → pin)

### 3. Initial State Verification
- **Allowlist should be EMPTY** (no sites enabled)
- **Badge should be clear** (no text/color)
- To verify: Click toolbar icon → popup shows "Enable Aletheia for this site" (OFF state)

### 4. AWS Lambda Control
- **Default:** Lambda should be OFF (concurrency=0) to prevent costs
- **During testing:** Turn ON only when needed for success tests
  ```bash
  aws_on   # Enable Lambda
  aws_off  # Disable Lambda (do this after testing!)
  ```

---

## Test Execution

### ✅ Test 010: Blocked State (NOT Allowlisted)
**Status:** ✓ PASSED (as of 2025-12-24)

**Setup:**
- Visit wsj.com (or any non-allowlisted site)
- Verify site NOT in allowlist (popup shows OFF)

**Action:**
1. Select any word on the page
2. Right-click → "Explain with AI"

**Expected:**
- ⚠️ **Overlay appears** near selection with warning message: "Enable Aletheia for this site first"
- 🟠 **Badge shows:** `!` with amber background (#FBBF24)
- ⏱️ **Overlay disappears** after 5 seconds
- 🚫 **Badge persists** (does NOT auto-clear)
- 📡 **No API call** (check: Lambda logs should be empty)

**Verification:**
```bash
# Check Lambda invocations (should be 0)
aws logs tail /aws/lambda/AletheiaAgent --since 5m
```

---

### ✅ Test 020: Clear Blocked Badge
**Status:** ✓ PASSED (as of 2025-12-24)

**Setup:**
- Complete Test 010 (badge shows amber `!`)

**Action:**
1. Click toolbar icon (Aletheia popup)

**Expected:**
- ✓ **Badge clears** immediately (no text, no color)
- ✓ **Popup opens normally**

**Why:** popup.js clears badge on DOMContentLoaded (service-worker.js line 169)

---

### ✅ Test 030: Success State
**Status:** ✓ PASSED (as of 2025-12-24)
**Known Issue:** ~~Double checkmark~~ FIXED in commit 5c41dd8

**Setup:**
- Visit wsj.com
- Click toolbar → enable Aletheia (toggle to ON)
- **CRITICAL:** Turn Lambda ON: `aws_on`

**Action:**
1. Select a simple word (e.g., "economy")
2. Right-click → "Explain with AI"

**Expected:**
- ✓ **Overlay appears** near selection: "Saved: economy"
- 🟢 **Badge shows:** `✓` with green background (#22C55E)
- ⏱️ **Both clear** after 3 seconds
- 📡 **API call succeeds** (200 status)

**Verification:**
```bash
# Check DynamoDB for new entry
poetry run python tools/log_viewer.py --tail 1
# Should show the selected word with timestamp

# Turn Lambda back OFF to prevent costs
aws_off
```

---

### ✅ Test 040: Error State
**Status:** ✓ PASSED (as of 2025-12-28)
**Fix:** Added response.ok check to catch HTTP failures (commit 03444b1)

**Setup:**
- Visit wsj.com (allowlisted)
- **CRITICAL:** Turn Lambda OFF: `aws_off`

**Action:**
1. Select a word
2. Right-click → "Explain with AI"

**Expected:**
- ✗ **Overlay appears** near selection: "Not saved. Try again later."
- 🔴 **Badge shows:** `✗` with red background (#EF4444)
- ⏱️ **Both clear** after 3 seconds

**Failure Modes to Test:**
1. **Network offline:** DevTools → Network → Offline
2. **Lambda concurrency=0:** Default state (aws_off)
3. **Invalid API key:** (requires manually breaking config)

**Verification:**
```bash
# Check for error in console (F12 → Console)
# Should see: [CV-6] Error: ...
```

---

### ✅ Test 050: Overlay Position (Top of Page)
**Status:** ✓ PASSED (as of 2025-12-28)

**Expected:** Overlay appears below selection when text is at top of page.
**Actual:** Overlay consistently appears below selection (as expected).
**Note:** Basic positioning works. Viewport-aware positioning (Test 060) moved to Issue #98.

---

### ⚠️ Test 060: Overlay Position (Bottom of Viewport)
**Status:** MOVED TO ISSUE #98

**Reason:** Viewport-aware positioning requires fixing overlay.js execution (root cause: overlay.js never runs).
**Expected (when fixed):** Overlay should appear ABOVE selection when at bottom of viewport.
**Current Behavior:** Always appears below (clips at bottom edge).
**Fix Branch:** 98-fix-positioning
**Note:** This test removed from Issue #77 scope. Feature shipped without viewport detection.

---

### ✅ Test 070: Shadow DOM Isolation
**Status:** ✓ PASSED (as of 2025-12-28)

**Setup:**
- Tested on:
  - ✅ economist.com
  - ✅ unherd.com
  - ✅ wsj.com

**Action:**
1. Enable Aletheia on each site
2. Trigger overlay (select word → "Explain with AI")
3. **Visual inspection:** Compare overlay appearance across sites

**Expected:**
- ✓ **Consistent styling** on all sites
- ✓ Dark background (#1F2937), light text (#F9FAFB)
- ✓ Border color matches type (green/amber/red)
- ✓ No style bleed from host page
- ✓ Overlay always readable (no font/color conflicts)

**Why This Matters:** Shadow DOM isolation (`mode: 'closed'`) prevents host page CSS from affecting overlay.

---

### ✅ Test 080: XSS Prevention
**Status:** ✓ PASSED (as of 2025-12-28)

**Test Method:**
- Tested on wsj.com using DevTools console to inject XSS payload
- Selected `<script>alert('xss')</script>` text and triggered "Explain with AI"

**Results:**
- ✅ **Overlay displayed text literally** (no alert popup)
- ✅ **No script execution**
- ✅ **DynamoDB entry #88 shows:** `<script>alert("xss")</script>` as literal text
- ✅ **End-to-end XSS prevention confirmed**

**Additional Payloads to Test:**
- `<img src=x onerror=alert(1)>`
- `<svg onload=alert('XSS')>`
- `<a href="javascript:alert('xss')">click</a>`
- `<div onmouseover="alert('xss')">hover</div>`

**Why This Matters:** Using `textContent` (not `innerHTML`) prevents XSS attacks (service-worker.js line 129).

**Test File:** `test-xss.html` has all payloads ready.

---

### ✅ Test 090: Rapid Clicks (Race Condition)
**Status:** ✓ PASSED (as of 2025-12-28)

**Setup:**
- Visit wsj.com (allowlisted)
- Lambda ON: `aws_on`

**Action:**
1. Select a word
2. **Rapidly click** "Explain with AI" 5 times in quick succession (< 1 second)

**Expected:**
- ✓ **Badge state coherent** (no stuck badges)
- ✓ **Multiple overlays appear** (one per click)
- ✓ **All overlays auto-dismiss** after timeout
- ✓ **Badge clears** after last overlay (not stuck green)

**Failure Modes:**
- Badge stuck on green/red/amber
- Overlays don't dismiss
- Console errors about duplicate executions

**Cleanup:**
```bash
aws_off  # Turn Lambda back OFF
```

---

## Post-Test Checklist

### 1. Lambda Cost Control
```bash
# CRITICAL: Ensure Lambda is OFF
aws_off
aws_status  # Verify: reservedConcurrentExecutions: 0
```

### 2. Test Results Summary
Update this file with results:
- ✅ PASSED - Test succeeded
- ❌ FAILED - Test failed (document failure)
- ⏸️ READY - Not yet tested
- ⚠️ BLOCKED - Cannot test due to dependency

### 3. Known Issues
- **Issue #98:** Overlay positioning broken (always below)
  - Fix in branch: 98-fix-positioning
  - Root cause: overlay.js never executes (showOverlay in service-worker.js line 30)
  - Tests 050 and 060 blocked until fixed

- **Issue #96:** Error state test requires Lambda OFF
  - Fixed in commit 03444b1
  - Needs human verification (Test 040)

- **Issue #93:** Double checkmark
  - ✅ FIXED in commit 5c41dd8
  - Verified in Test 030

### 4. If Tests Fail
1. **Document the failure** in this file
2. **Open a GitHub issue** (or update existing)
3. **Note the commit hash** where failure occurred
4. **Save screenshots** if visual issue
5. **Check browser console** for errors (F12)
6. **Check Lambda logs:**
   ```bash
   aws logs tail /aws/lambda/AletheiaAgent --since 30m --follow
   ```

---

## Branch Management

### Current State
- **Branch:** 77-action-feedback
- **Worktree:** C:\Users\mcwiz\Projects\Aletheia-77
- **Status:** Testing in progress
- **Blockers:** Issue #98 (positioning)

### When Testing Complete
1. **Do NOT merge** - leave for Orchestrator
2. **Update this file** with final results
3. **Commit test results:**
   ```bash
   git add TEST-SCRIPT-77.md
   git commit -m "test: complete manual smoke testing for Issue #77"
   ```
4. **Push to remote:**
   ```bash
   git push -u origin 77-action-feedback
   ```
5. **Create PR:**
   ```bash
   gh pr create --title "Feature: User feedback for context menu actions (#77)" \
                --body "$(cat TEST-SCRIPT-77.md)"
   ```

---

## Quick Reference

### Browser Extension Reload
**Chrome:**
1. `chrome://extensions/`
2. Click reload icon (circular arrow)
3. Close all test tabs
4. Open fresh tab

**Firefox:**
1. `about:debugging#/runtime/this-firefox`
2. Click "Reload"
3. Close all test tabs
4. Open fresh tab

### AWS Commands
```bash
aws_on      # Enable Lambda (unrestricted)
aws_off     # Disable Lambda (concurrency=0)
aws_status  # Check current state
```

### Log Viewer
```bash
# DynamoDB entries
poetry run python tools/log_viewer.py --tail 10

# Lambda logs
aws logs tail /aws/lambda/AletheiaAgent --since 30m --follow
```

### File Locations
- Extension: `C:\Users\mcwiz\Projects\Aletheia-77\extension`
- Service Worker: `extension/service-worker.js`
- Overlay (unused): `extension/overlay.js` ⚠️ NOT EXECUTED
- Manifest: `extension/manifest.json`
- Test Harness: `C:\Users\mcwiz\Projects\Aletheia-77\test-xss.html`
- LLD: `docs/1077-action-feedback.md`

---

## Notes for 3-Week Return

### Context to Remember
- **Last session:** 2025-12-28 (named "fixing_77_at_overlay")
- **Discovered:** overlay.js is dead code (showOverlay in service-worker.js is what runs)
- **Created:** Branch 98-fix-positioning for positioning fix
- **Tests passed:** 010, 020, 030 (blocked, clear badge, success)
- **Tests ready:** 040, 070, 080, 090 (error, isolation, XSS, race condition)
- **Tests blocked:** 050, 060 (positioning - Issue #98)

### Where You Left Off
1. Fixed double checkmark (Issue #93 ✅)
2. Fixed HTTP status check (Issue #96 - ready for test)
3. Discovered overlay positioning root cause (Issue #98)
4. Created test harness for XSS (test-xss.html)
5. Ready to finish smoke testing and close Issue #77

### Next Steps
1. Run tests 040, 070, 080, 090 (this script)
2. Document results in this file
3. Close Issue #77 (if all tests pass)
4. Move to Issue #80 (your main priority)
5. Issue #98 fix is on separate branch (for later)

---

**Good luck! 🚀**
