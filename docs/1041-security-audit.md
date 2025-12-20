# 1041 - Feature: Permission Culling & Security Hardening

## 1. Context & Goal
* **Issue:** #41
* **Objective:** Adhere to the "Principle of Least Privilege" to pass Chrome Web Store review.
* **Status:** Complete

## 2. Requirements
1. **Manifest Audit:** Remove `<all_urls>` and `activeTab` if not strictly required.
2. **Justification:** Write clear justification strings for any permission retained.
3. **Goal:** Eliminate any permission that triggers an automatic "Manual Review" flag.

## 3. Technical Approach
* **Module:** `manifest.json`
* **Dependencies:** None
* **Performance Budget:** N/A

## 4. Implementation Details
Review each permission in manifest.json and document justification or remove.

## 5. Verification & Testing

### 5.1 Test Commands
```bash
# Validate manifest syntax
cat manifest.json | jq .

# Check for problematic permissions
grep -E "(all_urls|tabs|webRequest)" manifest.json && echo "WARNING: Review required" || echo "OK: No broad permissions"
```

### 5.2 Test Scenarios
| Scenario | Input | Expected Output | Pass Criteria |
|:---------|:------|:----------------|:--------------|
| No `<all_urls>` | manifest.json | No match | grep returns empty |
| activeTab only | manifest.json | `activeTab` present | Extension works on click |
| Load extension | Chrome | No errors | Extension loads without permission warnings |

### 5.3 Manual Smoke Test
1. Load unpacked extension in Chrome
2. Check chrome://extensions for permission warnings
3. Verify context menu appears on right-click
4. Confirm no "broad host access" warning

## 6. Definition of Done
- [x] Code complete and linted
- [x] Manifest reviewed and permissions minimized
- [x] Extension loads without warnings
- [x] Doc updated with actual test results
- [x] PR merged to main
