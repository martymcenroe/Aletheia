# 0009 - Session Cleanup Protocol

A streamlined checklist for ending sessions cleanly. Three modes available based on scope.

## How to Invoke

```
/cleanup           # Normal mode (default)
/cleanup --quick   # Quick mode
/cleanup --full    # Full mode
```

| Mode | Time | Use Case |
|------|------|----------|
| **Quick** | ~2 min | End of chat, minimal changes made |
| **Normal** | ~5 min | Standard session end (default) |
| **Full** | ~12 min | Feature complete, before breaks, environment feels messy |

## Philosophy

> "Leave the campsite cleaner than you found it."

A proper cleanup takes 2-12 minutes but saves 30+ minutes of confusion in the next session.

### Core Principles

1. **Parallel Execution** - Run independent commands simultaneously
2. **Single Commit** - ONE commit at the end, not per-step
3. **Progressive Enhancement** - Quick ⊂ Normal ⊂ Full
4. **Fast-Fail** - Check critical state early (Lambda, branches)

---

## Execution Model

The `/cleanup` command delegates to **Sonnet** for cost efficiency (~80% cheaper than Opus). Results return to your main session.

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: PARALLEL INFORMATION GATHERING                        │
│ (All read-only, run simultaneously)                            │
├─────────────────────────────────────────────────────────────────┤
│ Quick:   status, branch --list, gh pr list                     │
│ Normal:  + stash list, fetch --prune, gh issue list            │
│ Full:    + worktree list, branch -vv, branch -r, lambda-status │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: CONDITIONAL FIXES (Sequential, only if needed)        │
├─────────────────────────────────────────────────────────────────┤
│ Normal:  Regenerate 6000-open-issues.md                        │
│ Full:    + Lambda off, stale branch/worktree cleanup           │
│          + Inventory audit, Wiki check                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: SESSION LOG                                           │
│ Append entry via tools/append_session_log.py                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 4: SINGLE COMMIT & PUSH                                  │
│ git add → git commit → git push (ONE commit total)             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 5: PARALLEL VERIFICATION                                 │
│ Confirm clean state                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Mode Details

### Quick Mode (~2 min)

**When to use:** End of chat with minimal or no file changes.

**Phase 1 - Parallel Reads (3 calls):**
```bash
git -C /c/Users/mcwiz/Projects/Aletheia status
git -C /c/Users/mcwiz/Projects/Aletheia branch --list
gh pr list --state open --repo martymcenroe/Aletheia
```

**Phase 3 - Session Log:**
```bash
poetry run python /c/Users/mcwiz/Projects/Aletheia/tools/append_session_log.py \
    --model "Claude Sonnet 4" \
    --summary "Quick cleanup" \
    --created "None" \
    --closed "None" \
    --next "Per user direction"
```

**Phase 4 - Commit & Push:**
```bash
git -C /c/Users/mcwiz/Projects/Aletheia add docs/session-logs/
git -C /c/Users/mcwiz/Projects/Aletheia commit -m "docs: quick cleanup YYYY-MM-DD"
git -C /c/Users/mcwiz/Projects/Aletheia push
```

**Phase 5 - Verify:**
```bash
git -C /c/Users/mcwiz/Projects/Aletheia status
```

---

### Normal Mode (~5 min) - DEFAULT

**When to use:** Standard session ending.

**Phase 1 - Parallel Reads (6 calls):**
```bash
git -C /c/Users/mcwiz/Projects/Aletheia status
git -C /c/Users/mcwiz/Projects/Aletheia branch --list
git -C /c/Users/mcwiz/Projects/Aletheia stash list
git -C /c/Users/mcwiz/Projects/Aletheia fetch --prune
gh pr list --state open --repo martymcenroe/Aletheia
gh issue list --state open --repo martymcenroe/Aletheia
```

**Phase 2 - Doc Sync:**
```bash
poetry run python /c/Users/mcwiz/Projects/Aletheia/tools/print/print_most_recent_open_issues.py
git -C /c/Users/mcwiz/Projects/Aletheia add docs/6000-open-issues.md
```

**Phase 3 - Session Log:**
```bash
poetry run python /c/Users/mcwiz/Projects/Aletheia/tools/append_session_log.py \
    --model "Claude Sonnet 4" \
    --summary "Session summary here" \
    --created "None" \
    --closed "None" \
    --next "Per user direction"
```

**Phase 4 - Commit & Push:**
```bash
git -C /c/Users/mcwiz/Projects/Aletheia add docs/session-logs/
git -C /c/Users/mcwiz/Projects/Aletheia add docs/6000-open-issues.md
git -C /c/Users/mcwiz/Projects/Aletheia commit -m "docs: normal cleanup YYYY-MM-DD"
git -C /c/Users/mcwiz/Projects/Aletheia push
```

**Phase 5 - Verify (2 parallel calls):**
```bash
git -C /c/Users/mcwiz/Projects/Aletheia status
gh pr list --state open --repo martymcenroe/Aletheia
```

---

### Full Mode (~12 min)

