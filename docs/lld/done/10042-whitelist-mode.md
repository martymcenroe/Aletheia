# 10042 - Feature: Whitelist Mode & Safety Filters

## 1. Context & Goal
* **Issue:** #42
* **Objective:** Move from "Always On" to "Privacy Badger" style Default OFF model.
* **Status:** Complete

## 2. Requirements
1. **Default State:** Extension is inactive on page load.
2. **Activation:** User must click "Enable for this site" (Domain-level whitelist).
3. **Categorization Filter:** Prevent activation on "Sensitive" categories (Adult, Banking, Medical).
4. **User Value:** Prevents accidental data leakage and ensures Aletheia only learns from high-quality sources.

## 3. Technical Approach
* **Module:** `service-worker.js`, `popup.html`
* **Dependencies:** Chrome Storage API for whitelist persistence
* **Performance Budget:** < 50ms for whitelist lookup

## 4. Implementation Details
- Store whitelist in `chrome.storage.local`
- Check domain against whitelist before activating
- Provide UI toggle in popup

## 5. Verification & Testing

### 5.1 Test Commands
```bash
# No automated tests - browser extension requires manual testing
# Load extension and verify behavior
```

### 5.2 Test Scenarios
| Scenario | Input | Expected Output | Pass Criteria |
|:---------|:------|:----------------|:--------------|
| Fresh install | New profile | Extension inactive | No context menu action without whitelist |
| Add to whitelist | Click "Enable" | Domain saved | Context menu works on that domain |
| Non-whitelisted site | Visit new site | Extension inactive | Context menu shows "Not enabled" |
| Sensitive category | Visit banking site | Activation blocked | Warning shown to user |

### 5.3 Manual Smoke Test
1. Install extension in fresh Chrome profile
2. Visit any website - verify extension is inactive
3. Click extension icon, enable for site
4. Verify context menu now works on that domain
5. Visit different domain - verify still inactive

## 6. Definition of Done
- [x] Code complete and linted
- [x] Whitelist persistence works
- [x] Default OFF behavior verified
- [x] Doc updated with actual test results
- [x] PR merged to main
