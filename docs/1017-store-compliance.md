# 1017 - Chrome Web Store Compliance Spec

## 1. Store Listing
* **Name:** Aletheia
* **Short Description (Max 132 chars):**
  A bespoke AI assistant that analyzes selected text within its full page context for deeper insight and verification.
* **Category:** Productivity / Workflow
* **Language:** English

## 2. Privacy & Permissions (The "Single Purpose")
* **Privacy Policy URL:** `https://martymcenroe.github.io/Aletheia/`
* **Permission Justification:**
    * **`activeTab`:** We do not request broad host permissions. The extension only accesses the current page when the user explicitly interacts with the extension.
    * **`scripting`:** Required to execute the content extraction script (`document.body.innerText`) strictly on the active tab during the user-initiated "Explain with AI" action.
    * **`contextMenus`:** The primary interface for triggering the AI analysis.
* **Data Usage:**
    * Does this extension handle user data? **Yes** (Page content).
    * Is data sold to third parties? **No**.
    * Is data used for unrelated purposes? **No**.

## 3. Graphic Assets Checklist
* **Icon:** 128x128 pixels (PNG).
* **Screenshot:** 1280x800 pixels (JPEG/PNG) - *Must show the Context Menu in action.*
* **Promo Tile (Optional):** 440x280 pixels.

## 4. Technical Notes
* **Manifest Version:** 3
* **Host Permissions:** None (Strict `activeTab` usage).
