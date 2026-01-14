# 10194 - Refactor: Replace innerHTML with DOM Methods

## 1. Context & Goal
* **Issue:** #194
* **Objective:** Eliminate `innerHTML` usage to pass Firefox Linter and strengthen XSS protection
* **Status:** Complete
* **Related Issues:** #193 (Firefox submission), #51 (Store Compliance)

### Open Questions
*All questions resolved via Gemini consultation 2026-01-08.*

## 2. Requirements

1. Replace all 3 `innerHTML` assignments in `overlay.js` with DOM methods
2. Preserve existing XSS protection (`.textContent` for dynamic content)
3. Maintain identical visual structure (classes, nesting, attributes)
4. Firefox Linter shows 0 warnings for "Unsafe assignment to innerHTML"
5. All existing E2E tests pass

## 3. Alternatives Considered

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| DOM methods (`createElement`) | No innerHTML, linter-safe | More verbose | **Selected** |
| DOMParser | Cleaner than createElement | Still flagged by linter | Rejected |
| Template literals + sanitizer | Less code change | Adds dependency | Rejected |

**Rationale:** Pure DOM methods are the only approach that fully satisfies Mozilla's linter.

## 4. Data & Fixtures

N/A - Refactoring existing code, no new data.

## 5. Diagram

N/A - Internal refactor, no architectural change.

## 6. Technical Approach

* **Files:** `extensions/chrome/overlay.js`, `extensions/firefox/overlay.js`
* **Dependencies:** None (native DOM APIs)
* **Pattern:** Replace template literals with programmatic DOM construction

### innerHTML Sites to Refactor

| Line | Function | Content Type | Approach |
|------|----------|--------------|----------|
| 428 | `showLoadingOverlay()` | Static styles + spinner | `createElement` for style, div, span |
| 488 | `showResultOverlay()` | Static card structure | `createElement` for all elements |
| 650 | `showAletheiaOverlay()` | Legacy simple overlay | `createElement` for style + div |

### Refactoring Pattern

**Before (innerHTML):**
```javascript
shadow.innerHTML = `
    <style>${OVERLAY_STYLES}</style>
    <div class="aletheia-card">...</div>
`;
```

**After (DOM methods):**
```javascript
const style = document.createElement('style');
style.textContent = OVERLAY_STYLES;
shadow.appendChild(style);

const card = document.createElement('div');
card.className = 'aletheia-card';
// ... build structure
shadow.appendChild(card);
```

### Critical Preservation

The following `.textContent` assignments MUST remain unchanged (they are the XSS protection):

```javascript
// Line 505 - signal text
signalEl.textContent = signal;

// Line 509 - blocked message
blockedEl.textContent = blockedReason;

// Line 512 - gem text
gemEl.textContent = gem;
```

## 7. Interface Specification

### 7.1 Helper Function (Optional)

If code becomes too verbose, consider a helper:

```javascript
/**
 * Create element with attributes and optional text content.
 * @param {string} tag - Element tag name
 * @param {Object} attrs - Attributes to set
 * @param {string} [text] - Optional text content
 * @returns {HTMLElement}
 */
function el(tag, attrs = {}, text = null) {
    const elem = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs)) {
        if (key === 'className') {
            elem.className = value;
        } else {
            elem.setAttribute(key, value);
        }
    }
    if (text !== null) {
        elem.textContent = text;
    }
    return elem;
}
```

### 7.2 Refactored showLoadingOverlay (Pseudocode)

```javascript
function showLoadingOverlay() {
    removeOverlay();
    const pos = calculatePosition();
    if (!pos) return;

    const host = document.createElement('div');
    host.id = 'aletheia-overlay-host';
    const shadow = host.attachShadow({ mode: 'open' });

    // Style element
    const style = document.createElement('style');
    style.textContent = OVERLAY_STYLES;
    shadow.appendChild(style);

    // Card container
    const card = document.createElement('div');
    card.className = `aletheia-card ${pos.position}`;
    card.style.cssText = `top: ${pos.top}px; left: ${pos.left}px;`;
    card.setAttribute('role', 'status');
    card.setAttribute('aria-label', 'Aletheia loading');

    // Loading content
    const loading = document.createElement('div');
    loading.className = 'aletheia-loading';

    const spinner = document.createElement('div');
    spinner.className = 'aletheia-spinner';
    loading.appendChild(spinner);

    const text = document.createElement('span');
    text.textContent = 'Analyzing...';
    loading.appendChild(text);

    card.appendChild(loading);
    shadow.appendChild(card);
    document.body.appendChild(host);
}
```

## 8. Security Considerations

| Concern | Mitigation | Status |
|---------|------------|--------|
| XSS via AI response | `.textContent` preserved for dynamic content | Addressed |
| XSS via user selection | `.textContent` used, never innerHTML | Addressed |
| Style injection | Styles are static constants, not user input | Addressed |

**Fail Mode:** Fail Closed - If DOM construction fails, overlay won't render (no silent degradation).

## 9. Performance Considerations

| Metric | Budget | Approach |
|--------|--------|----------|
| Render time | < 50ms | DOM operations are fast, negligible change |
| Memory | No change | Same DOM structure, different construction |

**Bottlenecks:** None expected. DOM methods are native and well-optimized.

## 10. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Visual regression | Med | Low | E2E visual tests catch differences |
| Event handler breakage | Med | Low | Existing E2E tests verify interactions |
| Accessibility breakage | Med | Low | ARIA attributes preserved explicitly |

## 11. Verification & Testing

### 11.1 Test Scenarios

| ID | Scenario | Type | Input | Expected Output | Pass Criteria |
|----|----------|------|-------|-----------------|---------------|
| 010 | No innerHTML in codebase | Auto | `grep innerHTML overlay.js` | No matches | 0 results |
| 020 | Loading overlay renders | Auto | Trigger loading state | Spinner visible | E2E assertion |
| 030 | Result overlay renders | Auto | Mock API response | Card with signal/gem | E2E assertion |
| 040 | XSS blocked | Auto | `<script>` in response | Text displayed, not executed | E2E assertion |
| 050 | Firefox linter passes | Manual | `web-ext lint` | 0 innerHTML warnings | Exit code 0 |
| 060 | Visual regression | Auto | Screenshot comparison | No pixel diff | Playwright toHaveScreenshot |

### 11.2 Test Commands

```bash
# Verify no innerHTML usage
grep -r "innerHTML" extensions/chrome/overlay.js

# Run E2E tests
npm run test:e2e

# Run visual regression tests
npm run test:visual

# Firefox linter
cd extensions/firefox && npx web-ext lint
```

### 11.3 Manual Tests

| ID | Scenario | Why Not Automated | Steps |
|----|----------|-------------------|-------|
| 050 | Firefox linter | Requires web-ext CLI | Run `web-ext lint`, check for innerHTML warnings |

## 12. Definition of Done

### Code
- [ ] All `innerHTML` assignments replaced in `overlay.js`
- [ ] Code synced between Chrome and Firefox versions
- [ ] Helper function added if needed for readability

### Tests
- [ ] `grep innerHTML overlay.js` returns 0 results
- [ ] All E2E museum-label tests pass
- [ ] Visual regression tests pass
- [ ] XSS protection tests pass

### Documentation
- [ ] LLD committed
- [ ] Implementation Report completed

### Review
- [ ] Code review completed
- [ ] Firefox linter shows 0 innerHTML warnings
