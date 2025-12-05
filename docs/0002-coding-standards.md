# 0002 - Coding Standards & Operational Procedures

## 1. Prime Directives for AI Agents
* **Root-Relative Paths:** You must ALWAYS generate file paths relative to the project root (e.g., `src/guardrails/engine.py`), regardless of which file is currently open. NEVER create a nested `src/` inside `docs/`.
* **Explicit Handoff:** At the end of every code generation turn, you MUST provide a "Verification Block" containing the exact terminal commands the user needs to run (e.g., `poetry run pytest`). Do not assume the user knows what to do next.

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

## 4. Version Control (Git)
* **Branching:** Format `ID-short-description`.
* **Commits:** Conventional Commits (`type: description`).

## 5. Documentation
* **Update First:** Update the relevant `docs/` file *before* writing code.
* **Lessons Learned:** Log new discoveries in `docs/9000-lessons-learned.md`.
