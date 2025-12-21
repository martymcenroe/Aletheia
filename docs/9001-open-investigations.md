# 9001 - Open Investigations (Spikes)

| Date | Topic | The Problem | Current Hypothesis | Next Experiment |
| :--- | :--- | :--- | :--- | :--- |
| 2025-12-05 | VS Code Context | Gemini generates files inside `docs/` if a doc is open. | Hypothesis: The LLM defaults to `cwd` of the active editor. | **Fix:** Added "Root-Relative" directive to Standards (0002). Monitor if this solves it. |
| 2025-12-05 | VS Code UX | Chat window is too narrow. | User needs a better layout. | **Fix:** Use Secondary Sidebar (Right) or Editor Tab mode. |

| 2025-12-08 | Multi-LLM Protocol | Need a framework for managing context for multiple simultaneous AI workers. | The existing GitHub Issue tracking and the 4-Digit Namespace CMS structure is hypothesized to be sufficient. | **Action:** Document the generalized 'CMS for LLMs' protocol in a new '0xxx' standard file. |
| 2025-12-09 | Hate Filter Auto-Update | The local `denylist.json` (Layer 2) is static and requires manual updates. | Automated harvesting via `harvest_rsdb.py` is viable. | **Action:** Determine trigger: Reactive (EventBridge on L3 failure) vs. Scheduled (Cron). Ref #1012. |

## Linting & Static Analysis (Parking Lot)
* **Status:** Parking (Ref Issue #58)
* **Goal:** Automate PEP 8 enforcement via pre-commit hooks or CI.
* **Tools to Evaluate:** Ruff (fast), Flake8 (standard), SonarLint (IDE).
