# 0002 - Coding Standards & Operational Procedures

## 1. Python Development
* **Version:** Python 3.12 (Strict).
* **Dependency Management:**
    * **Local Dev:** Use `poetry add <package>`. NEVER use `pip install` directly in the environment.
    * **Lambda Packaging:** handled by `deploy.sh`. Do not manually zip files.
* **Linting:** Follow PEP 8.
* **Type Hinting:** Required for all function signatures.

## 2. AWS & Infrastructure
* **Philosophy:** "Bare Metal" Scripting.
    * **No:** Terraform, CDK, CloudFormation.
    * **Yes:** AWS CLI (`aws lambda ...`), Bash scripts (`provision.sh`, `deploy.sh`).
* **Lambda Runtime:**
    * Assume `boto3` is pre-installed (standard AWS runtime).
    * Avoid heavy libraries (Pandas, Numpy) unless explicitly authorized by an ADR.

## 3. Version Control (Git)
* **Branching:**
    * Format: `ID-short-description` (e.g., `11-local-guardrails`).
    * Source: Always branch from `main`.
* **Commits:**
    * Format: Conventional Commits (`type: description`).
    * Types: `feat`, `fix`, `chore`, `docs`, `test`.
    * Example: `feat: implement validation logic for guardrails`
* **PRs:** Squash and merge only.

## 4. Documentation
* **Update First:** Update the relevant `docs/` file *before* writing code.
* **Lessons Learned:** If you solve a hard error, append it to `docs/9000-lessons-learned.md`.
