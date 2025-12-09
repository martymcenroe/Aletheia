# 0002 - Coding Standards & Operational Procedures

## 1. Prime Directives for AI Agents
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
