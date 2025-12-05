# 9000 - Lessons Learned Log

| Date | Session/Context | Turn ID | Topic | The Lesson | Action/Rule |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 2025-12-04 | Arch & Harvest | 124 | GH CLI | `gh issue close` strictly accepts only 1 argument. | Use bash loops for bulk ops: `for id in x y; do ...` |
| 2025-12-04 | Arch & Harvest | 105 | Python Deploy | Pip on Windows installs `.pyd` binaries; Lambda needs Linux `.so`. | **Always** use `deploy.sh` with `--platform manylinux2014_x86_64` (or `manylinux_2_28` for AL2023) to cross-compile. |
| 2025-12-04 | Arch & Harvest | 102 | Lambda Runtime | `awslambda` (streaming) is strictly incompatible with standard handlers. | Use standard JSON buffering for MVP. Revisit streaming only if latency demands it (See ADR-002). |
| 2025-12-04 | Arch & Harvest | 115 | Debugging | Local python scripts don't auto-update if you paste into the wrong file. | **Always** verify the file content (`cat file.py`) or use a distinct "Diagnostic Print" to confirm code version. |
| 2025-12-05 | Guardrails | 133 | Unit Testing | Tests must respect the *execution order* of validators. A "Fail Fast" check (like length) will mask downstream checks (like empty/entropy). | **Rule:** Assert the *first* failure reason in the chain, not just the existence of *a* failure. |