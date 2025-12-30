```markdown
# 0011 - Environment Cleanup Checklist

## Purpose
Comprehensive checklist to ensure development environment is clean before starting new work or taking extended breaks. Prevents orphaned branches, stray worktrees, unclosed issues, and unexpected costs.

## When to Use
- **Before starting new feature work** (Issue #N)
- **After completing a feature** (Issue #N closed)
- **Before taking a break** (weekend, vacation, project pause)
- **When environment feels "messy"** (gut check)

---

## Cleanup Checklist

### 1. Git Branch & Worktree Hygiene

#### 1.1 CRITICAL: Worktree Safety Protocol
**STOP and READ:** If you are using Git Worktrees, you **MUST** return to the `main` folder before merging or cleaning up.

**Action:** Return to Main Control Tower
```bash
cd /c/Users/mcwiz/Projects/Aletheia

```

#### 1.2 Check Worktrees

```bash
git worktree list

```

**Expected:** Only `main`.
**Risk:** If you see other worktrees, ensure no uncommitted work exists inside them before deletion.

**Action:** Remove stale worktrees

```bash
# 1. Check for uncommitted work inside the worktree
git -C ../Aletheia-{IssueNumber} status

# 2. If clean, remove the worktree
git worktree remove ../Aletheia-{IssueNumber}

```

#### 1.3 Check Local Branches

```bash
git branch -vv

```

**Expected:** Only `main` and active feature branches.

**Action:** Delete merged/abandoned branches

```bash
# Delete local branch (if already merged to main)
git branch -d {branch-name}

# Force delete (if not merged but work is abandoned/saved elsewhere)
git branch -D {branch-name}

```

#### 1.4 Check Remote Branches (The "Ghost" Check)

Local Git often lists remote branches that were already deleted on GitHub. We must prune the list first to avoid "remote ref does not exist" errors.

```bash
# 1. Update local cache and remove "ghost" branches
git fetch --prune origin

# 2. View TRUE list of remote branches
git branch -r

```

**Expected:** Only `origin/main` and active feature branches.

**Action:** Delete stale remote branches

```bash
git push origin --delete {branch-name}

```

---

### 2. GitHub Issue & PR Hygiene

#### 2.1 Check Open PRs

```bash
gh pr list --state open

```

**Action:**

* **Merge:** `gh pr merge {N} --squash --delete-branch` (RUN FROM MAIN FOLDER ONLY)
* **Close:** `gh pr close {N} --comment "Reason"`

#### 2.2 Check Open Issues (Verification Step)

Merging a PR does not always automatically close the issue, especially if the "Fixes #N" keyword was missing or the merge script crashed.

```bash
gh issue list --state open

```

**Review each issue:**

* [ ] **Is the work done?** → Close it immediately.
```bash
gh issue close {N} --comment "Fixed via PR #{PR_Number}"

```


* [ ] **Is it blocked?** → Add "blocked" label.
* [ ] **Is it obsolete?** → Close as "not planned".

---

### 3. Cost Control Verification

#### 3.1 AWS Lambda Concurrency

```bash
# Use repo scripts for reliable output
./tools/aws/lambda-status.sh

```

**Expected:** `✗ Lambda OFF (concurrency=0)`

**Action if ON:**

```bash
./tools/aws/lambda-off.sh
./tools/aws/lambda-status.sh  # Verify it's off

```

---

### 4. File System Cleanup

#### 4.1 Check Git Status

```bash
git status

```

**Expected:** "nothing to commit, working tree clean"

#### 4.2 Check for Temporary Files

```bash
# Find temporary files
ls -la | grep -E "(temp|tmp|\.bak|\.old|debug|test-)"

```

**Action:** Delete temp files not needed.

---

### 5. Browser Extension Cleanup

#### 5.1 Extension Installation Status

**Chrome:** `chrome://extensions/`

1. **Reload Extension:** Ensure you are running the latest code from `main`.
2. **Verify Version:** Check that the version number matches `manifest.json`.

---

### 6. Final Verification Checklist

Before considering environment "clean", verify ALL of these:

* [ ] `git worktree list` shows **only** `main`.
* [ ] `git branch -vv` shows **only** `main` (and active features).
* [ ] `git branch -r` shows **only** `origin/main` (and active features).
* [ ] `gh issue list` shows **no** issues that are actually completed.
* [ ] `./tools/aws/lambda-status.sh` shows OFF.
* [ ] `git status` is clean.

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

# 4. Check Issues
gh issue list --state open

```
