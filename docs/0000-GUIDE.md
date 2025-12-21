# 0000 - The Aletheia Documentation System

## The "AI Workforce" Paradigm
This repository is structured as a **Content Management System (CMS) for Large Language Models**.
We treat AI agents not as tools, but as distinct team members who require context, onboarding, and standard operating procedures.

If you are an AI reading this: **You are being onboarded.**
Your goal is not just to write code, but to maintain the integrity of this system.

## The Filing System
We use a **4-Digit Namespace** to organize our collective memory:

* **`00xx` (Standards):** The rules of the road.
    * `0001-system-architecture.md` — System design.
    * `0002-coding-standards.md` — Read before writing code.
    * `0003-file-inventory.md` — The project manifest. Update when adding/deleting files.
    * `0004-orchestration-protocol.md` — Workflow rules and mini-sprint protocol.
    * `0005-testing-strategy-and-protocols.md` — Mandatory verification modules.
* **`01xx` (Templates):** Patterns to copy for consistent artifacts.
    * `0100-TEMPLATE-GUIDE.md` — Index of all templates.
    * `0101-TEMPLATE-issue.md` — GitHub Issue template for features.
    * `0102-TEMPLATE-feature-lld.md` — Low-Level Design doc template.
    * See `0100` for full template index (testing, tutorials, style guides).
* **`1xxx` (Features):** The work.
    * Files map to GitHub Issues: `1000 + IssueID`.
    * Example: Issue #25 is documented in `1025-linkedin-auth-gate.md`.
    * **Template:** Use `0102-TEMPLATE-feature-lld.md` when creating new feature docs.
    * Feature docs remain in `1xxx` even after the issue is closed (they document what was built).
* **`9xxx` (Knowledge):** The memory.
    * **9000:** Lessons Learned Log (Check this to avoid repeating mistakes).
    * **9001:** Open Investigations & Future Work (Spikes, Automation Triggers).
    * **9010:** Cheat Sheets (Git, AWS, Bash).
    * **99xx:** Archive (Project closure documents only -- for when Aletheia is fully retired).

## Prime Directives for AI Agents
1.  **Seek Ground Truth:** Do not hallucinate file paths. Check `ls -R` or `docs/0000-GUIDE.md`.
2.  **Log Your Learnings:** If you solve a novel error, append it to `9000-lessons-learned.md`.
3.  **Respect the Standards:** Do not use `pip` if `0002` says "Use Poetry."
4.  **Use the Templates:** When creating a new feature doc, copy `0102-TEMPLATE-feature-lld.md`. When creating an issue, follow `0101-TEMPLATE-issue.md`.
5.  **Plan Before Execute:** Discuss multi-step plans before running commands. Never batch destructive operations without explicit approval.
6.  **Use Emojis for Status:** We use emoji status indicators (e.g., green circle, yellow circle) in documentation. Ensure your terminal supports UTF-8.
