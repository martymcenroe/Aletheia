# 9000 - Lessons Learned Log

| Date | Session/Context | Turn ID | Topic | The Lesson | Action/Rule |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 2025-12-04 | Arch & Harvest | 124 | GH CLI | `gh issue close` strictly accepts only 1 argument. | Use bash loops for bulk ops: `for id in x y; do ...` |
| 2025-12-04 | Arch & Harvest | 105 | Python Deploy | Pip on Windows installs `.pyd` binaries; Lambda needs Linux `.so`. | **Always** use `deploy.sh` with `--platform manylinux2014_x86_64` (or `manylinux_2_28` for AL2023) to cross-compile. |
| 2025-12-04 | Arch & Harvest | 102 | Lambda Runtime | `awslambda` (streaming) is strictly incompatible with standard handlers. | Use standard JSON buffering for MVP. Revisit streaming only if latency demands it (See ADR-002). |
| 2025-12-04 | Arch & Harvest | 115 | Debugging | Local python scripts don't auto-update if you paste into the wrong file. | **Always** verify the file content (`cat file.py`) or use a distinct "Diagnostic Print" to confirm code version. |
| 2025-12-05 | Guardrails | 133 | Unit Testing | Tests must respect the *execution order* of validators. A "Fail Fast" check (like length) will mask downstream checks (like empty/entropy). | **Rule:** Assert the *first* failure reason in the chain, not just the existence of *a* failure. |
| 2025-12-08 | Git Workflow | 20 | Branch Divergence | Branching from a stale `main` causes files created *after* that point to vanish from the workspace. | **Rule:** Always `git checkout main && git pull` before creating a new branch. |
| 2025-12-08 | Git Workflow | 12 | Squash Merge | Squash merging alters commit SHAs, triggering "not fully merged" warnings on local delete. | Ignore warning if PR merged; use `git branch -D` for cleanup. |
| 2025-12-08 | Env Setup | 9 | AWS IAM Login | Console access requires `iam:CreateLoginProfile` and is separate from CLI keys. | **Rule:** If Console access is disabled, use `aws iam create-login-profile` from an Admin CLI profile. |
| 2025-12-09 | Store Compliance | - | Google Chrome Web Store Manual Review Triggers | **Lesson:** Avoid `<all_urls>` permission at all costs. It triggers a multi-week manual review. Use `activeTab` for "Click-to-Run" privacy by default. |
| 2025-12-09 | Rapid Deployment | - | GitHub Pages for Legal Compliance | **Lesson:** Don't overengineer the Privacy Policy site. A single `index.html` pushed to a `gh-pages` branch (or main docs) is sufficient for Google Store compliance. |
| 2025-12-09 | Orchestration | 13 | Identity Mgmt | Multi-user LLM accounts create auth friction and cost ($4/mo). | **Rule:** Adopt Single-User CLI model. Orchestrator (`martymcenroe`) commits all code. (See `0004`). |
| 2025-12-11 | Repo Genesis | 11 | First PR Failure | The first branch pushed becomes default; cannot PR branch into itself. | **Rule:** Initialize and push main upstream before creating feature branches. |
