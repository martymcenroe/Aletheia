# 0009 - Session Closeout Protocol

A checklist for ending sessions cleanly. Two modes available based on scope.

## How to Prompt

| Mode | When to Use | Prompt |
|------|-------------|--------|
| **Session** | Daily closeout, quick wrap-up | "Run session closeout" or "Run 0009 session mode" |
| **Full** | Feature complete, before breaks, environment feels messy | "Run full cleanup" or "Run 0009 full mode" |

## Philosophy
> "Leave the campsite cleaner than you found it."

A proper closeout takes 5-10 minutes (session) or 20-30 minutes (full) but saves 30+ minutes of confusion in the next session.

---

## Mode Selection Guide

**Use Session Mode when:**
- Ending a normal work session
- No features were completed
- Environment is known-clean

**Use Full Mode when:**
- You completed a feature (Issue #N closed)
- You're about to start new feature work
- Before a break (weekend, vacation, project pause)
- Environment feels messy or you're unsure of state
- You changed multiple files across multiple issues

---

## Agent vs Human Actions

| Symbol | Meaning |
|--------|---------|
| 🤖 | Agent can/should do this automatically |
| 👤 | Human must do this (agent cannot) |
| ⚠️ | Unexpected condition - report to human |

---

# SESSION MODE

Quick 5-10 minute closeout for routine session endings.

### S1. Git Hygiene (Quick)

```bash
🤖 git -C /c/Users/mcwiz/Projects/Aletheia checkout main && git -C /c/Users/mcwiz/Projects/Aletheia pull
🤖 git -C /c/Users/mcwiz/Projects/Aletheia status                    # Should be clean
🤖 git -C /c/Users/mcwiz/Projects/Aletheia stash list                # Document or drop
🤖 git -C /c/Users/mcwiz/Projects/Aletheia branch --list             # Only main should remain
🤖 git -C /c/Users/mcwiz/Projects/Aletheia fetch --prune
```

### S2. Issue & PR Audit

```bash
🤖 gh issue list --state open --repo martymcenroe/Aletheia    # Review - any completed?
🤖 gh pr list --state open --repo martymcenroe/Aletheia       # Should be empty
```

### S3. Documentation Sync

```bash
🤖 poetry run python /c/Users/mcwiz/Projects/Aletheia/tools/print/print_most_recent_open_issues.py
🤖 git -C /c/Users/mcwiz/Projects/Aletheia add docs/6000-open-issues.md
🤖 git -C /c/Users/mcwiz/Projects/Aletheia commit -m "docs: regenerate 6000-open-issues.md" --allow-empty
🤖 git -C /c/Users/mcwiz/Projects/Aletheia push
```

### S4. Session Log Entry

**Option A: Use append script (recommended - avoids token limits)**
```bash
🤖 poetry run python /c/Users/mcwiz/Projects/Aletheia/tools/append_session_log.py \
    --model "Claude Opus 4.5" \
    --summary "Brief description of session accomplishments" \
    --created "None" \
    --closed "None" \
    --next "Per user direction"
```

**Option B: Manual append (if script unavailable)**
```bash
🤖 powershell.exe -Command "Get-Date -Format 'yyyy-MM-dd HH:mm'"
```
Then append entry to `docs/session-logs/Week-starting-YYYY-MM-DD.md` (read with offset if file is large).

### S5. Final Verification

```bash
🤖 git status           # Clean
🤖 gh pr list           # Empty
```

**Session mode complete.** If any issues found, escalate to Full Mode.

---

# FULL MODE

Comprehensive 20-30 minute cleanup. Includes everything in Session Mode plus deeper checks.

### F1. Return to Main Control Tower

No `cd` needed - use `git -C` and absolute paths throughout.

### F2. Branch Without Worktree Detection

**Run this check FIRST:**
```bash
🤖 git -C /c/Users/mcwiz/Projects/Aletheia branch --list | grep -v "^\* main$" | grep -v "^  main$"
```

**Expected:** Empty (no output).

**⚠️ FAILURE FLAG:** If branches exist without worktrees:
```
⚠️ UNEXPECTED: Detected branch without worktree: {branch-name}
   This violates CLAUDE.md workflow rules.
```

### F3. Worktree Hygiene

```bash
🤖 git -C /c/Users/mcwiz/Projects/Aletheia worktree list
```

**Expected:** Only the main worktree.

**Action:** Remove stale worktrees
```bash
🤖 git -C /c/Users/mcwiz/Projects/Aletheia-{IssueNumber} status    # Check for uncommitted work
🤖 git -C /c/Users/mcwiz/Projects/Aletheia worktree remove /c/Users/mcwiz/Projects/Aletheia-{IssueNumber}
```

### F4. Branch Cleanup

```bash
🤖 git -C /c/Users/mcwiz/Projects/Aletheia branch -vv                # Check local branches
🤖 git -C /c/Users/mcwiz/Projects/Aletheia fetch --prune origin      # Remove ghost refs
🤖 git -C /c/Users/mcwiz/Projects/Aletheia branch -r                 # Should only show origin/main
```

**Action:** Delete stale branches
```bash
🤖 git -C /c/Users/mcwiz/Projects/Aletheia branch -d {branch-name}              # Local (if merged)
🤖 git -C /c/Users/mcwiz/Projects/Aletheia push origin --delete {branch-name}   # Remote
```

### F5. GitHub Issue & PR Hygiene

```bash
🤖 gh pr list --state open --repo martymcenroe/Aletheia
🤖 gh issue list --state open --repo martymcenroe/Aletheia
```

**For each open issue, verify:**
- [ ] Is the work done? → Close it: `gh issue close {N} --comment "Fixed via PR #{N}"`
- [ ] Is it blocked? → Add "blocked" label
- [ ] Is it obsolete? → Close as "not planned"

**⚠️ FAILURE FLAG:**
```
⚠️ UNEXPECTED: Issue #{N} should be closed but is still open.
```

### F6. Issue Completion Reports

**For each issue closed this session:**
1. Create directory `docs/reports/{IssueID}/`
2. Write `implementation-report.md` using template `docs/0103-TEMPLATE-implementation-report.md`
3. Write `test-report.md` using template `docs/0113-TEMPLATE-test-report.md`
4. Update `docs/0003-file-inventory.md` with new report files

**Exceptions:** Documentation-only and chore issues don't need reports.

### F7. Cost Control Verification

```bash
🤖 /c/Users/mcwiz/Projects/Aletheia/tools/aws/lambda-status.sh
```

**Expected:** `✗ Lambda OFF (concurrency=0)`

**Action if ON:**
```bash
🤖 /c/Users/mcwiz/Projects/Aletheia/tools/aws/lambda-off.sh
🤖 /c/Users/mcwiz/Projects/Aletheia/tools/aws/lambda-status.sh  # Verify
```

### F8. File System Cleanup

```bash
🤖 git -C /c/Users/mcwiz/Projects/Aletheia status                    # Should be clean
🤖 ls -la /c/Users/mcwiz/Projects/Aletheia | grep -E "(temp|tmp|\.bak|\.old|debug|test-)"
```

**Action:** Delete temp files not needed.

### F9. File Inventory Audit (0003)

**Step 1: Find files NOT in inventory**
```bash
🤖 find /c/Users/mcwiz/Projects/Aletheia -type f \( -name "*.md" -o -name "*.py" -o -name "*.js" -o -name "*.json" -o -name "*.sh" -o -name "*.html" -o -name "*.css" \) ! -path "*/.git/*" ! -path "*/node_modules/*" ! -path "*/.venv/*" | sort > /tmp/actual_files.txt
```

**Step 2:** Compare against `docs/0003-file-inventory.md`

**Step 3:** Verify closed issue statuses
- 🟠 In-Progress → Check if closed → Update to 🟢 Stable

**⚠️ FAILURE FLAGS:**
- `⚠️ DRIFT: File {path} not in 0003-file-inventory.md`
- `⚠️ DRIFT: 0003 lists {path} but file doesn't exist`

**Action:**
```bash
🤖 git -C /c/Users/mcwiz/Projects/Aletheia add docs/0003-file-inventory.md
🤖 git -C /c/Users/mcwiz/Projects/Aletheia commit -m "docs: inventory audit and update"
🤖 git -C /c/Users/mcwiz/Projects/Aletheia push
```

### F10. Documentation Sync

```bash
🤖 poetry run python /c/Users/mcwiz/Projects/Aletheia/tools/print/print_most_recent_open_issues.py
🤖 git -C /c/Users/mcwiz/Projects/Aletheia add docs/6000-open-issues.md
🤖 git -C /c/Users/mcwiz/Projects/Aletheia commit -m "docs: regenerate 6000-open-issues.md" --allow-empty
🤖 git -C /c/Users/mcwiz/Projects/Aletheia push
```

**Also check:**
- [ ] LLD status updated? ("Approved" → "Complete" for finished features)
- [ ] Lessons captured in `docs/9000-lessons-learned.md`?

### F10a. Wiki Alignment Check (0817)

**If any user-facing changes were made this session:**

```bash
🤖 git -C /c/Users/mcwiz/Projects/Aletheia-wiki pull origin master
```

**Review for staleness:**
- [ ] Privacy.md reflects current data handling?
- [ ] Features list current?
- [ ] Any "coming soon" items now shipped?

**If updates needed:**
```bash
🤖 # Edit relevant .md files
🤖 git -C /c/Users/mcwiz/Projects/Aletheia-wiki add -A && git -C /c/Users/mcwiz/Projects/Aletheia-wiki commit -m "docs: wiki alignment update" && git -C /c/Users/mcwiz/Projects/Aletheia-wiki push origin master
```

See `docs/0817-audit-wiki-alignment.md` for full audit procedure.

### F11. Session Log Entry

**Option A: Use append script (recommended - avoids token limits)**
```bash
🤖 poetry run python /c/Users/mcwiz/Projects/Aletheia/tools/append_session_log.py \
    --model "Claude Opus 4.5" \
    --summary "Brief description of session accomplishments" \
    --created "#XX, #YY" \
    --closed "#ZZ" \
    --next "Next steps for following session"
```

**Option B: Manual append (if script unavailable)**
```bash
🤖 powershell.exe -Command "Get-Date -Format 'yyyy-MM-dd HH:mm'"
```
Then append entry to `docs/session-logs/Week-starting-YYYY-MM-DD.md` (read with offset if file is large).

For Full Mode, consider adding Feature Work and Tooling sections manually after script appends the base template.

### F12. Browser Extension Cleanup (👤 Human Only)

**Chrome:** `chrome://extensions/`
1. 👤 Reload Extension to run latest code from `main`
2. 👤 Verify version matches `manifest.json`

### F13. Final Verification Checklist

```bash
🤖 git -C /c/Users/mcwiz/Projects/Aletheia worktree list              # Only main
🤖 git -C /c/Users/mcwiz/Projects/Aletheia branch -vv                 # Only main
🤖 git -C /c/Users/mcwiz/Projects/Aletheia branch -r                  # Only origin/main
🤖 gh pr list --state open --repo martymcenroe/Aletheia               # Empty
🤖 gh issue list --state open --repo martymcenroe/Aletheia            # Review - none "done but unclosed"
🤖 /c/Users/mcwiz/Projects/Aletheia/tools/aws/lambda-status.sh        # OFF
🤖 git -C /c/Users/mcwiz/Projects/Aletheia status                     # Clean
```

**⚠️ Report any unexpected conditions to human before proceeding.**

---

## Quick Command Summary

### Session Mode (Copy-Paste)
```bash
git -C /c/Users/mcwiz/Projects/Aletheia checkout main && git -C /c/Users/mcwiz/Projects/Aletheia pull
git -C /c/Users/mcwiz/Projects/Aletheia status && git -C /c/Users/mcwiz/Projects/Aletheia stash list && git -C /c/Users/mcwiz/Projects/Aletheia branch --list
git -C /c/Users/mcwiz/Projects/Aletheia fetch --prune
gh issue list --state open --repo martymcenroe/Aletheia && gh pr list --state open --repo martymcenroe/Aletheia
poetry run python /c/Users/mcwiz/Projects/Aletheia/tools/print/print_most_recent_open_issues.py
git -C /c/Users/mcwiz/Projects/Aletheia add docs/6000-open-issues.md && git -C /c/Users/mcwiz/Projects/Aletheia commit -m "docs: regenerate 6000-open-issues.md" --allow-empty && git -C /c/Users/mcwiz/Projects/Aletheia push
```

### Full Mode (Copy-Paste)
```bash
git -C /c/Users/mcwiz/Projects/Aletheia branch --list | grep -v "^\* main$" | grep -v "^  main$"
git -C /c/Users/mcwiz/Projects/Aletheia worktree list
git -C /c/Users/mcwiz/Projects/Aletheia branch -vv && git -C /c/Users/mcwiz/Projects/Aletheia fetch --prune origin && git -C /c/Users/mcwiz/Projects/Aletheia branch -r
gh pr list --state open --repo martymcenroe/Aletheia && gh issue list --state open --repo martymcenroe/Aletheia
/c/Users/mcwiz/Projects/Aletheia/tools/aws/lambda-status.sh
git -C /c/Users/mcwiz/Projects/Aletheia status
poetry run python /c/Users/mcwiz/Projects/Aletheia/tools/print/print_most_recent_open_issues.py
/c/Users/mcwiz/Projects/Aletheia/tools/aws/lambda-off.sh
```

---

## Unexpected Condition Summary

Report to human if any of these occur:

| Condition | Message |
|-----------|---------|
| Branch exists without worktree | `⚠️ UNEXPECTED: Detected branch without worktree: {name}` |
| Issue should be closed but isn't | `⚠️ UNEXPECTED: Issue #{N} should be closed but is still open` |
| PR merge failed silently | `⚠️ UNEXPECTED: PR #{N} merge may have failed` |
| Lambda still ON after off command | `⚠️ UNEXPECTED: Lambda still showing ON` |
| Uncommitted work in worktree | `⚠️ UNEXPECTED: Uncommitted changes in ../Aletheia-{N}` |
| File exists but not in inventory | `⚠️ DRIFT: File {path} not in 0003` |
| Inventory lists deleted file | `⚠️ DRIFT: 0003 lists {path} but doesn't exist` |

---

## Anti-Patterns

| Don't | Do Instead |
|:------|:-----------|
| Close laptop mid-conversation | Complete the turn, write session-log |
| Leave feature branch checked out | Return to main |
| Assume issues auto-closed | Verify with `gh issue view` |
| Skip session-log "just this once" | It's 2 minutes, do it |
| Leave stash entries unexplained | Document or drop them |
