# CLAUDE.md - Agent Onboarding

You are a team member on the Aletheia project, not a tool.

## First Action
Read `docs/0000-GUIDE.md`. It contains the filing system, prime directives, and pointers to all standards. Do this before any work.

## Workflow Rules
- **Branch before code:** `git checkout -b {IssueID}-short-desc`
- **Commit format:** `type: description (ref #ID)` or `(close #ID)` when complete
- **No merging:** Push and create PR, but leave merge to Orchestrator
- **Update inventory:** Add new files to `docs/0003-file-inventory.md`
## Logging Lessons
When you solve a novel problem:
- **Aletheia-specific** (Chrome extension, Bedrock, this codebase) → `docs/9000-lessons-learned.md`
- **Cross-project** (Git, AWS, Python, general engineering) → Report to Orchestrator for Engineering Journal

## Session Logging
At the end of your session, output a log entry for the Orchestrator to append to `.session-log.md`:

```
## YYYY-MM-DD HH:MM CT | Claude Code (Sonnet)
**Summary:** [1-2 sentences]
**Files Modified:** [list]
**Issues:** [numbers and status]
**State on Exit:** [branch, last commit SHA]
```

## Communication Style
- Ask clarifying questions before assuming
- If you hit a blocker, stop and report — don't guess
- Respect the existing code style and patterns

## You Are Not Alone
Other agents work on this project. Check `.session-log.md` for recent context. The Orchestrator (Marty) coordinates all work via GitHub Projects.

## Session Logging
At end of session, append a summary to `.session-log.md` using the template in docs/0100-TEMPLATE-GUIDE.md. Include:
- Date/time and model name
- Summary of work done
- Files created/modified
- Issues created/closed
- Key decisions
- State on exit (branch, last commit, next steps)
