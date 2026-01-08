# 1193 - Fix: Firefox Manifest Data Collection Permissions

## 1. Context & Goal
* **Issue:** #193
* **Objective:** Add required `data_collection_permissions` and `gecko_android` settings to pass Mozilla Linter
* **Status:** Complete
* **Related Issues:** #51 (Store Compliance)

### Open Questions
*All questions resolved via Gemini consultation 2026-01-08.*

## 2. Requirements

1. Add `data_collection_permissions` block under `gecko` with:
   - `websiteContent` (required) - we read user's text selection
   - `personallyIdentifyingInfo` (required) - LinkedIn OAuth returns user name
2. Add `gecko_android` sibling block with `strict_min_version: "120.0"`
3. Update `gecko.strict_min_version` from `"57.0"` to `"109.0"` (modern baseline)
4. Mozilla Linter produces 0 errors and 0 warnings about version/permissions

## 3. Alternatives Considered

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| Add only required permissions | Minimal disclosure | N/A | **Selected** |
| Mark permissions as optional | Less scary UI | Inaccurate - we require both | Rejected |

**Rationale:** Both permissions are genuinely required for core functionality.

## 4. Data & Fixtures

N/A - Configuration change only, no data pipeline.

## 5. Diagram

N/A - Single file modification.

## 6. Technical Approach

* **File:** `extensions/firefox/manifest.json`
* **Dependencies:** None
* **Pattern:** JSON schema compliance

### Target Structure

```json
{
  "manifest_version": 2,
  "name": "Aletheia",
  "version": "1.0",
  "description": "AI-Powered Context Analysis",
  "permissions": ["activeTab", "tabs", "contextMenus", "storage"],
  "background": {
    "scripts": ["service-worker.js"]
  },
  "browser_specific_settings": {
    "gecko": {
      "id": "extension@aletheia.study",
      "strict_min_version": "109.0",
      "data_collection_permissions": {
        "required": ["websiteContent", "personallyIdentifyingInfo"],
        "optional": []
      }
    },
    "gecko_android": {
      "strict_min_version": "120.0"
    }
  },
  "icons": { ... },
  "browser_action": { ... }
}
```

## 7. Interface Specification

N/A - No code interfaces, JSON config only.

## 8. Security Considerations

| Concern | Mitigation | Status |
|---------|------------|--------|
| Over-requesting permissions | Only declare what we actually use | Addressed |
| Privacy disclosure | Mozilla shows standard explanations to users | Addressed |

**Fail Mode:** Fail Closed - Extension won't install if manifest is invalid.

## 9. Performance Considerations

N/A - No runtime impact.

## 10. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Schema changes in future Firefox | Low | Low | Monitor Mozilla docs |

## 11. Verification & Testing

### 11.1 Test Scenarios

| ID | Scenario | Type | Input | Expected Output | Pass Criteria |
|----|----------|------|-------|-----------------|---------------|
| 010 | Linter passes | Manual | `web-ext lint` | 0 errors, 0 warnings | Exit code 0 |
| 020 | Extension loads in Firefox | Manual | Install .xpi | Popup opens | No console errors |
| 030 | Build script succeeds | Auto | `build_release.py` | .zip created | Script exits 0 |

### 11.2 Test Commands

```bash
# Lint the Firefox extension
cd extensions/firefox && npx web-ext lint

# Build release artifacts
poetry run python tools/build_release.py
```

### 11.3 Manual Tests

| ID | Scenario | Why Not Automated | Steps |
|----|----------|-------------------|-------|
| 010 | Linter passes | Requires web-ext CLI in path | Run `web-ext lint`, verify 0 errors |
| 020 | Extension loads | Requires Firefox browser | Load temp extension, click icon |

## 12. Definition of Done

### Code
- [ ] `extensions/firefox/manifest.json` updated
- [ ] JSON validates (no syntax errors)

### Tests
- [ ] `web-ext lint` passes
- [ ] Extension loads in Firefox Developer Edition
- [ ] `build_release.py` succeeds

### Documentation
- [ ] LLD committed
- [ ] Implementation Report completed

### Review
- [ ] Code review completed
- [ ] Resubmit to Mozilla Add-ons
