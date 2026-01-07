# 1162 - NoArchive Transform Layer

**Issue:** #162
**Status:** Implementation
**Author:** Claude Opus 4.5
**Date:** 2026-01-07

---

## 1. Problem Statement

Publishers can signal "do not cache/archive my content" via the `noarchive` meta tag:
```html
<meta name="robots" content="noarchive">
```

Aletheia must respect this signal as a "Good Citizen" of the web. When noarchive is present, we MUST NOT persist user queries or AI responses to DynamoDB.

**Blocking Release:** Chrome Web Store reviewers may flag applications that ignore standard publisher signals.

---

## 2. Solution Overview

### 2.1 Signal Flow

```
[Page] → [Extension extracts meta] → [Lambda receives signal] → [Skip persistence]
```

1. **Client-side (content-check.js):** Detect `noarchive` in robots meta tag
2. **Client-side (service-worker.js):** Include `signals.noarchive: true` in API payload
3. **Server-side (lambda_function.py):** Check signal, skip `save_state` if true

### 2.2 Key Principle

**Generate but don't persist.** The user still gets their etymology response - we just don't store it in DynamoDB.

---

## 3. Technical Design

### 3.1 Client: Meta Tag Detection

Extend `content-check.js` to detect noarchive:

```javascript
function checkNoArchive() {
    // Check robots meta tag
    const robotsMeta = document.querySelector('meta[name="robots"]');
    const content = robotsMeta?.getAttribute('content') || '';

    // noarchive can appear alone or with other directives (comma-separated)
    return content.toLowerCase().includes('noarchive');
}
```

**Detection targets:**
- `<meta name="robots" content="noarchive">`
- `<meta name="robots" content="noindex, noarchive">`
- `<meta name="googlebot" content="noarchive">` (Google-specific variant)

### 3.2 Client: Payload Structure

Modify `service-worker.js` payload:

```javascript
const payload = {
    text: info.selectionText,
    url: info.pageUrl,
    title: tab.title,
    domContext: fullPageText,
    signals: {
        noarchive: hasNoArchive  // boolean from content-check.js
    }
};
```

### 3.3 Server: Lambda Handler

In `lambda_handler`, check signal before persistence:

```python
# Extract signals
signals = body.get('signals', {})
skip_persistence = signals.get('noarchive', False)

# ... generation code ...

# Conditional persistence
if not skip_persistence:
    save_state(thread_id, {...})
else:
    logger.info(f"NOARCHIVE: Skipping persistence for thread_id={thread_id}")
```

### 3.4 Server: save_state Modification

No change to `save_state` signature needed. The skip logic is in the caller.

---

## 4. Test Plan

### 4.1 Unit Tests (tests/test_noarchive.py)

| Test | Input | Expected |
|------|-------|----------|
| `test_noarchive_skips_persistence` | `signals.noarchive=True` | DynamoDB NOT called |
| `test_no_signal_persists` | No signals | DynamoDB IS called |
| `test_explicit_false_persists` | `signals.noarchive=False` | DynamoDB IS called |
| `test_response_returned_regardless` | Any | 200 OK with etymology |

### 4.2 Manual Verification

1. Find a page with `<meta name="robots" content="noarchive">`
2. Select text, trigger Aletheia
3. Verify response appears in overlay
4. Check DynamoDB - record should NOT exist

---

## 5. Security Considerations

- **Client can lie:** A malicious client could always send `noarchive=true` to avoid persistence. This is acceptable - it's their data.
- **No PII in logs:** Log the skip event but NOT the content that was skipped.

---

## 6. Files Changed

| File | Change |
|------|--------|
| `extensions/chrome/content-check.js` | Add `checkNoArchive()` function |
| `extensions/chrome/service-worker.js` | Extract signal, include in payload |
| `src/lambda_function.py` | Check signal, conditional persistence |
| `tests/test_noarchive.py` | New test file |

---

## 7. Rollback Plan

If issues arise, remove the `signals` check in lambda_handler. The extension changes are backward-compatible (Lambda ignores unknown fields).
