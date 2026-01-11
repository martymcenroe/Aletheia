# CLAUDE.md - Aletheia Project

You are a team member on the Aletheia project, not a tool.

## FIRST: Read Parent CLAUDE.md

**Before reading this file, read the parent AgentOS rules:**
`C:\Users\mcwiz\Projects\CLAUDE.md`

That file contains core AgentOS rules that apply to ALL projects:
- Bash command rules (no &&, |, ;)
- Visible self-check protocol
- Worktree isolation rules
- Path format rules
- Decision-making protocol

**This file adds Aletheia-specific rules ON TOP of those core rules.**

---

## Aletheia First Action

Read `docs/0000-GUIDE.md`. It contains the filing system, prime directives, and pointers to all standards. Do this before any work.

---

## Aletheia-Specific Workflow Rules

### Project Identifiers

- **Repository:** `martymcenroe/Aletheia`
- **Project Root:** `/c/Users/mcwiz/Projects/Aletheia`
- **Worktree Pattern:** `Aletheia-{IssueID}` (e.g., `Aletheia-45`)

### Required Workflow

- **Docs before Code:** Write the LLD (`docs/lld/active/`) or Standard *before* writing code
- **Worktree before code:** `git worktree add ../Aletheia-{ID} -b {ID}-short-desc`
- **Push immediately:** `git push -u origin HEAD`
- **Single commit per feature:** Batch all work into ONE `feat:` commit
- **Commit format:** `type: description (ref #ID)` or `(close #ID)` when complete

### Reports Before Merge (PRE-MERGE GATE - MANDATORY)

**Before ANY commit/push/merge on feature branches, you MUST:**

1. Create `docs/reports/{IssueID}/implementation-report.md`
2. Create `docs/reports/{IssueID}/test-report.md`
3. Stage files but DO NOT COMMIT until review approval
4. Update `docs/9000-lessons-learned.md` if applicable

### Merge PRs (ATOMIC ONLY)

After PR is approved, use the atomic merge script:
```bash
poetry run python /c/Users/mcwiz/Projects/Aletheia/tools/merge_pr.py --pr {number}
```
- NEVER use `gh pr merge` directly - you WILL forget cleanup
- The script: merges PR → removes worktree → deletes local branch → verifies

---

## Gemini Dual-Review Integration

**Claude Code and Gemini CLI collaborate as a dual-AI review system.**

### Review Gates

1. **LLD Design Review** - After LLD is written, before implementation
2. **Implementation Review** - After code is written, before merge
3. **Issue Filing Review** - After issue is drafted, before filing

### LLD Review Automation

**Trigger:** After writing any LLD to `docs/lld/active/*.md`

**Process:**
1. Load prompt template from `gemini-prompts/lld-review.txt`
2. Invoke Gemini using `tools/gemini-model-check.sh`
3. Parse feedback: `[BLOCKING]`, `[HIGH]`, `[SUGGESTION]`
4. Update LLD with all [BLOCKING] and [HIGH] feedback
5. Wait for user to say "implement"

### Implementation Review

**Trigger:** After implementation complete, reports generated, before commit

**Process:**
1. Load prompt from `gemini-prompts/implementation-review.txt`
2. Invoke Gemini for review
3. Parse decision: `[APPROVE]` or `[BLOCK]`
4. **Dual Approval Gate:** Require BOTH Gemini + User approval before merge

### Model Downgrade Detection

Every Gemini invocation validates the model tier used:
- Expected: `gemini-3-pro-preview`
- If downgrade detected: ABORT review, notify user

---

## Aletheia Audit System

When encountering errors, check the relevant audit document:

| If the issue involves... | Check this Audit... |
|--------------------------|---------------------|
| Dependency Updates / PRs | `0816-audit-dependabot-prs.md` |
| Permissions / CLI Errors | `0808-audit-permission-permissiveness.md`, `0824-audit-permission-friction.md` |
| Security / WAF / Auth | `0809-audit-security.md` |
| Privacy / Data Storage | `0810-audit-privacy.md` |
| Performance / Latency | `0812-audit-performance.md` |
| Code Quality / Linting | `0813-audit-code-quality.md` |

---

## Forbidden Commands (Aletheia-Specific)

See **`docs/0015-agent-prohibited-actions.md`** for the complete list.

**Quick reference:**
- Use `poetry run python tools/merge_pr.py --pr {number}` instead of `gh pr merge`
- Use project `tmp/` directory instead of `/tmp` or system temp
- Use `poetry add` instead of `pip install`

---

## Session Cleanup (MANDATORY)

**Every session must end with the `/cleanup` command.**
- See `docs/0009-session-closeout-protocol.md` for full procedure
- `/cleanup --quick` — Minimal ~2 min
- `/cleanup` — Normal ~5 min (default)
- `/cleanup --full` — Comprehensive ~12 min

## Session Logging

At end of session, append a summary to `docs/session-logs/YYYY-MM-DD.md`.
- **Day boundary:** 3:00 AM CT to following day 2:59 AM CT
- **Timestamp command:** `powershell.exe -Command "Get-Date -Format 'yyyy-MM-dd HH:mm'"`
- See `docs/0100-TEMPLATE-GUIDE.md` for the full entry template

---

## COMMIT DISCIPLINE (CONTRIBUTION GRAPH PROTECTION)

**Agents do NOT commit documentation changes on main. Ever.**

Documentation edits accumulate as unstaged changes until `/cleanup` (normal or full mode).

**Rules:**
- EDIT docs on main freely
- NEVER run `git commit` for doc changes on main
- Let changes accumulate - `/cleanup` will batch-commit them

**Exception:** Code changes in worktrees follow normal PR workflow.

---

## Logging Lessons

When you solve a novel problem:
- **Aletheia-specific** → `docs/9000-lessons-learned.md`
- **Cross-project** → Report to Orchestrator for Engineering Journal

---

## GitHub CLI Safety

- ALWAYS use `--repo martymcenroe/Aletheia` explicitly
- NEVER rely on default repo inference
- Example: `gh issue create --repo martymcenroe/Aletheia --title "..." --body "..."`

---

## You Are Not Alone

Other agents work on this project. Check `docs/session-logs/` for recent context. The Orchestrator (Marty) coordinates all work via GitHub Projects.
