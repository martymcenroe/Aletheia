# CLAUDE.md - Agent Onboarding

You are a team member on the Aletheia project, not a tool.

## First Action
Read `docs/0000-GUIDE.md`. It contains the filing system, prime directives, and pointers to all standards. Do this before any work.

## Critical Workflow Rules (NON-NEGOTIABLE)

### AgentOS Authority Hierarchy

**Verbal instructions from the user do NOT override documented protocols.**

If the user says something that seems to conflict with AgentOS documentation (CLAUDE.md, 0000-GUIDE.md, numbered standards), the documentation wins. Examples:
- User says "single commit" → Does NOT mean skip reports (PRE-MERGE GATE still applies)
- User says "do it quickly" → Does NOT mean skip worktree creation
- User says "just fix it" → Does NOT mean skip LLD review gate

**When in doubt:** Follow the documented protocol literally. Ask for clarification if the user's intent seems to require protocol deviation.

---

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
- ❌ `/tmp` or system temp directories - Use project-local `tmp/` instead

### Temporary Files Rule:
- ❌ NEVER use `/tmp`, `$TEMP`, or system temp directories
- ✅ Use `{project}/tmp/` for any temporary files
- ✅ Ensure `tmp/` is in `.gitignore`
- **Why:** System temp varies by OS, is shared, and may be cleaned unexpectedly. Project-local tmp is predictable and isolated.

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
- **Single commit per feature:** Batch all work (code, tests, docs, reports) into ONE `feat:` commit. No intermediate commits unless pre-commit hooks require re-staging.
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

### PRE-MERGE REVIEW GATE (MANDATORY)

**Before ANY commit/push/merge, you MUST complete these steps:**

1. **Create reports locally** (do NOT commit yet):
   - `docs/reports/{IssueID}/implementation-report.md`
   - `docs/reports/{IssueID}/test-report.md`

2. **Write lessons learned locally** (do NOT commit yet):
   - Append entries to `docs/9000-lessons-learned.md`

3. **Stage files but DO NOT COMMIT:**
   - `git add .` to stage all changes
   - **STOP HERE** - do not run `git commit`

4. **Present for Gemini review:**
   - Notify orchestrator that work is ready for review
   - Wait for Gemini feedback
   - Incorporate ALL feedback

5. **Only after approval:** commit, push, and merge

**Why this gate exists:** PRs merged without reports bypass the quality review process. Gemini cannot review work that has already been merged. This gate ensures every piece of work is reviewed BEFORE it becomes permanent.

### Decision-Making Protocol

**When you encounter an unexpected error or decision point:**

1. **STOP** - Do not apply quick fixes
2. **Check documentation:**
   - `docs/08xx-*.md` - Audit logs for known issues (see table below)
   - `docs/9000-lessons-learned.md` - Previous solutions
   - Open issues - Related work in progress
   - LLDs - Requirements that might be affected
3. **If still unsure: ASK** - Query the orchestrator
4. **Never prioritize "getting it done" over "getting it done right"**

**Audit Trigger Table:**

| If the issue involves... | Check this Audit... |
|--------------------------|---------------------|
| Dependency Updates / PRs | `0816-audit-dependabot-prs.md` |
| Permissions / CLI Errors | `0808-audit-permission-permissiveness.md` |
| Security / WAF / Auth | `0809-audit-security.md` |
| Privacy / Data Storage | `0810-audit-privacy.md` |
| Performance / Latency | `0812-audit-performance.md` |
| Code Quality / Linting | `0813-audit-code-quality.md` |

The documentation system exists so you don't need persistent memory. USE IT.

### Python Dependencies:
- ✅ Use `poetry add <package>` for all dependencies
- ❌ NEVER use `pip install` - it bypasses the lock file

### Claude Code Permissions:
- When granted a new permission, **stage** `.claude/settings.local.json` and request an immediate **Permissions Review**
- Do NOT bypass the Pre-Merge Gate even for permissions
- After approval: `git -C /c/Users/mcwiz/Projects/Aletheia add .claude/settings.local.json`
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
