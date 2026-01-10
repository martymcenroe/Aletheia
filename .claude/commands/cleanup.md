---
description: Session cleanup with quick/normal/full modes (project)
argument-hint: "[--help] [--quick|--normal|--full]"
aliases: ["/closeout", "/goodbye"]
---

# Cleanup

**Aliases:** `/closeout` (same as `/cleanup`), `/goodbye` (same as `/cleanup --quick`)

**If `$ARGUMENTS` contains `--help`:** Display the Help section below and STOP.

---

## Help

Usage: `/cleanup [--help] [--quick|--normal|--full] [--no-auto-delete]`

| Argument | Description |
|----------|-------------|
| `--help` | Show this help message and exit |
| `--quick` | Minimal cleanup (~2 min) - appends session log, does NOT commit |
| `--normal` | Standard cleanup (~5 min) - typical session end (default) |
| `--full` | Comprehensive cleanup (~12 min) - after features, before breaks |
| `--no-auto-delete` | Skip automatic deletion of orphaned branches |

**Examples:**
- `/cleanup --help` - show this help
- `/cleanup` - normal mode (default)
- `/cleanup --quick` - fast exit
- `/cleanup --full` - thorough cleanup

**What each mode does:**
| Check | Quick | Normal | Full |
|-------|:-----:|:------:|:----:|
| Git status | ✅ | ✅ | ✅ |
| Branch list | ✅ | ✅ | ✅ |
| Open PRs | ✅ | ✅ | ✅ |
| **Session log append** | ✅ | ✅ | ✅ |
| **Commit & push** | | ✅ | ✅ |
| Stash list | | ✅ | ✅ |
| Regenerate 6000 | | ✅ | ✅ |
| Worktree list | | ✅ | ✅ |
| **POST-MERGE cleanup** | | ✅ | ✅ |
| **Auto-delete orphans** | | ✅ | ✅ |
| Inventory audit | | | ✅ |
| **Index consistency** | | | ✅ |
| **Plan staleness** | | | ✅ |

**Quick mode philosophy:** Record what happened (session log), but don't commit. Changes accumulate until a normal/full cleanup commits them. Protects contribution graph from trivial commits.

---

## Execution

**Mode:** Parse `$ARGUMENTS` for flags. Default is `--normal` if no flag provided.

**Session Name:** Determine the session identifier to include in the session log:
1. If `/rename` was used in this conversation, extract the name from the output (e.g., "Session renamed to: my-session-name")
2. If no rename, look for the session ID in any visible transcript path (UUID like `00893aaf-19fa-41d2-8238-13269b9b3ca0`)
3. If neither available, use "unnamed"

Pass this as `SESSION_NAME` in the Task prompt below.

| Flag | Mode | Time | Use Case |
|------|------|------|----------|
| `--quick` | Quick | ~2 min | End of chat, minimal changes |
| `--normal` | Normal | ~5 min | Standard session end (default) |
| `--full` | Full | ~12 min | Feature complete, before breaks |

### CACHE REFRESH (MANDATORY)

**Before spawning the Task agent, you MUST read this file from disk:**

```
Read: C:\Users\mcwiz\Projects\Aletheia\.claude\commands\cleanup.md
```

**Why:** The skill expansion in system-reminder can be STALE (cached from earlier in conversation). The disk version is authoritative. Use the Task Prompt from the freshly-read file, NOT from the system-reminder content.

**Incident 2026-01-08:** Stale cache had "Lambda - If ON, turn off" rule. Disk had this removed. Lambda was wrongly turned off in production.

---

**IMPORTANT:** Use the **Task tool** with `model: sonnet` to execute the cleanup. This saves budget while keeping your main session on Opus.

Spawn a Task with `subagent_type: general-purpose` and `model: sonnet` with the following prompt (substitute MODE based on parsed arguments):

---

### Task Prompt for Sonnet Agent

