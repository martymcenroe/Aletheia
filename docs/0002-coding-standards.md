# 0002 - Coding Standards & Operational Procedures

## 1. Prime Directives for AI Agents
* **Plan Before Execute:** Discuss multi-step plans with the Orchestrator BEFORE running commands. Never batch destructive operations without explicit approval.
* **Root-Relative Paths:** You must ALWAYS generate file paths relative to the project root (e.g., `src/guardrails/engine.py`).
* **Explicit Handoff:** At the end of every code generation turn, you MUST provide a "Verification Block".
* **Protocol Adherence:** Strictly follow the Orchestration Protocol defined in `docs/0004-orchestration-protocol.md`.

## 2. Forbidden Commands (NEVER USE)

**Full policy:** See `docs/0015-agent-prohibited-actions.md` for complete list, rationale, and safe alternatives.

AI agents must NEVER use these commands under ANY circumstances:

| Command | Why Forbidden | Use Instead |
|:--------|:--------------|:------------|
| `git reset --hard` | Destroys commit history, irrecoverable | `git revert <commit>` to undo commits safely |
| `git reset HEAD~N` | Rewrites history on shared branches | `git revert` for published commits |
| `git push --force` | Overwrites remote history, breaks collaboration | `git push --force-with-lease` (and only if orchestrator approves) |
| `git clean -fd` | Permanently deletes untracked files | `git status` first, then `git clean -n` (dry run) to preview |
| `pip install` | Bypasses dependency lock file | `poetry add <package>` to maintain poetry.lock |
| `pip freeze` | Creates requirements.txt instead of poetry.lock | `poetry export` if requirements.txt needed |

**Rationale:**
- **History Rewriting:** Git reset rewrites commit history. Once pushed to remote, this breaks other developers' branches and causes "diverged history" errors.
- **Data Loss:** Git reset --hard and git clean -fd permanently delete uncommitted work with no recovery.
- **Dependency Chaos:** pip install modifies site-packages without updating poetry.lock, causing "works on my machine" bugs.

**The Golden Rule:** If you need to undo a commit that's been pushed to remote, use `git revert`. It creates a new commit that undoes the changes, preserving history.

**Example:**
```bash
# WRONG - destroys history
git reset --hard HEAD~1
git push --force

# CORRECT - preserves history
git revert HEAD
git push
```

## 3. Python Development
* **Version:** Python 3.12 (Strict).
* **Dependency Management:**
    * **Local Dev:** Use `poetry add <package>`. NEVER use `pip install` directly.
    * **Lambda Packaging:** Handled by `deploy.sh`.
* **Linting:** Follow PEP 8.
* **Type Hinting:** Required for all function signatures.

## 3. AWS & Infrastructure
* **Philosophy:** "Bare Metal" Scripting (Bash + AWS CLI).
* **Lambda Runtime:** Assume `boto3` is pre-installed.
* **Fail Closed:** Deployment scripts must abort (`exit 1`) if source files are missing. Never deploy placeholders.

## 4. The 9-Step Workflow ("The Flip Turn")
1. **Issue:** Discovery (`gh issue list`).
2. **Worktree:** Isolation (`git worktree add ../Aletheia-{IssueID} -b {IssueID}-short-desc && cd ../Aletheia-{IssueID}`). See Section 10. ❌ NEVER use `git checkout -b` in the main folder.
3. **Edit:** Implementation.
4. **Stage:** Preparation (`git add`).
5. **Commit:** Conventional (`type: desc (ref #ID)`).
6. **Push:** Team Visibility (`git push -u origin HEAD`). REQUIRED - never keep branches local-only. Remote branches provide backup, enable collaboration, and allow orchestrator visibility.
7. **PR:** Review (`gh pr create`).
8. **Merge:** Finalize - return to main folder first (`cd ../Aletheia && gh pr merge`).
9. **Cleanup:** Remove worktree and delete branches (`git worktree remove ../Aletheia-{IssueID} && git branch -d {branch} && git push origin --delete {branch}`).

## 5. Documentation
* **Update First:** Update the relevant `docs/` file *before* writing code.
* **Lessons Learned:** Log new discoveries in `docs/9000-lessons-learned.md`.

## 6. Naming Conventions

### 6.1 Branch Naming
Format: `{IssueID}-short-description`

| Example | Correct |
|:--------|:--------|
| Issue #25 → LinkedIn auth gate | `25-linkedin-auth-gate` ✅ |
| Issue #45 → Hate speech filter | `45-hate-filter` ✅ |
| ~~`feature/linkedin-auth-gate-issue-25`~~ | ❌ Too verbose, wrong format |
| ~~`feat/wire-compliance-engine`~~ | ❌ Missing issue ID |

### 6.2 Documentation File Naming
Format: `1{IssueID}-short-description.md` (for feature specs in the `1xxx` namespace)

| GitHub Issue | Doc File |
|:-------------|:---------|
| #10 | `docs/1010-semantic-guardrails.md` |
| #25 | `docs/1025-linkedin-auth-gate.md` |
| #45 | `docs/1045-hate-filter.md` |

