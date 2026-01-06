---
description: Session cleanup with quick/normal/full modes (project)
---

# Cleanup

**Mode:** Parse `$ARGUMENTS` for flags. Default is `--normal` if no flag provided.

| Flag | Mode | Time | Use Case |
|------|------|------|----------|
| `--quick` | Quick | ~2 min | End of chat, minimal changes |
| `--normal` | Normal | ~5 min | Standard session end (default) |
| `--full` | Full | ~12 min | Feature complete, before breaks |

## Execution

**IMPORTANT:** Use the **Task tool** with `model: sonnet` to execute the cleanup. This saves budget while keeping your main session on Opus.

Spawn a Task with `subagent_type: general-purpose` and `model: sonnet` with the following prompt (substitute MODE based on parsed arguments):

---

### Task Prompt for Sonnet Agent

```
You are executing a cleanup procedure for the Aletheia project.
Mode: [MODE: quick|normal|full]

## Rules
- Use absolute paths with git -C /c/Users/mcwiz/Projects/Aletheia
- Use --repo martymcenroe/Aletheia for all gh commands
- NO pipes (|) or chain operators (&&) - one command per Bash call
- Run independent commands in PARALLEL (multiple Bash calls in one message)
- ONE commit at the end - stage files as you go, commit once

## Phase 1: Information Gathering (ALL PARALLEL)

Run these commands simultaneously in a single message with multiple Bash tool calls:

**Quick mode (3 parallel calls):**
- git -C /c/Users/mcwiz/Projects/Aletheia status
- git -C /c/Users/mcwiz/Projects/Aletheia branch --list
- gh pr list --state open --repo martymcenroe/Aletheia

**Normal mode adds (6 parallel calls total):**
- git -C /c/Users/mcwiz/Projects/Aletheia stash list
- git -C /c/Users/mcwiz/Projects/Aletheia fetch --prune
- gh issue list --state open --repo martymcenroe/Aletheia

**Full mode adds (10 parallel calls total):**
- git -C /c/Users/mcwiz/Projects/Aletheia worktree list
- git -C /c/Users/mcwiz/Projects/Aletheia branch -vv
- git -C /c/Users/mcwiz/Projects/Aletheia branch -r
- /c/Users/mcwiz/Projects/Aletheia/tools/aws/lambda-status.sh

## Phase 2: Conditional Fixes

**Analyze Phase 1 results:**

1. **Branches** - Flag if any branch other than main exists:
   - Report: "⚠️ UNEXPECTED: Branch {name} exists without worktree"

2. **Worktrees** (Full only) - Flag if stale worktrees exist:
   - Report and offer to remove with: git -C /c/Users/mcwiz/Projects/Aletheia worktree remove {path}

3. **Lambda** (Full only) - If ON, turn off:
   - /c/Users/mcwiz/Projects/Aletheia/tools/aws/lambda-off.sh

4. **Open PRs** - Should be 0. Flag if any exist.

5. **Stashes** - Document any stash entries found.

**Normal and Full: Regenerate open issues**
```bash
poetry run python /c/Users/mcwiz/Projects/Aletheia/tools/print/print_most_recent_open_issues.py
```
Then stage (do NOT commit yet):
```bash
git -C /c/Users/mcwiz/Projects/Aletheia add docs/6000-open-issues.md
```

**Full mode only: Additional checks**
- Inventory audit: Use Glob tool with patterns **/*.py, **/*.js, **/*.md, **/*.sh
  Compare against docs/0003-file-inventory.md, flag drift
- Check if docs/0000a-IMMEDIATE-PLAN.md needs updates based on closed issues

## Phase 3: Session Log

Append session log entry:
```bash
poetry run python /c/Users/mcwiz/Projects/Aletheia/tools/append_session_log.py \
    --model "Claude Sonnet 4" \
    --summary "Cleanup ([MODE] mode)" \
    --created "None" \
    --closed "None" \
    --next "Per user direction"
```

If the script fails, manually append to the current week's session log file.

## Phase 4: Single Commit & Push

Stage all documentation changes:
```bash
git -C /c/Users/mcwiz/Projects/Aletheia add docs/session-logs/
git -C /c/Users/mcwiz/Projects/Aletheia add docs/6000-open-issues.md
```

For Full mode, also stage:
```bash
git -C /c/Users/mcwiz/Projects/Aletheia add docs/0003-file-inventory.md
git -C /c/Users/mcwiz/Projects/Aletheia add docs/0000a-IMMEDIATE-PLAN.md
git -C /c/Users/mcwiz/Projects/Aletheia add docs/9000-lessons-learned.md
```

Review staged changes:
```bash
git -C /c/Users/mcwiz/Projects/Aletheia status
```

Commit (ONE commit for everything):
```bash
git -C /c/Users/mcwiz/Projects/Aletheia commit -m "docs: [MODE] cleanup $(powershell.exe -Command "Get-Date -Format 'yyyy-MM-dd'")"
```

Push:
```bash
git -C /c/Users/mcwiz/Projects/Aletheia push
```

## Phase 5: Verification (PARALLEL)

Run these simultaneously:
```bash
git -C /c/Users/mcwiz/Projects/Aletheia status
gh pr list --state open --repo martymcenroe/Aletheia
```

For Full mode, add:
```bash
git -C /c/Users/mcwiz/Projects/Aletheia worktree list
git -C /c/Users/mcwiz/Projects/Aletheia branch -r
/c/Users/mcwiz/Projects/Aletheia/tools/aws/lambda-status.sh
```

## Return Results

Return a summary table:

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

Flag any unexpected conditions with ⚠️ prefix.
```

---

## After Task Completes

When the Sonnet task returns, display the results summary to the user. If any ⚠️ warnings were flagged, highlight them.

**Human reminder for Full mode:**
- Chrome: `chrome://extensions/` → Reload extension
- Firefox: `about:debugging` → Reload extension
