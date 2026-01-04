# 1104 - Feature: Block Age-Restricted Sites

## 1. Context & Goal
* **Issue:** #104
* **Objective:** Prevent Aletheia from activating on age-restricted websites by detecting adult content meta tags.
* **Status:** Implementation Complete
* **Related Issues:** #105 (test site infrastructure for verification)

## 2. Requirements

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| R1 | Detect `<meta name="rating" content="adult">` tag | Extension identifies adult-rated pages |
| R2 | Detect RTA label pattern | Recognize `RTA-5042-1996-1400-1577-RTA` content value |
| R3 | Block text selection prompt | Show "not permitted" message instead of "Enable Aletheia" |
| R4 | Display prohibition icon | Extension icon shows red prohibition symbol on restricted tabs |
| R5 | Icon persists until tab close | No timer - state lasts for tab lifetime |
| R6 | No data persistence | Forget site restriction when tab closes |
| R7 | Popup shows disabled state | All controls disabled with explanation when on restricted site |
| R8 | Allow `content="mature"` | Do NOT block on mature rating (movie reviews, medical sites) |

## 3. Alternatives Considered

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| A. Block on any rating | Simple implementation | Over-blocks legitimate content (mature != adult) | **Rejected** |
| B. Block only on `adult` + RTA | Precise, follows Google guidance | Two patterns to check | **Selected** |
| C. Maintain persistent blocklist | Remembers known adult sites | Privacy concern, storage overhead | **Rejected** |
| D. Time-limited blocking | Allows accidental visits to recover | Could enable bypass attempts | **Rejected** |

**Rationale:** Google's SafeSearch guidelines explicitly distinguish `adult` from `mature`. We block on definitive adult indicators only, per-tab without persistence to maintain privacy.

## 4. Data & Fixtures

### 4.1 Data Sources

| Attribute | Value |
|-----------|-------|
| Source | Host page `<meta>` tags (DOM) |
| Format | HTML meta element |
| Size | Single DOM query per page |
| Refresh | On page load / tab update |
| Copyright/License | N/A - reading public page metadata |

### 4.2 Data Pipeline

```
Page Load ──DOM query──► Content Script ──message──► Service Worker ──state──► Tab State Map
```

### 4.3 Test Fixtures

| Fixture | Source | Notes |
|---------|--------|-------|
| `test-adult.html` | Created for testing | `<meta name="rating" content="adult">` |
| `test-rta.html` | Created for testing | `<meta name="rating" content="RTA-5042-...">` |
| `test-mature.html` | Created for testing | `<meta name="rating" content="mature">` - should NOT block |
| `test-clean.html` | Created for testing | No rating meta tag |

### 4.4 Deployment Pipeline

