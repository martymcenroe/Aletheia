# 9000 - Lessons Learned (Aletheia-Specific)

Project-specific gotchas, decisions, and solutions. For cross-project engineering lessons, see the [Engineering Journal](https://github.com/martymcenroe/martymcenroe/blob/main/ENGINEERING-JOURNAL.md).

## Format
Append new entries to the bottom of the log table:
```
| YYYY-MM-DD | What happened | The rule I now follow |
```

---

## Log

| Date | Lesson | Rule/Action |
|:-----|:-------|:------------|
| 2025-12-21 | `host_permissions: ["<all_urls>"]` triggers scary Chrome warning and delays store review. | Use `activeTab` for privacy-first design. Accept static toolbar icon as tradeoff. |
| 2025-12-21 | Subdomain handling (e.g., `finance.yahoo.com` vs `yahoo.com`) is complex. Public Suffix List needed for proper root domain extraction. | MVP: Store full hostname. Document as known limitation. |
| 2025-12-21 | `contextMenus.onClicked` provides `info.pageUrl` without needing broad permissions. | Allowlist gate can run inside handler before any fetch/inject calls. || 2025-12-22 | Anti-aliasing artifacts remain when converting black background to transparent. PIL threshold of 30 leaves dark edge pixels. | Use threshold ~250 for clean edges (R+G+B sum, higher = more aggressive). |
| 2025-12-22 | Chrome extension reload doesn't require remove/reinstall during development. | Just click refresh icon on `chrome://extensions/` page, then close/reopen popup. |
| 2025-12-22 | `chrome.storage.local` survives "Clear browsing data" including "Hosted app data" checkbox. | Storage is extension-owned, not site-owned. Safe to use for user preferences. |
| 2025-12-22 | Duplicate context menu error on extension reload: `Cannot create item with duplicate id`. | Wrap `contextMenus.create` in try/catch or check existence first. (Issue #89) |