**Note:** GitHub shares a single sequence across Issues, PRs, and Discussions. Plan for Issue IDs up to #999 in the current 4-digit scheme. If the project approaches #900, migrate to a 5-digit namespace.

### 6.3 Commit Message Format
Format: `type: description (KEYWORD #ID)`

Types: `feat`, `fix`, `docs`, `chore`, `test`, `refactor`

**Issue Keywords:**
* **`ref #ID` (Reference):** Use when the commit contributes to an issue but work is **In-Progress**. Do not close the issue.
* **`close #ID` (Close):** Use **ONLY** when the issue's "Definition of Done" is fully met. This automatically closes the issue in GitHub.

Examples:
* `feat: implement semantic guardrail engine (ref #10)`
* `fix: final validation of auth gate (close #25)`
* `chore: rename doc to follow naming convention (ref #25)`

### 6.4 Auto-Closing Issues (Belt & Suspenders)
When an issue is **COMPLETE** (all Definition of Done items checked), use closing keywords in BOTH:
1. **Commit message:** `feat: description (close #ID)`
2. **PR body:** Include `Closes #ID` on its own line

**GitHub Closing Keywords:** `close`, `closes`, `closed`, `fix`, `fixes`, `fixed`, `resolve`, `resolves`, `resolved`

**Rule:** If you know the issue is done, ALWAYS use `close #ID`. Never use `ref #ID` for completed work.

### 6.5 Testing Before Closing (AI Agent Rule)
**CRITICAL:** AI agents must NEVER close an issue until human testing is complete.

**Workflow:**
1. AI agent implements the fix/feature and commits with `(ref #ID)`
2. AI agent reports completion to user: "Fix ready for testing in commit XXXXXX"
3. User tests the implementation
4. User confirms testing results
5. **ONLY THEN** may the AI agent close the issue (manually via `gh issue close`, not via commit message)

**Exception:** For documentation-only issues (no code changes), the AI agent may close immediately after committing.

**Rationale:** Only the human orchestrator can verify that code changes work as expected in the real environment. Premature closure creates false completion signals and breaks project tracking.

**Example:**
```bash
# WRONG - AI agent closes issue in commit message before testing
git commit -m "fix: remove duplicate checkmark (close #93)"

# CORRECT - AI agent uses ref, waits for human testing
git commit -m "fix: remove duplicate checkmark (ref #93)"
# Later, after user confirms testing:
gh issue close 93 --comment "Human testing verified. Closing."
```

## 7. Documentation Standards

### 7.0 Link Formatting
* **Relative Paths Only:** All internal documentation links must use relative paths (e.g., `[0005-testing](0005-testing-strategy-and-protocols.md)`). Never use absolute URLs or search engine URLs.
* **No Google Search Links:** Do not wrap file references in `https://www.google.com/search?q=...` — this is a known Gemini artifact that breaks links.
* **Verify Links:** Before committing, grep for `google.com/search` to catch accidental search URL insertions.

### 7.1 The Inventory Rule
* **Authority:** `docs/0003-file-inventory.md` is the source of truth for file reliability.
* **Requirement:** You MUST add any new file to the inventory immediately upon creation.
* **Status Taxonomy:**
    * 🟢 **Stable:** Verified, Documented, Production-Ready.
    * 🟡 **Beta:** Functional but partial coverage.
    * 🟠 **In-Progress:** Active dev, expect breakage.
    * ⚪ **Placeholder:** Skeleton only.
    * ⚫ **Legacy:** Deprecated (Do not use).
    * ❓ **Unknown:** Needs audit.

### 7.2 Documentation Lives in Main (The "Docs in Main" Policy)
* **Rule:** ALL documentation changes MUST be committed to the `main` branch, NEVER to feature branches.
* **Rationale:** The orchestrator (Marty) needs immediate visibility into all feature documentation (especially `10xx` LLDs) when building implementation plans. Keeping docs in long-running feature branches creates documentation drift and planning blindness.
* **Scope:** This applies to ALL files in `docs/`:
    * Feature specifications (`10xx` files)
    * Templates (`01xx` files)
    * Core standards (`00xx` files)
    * Implementation reports (`docs/reports/`)
    * Session logs (`docs/session-logs/`)
    * All other documentation

**Workflow:**
1. When starting work on a feature, create the `10xx` LLD in `main` branch first
2. Commit the LLD to `main` before creating the feature branch
3. If updates to the LLD are needed during implementation, make those changes in `main` (not the feature branch)
4. Implementation reports go in `main` when complete

**Exception:** Code-adjacent documentation (like inline comments or docstrings) naturally lives with the code in feature branches.

**Migration:** When cherry-picking or merging feature branches created before this policy, extract any NEW documentation files and commit them to `main` separately. See commit `7c8336d` for reference implementation.

### 7.3 The Legacy Protocol ("The Graveyard")
To keep the `docs/` folder focused on *active* truth, we aggressively archive outdated files.

**Criteria for Archival:**
* **Superseded:** A new Spec/ADR replaces the old one (e.g., switching from LangGraph to Naked Python).
* **Abandoned:** A feature was cancelled or "won't fix."
* **Deprecated:** A standard is no longer in force.

