# 0011 - Environment Cleanup Checklist

## Purpose
Comprehensive checklist to ensure development environment is clean before starting new work or taking extended breaks. Prevents orphaned branches, stray worktrees, unclosed issues, and unexpected costs.

## When to Use
- **Before starting new feature work** (Issue #N)
- **After completing a feature** (Issue #N closed)
- **Before taking a break** (weekend, vacation, project pause)
- **After debugging sessions** (cleanup debug artifacts)
- **When environment feels "messy"** (gut check)

---

## Cleanup Checklist

### 1. Git Branch Hygiene

#### 1.1 Check Local Branches
```bash
cd /c/Users/mcwiz/Projects/Aletheia
git branch --list
```

**Expected:** Only `main` and active feature branches (ones you're actually working on)

**Action:** Delete merged/abandoned branches
```bash
# Delete local branch (if already merged to main)
git branch -d {branch-name}

# Force delete (if not merged but work is done/abandoned)
git branch -D {branch-name}
```

#### 1.2 Check Remote Branches
```bash
git branch -r
```

**Expected:** Only `origin/main` and active feature branches with open PRs

**Action:** Delete stale remote branches
```bash
# Delete remote branch
git push origin --delete {branch-name}
```

#### 1.3 Sync Remote Branch List
```bash
# Prune deleted remote branches from local tracking
git fetch --prune
git branch -r
```

#### 1.4 Check Worktrees
```bash
git worktree list
```

**Expected:** Only worktrees for active branches you're currently working on

**Action:** Remove stale worktrees
```bash
git worktree remove /c/Users/mcwiz/Projects/{ProjectName}-{IssueNumber}
```

**Note:** After removing worktree, also delete the local branch (see 1.1)

---

### 2. GitHub Issue & PR Hygiene

#### 2.1 Check Open Issues
```bash
gh issue list --state open
```

**Review each issue:**
- [ ] Is work complete? → Close it: `gh issue close {N} --comment "Reason"`
- [ ] Is it blocked? → Add "blocked" label and comment why
- [ ] Is it obsolete? → Close as "not planned": `gh issue close {N} --reason "not planned"`
- [ ] Is it actually open work? → Leave open

#### 2.2 Check Open PRs
```bash
gh pr list --state open
```

**Review each PR:**
- [ ] Is it ready to merge? → Merge it: `gh pr merge {N} --squash --delete-branch`
- [ ] Has merge conflicts? → Resolve or close and recreate
- [ ] Is it obsolete? → Close it: `gh pr close {N} --comment "Reason"`
- [ ] Still in progress? → Leave open

#### 2.3 Check Closed Issues Without PRs
```bash
gh issue list --state closed --limit 10
```

**Verify:** Recent closed issues have corresponding merged PRs or direct commits to main

---

### 3. Cost Control Verification

#### 3.1 AWS Lambda Concurrency
```bash
aws_status
```

**Expected:** `reservedConcurrentExecutions: 0` (Lambda OFF)

**Action if ON:**
```bash
aws_off
aws_status  # Verify it's off
```

#### 3.2 Check for Running Services
```bash
# AWS Lambda invocations (should be 0 if Lambda is OFF)
aws logs tail /aws/lambda/AletheiaAgent --since 1h

# Check for any recent invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=AletheiaAgent \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum
```

**Expected:** No recent invocations if Lambda is OFF

---

### 4. File System Cleanup

#### 4.1 Check Git Status
```bash
cd /c/Users/mcwiz/Projects/Aletheia
git status
```

**Expected:** "nothing to commit, working tree clean"

**Action:** Handle uncommitted changes
```bash
# Option 1: Commit them
git add {files}
git commit -m "type: description"

# Option 2: Stash them (save for later)
git stash save "description of changes"

# Option 3: Discard them (if experimental/unwanted)
git restore {file}
git clean -fd  # Remove untracked files (USE WITH CAUTION)
```

#### 4.2 Check for Temporary Files
```bash
# Find temporary files
ls -la | grep -E "(temp|tmp|\.bak|\.old|debug|test-)"

# Common temp files to check:
ls -la *.bak 2>/dev/null
ls -la *.tmp 2>/dev/null
ls -la temp-* 2>/dev/null
ls -la debug-* 2>/dev/null
```

**Action:** Delete temp files not needed
```bash
rm {temp-file}
```

#### 4.3 Check for Gitignored Artifacts
```bash
# See what Git is ignoring
git status --ignored

# Common gitignored items to verify:
ls -la dist/ 2>/dev/null
ls -la __pycache__/ 2>/dev/null
ls -la *.pyc 2>/dev/null
ls -la .env 2>/dev/null
```

**Expected:** Build artifacts, cache files, secrets (all should be gitignored)

**Action:** Verify .gitignore is comprehensive, delete unnecessary artifacts

#### 4.4 Check for Large Files
```bash
# Find files larger than 1MB
find . -type f -size +1M -not -path "./.git/*" -exec ls -lh {} \;
```

**Expected:** Only intentional large files (images, test data, etc.)

**Action:** Remove unnecessary large files, consider Git LFS for legitimate large files

---

### 5. Browser Extension Cleanup

#### 5.1 Extension Installation Status
**Chrome:**
1. Open `chrome://extensions/`
2. Find "Aletheia" extension
3. Verify status: Enabled or Disabled?
4. Check version matches current main branch

**Action:** Remove old/test versions
- If multiple versions installed → Remove duplicates
- If testing complete → Remove test version

#### 5.2 Extension Storage/State
**Chrome DevTools:**
1. Right-click extension icon → "Inspect"
2. Go to "Application" tab → "Storage"
3. Check `chrome.storage.local`

**Expected:** Allowlist with intentional test sites (or empty)

**Action:** Clear test data if no longer needed
```javascript
// In extension DevTools console:
chrome.storage.local.clear();
```

---

### 6. Documentation Hygiene

#### 6.1 Session Logs Up to Date
```bash
# Check recent session logs
ls -lt docs/session-logs/ | head -5

# View last entry in current week's log
tail -20 docs/session-logs/Week-starting-*.md
```

**Expected:** Last entry reflects current session or most recent work

**Action:** Update session log if needed (see 0009-session-closeout-protocol.md)

#### 6.2 File Inventory Current
```bash
git diff docs/0003-file-inventory.md
```

**Expected:** No uncommitted changes (inventory is current)

**Action:** Update inventory if new files added/removed

#### 6.3 TODOs Resolved
```bash
# Search for TODO comments in code
grep -r "TODO" src/ extension/ --exclude-dir=node_modules

# Search for FIXME comments
grep -r "FIXME" src/ extension/ --exclude-dir=node_modules
```

**Expected:** All TODOs have corresponding issues or are removed

**Action:**
- Create issues for TODOs: `gh issue create --title "TODO: {description}"`
- Or remove TODO if obsolete

---

### 7. Test Artifacts Cleanup

#### 7.1 Test Files
```bash
# Check for test artifacts
ls -la test-*.html 2>/dev/null
ls -la test-*.md 2>/dev/null
ls -la *-test.* 2>/dev/null
```

**Expected:**
- Committed test files in proper location (e.g., `tests/`)
- Temporary test files cleaned up

**Action:**
- Move test files to proper location or delete if temporary
- Update .gitignore if needed

#### 7.2 Test Data
```bash
# Check for test databases, logs, screenshots
ls -la screenshots/ 2>/dev/null
ls -la logs/test-* 2>/dev/null
ls -la *.db 2>/dev/null
```

**Action:** Archive or delete test data no longer needed

---

### 8. Dependency & Environment Verification

#### 8.1 Python Dependencies
```bash
# Check for uncommitted dependency changes
git diff pyproject.toml poetry.lock requirements.txt 2>/dev/null
```

**Expected:** No uncommitted dependency changes

**Action:** Commit dependency updates or revert if experimental

#### 8.2 Node Dependencies (if applicable)
```bash
# Check for uncommitted package changes
git diff package.json package-lock.json 2>/dev/null
```

**Expected:** No uncommitted dependency changes

**Action:** Commit dependency updates or revert if experimental

---

### 9. Security Checks

#### 9.1 No Secrets in Code
```bash
# Check for potential secrets
grep -r "api[_-]key\|API[_-]KEY\|secret\|password\|token" . --exclude-dir=.git --exclude-dir=node_modules --exclude="*.md" | grep -v "# Check for"
```

**Expected:** No hardcoded secrets (all via environment variables or config)

**Action:** Move secrets to .env, verify .env is gitignored

#### 9.2 .env File Status
```bash
ls -la .env 2>/dev/null
git check-ignore .env
```

**Expected:**
- .env file exists (if using secrets)
- .env is gitignored

**Action:** Verify .env in .gitignore

---

### 10. Communication & Handoff

#### 10.1 Update README (if needed)
```bash
git diff README.md
```

**Expected:** README reflects current project state

**Action:** Update README if major changes occurred

#### 10.2 Create Handoff Notes
If taking extended break or handing off to another agent:

**Create:** `HANDOFF.md` with:
- Current state of work
- Open branches and their purpose
- Blockers or decisions needed
- Next steps

**Or:** Update session log with comprehensive "State on Exit" section

---

## Final Verification Checklist

Before considering environment "clean", verify ALL of these:

- [ ] `git worktree list` shows only active worktrees
- [ ] `git branch --list` shows only main + active feature branches
- [ ] `git branch -r` shows only main + active feature branches on remote
- [ ] `git status` shows "nothing to commit, working tree clean"
- [ ] `gh issue list --state open` shows only actual open work
- [ ] `gh pr list --state open` shows only active PRs
- [ ] `aws_status` shows Lambda is OFF (concurrency=0)
- [ ] No temporary files in project root
- [ ] Session log is up to date
- [ ] File inventory is current (0003-file-inventory.md)
- [ ] Browser extension state is clean (test data cleared)
- [ ] No uncommitted secrets or API keys
- [ ] All test artifacts archived or deleted

---

## Quick Command Summary

```bash
# Git cleanup
git worktree list
git branch --list
git branch -r
git fetch --prune
git status

# GitHub cleanup
gh issue list --state open
gh pr list --state open

# Cost control
aws_status
aws_off

# File system
ls -la | grep temp
git status --ignored

# Documentation
tail -20 docs/session-logs/Week-starting-*.md
git diff docs/0003-file-inventory.md

# Security
git check-ignore .env
grep -r "api[_-]key" . --exclude-dir=.git
```

---

## For LLMs: Cleanup Automation

When user says "clean up environment" or "environment cleanup":

1. **Run all verification commands** in sections 1-9
2. **Report findings** - what needs attention
3. **Ask for confirmation** before destructive actions (delete branches, remove files)
4. **Execute cleanup** with user approval
5. **Verify final state** using Final Verification Checklist
6. **Report summary** - what was cleaned, current state

**Never assume:**
- User wants branches deleted (ask first)
- Files are temporary (ask first)
- Issues should be closed (verify first)

**Always preserve:**
- Work in progress
- Uncommitted valuable changes
- Open issues that are actual work
- Branches with unmerged work

---

## Notes

**Philosophy:** Clean environment = clear mind. Keep only what you're actively working on. Everything else should be committed to main or documented in issues.

**Frequency:** Run quick check (sections 1-3) daily. Full cleanup weekly or before/after major features.

**Recovery:** Everything deleted from Git can be recovered (for ~30 days). Don't panic. Use `git reflog` to find lost commits.
