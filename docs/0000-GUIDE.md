# 0000 - The Aletheia Documentation System

## The "AI Workforce" Paradigm
This repository is structured as an **Agent Operating System (AOS)**—executable documentation that AI agents run as their program.

We treat AI agents not as tools, but as distinct team members who require context, onboarding, and standard operating procedures. The docs aren't just reference material—they're the instructions agents execute.

If you are an AI reading this: **You are being onboarded.**
Your goal is not just to write code, but to maintain the integrity of this system.

## Agent Operating System: What This Really Is

This is more than a Content Management System. It's:

| Layer | What It Does | Examples |
|-------|--------------|----------|
| **Process Automation** | Checklists that execute, not just document | 0009 (Closeout), 0011 (Cleanup) |
| **Context Persistence** | State preserved across sessions and agents | Session logs, 0000a-IMMEDIATE-PLAN |
| **Agent Orchestration** | Who does what, when, how | CLAUDE.md, GEMINI.md, 0004 |
| **Reality Verification** | Don't trust metadata—verify actual state | 0011 Section 6 (0000a check) |
| **Executable Standards** | Rules that agents can follow literally | 0002 (Coding), Forbidden Commands |

**The Operating System Metaphor:**
- **Docs = Programs** — Agents read and execute them
- **Session Logs = Process State** — Preserved across restarts
- **0000a-IMMEDIATE-PLAN = Current Task** — The foreground process
- **Checklists = Subroutines** — Called when conditions are met
- **Orchestrator = Scheduler** — Decides which agent runs which task

## Philosophy: Eliminating Context Burden

**The Problem:** LLM sessions have limited context windows. Orchestrators (humans) cannot reliably remember what was discussed across dozens of sessions with multiple AI agents. Web-based chat sessions are ephemeral and hard to search. Context is lost, work is repeated, momentum dies.

**The Solution:** Everything an LLM needs to know lives in this system. The orchestrator's job is NOT to remember context—it's to point the LLM at the right documents.

**How to Start Any Session:**
1. Read this file (`docs/0000-GUIDE.md`) - understand the system
2. Read `docs/0000a-IMMEDIATE-PLAN.md` - current focus and context
3. Read `docs/6000-open-issues.md` - what's open
4. Read relevant session logs in `docs/session-logs/` - recent history

**The Guarantee:** If you follow these steps, you have everything you need. No asking "what did we discuss last time?" No orchestrator scrambling to recall context. The AOS is the single source of truth.

**Your Responsibility:** Maintain this guarantee. Update documentation. Write session logs. Keep the system accurate so the next agent (or your future self) can pick up seamlessly.

---

# Project Aletheia: AI Workforce Guide

## 1. Context & Standards
All agents must adhere to the core documentation:
- **Project Overview:** `README.md` (at repository root - read this first for project context)
- **Standards:** `docs/0002-coding-standards.md` (The 9-Step Flip Turn)
- **Inventory:** `docs/0003-file-inventory.md`

## 2. Agent Routing
Identify yourself and load your specific protocols immediately:

### ♊ If you are Gemini:
Read and execute `GEMINI.md` (in repository root).
*Critical: You must initiate the Identity Handshake defined there.*

### 🔶 If you are Claude:
Read and execute `CLAUDE.md` (in repository root).

### 🤖 If you are ChatGPT:
Read and execute `CHATGPT.md` (in repository root).

## 3. The Filing System
We use a **4-Digit Namespace** to organize our collective memory:

* **`00xx` (Standards):** The rules of the road.
    * `0000a-IMMEDIATE-PLAN.md` — **Current sprint focus.** Read this second, after 0000.
    * `0001-system-architecture.md` — System design.
    * `0002-coding-standards.md` — Read before writing code.
    * `0003-file-inventory.md` — The project manifest. Update when adding/deleting files.
    * `0004-orchestration-protocol.md` — Workflow rules and mini-sprint protocol.
    * `0005-testing-strategy-and-protocols.md` — Mandatory verification modules.
* **`01xx` (Templates):** Patterns to copy for consistent artifacts.
    * `0100-TEMPLATE-GUIDE.md` — Index of all templates.
    * `0101-TEMPLATE-issue.md` — GitHub Issue template for features.
    * `0102-TEMPLATE-feature-lld.md` — Low-Level Design doc template.
    * `0104-TEMPLATE-adr.md` — Architecture Decision Record template.
    * See `0100` for full template index (testing, tutorials, style guides).
* **`02xx` (ADRs):** Architecture Decision Records.
    * `0200-ADR-index.md` — Master index of all ADRs with category cross-reference.
    * Records significant architecture decisions following Michael Nygard's format.
    * Status: Proposed → Implemented → Deprecated → Superseded.
    * Every ADR requires a Security Risk Analysis section.
