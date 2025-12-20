# 1043 - Feature: Privacy Policy & Store Compliance

## 1. Context & Goal
* **Issue:** #43
* **Objective:** Publish Privacy Policy to satisfy Chrome Web Store requirements.
* **Status:** Complete

## 2. Requirements
1. **Policy Page:** Host a static page (GitHub Pages or similar).
2. **Content:** Explicit statement that:
   - Data is stored locally (unless sync is enabled)
   - We do not sell browsing history
   - We do not collect PII

## 3. Technical Approach
* **Module:** `gh-pages` branch or external hosting
* **Dependencies:** GitHub Pages
* **Performance Budget:** N/A (static page)

## 4. Implementation Details
- Create `index.html` with privacy policy content
- Deploy to GitHub Pages
- Link from Chrome Web Store listing

## 5. Verification & Testing

### 5.1 Test Commands
```bash
# Verify GitHub Pages is accessible
curl -I https://martymcenroe.github.io/Aletheia/

# Check for required content
curl -s https://martymcenroe.github.io/Aletheia/ | grep -i "privacy"
```

### 5.2 Test Scenarios
| Scenario | Input | Expected Output | Pass Criteria |
|:---------|:------|:----------------|:--------------|
| Page accessible | HTTP GET | 200 OK | curl returns 200 |
| Privacy content | Page HTML | Contains policy text | grep finds "privacy" |
| No PII collection stated | Page HTML | Explicit statement | Text confirms no PII |
| Store link works | Chrome Web Store | Clickable link | Opens policy page |

### 5.3 Manual Smoke Test
1. Visit https://martymcenroe.github.io/Aletheia/
2. Verify page loads without errors
3. Confirm privacy policy text is present and readable
4. Check that required disclosures are included

## 6. Definition of Done
- [x] Privacy policy page created
- [x] Deployed to GitHub Pages
- [x] URL accessible publicly
- [x] Required disclosures included
- [x] PR merged to main
