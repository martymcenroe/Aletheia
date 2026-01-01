# MVP Assessment Checklist

**Purpose:** Verify the extension is ready for Chrome Web Store submission.
**Time:** ~15 minutes
**Prerequisites:** Chrome, unpacked extension loaded, Lambda ON

---

## Quick Setup

```bash
# 1. Turn Lambda ON
./tools/aws/lambda-on.sh

# 2. Run backend smoke test
poetry run python tools/smoke_test.py

# 3. Load extension in Chrome
# chrome://extensions → Developer mode → Load unpacked → select extension/
```

---

## Part 1: Backend (Lambda) ✓ or ✗

Run `poetry run python tools/smoke_test.py` and verify:

| Test | Expected | Result |
|------|----------|--------|
| Valid input | 200 OK, response text | |
| Blocked input | 403, "blocked" message | |
| Empty input | 400, validation error | |

---

## Part 2: Extension Loading ✓ or ✗

| Check | How | Result |
|-------|-----|--------|
| Extension loads | chrome://extensions shows Aletheia | |
| No manifest errors | No red error banner | |
| Icon visible | Lambda icon in toolbar | |

---

## Part 3: Popup UI ✓ or ✗

Click the toolbar icon:

| Check | Expected | Result |
|-------|----------|--------|
| Popup opens | Dark popup appears | |
| Shows "disabled" | Power button in off state | |
| Domain shown | Current domain displayed | |
| Toggle works | Click power → animates to ON | |
| Persists | Reload page → still enabled | |

---

## Part 4: Context Menu ✓ or ✗

Select text on an **enabled** domain:

| Check | Expected | Result |
|-------|----------|--------|
| Context menu | Right-click shows "Explain with AI" | |
| Success overlay | Green border, shows saved word | |
| Success badge | Green ✓ briefly in toolbar | |

---

## Part 5: Blocking ✓ or ✗

### 5a. Domain Block (Allowlist)

On a **disabled** domain, select text:

| Check | Expected | Result |
|-------|----------|--------|
| Blocked overlay | Amber border, "Enable first" | |
| Blocked badge | Amber ! in toolbar | |
| No API call | Network tab shows no request | |

### 5b. Content Block (Denylist)

On an **enabled** domain, select a known slur:

| Check | Expected | Result |
|-------|----------|--------|
| Blocked response | Red overlay, "blocked" message | |

---

## Part 6: Edge Cases ✓ or ✗

| Check | Action | Expected | Result |
|-------|--------|----------|--------|
| XSS prevention | Select `<script>alert(1)</script>` | Text shown literally | |
| Long text | Select paragraph | Truncates gracefully | |
| Rapid clicks | Click "Explain" 5x fast | No stuck states | |

---

## Part 7: Privacy Check ✓ or ✗

| Check | How | Result |
|-------|-----|--------|
| No tracking | Check Network tab for analytics | None |
| Local storage only | Check chrome.storage.local | Only allowlist |
| Minimal permissions | Check manifest.json | activeTab, storage, contextMenus only |

---

## Summary

| Section | Pass/Fail |
|---------|-----------|
| 1. Backend | |
| 2. Extension Loading | |
| 3. Popup UI | |
| 4. Context Menu | |
| 5. Blocking | |
| 6. Edge Cases | |
| 7. Privacy | |

**MVP Ready:** ☐ Yes ☐ No

**Blockers (if No):**
-

---

## After Assessment

```bash
# Turn Lambda OFF when done
./tools/aws/lambda-off.sh
```

**If all pass:** Proceed to #51 (Store Compliance) and #53 (Store Assets).
