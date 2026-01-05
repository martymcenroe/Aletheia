---
description: Comprehensive 20-30 min cleanup (0009 Full Mode)
---

# Full Cleanup (0009 Full Mode)

Execute the comprehensive cleanup checklist from @docs/0009-session-closeout-protocol.md

This is **explicit approval** to execute all steps autonomously.

## Rules
- Use absolute paths and `git -C` patterns (no cd && chaining)
- Use `--repo martymcenroe/Aletheia` for all gh commands
- Never modify `.claude/settings.local.json` (HAL clause protection)
- Never use forbidden commands (git reset, git push --force, etc.)
- Report any unexpected conditions with `⚠️ UNEXPECTED:` prefix

## Steps

### F2. Branch Without Worktree Detection
```bash
git -C /c/Users/mcwiz/Projects/Aletheia branch --list
```
Expected: Only `* main`. **Agent:** Analyze output - flag any branch other than main.

### F3. Worktree Hygiene
```bash
git -C /c/Users/mcwiz/Projects/Aletheia worktree list
```
Expected: Only main worktree. Remove stale worktrees if found.

### F4. Branch Cleanup
```bash
git -C /c/Users/mcwiz/Projects/Aletheia branch -vv
git -C /c/Users/mcwiz/Projects/Aletheia fetch --prune origin
git -C /c/Users/mcwiz/Projects/Aletheia branch -r
```
Delete stale local and remote branches (except main).

### F5. GitHub Issue & PR Hygiene
```bash
gh pr list --state open --repo martymcenroe/Aletheia
gh issue list --state open --repo martymcenroe/Aletheia
```
Verify each open issue is truly in progress. Close any that are done.

### F6. Issue Completion Reports
For each issue closed this session, verify reports exist in `docs/reports/{IssueID}/`.

### F7. Cost Control Verification
```bash
/c/Users/mcwiz/Projects/Aletheia/tools/aws/lambda-status.sh
```
Expected: `Lambda OFF (concurrency=0)`. Turn off if ON.

### F8. File System Cleanup
```bash
git -C /c/Users/mcwiz/Projects/Aletheia status
ls -la /c/Users/mcwiz/Projects/Aletheia
```
**Agent:** Scan output for temp/tmp/.bak/.old/debug/test- files.

### F9. File Inventory Audit (0003)

Use the **Glob tool** (not bash) with patterns: `**/*.md`, `**/*.py`, `**/*.js`, `**/*.json`, `**/*.sh`. Exclude `.git/`, `node_modules/`, `.venv/`.

Compare against `docs/0003-file-inventory.md`. Flag drift.

### F10. Documentation Sync
```bash
poetry run python /c/Users/mcwiz/Projects/Aletheia/tools/print/print_most_recent_open_issues.py
git -C /c/Users/mcwiz/Projects/Aletheia add docs/6000-open-issues.md
git -C /c/Users/mcwiz/Projects/Aletheia commit -m "docs: regenerate 6000-open-issues.md" --allow-empty
git -C /c/Users/mcwiz/Projects/Aletheia push
```

### F10a. Wiki Alignment Check (if user-facing changes made)
Check if wiki needs updates per `docs/0817-audit-wiki-alignment.md`.

### F11. Session Log Entry
```bash
poetry run python /c/Users/mcwiz/Projects/Aletheia/tools/append_session_log.py \
    --model "Claude Opus 4.5" \
    --summary "SESSION_SUMMARY_HERE" \
    --created "#XX" \
    --closed "#YY" \
    --next "Next steps"
```
Then commit and push.

### F12. Browser Extension Cleanup
Remind human: `chrome://extensions/` - Reload extension, verify version.

### F13. Final Verification Checklist
```bash
git -C /c/Users/mcwiz/Projects/Aletheia worktree list
git -C /c/Users/mcwiz/Projects/Aletheia branch -vv
git -C /c/Users/mcwiz/Projects/Aletheia branch -r
gh pr list --state open --repo martymcenroe/Aletheia
gh issue list --state open --repo martymcenroe/Aletheia
/c/Users/mcwiz/Projects/Aletheia/tools/aws/lambda-status.sh
git -C /c/Users/mcwiz/Projects/Aletheia status
```

Report all results in a summary table with pass/fail status.
