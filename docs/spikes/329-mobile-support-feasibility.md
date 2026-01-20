# Spike #329: Mobile Reading Experience Solutions

**Date:** 2026-01-14
**Time-box:** 3 hours (actual: ~1.5 hours)
**Status:** COMPLETE

---

## Executive Summary

**Recommended MVP: Safari iOS Extension + PWA with Share Target**

Mobile support requires a multi-pronged approach due to platform fragmentation. The most promising path is:
1. **iOS:** Safari Web Extension (from Spike #328) - same codebase as desktop
2. **Android:** PWA with Web Share Target API - receives URLs from any app's share sheet

**Effort Estimate:** Medium-Large (M-L) - 1-2 weeks total

---

## 1. Browser Extension Options

### 1.1 Platform Support Matrix

| Platform | Extension Support | Aletheia Viability | Notes |
|----------|-------------------|-------------------|-------|
| Safari iOS 15+ | ✅ Full | ✅ High | Same extension as macOS (Spike #328) |
| Firefox Android | ✅ Full (since v120) | ✅ Medium | Need to publish to AMO |
| Chrome Android | ❌ None | ❌ Blocked | Google has no plans to add support |
| Edge Android | ⚠️ Limited | ⚠️ Low | Requires manual extension ID paste |
| Samsung Internet | ⚠️ Limited | ⚠️ Low | Own extension store, not Chrome Web Store |
| Kiwi Browser | ❌ Discontinued | ❌ Dead | Archived early 2025, security concerns |
| Yandex Browser | ✅ Chrome extensions | ⚠️ Low | Niche market, Russian-focused |

### 1.2 Recommendation

**Invest in:**
- Safari iOS (already covered by Spike #328)
- Firefox Android (minor manifest tweaks, same codebase)

**Do not invest in:**
- Chrome Android (impossible)
- Edge/Samsung/Yandex (low ROI for niche browsers)

---

## 2. Alternative Approaches Analysis

### 2.1 Progressive Web App (PWA) with Share Target

**How it works:**
1. User installs Aletheia PWA (Add to Home Screen)
2. When reading an article, user taps Share → Aletheia
3. PWA receives URL, fetches article, sends to API for analysis

**Technical Implementation:**
```json
// manifest.json
{
  "share_target": {
    "action": "/analyze",
    "method": "GET",
    "params": {
      "url": "url",
      "text": "text",
      "title": "title"
    }
  }
}
```

| Aspect | iOS | Android |
|--------|-----|---------|
| Share Target API | ⚠️ Requires App Store PWA | ✅ Full support |
| Installation | Home Screen | Home Screen |
| CORS | Server-side proxy needed | Server-side proxy needed |
| Offline | ❌ Needs connectivity | ❌ Needs connectivity |

**Pros:**
- Single codebase (web)
- No app store approval needed (except iOS)
- Integrates with native share sheet

**Cons:**
- iOS requires PWA published via App Store (e.g., PWABuilder)
- User must install PWA first
- Can't analyze text selections (only full URLs)

**Effort:** Medium (1 week)

---

### 2.2 Bookmarklet

**Status: NOT VIABLE**

Modern mobile browsers have severely restricted bookmarklet functionality:

| Browser | Bookmarklet Support | Notes |
|---------|---------------------|-------|
| Safari iOS 15+ | ❌ Blocked | Apple disabled JS in address bar |
| Chrome Android | ⚠️ Crippled | No bookmarks bar, can't access current page |
| Firefox Android | ⚠️ Limited | Must type bookmarklet name in address bar |

**Verdict:** Do not pursue. Too much user friction, unreliable cross-browser.

---

### 2.3 Native App with Share Extension

**How it works:**
1. User installs native Aletheia app
2. App registers as share target (iOS Share Extension / Android Intent Filter)
3. When sharing from any browser, Aletheia appears in share sheet
4. User selects text OR shares URL, app receives and analyzes

**Technical Options:**

| Framework | iOS | Android | Effort | Notes |
|-----------|-----|---------|--------|-------|
| React Native | ✅ | ✅ | High | `expo-share-intent` or `react-native-receive-sharing-intent` |
| Native (Swift/Kotlin) | ✅ | ✅ | Very High | Maximum control, most maintenance |
| Flutter | ✅ | ✅ | High | `receive_sharing_intent` package |
| Capacitor/Ionic | ✅ | ✅ | Medium | Web-first, native wrappers |

**iOS Share Extension Flow:**
```
Safari → Share → Aletheia → Receive URL + selected text → API call → Display result
```

**Pros:**
- Best UX (native share sheet integration)
- Can receive selected text (not just URLs)
- Works with ANY app, not just browsers
- Offline queueing possible

**Cons:**
- Requires App Store approval (both iOS and Android)
- Separate codebase to maintain
- Higher development effort

**Effort:** Large (2-3 weeks for cross-platform)

---

### 2.4 Copy-Paste Web Interface

**How it works:**
1. User navigates to aletheia.study/mobile
2. User copies text from article
3. User pastes into Aletheia web interface
4. Analysis results displayed

**Pros:**
- Zero installation
- Works on any device/browser
- No app store approval

**Cons:**
- High friction (manual copy-paste)
- Can't get URL context automatically
- Poor UX compared to share sheet

**Effort:** Low (2-3 days)

---

## 3. User Experience Comparison

| Approach | Steps to Analyze | UX Rating | Works Everywhere |
|----------|------------------|-----------|------------------|
| Safari iOS Extension | 2 (select, right-click) | ⭐⭐⭐⭐⭐ | iOS only |
| Firefox Android Extension | 2 (select, right-click) | ⭐⭐⭐⭐⭐ | FF Android only |
| Native App Share Extension | 3 (select, share, tap Aletheia) | ⭐⭐⭐⭐ | iOS + Android |
| PWA Share Target | 3 (share URL, tap Aletheia, wait) | ⭐⭐⭐ | Android only |
| Copy-Paste Web | 5+ (copy, switch, paste, submit, wait) | ⭐⭐ | Universal |

---

## 4. Technical Constraints

### 4.1 CORS Limitations

All web-based solutions (PWA, copy-paste) cannot directly fetch article content from other domains due to CORS. Solutions:

1. **Server-side proxy** - Aletheia API fetches article content (already implemented)
2. **User pastes text** - No CORS needed, but worse UX

### 4.2 App Store Requirements

| Platform | Review Time | Cost | Requirements |
|----------|-------------|------|--------------|
| Apple App Store | 1-3 days | $99/year | Apple Developer Program |
| Google Play Store | Hours-days | $25 one-time | Google Play Console |
| Firefox AMO | Hours-days | Free | Mozilla Add-on Developer |

### 4.3 Content Security Policy

Some sites have strict CSP that blocks injected scripts. Extensions can bypass this, but PWAs cannot.

---

## 5. Recommended MVP Strategy

### Phase 1: Safari iOS Extension (Already Planned)
- From Spike #328
- Same codebase as desktop Safari
- Covers ~27% of mobile browser market (iOS)
- **Effort:** Included in Spike #328

### Phase 2: Firefox Android Extension
- Minimal changes from desktop Firefox extension
- Already have `gecko_android` settings in manifest
- Publish to addons.mozilla.org
- **Effort:** Small (0.5-1 day)

### Phase 3: PWA Share Target (Android)
- Build simple PWA that receives shared URLs
- Integrates with existing API
- Covers Chrome Android users who can't use extensions
- **Effort:** Medium (1 week)

### Phase 4: Native App (Future)
- Consider React Native or Capacitor for cross-platform
- Best UX for power users
- Only pursue if PWA adoption is high
- **Effort:** Large (2-3 weeks)

---

## 6. User Flow Mockups

### 6.1 Safari iOS (Extension)
```
User reads article in Safari
→ Selects text
→ Long-press → "Explain with AI" in context menu
→ Aletheia overlay appears with analysis
```

### 6.2 Firefox Android (Extension)
```
User reads article in Firefox
→ Selects text
→ Long-press → "Explain with AI" in context menu
→ Aletheia overlay appears with analysis
```

### 6.3 PWA Share Target (Android)
```
User reads article in Chrome
→ Taps Share button
→ Selects "Aletheia" from share sheet
→ Aletheia PWA opens with URL pre-filled
→ PWA fetches article, sends to API
→ Analysis displayed in PWA interface
```

### 6.4 Copy-Paste Web (Universal Fallback)
```
User reads article in any browser
→ Selects and copies text
→ Opens aletheia.study/mobile
→ Pastes text into input field
→ Clicks "Analyze"
→ Analysis displayed
```

---

## 7. Decision Matrix

| Approach | Coverage | Effort | UX | Maintenance | Recommend |
|----------|----------|--------|----|-----------| |
| Safari iOS Extension | 27% mobile | M | ⭐⭐⭐⭐⭐ | Low | ✅ Yes (Phase 1) |
| Firefox Android | ~3% mobile | S | ⭐⭐⭐⭐⭐ | Low | ✅ Yes (Phase 2) |
| PWA Share Target | 60% Android | M | ⭐⭐⭐ | Low | ✅ Yes (Phase 3) |
| Native App | 100% mobile | L | ⭐⭐⭐⭐ | High | ⚠️ Future |
| Copy-Paste Web | 100% | S | ⭐⭐ | Very Low | ✅ Fallback |
| Bookmarklet | ~0% | - | ❌ | - | ❌ No |

---

## 8. Conclusion

**Recommended Approach:**
1. **Immediate:** Safari iOS Extension (Spike #328) + Firefox Android Extension
2. **Short-term:** PWA with Share Target for Android Chrome users
3. **Fallback:** Simple copy-paste web interface
4. **Future:** Native app if demand warrants

This strategy covers ~90% of mobile users with moderate effort while maintaining a single core codebase philosophy.

---

## Sources

- [Mozilla: Firefox Android Extensions](https://addons.mozilla.org/en-US/android/)
- [MDN: Share Data Between Apps (PWA)](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/How_to/Share_data_between_apps)
- [web.dev: OS Integration for PWAs](https://web.dev/learn/pwa/os-integration)
- [Quetta: Android Browsers with Extension Support 2025](https://www.quetta.net/blog/best-browsers-for-android-that-support-extensions-in-2025)
- [Devas.life: React Native Share Extensions](https://www.devas.life/supporting-ios-share-extensions-android-intents-on-react-native/)
- [expo-share-intent npm](https://www.npmjs.com/package/expo-share-intent)
- [Do Your Own SEO: Bookmarklets on Mobile](https://do-your-own-seo.com/how-to-use-JS-bookmarklets-on-mobile)
- [Brainhub: PWA on iOS Limitations 2025](https://brainhub.eu/library/pwa-on-ios)
