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
| 2025-12-23 | `fatal: 'main' is already used by worktree` | Git forbids checking out the same branch in multiple dirs. Merge `origin/main` instead of checking out `main`. |
| 2025-12-28 | Git Bash `TZ='America/Chicago' date` returns UTC on Windows, not local time. Created wrong session log file (Week-starting-2025-12-29 instead of 2025-12-22). | **Technical:** Use `powershell.exe -Command "Get-Date -Format 'yyyy-MM-dd HH:mm'"` on Windows for timestamps. **Meta-lesson:** Don't blame tools for my logic errors - I used the wrong command, then deflected responsibility by calling it a "Windows bug". Take accountability. When wrong, fix it and document the real cause. |
| 2025-12-31 | **#45 Denylist:** LLD specified `denylist.json` but never documented where the data comes from (RSDB), how to download it, or how it gets to Lambda. Implemented code that depends on a file that doesn't exist in any usable form. | **Process fix:** LLD template needs a "Data & Fixtures" section. Before coding, reviewer must ask: (1) Where does the data come from? (2) How does it get there? (3) Is a separate utility needed? See `docs/0108-lld-pre-implementation-review.md` for the full checklist. |
| 2025-12-31 | **#45 Denylist:** Tests mock the denylist with safe placeholders (good), but no integration test verifies the full data pipeline from RSDB → JSON → Lambda. Unit tests pass but system isn't actually usable. | **Rule:** For features with external data sources, create at minimum: (1) Utility to fetch/transform data (#119), (2) Integration test that loads real file format, (3) Deployment docs showing data flow. |
