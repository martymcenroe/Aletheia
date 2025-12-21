# 1051 - Feature: Chrome Web Store Compliance

## 1. Context & Goal
* **Issue:** #51
* **Objective:** Define the submission artifacts, privacy justifications, and technical configurations required for a successful Chrome Web Store listing.
* **Status:** In Progress

## 2. Requirements
* **Store Listing:** Title, Short Description (132 chars), Long Description, Category (Productivity).
* **Privacy Policy:** Publicly accessible URL.
* **Assets:** Icon (128px), Screenshots (1280x800), Promo Tile (440x280).
* **Compliance:** Strict adherence to "Single Purpose" policy via `activeTab`.

## 3. Technical Approach
* **Module:** `extension/manifest.json`
* **Dependencies:** Chrome Web Store Developer Dashboard.
* **Performance Budget:** N/A (Static Asset).

## 4. Implementation Details

### 4.1 Store Listing Text
* **Name:** Aletheia
* **Short Description:** A bespoke AI assistant that analyzes selected text within its full page context for deeper insight and verification.
* **Category:** Productivity / Workflow
* **Language:** English

### 4.2 Privacy Justification (Dashboard Copy-Paste)
* **Privacy Policy URL:** `https://martymcenroe.github.io/Aletheia/`
* **Permission Justification:**
    * **`activeTab`:** Extension only accesses the current page when the user explicitly interacts (Right-click).
    * **`scripting`:** Required to execute `document.body.innerText` strictly on the active tab during the "Explain with AI" action.
    * **`contextMenus`:** Primary trigger interface.
* **Data Usage:**
    * Handles user data? **Yes** (Page content).
    * Sold to 3rd parties? **No**.
    * Used for unrelated purposes? **No**.

### 4.3 Graphic Assets
* **Icon:** `dist/icon-128.png` (128x128)
* **Screenshot:** `dist/screenshot-1280x800.png` (1280x800)
* **Promo:** `dist/small-promo-440x280.png` (440x280)

## 5. Verification & Testing
*Ref: [0005-testing-strategy-and-protocols.md](../0005-testing-strategy-and-protocols.md)*

### 5.1 Test Modules
* **Module A (Unit):** Verify `manifest.json` does not contain `<all_urls>`.

### 5.2 Test Scenarios
| Scenario | Input | Expected Output | Pass Criteria |
|:---------|:------|:----------------|:--------------|
| **Manifest Audit** | `cat extension/manifest.json` | `"host_permissions": []` | No broad permissions found. |
| **Asset Dimensions** | `file dist/screenshot-1280x800.png` | `1280x800` | Output matches requirements. |

### 5.3 Manual Smoke Test
1. Build the zip: `python tools/generate_store_assets.py`
2. Attempt upload to Chrome Developer Dashboard.
3. Verify no "Manifest Error" alerts appear.

## 6. Definition of Done
- [ ] Document adheres to `1000-TEMPLATE-feature.md`
- [ ] Manifest verified as compliant
- [ ] Assets generated and verified
- [ ] Store Listing text finalized
