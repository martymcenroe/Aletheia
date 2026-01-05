# CLAUDE.md - Agent Onboarding

You are a team member on the Aletheia project, not a tool.

## First Action
Read `docs/0000-GUIDE.md`. It contains the filing system, prime directives, and pointers to all standards. Do this before any work.

## Critical Workflow Rules (NON-NEGOTIABLE)

### STOP - READ THIS FIRST (Bash Command Rules)

**At session start, you MUST state:** *"I have read the Bash command rules. I will not use pipes or && in Bash commands. I will use single commands with absolute paths."*

**BANNED IN BASH COMMANDS:**
- ❌ `&&` - Chain operator triggers approval dialogs
- ❌ `|` (pipe) - Triggers approval dialogs
- ❌ `;` - Command separator triggers approval dialogs

**REQUIRED PATTERN:**
- ✅ One command per Bash tool call
- ✅ Use absolute paths (e.g., `/c/Users/mcwiz/Projects/Aletheia-102`)
- ✅ Use `git -C /path/to/repo` instead of `cd /path && git`
- ✅ Run multiple independent commands as parallel Bash tool calls

**Why:** Pipes and `&&` trigger permission approval dialogs that interrupt the user's workflow. This is unacceptable. Single commands with absolute paths are pre-approved and run silently.

**Example - WRONG:**
```bash
cd /c/Users/mcwiz/Projects/Aletheia-102 && git status
```

**Example - CORRECT:**
```bash
git -C /c/Users/mcwiz/Projects/Aletheia-102 status
```

---

### Forbidden Commands - NEVER USE:
- ❌ `git reset` (any form) - Use `git revert` instead
- ❌ `git push --force` - Destroys collaboration
- ❌ `git clean -fd` - Permanent data loss
- ❌ `pip install` - Use `poetry add` instead
- ❌ `TZ='America/Chicago' date` - Returns UTC on Windows, not local time

### Required Workflow:
- **Docs before Code:** You MUST write the relevant `docs/` file (LLD or Standard) *before* writing a single line of code.
- **Review Gate (MANDATORY):** After writing the LLD:
  1. **STOP.** Do not create a worktree or write any code.
  2. Submit the LLD for orchestrator review.
  3. Orchestrator routes to senior LLM architect for feedback.
  4. Incorporate all feedback into the LLD.
  5. Discuss until there are no remaining questions.
  6. Make explicit statement: *"All feedback has been incorporated. I am ready to code."*
  7. **ASK PERMISSION:** *"May I proceed with implementation?"*
  8. Only after orchestrator approval: create worktree and code.
- **Worktree before code:** Create isolated worktree for each feature:
  ```bash
  git worktree add ../Aletheia-{IssueID} -b {IssueID}-short-desc
  cd ../Aletheia-{IssueID}
  ```
  - Example: Issue #45 → `git worktree add ../Aletheia-45 -b 45-denylist`
  - ❌ NEVER use `git checkout -b` in the main folder
  - See ADR 0210 for rationale
- **Push immediately:** `git push -u origin HEAD` - NEVER keep branches local-only
- **Commit format:** `type: description (ref #ID)` or `(close #ID)` when complete
- **Cleanup completely:** Delete BOTH local and remote branches after merge:
  - `git branch -d {branch-name}` (local)
  - `git push origin --delete {branch-name}` (remote)
- **Merge and cleanup:** After PR is created and tests pass, merge it (`gh pr merge`), then cleanup worktree and branches per 0002 §4
- **Reports before cleanup (MANDATORY):** Before closing ANY issue, create:
  - `docs/reports/{IssueID}/implementation-report.md` - What was built and why
  - `docs/reports/{IssueID}/test-report.md` - Evidence it works
  - See `docs/0004-orchestration-protocol.md` §8.6 for requirements
- **Update inventory:** Add new files to `docs/0003-file-inventory.md`

### Python Dependencies:
- ✅ Use `poetry add <package>` for all dependencies
- ❌ NEVER use `pip install` - it bypasses the lock file

### Claude Code Permissions:
- When you are granted a new permission, **commit `.claude/settings.local.json` to main immediately**
- Use the main worktree to commit: `cd /c/Users/mcwiz/Projects/Aletheia && git add .claude/settings.local.json && git commit -m "chore: update Claude Code permissions" && git push`
- This prevents permission loss when branches are abandoned

### Pre-Code Checklist (MANDATORY):
Before writing ANY code file, verify:
1. [ ] LLD is written and committed to main
2. [ ] You are in a worktree (run `git worktree list` to check)
3. [ ] Branch name matches issue ID pattern (e.g., `45-denylist`)

If any check fails, STOP and fix before writing code.

### Document Mutability (WORM Policy):
Some documents are **immutable** — NEVER modify after creation:
- ❌ Session logs (`docs/session-logs/*.md`) - historical record
- ❌ Closed issue reports (`docs/6001-closed-issues.md`)
- ❌ Implementation reports (`docs/reports/*/`)
- ❌ Previous ADRs - supersede with new ADR, don't edit old ones

**Living documents** (update to reflect current reality):
- ✅ LLDs, Standards, Protocols, Inventories, CLAUDE.md, 0000-GUIDE.md

See `docs/0000-GUIDE.md` § "Document Mutability Rules" for full policy.

### GitHub CLI Safety:
- ✅ ALWAYS use `--repo martymcenroe/Aletheia` explicitly
- ❌ NEVER rely on default repo inference
- Example: `gh issue create --repo martymcenroe/Aletheia --title "..." --body "..."`
## Logging Lessons
When you solve a novel problem:
- **Aletheia-specific** (Chrome extension, Bedrock, this codebase) → `docs/9000-lessons-learned.md`
- **Cross-project** (Git, AWS, Python, general engineering) → Report to Orchestrator for Engineering Journal

## Communication Style
- Ask clarifying questions before assuming
- If you hit a blocker, stop and report — don't guess
- Respect the existing code style and patterns

## You Are Not Alone
Other agents work on this project. Check `docs/session-logs/` for recent context. The Orchestrator (Marty) coordinates all work via GitHub Projects.

## Session Closeout (MANDATORY)
**Every session must end with the 0009 closeout protocol.**
- See `docs/0009-session-closeout-protocol.md` for full procedure
- **Session Mode:** Quick 5-10 min closeout for routine endings
- **Full Mode:** Comprehensive 20-30 min cleanup (after features, before breaks)

## Session Logging
At end of session, append a summary to the current week's file in `docs/session-logs/Week-starting-YYYY-MM-DD.md`.
- **Week boundary:** Monday 3:00 AM CT to following Monday 2:59 AM CT
- **Format:** Use ISO 8601 dates (YYYY-MM-DD) where the date is the Monday starting the week
- **Timestamp command:** `powershell.exe -Command "Get-Date -Format 'yyyy-MM-dd HH:mm'"`
- See `docs/0100-TEMPLATE-GUIDE.md` for the full entry template
- Include: date/time, model name, summary, files, issues, state on exit
- **Entries must be sorted chronologically** within each file
