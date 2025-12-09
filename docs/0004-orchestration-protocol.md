# 0004 - Orchestration Protocol

## 1. The "Single-User Orchestrator" Model
To eliminate the friction of managing multiple GitHub accounts and the cost of Organization seats, this project operates under a **Single-User Orchestration** model.

* **The Human (Orchestrator):** You (`martymcenroe`) are the sole authenticated user. You execute all commands and authorize all code.
* **The AI (Mentor):** The AI functions as a "Bespoke Accelerated Mentor," generating CLI instructions for the Orchestrator to execute.
* **Attribution:** All commits are authored by `martymcenroe`. We do not use separate "bot" accounts for AI-generated code.

## 2. Tooling Constraints
* **CLI Exclusive:** All interactions must occur via the command line (`bash` or `zsh`).
* **GitHub CLI (`gh`):** Used for Issue tracking (`gh issue`) and Pull Requests (`gh pr`).
* **Git (`git`):** Used for version control.
* **No GUIs:** Do not rely on the GitHub web interface or IDE buttons for core workflow tasks.

## 3. The "Flip Turn" Workflow (9 Steps)
Every feature or fix must strictly follow this 9-step execution loop to ensure hygiene and recoverability.

| Step | Action | Command Pattern |
| :--- | :--- | :--- |
| **1. Issue** | Discovery & Claim | `gh issue create` or `gh issue list` |
| **2. Branch** | Isolation | `git checkout main && git pull && git checkout -b ID-desc` |
| **3. Edit** | Implementation | `cat << 'EOF' > file.py` or `nano file.py` |
| **4. Stage** | Preparation | `git add file.py` |
| **5. Commit** | Save | `git commit -m "type: desc (ref #ID)"` |
| **6. Push** | Backup | `git push -u origin HEAD` |
| **7. PR** | Review | `gh pr create --fill` |
| **8. Merge** | Finalize | `gh pr merge --squash` |
| **9. Cleanup** | Hygiene | `git checkout main && git pull && git branch -d ID-desc` |

## 4. Emergency Recovery
If the session context is lost or the environment destabilizes:
1.  **Stop:** Do not execute further changes.
2.  **Verify:** Run `git status` to establish ground truth.
3.  **Sync:** Pull from `main` to ensure local state matches upstream.
