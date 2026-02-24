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

---

## Change Control (Mandatory)

### Issue Before Code

**NEVER change code, configuration, or infrastructure without a tracking GitHub issue.**

This is non-negotiable. Before touching ANY of the following, an issue MUST exist:
- Lambda environment variables (AUTH_ENABLED, etc.)
- IAM policies or roles
- CloudFlare Worker config
- Extension manifest permissions
- API endpoint behavior
- provision.sh

The issue MUST contain:
1. **What** is being changed
2. **Why** it's being changed
3. **Blast radius** — what breaks if this goes wrong
4. **Rollback plan** — exact commands to undo
5. **Verification** — how to confirm it worked

### No Bundling Config Changes

**NEVER bundle configuration changes with feature work.**

`AUTH_ENABLED=true` is a separate issue from "build admin dashboard." Config changes that affect all users get their own issue, their own PR, their own verification.

### Post-Change Verification

After ANY change to Lambda environment variables or extension code:
1. Curl the production API and verify expected behavior
2. If the change affects the extension, load the extension and verify the core flow: select text → analyze → overlay appears with content
3. Document the verification in the issue

### Smoke Test After Deploy

After running `provision.sh` or any AWS CLI config change:
```bash
# Health check
curl -s https://api.aletheia.study/health
# Analysis (should return signal + gem, not an error)
curl -s -X POST https://api.aletheia.study/ \
  -H "Content-Type: application/json" \
  -H "X-Aletheia-Client-Version: 1.0" \
  -d '{"text":"test"}'
```
If either fails, STOP and revert immediately.