**When to use:** Feature complete, before breaks, environment feels messy.

**Phase 1 - Parallel Reads (10 calls):**
```bash
git -C /c/Users/mcwiz/Projects/Aletheia status
git -C /c/Users/mcwiz/Projects/Aletheia branch --list
git -C /c/Users/mcwiz/Projects/Aletheia stash list
git -C /c/Users/mcwiz/Projects/Aletheia fetch --prune
git -C /c/Users/mcwiz/Projects/Aletheia worktree list
git -C /c/Users/mcwiz/Projects/Aletheia branch -vv
git -C /c/Users/mcwiz/Projects/Aletheia branch -r
gh pr list --state open --repo martymcenroe/Aletheia
gh issue list --state open --repo martymcenroe/Aletheia
/c/Users/mcwiz/Projects/Aletheia/tools/aws/lambda-status.sh
```

**Phase 2 - Analysis & Fixes:**

1. **Branch Check** - Flag any branch other than main
2. **Worktree Check** - Remove stale worktrees
3. **Lambda Check** - Turn off if ON:
   ```bash
   /c/Users/mcwiz/Projects/Aletheia/tools/aws/lambda-off.sh
   ```
4. **Stash Check** - Document any stash entries
5. **Doc Sync** - Regenerate 6000-open-issues.md
6. **Inventory Audit** - Glob check against 0003-file-inventory.md
7. **Plan Check** - Update 0000a-IMMEDIATE-PLAN.md if needed
8. **Wiki Check** - If user-facing changes, check wiki alignment (0817)

**Phase 3 - Session Log:**
```bash
poetry run python /c/Users/mcwiz/Projects/Aletheia/tools/append_session_log.py \
    --model "Claude Sonnet 4" \
    --summary "Full cleanup - detailed summary" \
    --created "#XX" \
    --closed "#YY" \
    --next "Next steps"
```

**Phase 4 - Commit & Push:**
```bash
git -C /c/Users/mcwiz/Projects/Aletheia add docs/session-logs/
git -C /c/Users/mcwiz/Projects/Aletheia add docs/6000-open-issues.md
git -C /c/Users/mcwiz/Projects/Aletheia add docs/0003-file-inventory.md
git -C /c/Users/mcwiz/Projects/Aletheia add docs/0000a-IMMEDIATE-PLAN.md
git -C /c/Users/mcwiz/Projects/Aletheia add docs/9000-lessons-learned.md
git -C /c/Users/mcwiz/Projects/Aletheia commit -m "docs: full cleanup YYYY-MM-DD"
git -C /c/Users/mcwiz/Projects/Aletheia push
```

**Phase 5 - Verify (5 parallel calls):**
```bash
git -C /c/Users/mcwiz/Projects/Aletheia status
git -C /c/Users/mcwiz/Projects/Aletheia worktree list
git -C /c/Users/mcwiz/Projects/Aletheia branch -r
gh pr list --state open --repo martymcenroe/Aletheia
/c/Users/mcwiz/Projects/Aletheia/tools/aws/lambda-status.sh
```

**Human Reminder:**
- Chrome: `chrome://extensions/` → Reload extension
- Firefox: `about:debugging` → Reload extension

---

## Expected Output

The cleanup returns a summary table:

| Check | Status |
|-------|--------|
| Git Status | ✅ Clean / ⚠️ {details} |
| Open PRs | ✅ 0 / ⚠️ {count} open |
| Open Issues | {count} |
| Branches | ✅ Only main / ⚠️ {list} |
| Worktrees | ✅ Only main / ⚠️ {list} |
| Lambda | ✅ OFF / ⚠️ ON |
| Stashes | ✅ None / ⚠️ {count} |
| Commit | ✅ Pushed / ❌ Failed |

---

## Unexpected Conditions

Report to human if any of these occur:

| Condition | Message |
|-----------|---------|
| Branch exists without worktree | `⚠️ UNEXPECTED: Branch {name} exists` |
| Issue should be closed but isn't | `⚠️ UNEXPECTED: Issue #{N} appears done` |
| Lambda still ON after off command | `⚠️ UNEXPECTED: Lambda still ON` |
| Uncommitted work in worktree | `⚠️ UNEXPECTED: Uncommitted changes` |
| File not in inventory | `⚠️ DRIFT: File {path} not in 0003` |

---

## Anti-Patterns

| Don't | Do Instead |
|:------|:-----------|
| **Commit after each step** | **Stage with `git add`, ONE commit at end** |
| **Run commands sequentially** | **Run independent commands in parallel** |
| Close laptop mid-conversation | Complete the turn, write session-log |
| Leave feature branch checked out | Return to main |
| Skip session-log "just this once" | It's 2 minutes, do it |
| Leave stash entries unexplained | Document or drop them |

---

## Rules

- Use absolute paths and `git -C` patterns (no cd && chaining)
- Use `--repo martymcenroe/Aletheia` for all gh commands
- Never modify `.claude/settings.local.json` during cleanup
- Never use forbidden commands (git reset, git push --force, etc.)
