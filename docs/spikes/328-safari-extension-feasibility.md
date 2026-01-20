# Spike #328: Safari Web Extension Feasibility Report

**Date:** 2026-01-14
**Time-box:** 2 hours (actual: ~1 hour)
**Status:** COMPLETE

---

## Executive Summary

**Verdict: FEASIBLE** - Porting Aletheia to Safari is technically feasible with moderate effort. The primary blocker is the need for an Apple Developer Program membership ($99/year) and a macOS development environment.

**Effort Estimate:** Medium (M) - 2-3 days development, plus App Store review time

---

## 1. Technical Compatibility Assessment

### 1.1 Manifest V3 Support

| Feature | Safari Support | Aletheia Usage | Compatibility |
|---------|----------------|----------------|---------------|
| `manifest_version: 3` | Yes (Safari 15.4+) | Yes | ✅ Compatible |
| `service_worker` background | Yes | Yes | ✅ Compatible |
| `permissions` | Yes | All used | ✅ Compatible |
| `host_permissions` | Yes | Empty array | ✅ Compatible |
| `action` (popup) | Yes | Yes | ✅ Compatible |

### 1.2 API Compatibility

| Chrome API | Safari Support | Aletheia Usage | Notes |
|------------|----------------|----------------|-------|
| `chrome.scripting.executeScript` | ✅ Full | Heavy use | Works identically |
| `chrome.contextMenus` | ✅ Full | Context menu | Works identically |
| `chrome.storage.local` | ✅ Full | Allowlist storage | Works identically |
| `chrome.action.setBadgeText` | ✅ Full | Badge indicators | Works identically |
| `chrome.tabs` | ✅ Full | Tab queries | Works identically |
| `chrome.runtime.onMessage` | ✅ Full | Message passing | Works identically |
| `chrome.runtime.id` | ✅ Full | Security validation | Works identically |
| `chrome.identity` | ⚠️ Limited | **Not used** | N/A for Aletheia |

**Key Finding:** Aletheia does NOT use the problematic `chrome.identity` API. Our OAuth flow is handled server-side via LinkedIn OAuth, not client-side browser auth. This significantly reduces porting complexity.

### 1.3 Content Script / Shadow DOM

Aletheia injects `overlay.js` using `chrome.scripting.executeScript` which works identically in Safari. The overlay uses standard DOM manipulation (no Shadow DOM injection issues expected).

---

## 2. Development Requirements

### 2.1 Tools Required

| Tool | Required | Notes |
|------|----------|-------|
| macOS | Yes | Xcode only runs on macOS |
| Xcode 12+ | Yes | Safari Web Extension Converter tool |
| Apple Developer Account | **Yes (for distribution)** | Free account works for development |
| Apple Developer Program | **Yes (for App Store)** | $99/year |

### 2.2 Conversion Process

```bash
# One-command conversion (90% automated)
xcrun safari-web-extension-converter /path/to/extensions/chrome \
  --app-name "Aletheia" \
  --bundle-identifier "study.aletheia.extension"
```

This creates:
- macOS container app
- iOS container app (by default)
- Xcode project with extension embedded

### 2.3 Manual Steps Required

1. **Remove Chrome-specific manifest key** - The `"key"` field in Chrome manifest (for stable extension ID) must be removed
2. **Add Safari-specific settings** - Similar to Firefox's `browser_specific_settings`
3. **Test and fix** - Address any runtime issues
4. **Add app icons** - Container app needs icons for App Store

---

## 3. Distribution Options

### 3.1 App Store (Primary)

| Requirement | Details |
|-------------|---------|
| Apple Developer Program | $99/year membership |
| Review Process | Apple reviews all extensions |
| Timeline | Typically 1-3 days for review |
| Updates | Each update requires re-review |

**Pros:** Automatic updates, user trust, single distribution point
**Cons:** $99/year cost, review delays, Apple guidelines compliance

### 3.2 Direct Distribution (Alternative)

| Requirement | Details |
|-------------|---------|
| Notarization | Required for macOS distribution outside App Store |
| Apple Developer Program | Still required ($99/year) |
| User Experience | Users must manually download and install |

**Pros:** No review delays, full control
**Cons:** Manual updates, lower discoverability, user friction

### 3.3 NEW: ZIP Upload (No Xcode Required)

Apple now allows uploading a ZIP file directly to App Store Connect for conversion. This could enable:
- CI/CD pipeline for Safari builds
- No macOS development machine required for distribution

**Status:** Worth investigating for automation

---

## 4. iOS Safari Support

### 4.1 Compatibility

