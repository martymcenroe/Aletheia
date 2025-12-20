# 0002 - Coding Standards & Operational Procedures

## 1. Prime Directives for AI Agents
* **Plan Before Execute:** Discuss multi-step plans with the Orchestrator BEFORE running commands. Never batch destructive operations without explicit approval.
* **Root-Relative Paths:** You must ALWAYS generate file paths relative to the project root (e.g., `src/guardrails/engine.py`).
* **Explicit Handoff:** At the end of every code generation turn, you MUST provide a "Verification Block".
* **Protocol Adherence:** Strictly follow the Orchestration Protocol defined in `docs/0004-orchestration-protocol.md`.

## 2. Python Development
* **Version:** Python 3.12 (Strict).
* **Dependency Management:**
    * **Local Dev:** Use `poetry add <package>`. NEVER use `pip install` directly.
    * **Lambda Packaging:** Handled by `deploy.sh`.
* **Linting:** Follow PEP 8.
* **Type Hinting:** Required for all function signatures.

## 3. AWS & Infrastructure
* **Philosophy:** "Bare Metal" Scripting (Bash + AWS CLI).
* **Lambda Runtime:** Assume `boto3` is pre-installed.

## 4. The 9-Step Workflow ("The Flip Turn")
1. **Issue:** Discovery (`gh issue list`).
2. **Branch:** Isolation (`git checkout -b`).
3. **Edit:** Implementation.
4. **Stage:** Preparation (`git add`).
5. **Commit:** Conventional (`type: desc (ref #ID)`).
6. **Push:** Backup (`git push`).
7. **PR:** Review (`gh pr create`).
8. **Merge:** Finalize (`gh pr merge`).
9. **Cleanup:** Hygiene (`git branch -d`).

## 5. Documentation
* **Update First:** Update the relevant `docs/` file *before* writing code.
* **Lessons Learned:** Log new discoveries in `docs/9000-lessons-learned.md`.

## 6. Naming Conventions

### 6.1 Branch Naming
Format: `{IssueID}-short-description`

| Example | Correct |
|:--------|:--------|
| Issue #25 → LinkedIn auth gate | `25-linkedin-auth-gate` ✅ |
| Issue #45 → Hate speech filter | `45-hate-filter` ✅ |
| ~~`feature/linkedin-auth-gate-issue-25`~~ | ❌ Too verbose, wrong format |
| ~~`feat/wire-compliance-engine`~~ | ❌ Missing issue ID |

### 6.2 Documentation File Naming
Format: `1{IssueID}-short-description.md` (for feature specs in the `1xxx` namespace)

| GitHub Issue | Doc File |
|:-------------|:---------|
| #10 | `docs/1010-semantic-guardrails.md` |
| #25 | `docs/1025-linkedin-auth-gate.md` |
| #45 | `docs/1045-hate-filter.md` |

**Note:** GitHub shares a single sequence across Issues, PRs, and Discussions. Plan for Issue IDs up to #999 in the current 4-digit scheme. If the project approaches #900, migrate to a 5-digit namespace.

### 6.3 Commit Message Format
Format: `type: description (ref #ID)`

Types: `feat`, `fix`, `docs`, `chore`, `test`, `refactor`

Examples:
* `feat: implement semantic guardrail engine (ref #10)`
* `docs: add store compliance spec (ref #51)`
* `chore: rename doc to follow naming convention (ref #25)`