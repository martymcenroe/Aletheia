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
| 2025-12-21 | `contextMenus.onClicked` provides `info.pageUrl` without needing broad permissions. | Allowlist gate can run inside handler before any fetch/inject calls. |