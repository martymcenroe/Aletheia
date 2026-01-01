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
| 2025-12-24 | **Lambda kill switch:** Setting concurrency=0 immediately stops all invocations. Use as "Denial of Wallet" defense when not actively testing. | Run `./tools/aws/lambda-off.sh` at end of every session. Verify with `lambda-status.sh`. |
| 2025-12-25 | **False success bug:** Extension showed success feedback even when Lambda returned HTTP 429/500. Network failures were masked. | Always check `response.ok` before showing success feedback. Never trust fetch completion alone. |
| 2025-12-28 | **Dead code trap:** `chrome.scripting.executeScript({ func: myFunc })` serializes function from CURRENT scope—does NOT load external files. `overlay.js` existed but was never executed because `showOverlay` was defined in service-worker.js. | When using `executeScript`, verify which file contains the function. Use `files: ['overlay.js']` to actually load external scripts. |
| 2025-12-28 | **file:// URLs can't be allowlisted:** `popup.js` returns null domain for file:// URLs, disabling the toggle. Can't test extension on local HTML files via popup. | Use DevTools console injection for XSS testing on allowlisted sites, or load test files via local server. |
| 2025-12-31 | **AWS_REGION is reserved:** Lambda rejects `AWS_REGION` as an environment variable—it's set automatically by the runtime. | Never set `AWS_REGION` in deploy.sh or Lambda config. Use `AWS_DEFAULT_REGION` if needed, or rely on boto3 auto-detection. |
| 2025-12-31 | **Bedrock model compatibility:** Claude 3.5 Sonnet v2 (`anthropic.claude-3-5-sonnet-20241022-v2:0`) requires inference profile for on-demand. Older models work directly. | Use `anthropic.claude-3-sonnet-20240229-v1:0` for on-demand invocation without inference profile setup. |
| 2025-12-31 | **Bedrock streaming permission:** `bedrock:InvokeModel` alone is insufficient for streaming responses. | Add `bedrock:InvokeModelWithResponseStream` to IAM policy for any streaming Bedrock calls. |
| 2026-01-01 | **Developed code on main branch.** Wrote `manifest.firefox.json` and `build_release.py` directly on main instead of creating a worktree first. Had to stash/move files to fix. | **Pre-Code Checklist:** Before writing ANY code file: (1) LLD committed to main, (2) Verify in worktree (`git worktree list`), (3) Branch name matches issue. |
| 2026-01-01 | **Tried to move docs with code.** When fixing the above, almost moved LLD docs to worktree instead of committing them to main first. Confused "docs before code" with "docs with code". | **Separation rule:** Docs commit to main FIRST. Then create worktree. Then write code in worktree. These are three distinct steps. |
| 2026-01-01 | **Created GitHub issue on wrong repo.** Used `gh issue create` without `--repo` flag. Issue #15992 was created on anthropics/claude-code instead of martymcenroe/Aletheia. | **Always** use `--repo martymcenroe/Aletheia` explicitly with `gh` commands. Never rely on default repo inference. |
