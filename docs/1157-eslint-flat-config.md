# 1157 - Chore: Migrate ESLint to Flat Config Format

## 1. Context & Goal
* **Issue:** #157
* **Objective:** Migrate ESLint configuration from legacy `.eslintrc.json` to flat config `eslint.config.js` for ESLint v9+ compatibility.
* **Status:** Draft
* **Related Issues:** Audit 0816 (Dependabot PR Audit - CI Consistency Check)

### CRITICAL: Current State (2026-01-05)

**Technical Debt Added by PR #163:**

During repo reorganization (#102), CI failed because ESLint v9 requires flat config. Instead of:
- A) Downgrading ESLint to v8 in package.json, OR
- B) Properly migrating to flat config

A band-aid was applied:
```yaml
# .github/workflows/ci.yml
- name: Lint Chrome extension
  run: npx eslint extensions/chrome/ --ext .js
  env:
    ESLINT_USE_FLAT_CONFIG: false  # <-- BAND-AID - REMOVE WHEN THIS LLD IS IMPLEMENTED
```

**This is technical debt, not a solution.** This LLD must be implemented to remove the band-aid.

**Current Versions:**
- `package.json`: ESLint `^9.39.2` (v9)
- Config: `.eslintrc.json` (legacy format)
- CI: `ESLINT_USE_FLAT_CONFIG=false` (band-aid)

### Open Questions
*Questions that need clarification before or during implementation. Remove when resolved.*

- [ ] Are we upgrading ESLint to v9 as part of this, or just preparing the config format?
- [ ] Do we need to maintain backwards compatibility with ESLint v8 during transition?
- [ ] Any custom rules or plugins that may not support flat config yet?
- [ ] Should we also migrate to ESM (`eslint.config.mjs`) or stay with CommonJS?
- [x] ~~Does `globals` package have `webextensions` key?~~ **Verify - may need manual definitions**

### Resolved Questions (Gemini Review 2026-01-05)

1. **Q: Does `globals.webextensions` exist in the globals package?**
   **A: Verify before using.** The `globals` npm package may not export `webextensions`. If not available, manually define:
   ```javascript
   globals: {
     ...globals.browser,
     chrome: "readonly",
     browser: "readonly"  // Firefox API
   }
   ```

## 2. Requirements

1. Create `eslint.config.js` with equivalent rules to current `.eslintrc.json`
2. Test on both Chrome and Firefox extension code
3. Update CI workflow if env vars change
4. Remove legacy `.eslintrc.json` after verification
5. Document any rule changes or plugin updates needed

## 3. Alternatives Considered

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| Migrate to flat config now | Future-proof | Effort, possible plugin issues | **Selected** |
| Keep legacy config | No work | Will break on ESLint v9 | Rejected |
| Use eslintrc compatibility mode | Quick fix | Technical debt | Rejected |

**Rationale:** ESLint v9+ requires flat config; better to migrate proactively.

## 4. Data & Fixtures

N/A - Configuration change only.

## 5. Diagram

N/A

## 6. Technical Approach

* **Module:** `.eslintrc.json` → `eslint.config.js`
* **Dependencies:** eslint, @eslint/js, possibly @eslint/eslintrc for migration
* **Pattern:** ESLint flat config array

### Current Config (Legacy)

```json
// .eslintrc.json (current)
{
  "env": {
    "browser": true,
    "es2021": true,
    "webextensions": true
  },
  "extends": "eslint:recommended",
  "parserOptions": {
    "ecmaVersion": "latest",
    "sourceType": "module"
  },
  "rules": {
    // ... existing rules
  }
}
```

### Target Config (Flat)

```javascript
// eslint.config.js (target)
import js from "@eslint/js";
import globals from "globals";

// Check if webextensions exists, fallback to manual definitions
const webExtensionGlobals = globals.webextensions || {
  chrome: "readonly",
  browser: "readonly"
};

export default [
  js.configs.recommended,
  {
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: {
        ...globals.browser,
        ...webExtensionGlobals,
        chrome: "readonly",   // Explicit - Chrome extension API
        browser: "readonly"   // Explicit - Firefox extension API
      }
    },
    rules: {
      // ... migrated rules
    }
  },
  {
    files: ["extensions/chrome/**/*.js"],
    // Chrome-specific overrides
  },
  {
    files: ["extensions/firefox/**/*.js"],
    // Firefox-specific overrides
  }
];
```

**Note:** The explicit `chrome: "readonly"` and `browser: "readonly"` ensure WebExtension APIs are available regardless of whether `globals.webextensions` exists.

## 7. Interface Specification

N/A - Configuration file, no code interfaces.

## 8. Security Considerations

| Concern | Mitigation | Status |
|---------|------------|--------|
| Security rules disabled accidentally | Verify all rules preserved | TODO |

**Fail Mode:** N/A

## 9. Performance Considerations

| Metric | Budget | Approach |
|--------|--------|----------|
| Lint time | Same or faster | Flat config may be slightly faster |

**Bottlenecks:** None expected.

## 10. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Plugin incompatibility | Med | Low | Check plugin docs |
| Rule behavior changes | Med | Low | Compare lint outputs |
| CI breaks | High | Med | Test in branch first |

## 11. Verification & Testing

### 11.1 Test Scenarios

| ID | Scenario | Type | Input | Expected Output | Pass Criteria |
|----|----------|------|-------|-----------------|---------------|
| 010 | Lint Chrome extension | Auto | `npx eslint extensions/chrome/` | Same warnings/errors | Output matches |
| 020 | Lint Firefox extension | Auto | `npx eslint extensions/firefox/` | Same warnings/errors | Output matches |
| 030 | CI workflow passes | Auto | Push to branch | Green CI | Lint step passes |

### 11.2 Test Commands

```bash
# Compare outputs before/after migration
# Before (with .eslintrc.json)
ESLINT_USE_FLAT_CONFIG=false npx eslint extensions/chrome/ > eslint-before.txt

# After (with eslint.config.js)
npx eslint extensions/chrome/ > eslint-after.txt

diff eslint-before.txt eslint-after.txt
```

## 12. Definition of Done

### Code
- [ ] `eslint.config.js` created with equivalent rules
- [ ] Both extension directories lint successfully
- [ ] `.eslintrc.json` removed

### CI Cleanup (CRITICAL)
- [ ] Remove `ESLINT_USE_FLAT_CONFIG: false` from `.github/workflows/ci.yml`
- [ ] Verify CI passes without the band-aid environment variable

### Tests
- [ ] CI lint step passes
- [ ] No new lint errors introduced

### Documentation
- [ ] Update any ESLint instructions in README or contributing docs

---

## Appendix A: Original Gemini Review (2026-01-05)

**Review Date:** 2026-01-05
**Reviewer:** Gemini 3 Pro
**Scope:** Original LLD content (sections 2-11)

### Tier 2 Issues (HIGH) - Addressed

| Issue | Resolution |
|-------|------------|
| WebExtension globals verification | Added fallback pattern with explicit `chrome`/`browser` definitions |

**Verdict:** APPROVED for original scope.

---

## Appendix B: Band-Aid Documentation (2026-01-05)

**Added by:** Claude Opus 4.5
**Status:** [Pending Gemini Review]

Section 1 was updated to document technical debt from PR #163. This addition requires separate review before implementation proceeds.

**Rule for future LLDs:** Never pre-fill the "Reviewer" field. Leave as `[Pending Gemini Review]` until explicit review is provided.
