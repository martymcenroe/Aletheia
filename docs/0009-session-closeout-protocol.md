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
🤖 cd /c/Users/mcwiz/Projects/Aletheia
🤖 git checkout main && git pull
🤖 git status                    # Should be clean
🤖 git stash list                # Document or drop
🤖 git branch --list             # Only main should remain
🤖 git fetch --prune
```

### S2. Issue & PR Audit

```bash
🤖 gh issue list --state open    # Review - any completed?
🤖 gh pr list --state open       # Should be empty
```

### S3. Documentation Sync

```bash
🤖 python tools/print/print_most_recent_open_issues.py > docs/6000-open-issues.md
🤖 git add docs/6000-open-issues.md
🤖 git commit -m "docs: regenerate 6000-open-issues.md" --allow-empty
🤖 git push
```

### S4. Session Log Entry

```bash
🤖 powershell.exe -Command "Get-Date -Format 'yyyy-MM-dd HH:mm'"
```

Append entry to `docs/session-logs/Week-starting-YYYY-MM-DD.md`:

```markdown
## YYYY-MM-DD HH:MM CT | Model Name

### Summary
One paragraph describing the session's main accomplishment.

### Issues
- Created: #XX, #YY
- Closed: #ZZ

### State on Exit
- Branch: main
- Last commit: <sha>
- Next: What the next session should pick up
```

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

```bash
🤖 cd /c/Users/mcwiz/Projects/Aletheia
```

### F2. Branch Without Worktree Detection

**Run this check FIRST:**
```bash
🤖 git branch --list | grep -v "^\* main$" | grep -v "^  main$"
```

**Expected:** Empty (no output).

**⚠️ FAILURE FLAG:** If branches exist without worktrees:
```
⚠️ UNEXPECTED: Detected branch without worktree: {branch-name}
   This violates CLAUDE.md workflow rules.
```

### F3. Worktree Hygiene

```bash
🤖 git worktree list
```

**Expected:** Only the main worktree.

**Action:** Remove stale worktrees
```bash
🤖 git -C ../Aletheia-{IssueNumber} status    # Check for uncommitted work
🤖 git worktree remove ../Aletheia-{IssueNumber}
```

### F4. Branch Cleanup

```bash
🤖 git branch -vv                # Check local branches
🤖 git fetch --prune origin      # Remove ghost refs
🤖 git branch -r                 # Should only show origin/main
```

**Action:** Delete stale branches
```bash
🤖 git branch -d {branch-name}              # Local (if merged)
🤖 git push origin --delete {branch-name}   # Remote
```

### F5. GitHub Issue & PR Hygiene

```bash
🤖 gh pr list --state open
🤖 gh issue list --state open
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
🤖 ./tools/aws/lambda-status.sh
```

**Expected:** `✗ Lambda OFF (concurrency=0)`

**Action if ON:**
```bash
🤖 ./tools/aws/lambda-off.sh
🤖 ./tools/aws/lambda-status.sh  # Verify
```

### F8. File System Cleanup

```bash
🤖 git status                    # Should be clean
🤖 ls -la | grep -E "(temp|tmp|\.bak|\.old|debug|test-)"
```

**Action:** Delete temp files not needed.

### F9. File Inventory Audit (0003)

**Step 1: Find files NOT in inventory**
```bash
🤖 find . -type f \( -name "*.md" -o -name "*.py" -o -name "*.js" -o -name "*.json" -o -name "*.sh" -o -name "*.html" -o -name "*.css" \) ! -path "./.git/*" ! -path "./node_modules/*" ! -path "./.venv/*" | sort > /tmp/actual_files.txt
```

**Step 2:** Compare against `docs/0003-file-inventory.md`

**Step 3:** Verify closed issue statuses
- 🟠 In-Progress → Check if closed → Update to 🟢 Stable

**⚠️ FAILURE FLAGS:**
- `⚠️ DRIFT: File {path} not in 0003-file-inventory.md`
- `⚠️ DRIFT: 0003 lists {path} but file doesn't exist`

**Action:**
```bash
🤖 git add docs/0003-file-inventory.md
🤖 git commit -m "docs: inventory audit and update"
🤖 git push
```

### F10. Documentation Sync

```bash
🤖 python tools/print/print_most_recent_open_issues.py > docs/6000-open-issues.md
🤖 git add docs/6000-open-issues.md
🤖 git commit -m "docs: regenerate 6000-open-issues.md" --allow-empty
🤖 git push
```

**Also check:**
- [ ] LLD status updated? ("Approved" → "Complete" for finished features)
- [ ] Lessons captured in `docs/9000-lessons-learned.md`?

### F10a. Wiki Alignment Check (0817)

**If any user-facing changes were made this session:**

```bash
🤖 cd /c/Users/mcwiz/Projects/Aletheia-wiki
🤖 git pull origin master
```

**Review for staleness:**
- [ ] Privacy.md reflects current data handling?
- [ ] Features list current?
- [ ] Any "coming soon" items now shipped?

**If updates needed:**
```bash
🤖 # Edit relevant .md files
🤖 git add -A && git commit -m "docs: wiki alignment update" && git push origin master
```

See `docs/0817-audit-wiki-alignment.md` for full audit procedure.

### F11. Session Log Entry

```bash
🤖 powershell.exe -Command "Get-Date -Format 'yyyy-MM-dd HH:mm'"
```

Append entry to `docs/session-logs/Week-starting-YYYY-MM-DD.md`:

```markdown
## YYYY-MM-DD HH:MM CT | Model Name

### Summary
One paragraph describing the session's main accomplishment.

### Feature Work
- Shipped features, implementations, bug fixes

### Tooling
- Documentation updates, template improvements, process refinements

### Issues
- Created: #XX, #YY
- Closed: #ZZ

### State on Exit
- Branch: main
- Last commit: <sha>
- Open PRs: 0
- Next: What the next session should pick up
```

### F12. Browser Extension Cleanup (👤 Human Only)

**Chrome:** `chrome://extensions/`
1. 👤 Reload Extension to run latest code from `main`
2. 👤 Verify version matches `manifest.json`

### F13. Final Verification Checklist

```bash
🤖 git worktree list              # Only main
🤖 git branch -vv                 # Only main
🤖 git branch -r                  # Only origin/main
🤖 gh pr list --state open        # Empty
🤖 gh issue list --state open     # Review - none "done but unclosed"
🤖 ./tools/aws/lambda-status.sh   # OFF
🤖 git status                     # Clean
```

**⚠️ Report any unexpected conditions to human before proceeding.**

---

## Quick Command Summary

### Session Mode (Copy-Paste)
```bash
cd /c/Users/mcwiz/Projects/Aletheia
git checkout main && git pull
git status && git stash list && git branch --list
git fetch --prune
gh issue list --state open && gh pr list --state open
python tools/print/print_most_recent_open_issues.py > docs/6000-open-issues.md
git add docs/6000-open-issues.md && git commit -m "docs: regenerate 6000-open-issues.md" --allow-empty && git push
```

### Full Mode (Copy-Paste)
```bash
cd /c/Users/mcwiz/Projects/Aletheia
git branch --list | grep -v "^\* main$" | grep -v "^  main$"
git worktree list
git branch -vv && git fetch --prune origin && git branch -r
gh pr list --state open && gh issue list --state open
./tools/aws/lambda-status.sh
git status
python tools/print/print_most_recent_open_issues.py > docs/6000-open-issues.md
./tools/aws/lambda-off.sh
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