Test pages deployed via GitHub Pages or similar (see #105). Extension updated via normal Chrome extension deployment.

## 5. Diagram

```mermaid
sequenceDiagram
    participant Tab as Browser Tab
    participant CS as Content Script
    participant SW as Service Worker
    participant UI as Popup/Overlay

    Tab->>SW: onUpdated (tab loaded)
    SW->>Tab: Inject content script
    Tab->>CS: Execute script
    CS->>CS: Query meta[name="rating"]

    alt content="adult" OR contains "RTA-5042"
        CS->>SW: Message: AGE_RESTRICTED
        SW->>SW: tabStates[tabId] = "restricted"
        SW->>Tab: Set badge (red prohibition)
    else content="mature" OR no rating
        CS->>SW: Message: ALLOWED
        SW->>SW: tabStates[tabId] = "allowed"
    end

    Note over Tab,UI: User selects text

    alt Tab is restricted
        UI->>UI: Show "not permitted" message
        UI->>UI: Disable all controls
    else Tab is allowed
        UI->>UI: Normal Aletheia flow
    end

    Tab->>SW: onRemoved (tab closed)
    SW->>SW: delete tabStates[tabId]
```

## 6. Technical Approach

* **Module:** `extension-chrome-V3/service-worker.js`, `extension-chrome-V3/content-check.js` (new), `extension-chrome-V3/content-safety.js` (new - pure logic)
* **Dependencies:** Chrome Extension APIs (`scripting`, `tabs`, `action`)
* **Required Permissions:** `scripting`, `tabs`, `<all_urls>` host permission (added to manifest.json)
* **Pattern:** Event-driven state machine per tab

### 6.1 Constants

```javascript
// content-safety.js - Shared constants
const RTA_LABEL_PATTERN = 'rta-5042-1996-1400-1577-rta';
const ADULT_RATING = 'adult';
const MATURE_RATING = 'mature';  // Explicitly allowed
```

### 6.2 Detection Logic (Pure Function - Testable)

```javascript
// content-safety.js - Pure logic, no DOM dependencies
function isAgeRestricted(ratingContent) {
    if (!ratingContent || typeof ratingContent !== 'string') {
        return false;
    }
    const normalized = ratingContent.toLowerCase().trim();
    return normalized === ADULT_RATING ||
           normalized.includes(RTA_LABEL_PATTERN);
}

// content-check.js - DOM wrapper (calls pure function)
function checkPageRating() {
    const ratingMeta = document.querySelector('meta[name="rating"]');
    const content = ratingMeta?.getAttribute('content') || '';
    return {
        type: 'RATING_CHECK',
        isRestricted: isAgeRestricted(content),
        ratingValue: content || null
    };
}
```

### 6.3 State Management

Tab states stored in memory (not `chrome.storage`):
```javascript
// service-worker.js
const TabState = {
    UNKNOWN: 'unknown',      // Not yet checked (race condition safe)
    RESTRICTED: 'restricted', // Adult content detected
    ALLOWED: 'allowed'        // No adult content
};

const tabStates = new Map(); // tabId -> TabState value
```

Cleared automatically when tab closes via `chrome.tabs.onRemoved`.

### 6.4 URL Scheme Filtering

Only inject detection script on navigable web pages:
```javascript
// service-worker.js - in onUpdated handler
function shouldCheckTab(url) {
    if (!url) return false;
    return url.startsWith('http://') || url.startsWith('https://');
    // Ignore: chrome://, chrome-extension://, file://, about:, etc.
}
```

### 6.5 Race Condition Handling

**Problem:** User may open popup before content script completes detection.

**Solution:** Three-state model with explicit UNKNOWN state:

```javascript
// popup.js - on open
async function getTabStatus(tabId) {
    const state = await chrome.runtime.sendMessage({
        type: 'GET_TAB_STATE',
        tabId
    });

    if (state === TabState.UNKNOWN) {
        // Show "Checking..." UI, trigger re-check
        await chrome.runtime.sendMessage({ type: 'RECHECK_TAB', tabId });
        return 'checking';
    }
    return state;
}
```

**Popup behavior by state:**
| State | UI Display | Controls |
|-------|------------|----------|
| UNKNOWN | "Checking site..." spinner | Disabled |
| RESTRICTED | "Not permitted on this site" | Disabled |
| ALLOWED | Normal Aletheia UI | Enabled |

## 7. Interface Specification

### 7.1 Data Structures

```javascript
// Tab state (in-memory only)
const TabState = {
    UNKNOWN: 'unknown',        // Not yet checked (initial state)
    RESTRICTED: 'restricted',  // Adult content detected
    ALLOWED: 'allowed',        // No adult content
};

// Message from content script to service worker
const RatingCheckMessage = {
    type: 'RATING_CHECK',
    isRestricted: boolean,
    ratingValue: string | null,  // For logging
};

// Message from popup to service worker
const GetTabStateMessage = {
    type: 'GET_TAB_STATE',
    tabId: number,
};

const RecheckTabMessage = {
    type: 'RECHECK_TAB',
    tabId: number,
};
```

### 7.2 Function Signatures

```javascript
// content-check.js
function checkPageRating(): RatingCheckMessage;

// service-worker.js
function handleRatingCheck(tabId: number, message: RatingCheckMessage): void;
function isTabRestricted(tabId: number): boolean;
function setRestrictedBadge(tabId: number): void;
function clearTabState(tabId: number): void;
```

### 7.3 Logic Flow (Pseudocode)

```
1. Tab loads or updates (onUpdated event)
2. Inject content-check.js into tab
3. Content script queries <meta name="rating">
4. IF content === "adult" OR content contains RTA pattern:
   - Send RESTRICTED message to service worker
   - Service worker stores tabStates[tabId] = "restricted"
   - Set badge to prohibition icon
   ELSE:
   - Send ALLOWED message
   - Service worker stores tabStates[tabId] = "allowed"

5. ON text selection (context menu):
   - Check tabStates[tabId]
   - IF restricted: show "not permitted" overlay, return
   - ELSE: normal Aletheia flow

6. ON tab close (onRemoved):
   - delete tabStates[tabId]
```

## 8. Security Considerations

| Concern | Mitigation | Status |
|---------|------------|--------|
| Bypass via meta tag removal | State set once on load, not re-checked | Addressed |
| Injection from page | Content script runs in isolated world | Addressed |
| False positives | Only block exact patterns per Google spec | Addressed |
| Storage of adult site visits | No persistence - memory only, cleared on tab close | Addressed |
| CSP blocks script injection | Fail open - treat as allowed (see below) | Addressed |
| Race condition (popup before check) | Three-state model with UNKNOWN state | Addressed |

**Fail Mode:** Fail Open - If detection fails (including CSP blocking script injection), site is treated as allowed. Rationale:
1. We cannot risk blocking legitimate sites that happen to have strict CSP
2. Adult site operators who want to be blocked must properly tag their content
3. CSP-heavy sites are typically enterprise/banking - not adult content
4. This is a content safety feature, not a security boundary

## 9. Performance Considerations

| Metric | Budget | Approach |
|--------|--------|----------|
| Detection latency | < 10ms | Single DOM query |
| Memory per tab | < 100 bytes | Simple string state |
| CPU | Negligible | Event-driven, no polling |

**Bottlenecks:** None expected. Single synchronous DOM query on page load.

## 10. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Site doesn't use rating meta | Low | High | Fail open - not our problem if site doesn't tag |
| User disables content scripts | Med | Low | Extension won't work anyway without scripts |
| RTA pattern changes | Low | Very Low | RTA-5042 is a fixed standard from 1996 |
| Browser caches old page | Low | Low | Detection runs on each page load event |

## 11. Verification & Testing

### 11.1 Test Scenarios

| ID | Scenario | Type | Input | Expected Output | Pass Criteria |
|----|----------|------|-------|-----------------|---------------|
| 010 | Detect adult rating | Auto | `"adult"` | `isAgeRestricted() === true` | Unit test passes |
| 011 | Detect ADULT (uppercase) | Auto | `"ADULT"` | `isAgeRestricted() === true` | Case insensitive |
| 012 | Detect adult with whitespace | Auto | `" adult "` | `isAgeRestricted() === true` | Trim handled |
| 020 | Detect RTA pattern | Auto | `"RTA-5042-1996-1400-1577-RTA"` | `isAgeRestricted() === true` | Unit test passes |
| 021 | Detect RTA lowercase | Auto | `"rta-5042-1996-1400-1577-rta"` | `isAgeRestricted() === true` | Case insensitive |
| 022 | Detect RTA embedded | Auto | `"some-RTA-5042-1996-1400-1577-RTA-text"` | `isAgeRestricted() === true` | Pattern found |
| 030 | Allow mature rating | Auto | `"mature"` | `isAgeRestricted() === false` | Not blocked |
| 040 | Allow no rating | Auto | `""` or `null` | `isAgeRestricted() === false` | Not blocked |
| 041 | Allow undefined | Auto | `undefined` | `isAgeRestricted() === false` | No crash |
| 050 | Text selection blocked | Manual | Select text on adult page | "Not permitted" message | No "Enable" prompt |
| 060 | State clears on tab close | Manual | Close restricted tab, reopen site | Fresh state check | No persistent block |
| 070 | Popup disabled state | Manual | Open popup on restricted tab | All controls disabled | Explanation shown |
| 080 | Multiple tabs independent | Manual | Adult tab + normal tab | Each has correct state | States don't leak |
| 090 | Popup during UNKNOWN state | Manual | Open popup immediately on load | Shows "Checking..." | Not assumed allowed |
| 100 | CSP blocks injection | Manual | Test on CSP-strict site | Fail open (allowed) | No crash, site works |

### 11.2 Test Modules (from 0005)

* **Unit Tests:** `tests/test_content_safety.js` - Pure logic tests for `isAgeRestricted()`
* **Semantic (Module B):** No
* **End-to-End (Module C):** Yes - requires test site hosting (#105)

### 11.3 Unit Test Implementation

```javascript
// tests/test_content_safety.js
const { isAgeRestricted, RTA_LABEL_PATTERN } = require('../extension-chrome-V3/content-safety.js');

describe('isAgeRestricted', () => {
    // Blocked cases
    test('blocks "adult"', () => expect(isAgeRestricted('adult')).toBe(true));
    test('blocks "ADULT" (case insensitive)', () => expect(isAgeRestricted('ADULT')).toBe(true));
    test('blocks " adult " (whitespace)', () => expect(isAgeRestricted(' adult ')).toBe(true));
    test('blocks RTA pattern', () => expect(isAgeRestricted('RTA-5042-1996-1400-1577-RTA')).toBe(true));
    test('blocks RTA lowercase', () => expect(isAgeRestricted('rta-5042-1996-1400-1577-rta')).toBe(true));
    test('blocks RTA embedded in string', () => expect(isAgeRestricted('x-RTA-5042-1996-1400-1577-RTA-y')).toBe(true));

    // Allowed cases
    test('allows "mature"', () => expect(isAgeRestricted('mature')).toBe(false));
    test('allows empty string', () => expect(isAgeRestricted('')).toBe(false));
    test('allows null', () => expect(isAgeRestricted(null)).toBe(false));
    test('allows undefined', () => expect(isAgeRestricted(undefined)).toBe(false));
    test('allows random string', () => expect(isAgeRestricted('general')).toBe(false));
    test('allows partial RTA', () => expect(isAgeRestricted('RTA-5042')).toBe(false));
});

describe('RTA_LABEL_PATTERN constant', () => {
    test('is lowercase', () => expect(RTA_LABEL_PATTERN).toBe('rta-5042-1996-1400-1577-rta'));
});
```

### 11.4 Manual Smoke Test

1. Deploy test pages (per #105)
2. Load `test-adult.html` - verify prohibition badge appears
3. Select text - verify "not permitted" message (not "Enable Aletheia")
4. Click extension icon - verify popup shows disabled state
5. Close tab
6. Load `test-mature.html` - verify normal operation
7. Load `test-clean.html` - verify normal operation
8. **NEW:** Rapidly click extension icon on slow page load - verify "Checking..." state (not assumed allowed)

## 12. Definition of Done

### Code
- [ ] `content-safety.js` created with pure detection logic and constants
- [ ] `content-check.js` created with DOM wrapper calling `isAgeRestricted()`
- [ ] `service-worker.js` updated with three-state tab management (UNKNOWN/RESTRICTED/ALLOWED)
- [ ] `service-worker.js` filters by URL scheme before injection
- [ ] `popup.js` handles UNKNOWN state with "Checking..." UI
- [ ] Prohibition badge implementation
- [ ] "Not permitted" overlay message
- [ ] Popup disabled state UI

### Tests
- [ ] Unit tests pass (`tests/test_content_safety.js`) - scenarios 010-041
- [ ] All manual test scenarios pass (050-100)
- [ ] Test pages created and deployed (#105)

### Documentation
- [ ] LLD updated with any deviations
- [ ] Decision recorded in 0202-DR-content-safety.md (referenced in issue)

### Review
- [ ] Code review completed
- [ ] User approval before closing issue
