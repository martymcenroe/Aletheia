# 0011 - Environment Cleanup Checklist

## Purpose
Comprehensive checklist to ensure development environment is clean before starting new work or taking extended breaks. Prevents orphaned branches, stray worktrees, unclosed issues, and unexpected costs.

## When to Use
- **Before starting new feature work** (Issue #N)
- **After completing a feature** (Issue #N closed)
- **Before taking a break** (weekend, vacation, project pause)
- **When environment feels "messy"** (gut check)
- **When 0009 (Session Closeout) instructs you to run this**

---

## Agent vs Human Actions

| Symbol | Meaning |
|--------|---------|
| 🤖 | Agent can/should do this automatically |
| 👤 | Human must do this (agent cannot) |
| ⚠️ | Unexpected condition - report to human |

---

## Pre-Cleanup: Session Start Reminder

**If you're about to test Lambda functionality:**
```bash
🤖 ./tools/aws/lambda-on.sh
🤖 ./tools/aws/lambda-status.sh  # Verify: ✓ Lambda ON
```

---

## Cleanup Checklist

### 1. Git Branch & Worktree Hygiene

#### 1.1 CRITICAL: Worktree Safety Protocol
**STOP and READ:** You **MUST** use Git Worktrees for feature work, not direct branches.

**Action:** Return to Main Control Tower
```bash
🤖 cd /c/Users/mcwiz/Projects/Aletheia
```

#### 1.2 Branch Without Worktree Detection

**Run this check FIRST:**
```bash
🤖 git branch --list | grep -v "^\* main$" | grep -v "^  main$"
```

**Expected:** Empty (no output).

**⚠️ FAILURE FLAG:** If branches exist that aren't associated with worktrees:
```
⚠️ UNEXPECTED: Detected branch without worktree: {branch-name}
   This violates CLAUDE.md workflow rules.
   Investigate: Was checkout -b used instead of worktree add?
```

**Agent Action:** Report this to human before proceeding.

#### 1.3 Check Worktrees

```bash
🤖 git worktree list
```

**Expected:** Only the main worktree.
**Risk:** If you see other worktrees, ensure no uncommitted work exists inside them before deletion.

**Action:** Remove stale worktrees
```bash
# 1. Check for uncommitted work inside the worktree
🤖 git -C ../Aletheia-{IssueNumber} status

# 2. If clean, remove the worktree
🤖 git worktree remove ../Aletheia-{IssueNumber}
```

#### 1.4 Check Local Branches

```bash
🤖 git branch -vv
```

**Expected:** Only `main`.

**Action:** Delete merged/abandoned branches
```bash
# Delete local branch (if already merged to main)
🤖 git branch -d {branch-name}

# Force delete (if not merged but work is abandoned/saved elsewhere)
🤖 git branch -D {branch-name}
```

#### 1.5 Check Remote Branches (The "Ghost" Check)

Local Git often lists remote branches that were already deleted on GitHub. We must prune the list first.

```bash
# 1. Update local cache and remove "ghost" branches
🤖 git fetch --prune origin

# 2. View TRUE list of remote branches
🤖 git branch -r
```

**Expected:** Only `origin/main`.

**Action:** Delete stale remote branches
```bash
🤖 git push origin --delete {branch-name}
```

---

### 2. GitHub Issue & PR Hygiene

#### 2.1 Check Open PRs

```bash
🤖 gh pr list --state open
```

**Action:**
* **Merge:** `gh pr merge {N} --merge --delete-branch` (RUN FROM MAIN FOLDER ONLY)
* **Close:** `gh pr close {N} --comment "Reason"`

#### 2.2 Check Open Issues (Verification Step)

Merging a PR does not always automatically close the issue, especially if the "Fixes #N" keyword was missing or the merge script crashed.

```bash
🤖 gh issue list --state open
```

**Review each issue:**
* [ ] **Is the work done?** → Close it immediately.
```bash
🤖 gh issue close {N} --comment "Fixed via PR #{PR_Number}"
```
* [ ] **Is it blocked?** → Add "blocked" label.
* [ ] **Is it obsolete?** → Close as "not planned".

**⚠️ FAILURE FLAG:** If you have evidence you tried to close an issue but it's still open:
```
⚠️ UNEXPECTED: Issue #{N} should be closed but is still open.
   Evidence: Commit message said "close #{N}" or PR merged.
   Investigate: Check GitHub for merge issues or keyword problems.
```

---

### 3. Cost Control Verification

#### 3.1 AWS Lambda Concurrency

```bash
# Use repo scripts for reliable output
🤖 ./tools/aws/lambda-status.sh
```

**Expected:** `✗ Lambda OFF (concurrency=0)`

**Action if ON:**
```bash
🤖 ./tools/aws/lambda-off.sh
🤖 ./tools/aws/lambda-status.sh  # Verify it's off
```

---

### 4. File System Cleanup

#### 4.1 Check Git Status

```bash
🤖 git status
```

**Expected:** "nothing to commit, working tree clean"

#### 4.2 Check for Temporary Files

```bash
🤖 ls -la | grep -E "(temp|tmp|\.bak|\.old|debug|test-)"
```

**Action:** Delete temp files not needed.

---

### 5. Documentation Updates

#### 5.1 Regenerate Open Issues List

**Always run (do not print output):**
```bash
🤖 python tools/print/print_most_recent_open_issues.py > docs/6000-open-issues.md
🤖 git add docs/6000-open-issues.md
🤖 git commit -m "docs: regenerate 6000-open-issues.md" --allow-empty
🤖 git push
```

#### 5.2 Permission Consolidation Note

If new permissions were granted during the session, note in session-log:
- What permissions were added to `.claude/settings.local.json`
- Why they were needed
- Consider if they should be broader patterns

---

### 6. IMMEDIATE-PLAN Verification

**🤖 CRITICAL:** Do not trust issue status—verify actual state.

```bash
🤖 # Read the current plan
cat IMMEDIATE-PLAN.md
```

**Verification Steps:**
1. For each "pending" item in the plan, check if the code/files actually exist
2. For each "complete" item, verify the issue is actually closed
3. If reality differs from the plan, the plan is wrong—not reality

**⚠️ FAILURE FLAGS:**
- Plan says pending, but code exists → Close the issue, update plan
- Plan says complete, but issue is open → Close the issue
- Plan references obsolete issues → Rewrite the plan

**Action:** Rewrite `IMMEDIATE-PLAN.md` to reflect:
- Current reality (what's actually done)
- Nearest-term objective (what's next on Critical Path)
- Simplified scope (remove completed items, focus on next step)

```bash
🤖 # After updating, commit the plan
git add IMMEDIATE-PLAN.md
git commit -m "docs: update IMMEDIATE-PLAN to reflect current state"
git push
```

---

### 7. Session Log Entry

**🤖 REQUIRED:** Write session log entry before ending.

```bash
🤖 powershell.exe -Command "Get-Date -Format 'yyyy-MM-dd HH:mm'"
```

Append entry to `docs/session-logs/Week-starting-YYYY-MM-DD.md` using template from `docs/0100-TEMPLATE-GUIDE.md`.

**Include in session log:**
- Summary of work completed
- Issues created/closed
- Any permission changes made
- State on exit (branch, last commit, next steps)

---

### 8. Browser Extension Cleanup

#### 8.1 Extension Installation Status (👤 Human Only)

**Chrome:** `chrome://extensions/`

1. 👤 **Reload Extension:** Ensure you are running the latest code from `main`.
2. 👤 **Verify Version:** Check that the version number matches `manifest.json`.

*Agent cannot access browser - human must verify.*

---

### 9. Final Verification Checklist

Before considering environment "clean", verify ALL of these:

```bash
🤖 # Run all checks
git worktree list              # Should show only main
git branch -vv                 # Should show only main
git branch -r                  # Should show only origin/main
gh pr list --state open        # Should be empty
gh issue list --state open     # Review - none should be "done but unclosed"
./tools/aws/lambda-status.sh   # Should show OFF
git status                     # Should be clean
```

**⚠️ Report any unexpected conditions to human before proceeding.**

---

## Unexpected Condition Summary

Report to human if any of these occur:

| Condition | Message |
|-----------|---------|
| Branch exists without worktree | `⚠️ UNEXPECTED: Detected branch without worktree: {name}` |
| Issue should be closed but isn't | `⚠️ UNEXPECTED: Issue #{N} should be closed but is still open` |
| PR merge failed silently | `⚠️ UNEXPECTED: PR #{N} merge may have failed - verify on GitHub` |
| Lambda still ON after off command | `⚠️ UNEXPECTED: Lambda still showing ON after lambda-off.sh` |
| Uncommitted work in worktree | `⚠️ UNEXPECTED: Uncommitted changes in ../Aletheia-{N}` |

---

## Quick Command Summary

```bash
# 1. Return to Main
cd /c/Users/mcwiz/Projects/Aletheia

# 2. Prune Ghosts & Check Remotes
git fetch --prune origin
git branch -r

# 3. Check Worktrees & Local Branches
git worktree list
git branch -vv

# 4. Check for branch-without-worktree violation
git branch --list | grep -v "^\* main$" | grep -v "^  main$"

# 5. Check Issues & PRs
gh issue list --state open
gh pr list --state open

# 6. Regenerate open issues
python tools/print/print_most_recent_open_issues.py > docs/6000-open-issues.md

# 7. Verify IMMEDIATE-PLAN (DO NOT TRUST - VERIFY!)
cat IMMEDIATE-PLAN.md
# Check each "pending" item - does the code exist?
# Check each "complete" item - is the issue closed?
# Rewrite if reality differs from plan

# 8. Turn off Lambda
./tools/aws/lambda-off.sh

# 9. Write session log
powershell.exe -Command "Get-Date -Format 'yyyy-MM-dd HH:mm'"
```
