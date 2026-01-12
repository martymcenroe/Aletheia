# 0806 - Architecture Audit ("Drift Detector")

*Formerly 0110. Moved to 08xx audit series 2026-01-01.*

**Role:** You are the Lead System Architect and Compliance Officer.
**Objective:** Perform a rigorous "Drift Detection" audit. Compare the *theoretical* architecture (Documentation) against the *actual* implementation (Source Code).

## Phase 1: Context Loading (The Map)

1.  **Read Core Architecture:**
    - `docs/0001-architecture.md` (Landing Page) and sub-documents (0001a-g)
    - `docs/0002-coding-standards.md` (The Rules)
    - `docs/0004-orchestration-protocol.md` (The Process)
    - `docs/0200-ADR-index.md` (The Decisions)

2.  **Read Feature Definitions (LLDs):**
    - Scan all `docs/1xxx-*.md` files. These are the promises we made.

3.  **Read the Criteria:**
    - `docs/0601-skill-gemini-lld-review.md` (Specifically the Tier 1/2/3 tables).

## Phase 2: Code Inspection (The Territory)

Read the following critical paths to determine the "As-Built" reality:
1.  **The Orchestrator:** `src/lambda_function.py`
2.  **The Logic Core:** `src/guardrails/*.py`
3.  **The Frontend:** `extension/manifest.json`, `extension/overlay.js`, `extension/service-worker.js`
4.  **The Infrastructure:** `provision.sh`, `deploy.sh`

## Phase 3: The Gap Analysis

Compare **Code vs. Docs** using the specific categories from `docs/0601-skill-gemini-lld-review.md`.

### Tier 1: Security & Correctness (Blocking)
* **Auth/AuthZ:** Does `lambda_function.py` actually enforce the authentication gates described in `1025-linkedin-auth-gate.md`? Or are they bypassed?
* **Input Validation:** Does the code strictly validate inputs as promised in `0001`?
* **Secrets:** Are any API keys hardcoded in `src/` that violate `0002`?

### Tier 2: Testing & Compliance (High Priority)
* **Willison Protocol:** Check `tests/`. Do the tests match the "Fail on Revert" promise? Are there gaps where code exists but tests do not?
* **Manifest Permissions:** Open `extension/manifest.json`. specificially check `permissions` and `host_permissions`. Do they exceed the "Privacy First" ADR `0201`?
* **Data Pipeline:** Does the `denylist.json` loading logic in `src/` match the update strategy defined in `1121-wikipedia-denylist.md`?

### Tier 3: Maintainability (Suggestions)
* **Structure:** Has the code evolved into "Spaghetti" that contradicts the modular design in `0001`?
* **Comments:** Does the code contain "TODOs" that correspond to missing Issues in `docs/6000-open-issues.md`?

---

## Phase 4: Auto-Fix (Default Behavior)

**This audit auto-fixes documentation drift rather than just reporting it.**

When drift is detected:

### Auto-Fixable Drift

| Drift Type | Detection | Auto-Fix |
|------------|-----------|----------|
| **Manifest version** | Compare `manifest.json` `manifest_version` vs docs | Update docs to match actual version |
| **Response type** | Grep code for `stream` vs `return` patterns | Update architecture diagrams |
| **File paths** | Check if referenced files exist at stated paths | Update paths in docs |
| **Permission lists** | Compare manifest `permissions` vs docs | Update permission lists in docs |

### Auto-Fix Procedure

```markdown
For each detected drift:
1. Verify the CODE is the source of truth (not a bug)
2. Update the DOCS to match the code
3. Add "Updated by 0806 audit {date}" comment if needed
4. Log the change to audit output

For security/correctness drift (Tier 1):
1. Do NOT auto-fix - these require investigation
2. Flag as BLOCKING finding
3. Create GitHub issue for human review
```

### Cannot Auto-Fix

- Security vulnerabilities (needs investigation)
- Missing tests (needs implementation)
- Architectural regressions (needs design review)

---

## Output Format: The "As-Built" Audit Report

```markdown
# As-Built Audit Report: {YYYY-MM-DD}

## Executive Summary
{Pass/Fail assessment of architectural drift. Is the code behaving as documented?}

## 🚨 Critical Drift (Tier 1)
* **[Security/Privacy]** {Drift Description}: Doc says "X", but Code does "Y".
    * *Fix:* {Action required}

## ⚠️ Compliance & Testing Gaps (Tier 2)
* **[Permission Creep]** Manifest requests `X`, but LLD `Y` only specified `Z`.
* **[Willison Gap]** Feature `X` implemented in `lambda_function.py` has no corresponding test in `tests/`.

## 📉 Technical Debt (Tier 3)
* **[Documentation Stale]** LLD `1045` refers to a function that was renamed in PR #122.
* **[Code Rot]** `src/legacy_module.py` exists but is not referenced in `0003-file-inventory.md`.

## Recommended Actions
1.  {Step 1}
2.  {Step 2}
