# 0000 - The Aletheia Documentation System

## The "AI Workforce" Paradigm
This repository is structured as a **Content Management System (CMS) for Large Language Models**.
We treat AI agents not as tools, but as distinct team members who require context, onboarding, and standard operating procedures.

If you are an AI reading this: **You are being onboarded.**
Your goal is not just to write code, but to maintain the integrity of this system.

## The Filing System
We use a **4-Digit Namespace** to organize our collective memory:

* **`0xxx` (Standards):** The rules of the road.
    * Read `0001-system-architecture.md` for the system design.
    * Read `0002-coding-standards.md` before writing a line of code.
    * Read `0003-file-inventory.md` for the strict project manifest. Update this file if you add/delete files.
    * Read `0004-orchestration-protocol.md` for the workflow rules.
* **`1xxx` (Features):** The work.
    * Files map to GitHub Issues: `1000 + IssueID`.
    * Example: Issue #25 is documented in `1025-linkedin-auth-gate.md`.
    * **Template:** Use `1000-TEMPLATE-feature.md` when creating new feature docs.
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
4.  **Use the Template:** When creating a new feature doc, copy `1000-TEMPLATE-feature.md` and fill in all sections, especially **Section 5: Verification & Testing**.
5.  **Plan Before Execute:** Discuss multi-step plans before running commands. Never batch destructive operations without explicit approval.
6.  **Use ASCII-Safe Text:** Avoid smart quotes, em-dashes, and non-ASCII characters in documentation to prevent encoding corruption (mojibake) across different LLM interfaces.