```
You are executing a cleanup procedure for the Aletheia project.
Mode: [MODE: quick|normal|full]
Session: [SESSION_NAME]

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

**Normal mode adds (7 parallel calls total):**
- git -C /c/Users/mcwiz/Projects/Aletheia stash list
- git -C /c/Users/mcwiz/Projects/Aletheia fetch --prune
- git -C /c/Users/mcwiz/Projects/Aletheia worktree list
- gh issue list --state open --repo martymcenroe/Aletheia

**Full mode adds (9 parallel calls total):**
- git -C /c/Users/mcwiz/Projects/Aletheia branch -vv
- git -C /c/Users/mcwiz/Projects/Aletheia branch -r

## Phase 2: Conditional Fixes

**Analyze Phase 1 results:**

1. **Branches vs Worktrees** - Cross-reference branch list against worktree list:
   - Parse worktree output: each line shows `path  commit [branch-name]`
   - For each branch OTHER than main, check if it appears in the worktree list
   - If branch HAS a worktree: ✅ OK (active multi-agent work - do NOT flag)
   - If branch has NO worktree: Flag as potential orphan for step 2
   - **CRITICAL:** Branches WITH worktrees are EXPECTED. Only process truly orphaned branches.

2. **Auto-Delete Orphaned Branches** (Normal and Full) - For each orphaned branch found in step 1:

   **Safety Criteria (ALL must be met to auto-delete):**
   - Branch is not `main`
   - Remote tracking shows `gone` (was deleted on GitHub)
   - No worktree exists for this branch

   **Detection:** Parse `git branch -vv` output for `[origin/...: gone]` marker:
   ```bash
   git -C /c/Users/mcwiz/Projects/Aletheia branch -vv
   ```
   Look for lines containing `: gone]` - these are branches whose remote was deleted.

   **Action based on `--no-auto-delete` flag:**

   a. If remote shows `gone` AND no worktree AND `--no-auto-delete` NOT set:
      - Auto-delete: `git -C /c/Users/mcwiz/Projects/Aletheia branch -D {branch-name}`
      - Report: "✅ AUTO-DELETE: Removed orphan branch {name} (remote gone)"

   b. If remote shows `gone` AND no worktree AND `--no-auto-delete` IS set:
      - Report: "⚠️ ORPHAN: Branch {name} has no remote (--no-auto-delete set, skipping)"

   c. If remote does NOT show `gone` (branch has no tracking or remote exists) AND no worktree:
      - Report: "⚠️ ORPHAN: Branch {name} has no worktree (manual review needed)"

3. **Stale Worktrees** (Full only) - Flag if worktree path doesn't exist on disk:
   - Report and offer to remove with: git -C /c/Users/mcwiz/Projects/Aletheia worktree remove {path}

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

**Full mode only: Transcript Archival**
```bash
poetry run python /c/Users/mcwiz/Projects/Aletheia/tools/archive_transcripts.py
```
Archives verbatim transcripts older than 7 days to monthly archive directories (`~/.claude/projects/.../archive/YYYY-MM/`).

**Full mode only: Additional checks**

1. **Inventory audit**: Use Glob tool with patterns **/*.py, **/*.js, **/*.md, **/*.sh
   Compare against docs/0003-file-inventory.md, flag drift

2. **Index Consistency Check** (MANDATORY):
   a. ADR Index - List actual ADR files:
      ```bash
      ls /c/Users/mcwiz/Projects/Aletheia/docs/02*-ADR-*.md
      ```
      Compare against entries in `docs/0200-ADR-index.md`. Flag missing/orphaned.

   b. Audit Index - List actual audit files:
      ```bash
      ls /c/Users/mcwiz/Projects/Aletheia/docs/08*-audit-*.md
      ```
      Compare against entries in `docs/0800-audit-index.md` §9.1. Flag missing/orphaned.

   c. Template Registry - List templates:
      ```bash
      ls /c/Users/mcwiz/Projects/Aletheia/docs/01*-TEMPLATE-*.md
      ```
      Verify all referenced in `docs/0100-TEMPLATE-GUIDE.md`.

   d. If drift found, update index files and stage:
      ```bash
      git -C /c/Users/mcwiz/Projects/Aletheia add docs/0200-ADR-index.md
      git -C /c/Users/mcwiz/Projects/Aletheia add docs/0800-audit-index.md
      ```

3. **IMMEDIATE-PLAN Staleness Check** (MANDATORY):
   a. Extract issue references:
      ```bash
      grep -oE '#[0-9]+' /c/Users/mcwiz/Projects/Aletheia/docs/0000a-IMMEDIATE-PLAN.md
      ```
   b. For each unique issue number, check state:
      ```bash
      gh issue view NNN --repo martymcenroe/Aletheia --json state,title
      ```
   c. If any referenced issue is CLOSED:
      - Report: `⚠️ STALE: Issue #NNN is CLOSED but still referenced in IMMEDIATE-PLAN`
      - Read the full IMMEDIATE-PLAN
      - Update to reflect current reality (mark complete, remove blocking constraints)
      - Stage: `git -C /c/Users/mcwiz/Projects/Aletheia add docs/0000a-IMMEDIATE-PLAN.md`

## Phase 3: Session Log

Append session log entry. Include the session name in the summary:
```bash
poetry run python /c/Users/mcwiz/Projects/Aletheia/tools/append_session_log.py \
    --model "Claude Sonnet 4" \
    --summary "Cleanup ([MODE] mode) | Session: [SESSION_NAME]" \
    --created "None" \
    --closed "None" \
    --next "Per user direction"
```

If the script fails, manually append to the current day's session log file. Include the session name in the header or summary.

## Phase 4: Single Commit & Push (SKIP FOR QUICK MODE)

**If mode is `quick`: SKIP this entire phase. Go directly to Phase 5.**

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
| Auto-Deleted | ✅ {count} branches / ⏭️ Skipped (--no-auto-delete) / ⚠️ {count} orphaned (no gone remote) |
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