**Execution:**
1.  **Move:** Physically move the file to `docs/legacy/`.
    ```bash
    mkdir -p docs/legacy
    git mv docs/1080-old-spec.md docs/legacy/1080-old-spec.md
    ```
2.  **Inventory:** Update `docs/0003-file-inventory.md`:
    * **Status:** Change to ⚫ **Legacy**.
    * **Path:** Update to `docs/legacy/...`.
3.  **Link Rot:** Do NOT worry about breaking links in other legacy files. Active files should never link to legacy files except as historical footnotes.

## 8. File Editing Patterns

### 8.1 Appending to Sectioned Files
When appending to a file with multiple sections (like `ENGINEERING-JOURNAL.md`), insert before the next section marker rather than at EOF.

**Pattern:** Find `---\n\n## NextSection` and insert before it.
```bash
# Insert a row before the "## Publishing" section
sed -i '/^---$/,/^## Publishing/{
  /^## Publishing/i\
| 2025-12-22 | New lesson here | New rule here |
}' docs/ENGINEERING-JOURNAL.md
```

**Alternative with awk** (for complex inserts):
```bash
awk '/^## TargetSection/{found=1} found && /^---$/{print "| NEW ROW |"; found=0} 1' file.md > tmp && mv tmp file.md
```

## 9. JavaScript / Extension Development

### 9.1 Never Use innerHTML with User Content
When displaying user-selected text or any external content, ALWAYS use `element.textContent`, NEVER `innerHTML`.

**Why:** Prevents Self-XSS attacks. A user could select malicious text like `<img src=x onerror=alert(1)>`.

**Rule:**
```javascript
// WRONG — XSS vulnerability
overlay.innerHTML = `Saved: ${selectedWord}`;

// CORRECT — safe
overlay.textContent = `Saved: ${selectedWord}`;
```

### 9.2 Shadow DOM for Injected UI
All UI injected into host pages must use Shadow DOM. See ADR-002 in `docs/0001-system-architecture.md`.
```javascript
// CORRECT — isolated styling
const host = document.createElement('div');
const shadow = host.attachShadow({ mode: 'closed' });
shadow.innerHTML = `<style>/* our styles */</style><div class="overlay">Content</div>`;
document.body.appendChild(host);
```

### 9.3 Dual-Extension Requirement (Chrome + Firefox)
The extension is maintained as **two separate codebases**:
- `extensions/chrome/` — Manifest V3 for Chrome (uses `chrome.*` APIs)
- `extensions/firefox/` — Manifest V2 for Firefox (uses `browser.*` APIs)

**Rule:** When making ANY change to extension logic, you MUST:
1. Apply the change to BOTH directories
2. Test in BOTH Chrome and Firefox before committing
3. Note in the commit message that both were updated

**API Differences:**
| Chrome V3 | Firefox V2 |
|:----------|:-----------|
| `chrome.scripting.executeScript()` | `browser.tabs.executeScript()` |
| `chrome.action.*` | `browser.browserAction.*` |
| `chrome.storage.local.get()` | `browser.storage.local.get()` |

**Rationale:** Firefox MV3 support is immature. Maintaining separate codebases avoids cross-browser timing bugs that are nearly impossible to debug.

### 9.4 Unit Testing

All extension logic (excluding pure DOM manipulation) must be unit tested. Use mocks for `chrome.*` APIs. No "logic in view" — separate pure functions where possible to make testing easier.

## 10. Git Worktree Protocols

### 10.1 The "Parallel Universe" Model
We use `git worktree` to maintain isolated environments for different features without destroying local state (e.g., server logs, temp files).

**Directory Structure:**
```text
Projects/
├── Aletheia/              # [Main Worktree] Always kept on 'main'
├── Aletheia-95-security/  # [Linked Worktree] Checked out to 'feature/95-...'
└── Aletheia-80-wire/      # [Linked Worktree] Checked out to 'feature/80-...'

```

### 10.2 The Golden Rule

**You cannot check out the same branch in two worktrees simultaneously.**

* **The Error:** `fatal: 'main' is already used by worktree`
* **The Cause:** You are in a feature folder trying to `git checkout main`, but `main` is already active in the root `Aletheia/` folder.
* **The Fix:**
* **To update:** Do not checkout main. Run `git fetch origin main` and `git merge origin/main`.
* **To browse:** Open a separate terminal in the root `Aletheia/` folder.



### 10.3 Common Commands

* **Create:** `git worktree add ../Aletheia-99-feature -b feature/99-name`
* **List:** `git worktree list`
* **Remove:** `git worktree remove ../Aletheia-99-feature` (then delete the folder)

### 11.3 The "No Nagging" Clause
If you cannot execute code (e.g., Chat interface), do NOT stop to ask the user to verify.
1.  Write the code.
2.  Write the `manual_smoke.py` tool.
3.  Submit both as complete.
**Rationale:** The user is the final verifier, not your debug loop. Do not hand work back until the solution is proposed complete.
