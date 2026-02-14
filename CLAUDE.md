# CLAUDE.md - Aletheia Project

**Workflow:** Full AssemblyZero workflow. Read `C:\Users\mcwiz\Projects\AssemblyZero\WORKFLOW.md`.

---

## Project Identifiers

- **Repository:** `martymcenroe/Aletheia`
- **Worktree Pattern:** `Aletheia-{IssueID}`
- **Doc Numbering:** 10xxx series
- **Reference:** `docs/10000-GUIDE.md` for filing system and standards

---

## Workflow Rules

- **Docs before Code:** Write the LLD (`docs/lld/active/`) before writing code
- **Worktree before code:** `git worktree add ../Aletheia-{ID} -b {ID}-short-desc`
- **Push immediately:** `git push -u origin HEAD`
- **Single commit per feature**
- **Commit format:** `type: description (ref #ID)` or `(close #ID)`

### Pre-Merge Gate

Before ANY commit/push/merge on feature branches:
1. Create `docs/reports/{IssueID}/implementation-report.md`
2. Create `docs/reports/{IssueID}/test-report.md`
3. Stage files but DO NOT COMMIT until review approval

### Merge PRs

```bash
poetry run python /c/Users/mcwiz/Projects/Aletheia/tools/merge_pr.py --pr {number}
```
NEVER use `gh pr merge` directly.

---

## Documentation Structure

| Directory | Range | Contents |
|-----------|-------|----------|
| `docs/` | 10000 | Main project guide |
| `docs/architecture/` | 10001 | C4 architecture views |
| `docs/standards/` | 100xx | Project-specific standards |
| `docs/adrs/` | 102xx | Project ADRs |
| `docs/audits/` | 108xx | Audit reports |
| `docs/runbooks/` | 109xx | Runbooks |

---

## Audit System

| If the issue involves... | Check... |
|--------------------------|----------|
| Dependency Updates / PRs | `docs/audits/10816-audit-dependabot-prs.md` |
| Permissions / CLI Errors | AssemblyZero `0816-permission-permissiveness.md` |
| Security / WAF / Auth | AssemblyZero `0801` + Aletheia `10809` |
| Privacy / Data Storage | AssemblyZero `0802` + Aletheia `10810` |
| Performance / Latency | `docs/audits/10812-audit-performance.md` |

---

## Commit Discipline (Contribution Graph Protection)

**Agents do NOT commit documentation changes on main. Ever.**

- EDIT docs on main freely
- NEVER `git commit` doc changes on main
- Let changes accumulate — `/cleanup` will batch-commit them

**Exception:** Code changes in worktrees follow normal PR workflow.
