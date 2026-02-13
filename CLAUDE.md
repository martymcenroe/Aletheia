# CLAUDE.md - Aletheia Project

You are a team member on the Aletheia project, not a tool.

**Workflow:** This project uses the full AssemblyZero workflow. Read `C:\Users\mcwiz\Projects\AssemblyZero\WORKFLOW.md`.

---

## Project Identifiers

- **Repository:** `martymcenroe/Aletheia`
- **Project Root (Windows):** `C:\Users\mcwiz\Projects\Aletheia`
- **Project Root (Unix):** `/c/Users/mcwiz/Projects/Aletheia`
- **Worktree Pattern:** `Aletheia-{IssueID}` (e.g., `Aletheia-45`)
- **Doc Numbering:** 10xxx series (project-specific implementations of AssemblyZero 0xxx)

---

## Aletheia First Action

Read `docs/10000-GUIDE.md`. It contains the filing system, prime directives, and pointers to all standards. Do this before any work.

---

## Aletheia-Specific Workflow Rules

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

## Documentation Structure

Aletheia uses the **10xxx numbering scheme** (project-specific implementations):

| Directory | Range | Contents |
|-----------|-------|----------|
| `docs/` | 10000 | Main project guide |
| `docs/architecture/` | 10001 | C4 architecture views |
| `docs/standards/` | 100xx | Project-specific standards |
| `docs/templates/` | 101xx | Project-specific templates |
| `docs/adrs/` | 102xx | Project ADRs |
| `docs/skills/` | 106xx | Gemini integration skills |
| `docs/audits/` | 108xx | Project audit reports |
| `docs/runbooks/` | 109xx | Project runbooks |

**Generic frameworks** are in AssemblyZero (`C:\Users\mcwiz\Projects\AssemblyZero\docs\`).
**Project implementations** are here with the `1` prefix.

---

## Aletheia Audit System

| If the issue involves... | Check... |
|--------------------------|----------|
| Dependency Updates / PRs | `docs/audits/10816-audit-dependabot-prs.md` |
| Permissions / CLI Errors | AssemblyZero `0816-permission-permissiveness.md` |
| Security / WAF / Auth | AssemblyZero `0801` + Aletheia `10809` |
| Privacy / Data Storage | AssemblyZero `0802` + Aletheia `10810` |
| Performance / Latency | `docs/audits/10812-audit-performance.md` |
| Code Quality / Linting | AssemblyZero `0803-code-quality-audit.md` |
| AI Safety / LLM | AssemblyZero `0808-ai-safety-audit.md` |

---

## Forbidden Commands (Aletheia-Specific)

See **AssemblyZero:** `C:\Users\mcwiz\Projects\AssemblyZero\docs\standards\0003-agent-prohibited-actions.md`

**Quick reference:**
- Use `poetry run python tools/merge_pr.py --pr {number}` instead of `gh pr merge`
- Use project `tmp/` directory instead of `/tmp` or system temp
- Use `poetry add` instead of `pip install`

---

## Mermaid Diagram Auto-Inspection

**Before committing ANY Mermaid diagram, you MUST visually inspect it.**

See AssemblyZero `docs/standards/0004-mermaid-diagrams.md` for full rules.

**Quick checklist:**
- [ ] No touching/overlapping elements
- [ ] No lines hidden behind boxes
- [ ] All labels readable (not truncated)
- [ ] Flow direction clear

---

## Session Cleanup (MANDATORY)

**Every session must end with the `/cleanup` command.**

See AssemblyZero `docs/standards/0005-session-closeout-protocol.md` for full procedure.

- `/cleanup --quick` — Minimal ~2 min
- `/cleanup` — Normal ~5 min (default)
- `/cleanup --full` — Comprehensive ~12 min

## Session Logging

At end of session, append a summary to `docs/session-logs/YYYY-MM-DD.md`.
- **Day boundary:** 3:00 AM CT to following day 2:59 AM CT
- **Timestamp command:** `powershell.exe -Command "Get-Date -Format 'yyyy-MM-dd HH:mm'"`
- See `docs/templates/10100-TEMPLATE-GUIDE.md` for the full entry template

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
