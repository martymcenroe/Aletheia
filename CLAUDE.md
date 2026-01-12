# CLAUDE.md - Aletheia Project

You are a team member on the Aletheia project, not a tool.

## STOP - MANDATORY PRE-TOOL CHECKLIST

**BEFORE calling ANY tool (Read, Write, Edit, Glob, Bash), you MUST complete this checklist OUT LOUD:**

```
PRE-TOOL CHECK:
1. Tool I'm about to use: [Read/Write/Edit/Glob/Bash]
2. Path I'm about to use: [write the full path]
3. Does path start with ~? → IF YES, STOP. Rewrite as C:\Users\mcwiz\Projects\...
4. Does path start with C:\ ? → IF YES for Read/Write/Edit/Glob, PROCEED
5. Does path start with /c/ ? → IF YES for Bash, PROCEED
6. Does Bash command contain && or | or ; ? → IF YES, STOP. Split into separate commands.
```

**IF YOU SKIP THIS CHECKLIST, YOU WILL CAUSE PERMISSION PROMPTS.**

---

## PATH FORMAT RULES

| Tool | MUST Start With | Example |
|------|-----------------|---------|
| Read, Write, Edit, Glob | `C:\Users\mcwiz\Projects\` | `C:\Users\mcwiz\Projects\Aletheia\file.md` |
| Bash | `/c/Users/mcwiz/Projects/` | `/c/Users/mcwiz/Projects/Aletheia/file.md` |

**THE TILDE CHARACTER (~) DOES NOT EXIST. NEVER USE IT.**

Windows does not support `~` for home directory. If you use `~`, you WILL trigger permission prompts.

**BANNED PATTERNS - MEMORIZE THESE:**
- `~\anything` - BANNED (tilde + backslash = ALWAYS WRONG)
- `~/anything` - BANNED (tilde + forward slash = ALWAYS WRONG on Windows)
- `&& ` in Bash - BANNED (split into separate commands)
- `| ` in Bash - BANNED (use dedicated tools instead)
- `; ` in Bash - BANNED (split into separate commands)

**YOUR WORKING DIRECTORY:**
- If in Aletheia: `C:\Users\mcwiz\Projects\Aletheia`
- If in Aletheia-106: `C:\Users\mcwiz\Projects\Aletheia-106`
- If in Aletheia-310: `C:\Users\mcwiz\Projects\Aletheia-310`

Use YOUR working directory as the base for all paths.

---

## WORKTREE PATH CONSTRUCTION (CRITICAL)

**When accessing worktrees (Aletheia-{ID}), the ONLY valid paths are:**

| Worktree | For Glob/Read/Write/Edit | For Bash |
|----------|--------------------------|----------|
| Aletheia-106 | `C:\Users\mcwiz\Projects\Aletheia-106` | `/c/Users/mcwiz/Projects/Aletheia-106` |
| Aletheia-310 | `C:\Users\mcwiz\Projects\Aletheia-310` | `/c/Users/mcwiz/Projects/Aletheia-310` |
| Any worktree | `C:\Users\mcwiz\Projects\Aletheia-{ID}` | `/c/Users/mcwiz/Projects/Aletheia-{ID}` |

**WORKTREES ARE NOT AT:**
- `~/Projects/Aletheia-{ID}` ← WRONG
- `~\Projects\Aletheia-{ID}` ← WRONG
- `~\Projects\...` ← WRONG

**BEFORE constructing ANY worktree path, STOP and verify:**
1. Does the path start with `C:\Users\mcwiz\Projects\` (for Read/Glob)?
2. Does the path start with `/c/Users/mcwiz/Projects/` (for Bash)?
3. If NO to both → you are constructing the path WRONG

---

## SECOND: Read Parent CLAUDE.md

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
- **Project Root (Windows - for Read/Glob):** `C:\Users\mcwiz\Projects\Aletheia`
- **Project Root (Unix - for Bash):** `/c/Users/mcwiz/Projects/Aletheia`
- **Worktree Pattern:** `Aletheia-{IssueID}` (e.g., `Aletheia-45`, located at `C:\Users\mcwiz\Projects\Aletheia-45`)

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

## Mermaid Diagram Auto-Inspection (MANDATORY)

**Before committing ANY Mermaid diagram, you MUST visually inspect it.**

You are a multimodal LLM. You can render and view diagrams using mermaid.ink:

```bash
# 1. Base64 encode the diagram
DIAGRAM=$(cat <<'EOF' | base64 -w 0
graph TB
    A --> B
EOF
)

# 2. Download rendered PNG
curl -s -o /tmp/diagram.png "https://mermaid.ink/img/$DIAGRAM"

# 3. Use Read tool to view the image
```

**Inspection Checklist:**
- [ ] No touching/overlapping elements
- [ ] No lines hidden behind boxes
- [ ] All labels readable (not truncated)
- [ ] Flow direction clear

**If ANY check fails:** Fix the diagram and re-inspect before committing.

**Reference:** `docs/0006-mermaid-diagrams.md` §8 Visual Quality Rules

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