| iOS Version | Support | Notes |
|-------------|---------|-------|
| iOS 15+ | ✅ Yes | Same extension works |
| iOS 17.x | ⚠️ Known issues | Service worker may stop after ~1 minute |
| iOS 18 | ⚠️ Improved but not fixed | Service worker stops after ~1 day |

### 4.2 iOS-Specific Requirements

1. **Non-persistent background** - `persistent: false` required (Aletheia already uses service_worker, so this is fine)
2. **User activation** - Users must manually enable in Settings → Safari → Extensions
3. **Per-site permissions** - Similar to desktop Safari

### 4.3 iOS Limitations

- **No automatic activation** - Extension doesn't auto-trigger on page load
- **User must tap** - Context menu requires explicit user action (matches Aletheia's current UX)
- **Service worker instability** - Known Apple bug, workaround is user re-enabling extension

**Impact for Aletheia:** The context menu flow ("Explain with AI") works well for iOS since it's already user-initiated. The service worker issues mainly affect extensions that need persistent background processing.

---

## 5. Blockers and Dependencies

### 5.1 Hard Blockers

| Blocker | Severity | Mitigation |
|---------|----------|------------|
| macOS development environment | HIGH | Required for initial setup; ZIP upload may help later |
| Apple Developer Program ($99/year) | MEDIUM | Necessary for App Store distribution |

### 5.2 Soft Blockers

| Issue | Severity | Mitigation |
|-------|----------|------------|
| iOS service worker instability | LOW | Aletheia's UX is context-menu based, minimally affected |
| App Store review time | LOW | Plan 1-3 day buffer for releases |

### 5.3 Dependencies

- Need a macOS machine (or CI with macOS runner) for initial conversion
- Need to decide on bundle identifier and signing certificates
- Need App Store listing assets (screenshots, descriptions)

---

## 6. Recommended Approach

### Phase 1: macOS Safari Extension (1-2 days)

1. Run converter: `xcrun safari-web-extension-converter`
2. Remove Chrome `key` from manifest
3. Test locally with unsigned extensions enabled
4. Fix any runtime issues
5. Add app icons and metadata

### Phase 2: iOS Safari Extension (0.5-1 day)

1. Enable iOS target in Xcode project (default)
2. Set `persistent: false` for iOS background
3. Test on iOS Simulator
4. Test on physical device

### Phase 3: App Store Submission (1-2 days)

1. Create App Store Connect listing
2. Generate screenshots for macOS and iOS
3. Submit for review
4. Address any review feedback

### Total Effort: 2-3 days + review time

---

## 7. Code Sharing Strategy

```
extensions/
├── chrome/           # Chrome-specific manifest + code
├── firefox/          # Firefox-specific manifest + code
├── safari/           # Safari-specific manifest (NEW)
└── shared/           # Shared JS/CSS (extract from chrome/)
    ├── service-worker.js
    ├── overlay.js
    ├── popup.js
    ├── popup.css
    ├── popup.html
    └── ...
```

**Recommendation:** Extract shared code to `extensions/shared/` and have each browser folder contain only browser-specific files (manifest, icons). This reduces maintenance burden.

---

## 8. Decision Matrix

| Option | Effort | Ongoing Cost | User Reach | Recommendation |
|--------|--------|--------------|------------|----------------|
| Do nothing | None | $0 | 0% Safari users | ❌ |
| macOS only | Medium | $99/year | ~4% desktop | ⚠️ Partial |
| macOS + iOS | Medium | $99/year | ~4% desktop + ~27% mobile | ✅ Recommended |

---

## 9. Conclusion

**GO decision recommended.** The technical compatibility is excellent (all Aletheia APIs are fully supported in Safari), and the effort is moderate. The $99/year Apple Developer fee is the only ongoing cost.

**Next Steps:**
1. Acquire macOS development environment (if not available)
2. Enroll in Apple Developer Program
3. Create implementation issue with detailed tasks
4. Execute Phase 1-3 as outlined above

---

## Sources

- [Apple: Assessing Safari Web Extension Browser Compatibility](https://developer.apple.com/documentation/safariservices/assessing-your-safari-web-extension-s-browser-compatibility)
- [Apple: Creating a Safari Web Extension](https://developer.apple.com/documentation/safariservices/creating-a-safari-web-extension)
- [Apple: Distributing your Safari Web Extension](https://developer.apple.com/documentation/safariservices/distributing-your-safari-web-extension)
- [Evil Martians: Converting Chrome Extensions to Safari](https://evilmartians.com/chronicles/how-to-quickly-and-weightlessly-convert-chrome-extensions-to-safari)
- [Extension.Ninja: Safari 15.4 MV3 Support](https://www.extension.ninja/blog/post/apple-safari-manifest-v3-support/)
- [MDN: Build a Cross-Browser Extension](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Build_a_cross_browser_extension)