* **`1xxx` (Features):** The work.
    * Files map to GitHub Issues: `1000 + IssueID`.
    * Example: Issue #25 is documented in `1025-linkedin-auth-gate.md`.
    * **Template:** Use `0102-TEMPLATE-feature-lld.md` when creating new feature docs.
    * Feature docs remain in `1xxx` even after the issue is closed (they document what was built).
* **`6xxx` (Reports):** Generated reports.
    * `6000-open-issues.md` — **Current open GitHub issues.** Regenerate with `poetry run python tools/print/print_most_recent_open_issues.py`.
* **`9xxx` (Knowledge):** The memory.
    * **9000:** Lessons Learned — **Aletheia-specific** gotchas and solutions (Chrome extension, Bedrock, this codebase).
    * **9001:** Open Investigations & Future Work (Spikes, Automation Triggers).
    * **9010:** Cheat Sheets (Git, AWS, Bash).
    * **99xx:** Archive (Project closure documents only — for when Aletheia is fully retired).
    * **Cross-project lessons** (Git workflow, AWS deployment, general engineering) live in the [Engineering Journal](https://github.com/martymcenroe/martymcenroe/blob/main/ENGINEERING-JOURNAL.md).

## Prime Directives for AI Agents
1.  **Seek Ground Truth:** Do not hallucinate file paths. Check `ls -R` or `docs/0000-GUIDE.md`.
2.  **Log Your Learnings:** If you solve a novel error, append it to `9000-lessons-learned.md`.
3.  **NEVER Use Forbidden Commands:** Absolutely forbidden: `git reset`, `git push --force`, `git clean -fd`, `pip install`. See [0002-coding-standards.md](0002-coding-standards.md) Section 2 for complete list and safe alternatives.
4.  **Use Poetry for Dependencies:** ALWAYS use `poetry add <package>`, NEVER `pip install`. Pip bypasses the lock file and causes dependency chaos.
5.  **Push Branches to Remote:** NEVER keep branches local-only. Use `git push -u origin HEAD` immediately after creating branch. Local-only branches violate team collaboration.
6.  **Delete Both Local and Remote Branches:** After merge, delete local (`git branch -d`) AND remote (`git push origin --delete`) branches. Zombie remote branches clutter the repository.
7.  **Use the Templates:** When creating a new feature doc, copy `0102-TEMPLATE-feature-lld.md`. When creating an issue, follow `0101-TEMPLATE-issue.md`.
8.  **Plan Before Execute:** Discuss multi-step plans before running commands. Never batch destructive operations without explicit approval.
9.  **Use Emojis for Status:** We use emoji status indicators (e.g., green circle, yellow circle) in documentation. Ensure your terminal supports UTF-8.
10.  **Log Your Sessions:** At session end, append a summary to `docs/session-logs/YYYY-MM-DD.md` (Monday date). Week boundary is Monday 3:00 AM CT. See `docs/0100-TEMPLATE-GUIDE.md` for format.

## Document Mutability Rules (WORM Policy)

Some documents are **immutable** (Write Once Read Many) — they capture historical state and must never be modified after creation. Others are **living documents** that should be updated to reflect current reality.

### Immutable Documents (NEVER modify)

| Category | Location | Rationale |
|----------|----------|-----------|
| **Session Logs** | `docs/session-logs/*.md` | Historical record of what happened when |
| **Closed Issue Reports** | `docs/6001-closed-issues.md` | Archive of completed work |
| **Implementation Reports** | `docs/reports/*/` | Point-in-time snapshots of deliverables |
| **Previous ADRs** | `docs/02xx-ADR-*.md` | Architectural history (supersede, don't edit) |

**If historical docs contain stale references (e.g., old file paths):** Leave them. They document what was true at that time. Future readers understand context evolves.

### Living Documents (Update freely)

| Category | Location | Update When |
|----------|----------|-------------|
| **Operating Procedures** | `docs/0000-GUIDE.md`, `CLAUDE.md`, `GEMINI.md` | Rules change |
| **Current Plan** | `docs/0000a-IMMEDIATE-PLAN.md` | Priorities shift |
| **Open Issues** | `docs/6000-open-issues.md` | Regenerate from GitHub |
| **File Inventory** | `docs/0003-file-inventory.md` | Files added/removed |
| **Feature LLDs** | `docs/1xxx-*.md` (open issues) | Design evolves before implementation |
| **Lessons Learned** | `docs/9000-lessons-learned.md` | New knowledge gained |

### ADR Special Rules

- **Never edit existing ADRs** without orchestrator approval
- **To change a decision:** Create a new ADR that supersedes the old one
- **Minor fixes** (typos, broken links): Ask orchestrator first
- ADRs document *why* decisions were made at a point in time

### Directory Structure Changes

When the repo structure changes (e.g., `extension/` → `extension-chrome-V3/`):
- **Update living docs** to reflect new paths
- **Leave historical docs alone** — they document what existed then
- **Create new LLD versions** if needed rather than editing closed issues
