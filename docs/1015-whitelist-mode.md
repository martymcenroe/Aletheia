# 1042 - Feature: Whitelist Mode & Safety Filters

## Context
Linked to Issue #42.
Current behavior is "Always On." This is intrusive and risky.
We are moving to a "Privacy Badger" style model: Default OFF.

## Requirements
1.  **Default State:** Extension is inactive on page load.
2.  **Activation:** User must click "Enable for this site" (Domain-level whitelist).
3.  **Categorization Filter:**
    * Prevent activation on "Sensitive" categories (Adult, Banking, Medical).
    * Strategy: Research lightweight local blocking lists or API calls.
4.  **User Value:** Prevents accidental data leakage and ensures Aletheia only learns from high-quality sources.
