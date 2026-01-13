# 0008 - Orchestrator Instructions

> **DEPRECATED (2026-01-09):** This document is superseded by the **09xx Operational Runbooks** namespace.
> See `docs/0900-runbook-index.md` for the new structure.
> This file is retained for historical reference per WORM policy.

---

Rules and guidance for the human orchestrator managing multi-agent AI sessions.

## 1. Session Continuity

### 1.1 Never Interrupt Gemini Mid-Turn
Gemini's context resets completely on interruption. Unlike Claude (which can recover via transcript), Gemini loses all session state. If you must stop:
- Wait for the current turn to complete
- Ask Gemini to write a handoff summary before closing

### 1.2 Monitor Timestamp Drift
Check the timestamp in turn meta-tags. LLMs can lose track of time during long sessions. If timestamps drift significantly:
- Explicitly state the current time
- Consider starting a fresh session

### 1.3 Power & Connectivity
- Use a UPS on desktop machines
- Save work frequently during long sessions
- If power loss occurs, check `docs/session-logs/` for last known state

## 2. Agent Management

### 2.1 Model Selection
| Task Type | Recommended Model |
|:----------|:------------------|
| Planning, architecture, design | Claude Opus |
| Implementation, code generation | Claude Sonnet (via Claude Code) |
| Security review, compliance audit | Gemini Pro |
| Quick questions, simple tasks | Claude Haiku |

### 2.2 Handoff Protocol
When switching between agents:
1. Have the outgoing agent write to the current week's session log (see Section 7)
2. Provide the incoming agent with:
   - Current branch
   - Last commit SHA
   - Specific file(s) to read for context
   - Clear task description

### 2.3 Agent Colors (GitHub Projects)
- Marty (Orchestrator): Blue
- Claude Opus: Orange
- Claude Sonnet: Yellow
- Gemini Pro: Purple
- Deprecated agents: White

## 3. Quality Gates

### 3.1 Before Merging Any PR
- [ ] All smoke test steps passed
- [ ] Definition of Done items checked
- [ ] Lessons learned captured
- [ ] Inventory updated if new files created

### 3.2 Before Ending Any Session
- [ ] Follow `0009-session-closeout-protocol.md`

## 4. Cost Optimization

### 4.1 Token Efficiency
- Use Opus for planning (high reasoning, low output)
- Use Sonnet for implementation (moderate reasoning, high output)
- Avoid regenerating large artifacts — iterate with edits

### 4.2 Context Management
- Compact conversations when context fills
- Use transcript files for recovery, not re-explanation
- Reference doc paths instead of pasting full content

## 5. Common Pitfalls

| Pitfall | Prevention |
|:--------|:-----------|
| Zombie remote branches accumulating | Delete BOTH local and remote branches after merge: `git branch -d {branch} && git push origin --delete {branch}` |
| Using git reset instead of git revert | NEVER use `git reset` - see 0002 Section 2 for forbidden commands |
| Keeping branches local-only | ALWAYS push branches to remote: `git push -u origin HEAD` |
| Using pip instead of poetry | ALWAYS use `poetry add`, NEVER `pip install` |
| Issues left open after completion | Use `close #ID` keyword in commit message, not `ref #ID` |
| Stash forgotten | Check `git stash list` at session end |
| LLD outdated after implementation | Update status to "Complete" and check DoD items |
| Session-log not updated | Make it the last action before closing (see Section 7) |
| Worktree removed but branches still exist | After `git worktree remove`, also delete local and remote branches |

## 6. Parallel Branch Work with Git Worktree

### Recommended Pattern
Keep `main` in your primary directory for docs, reviews, and stable reference. Use worktrees for feature branches:
```
~/Projects/Aletheia/        → always main (stable)
~/Projects/Aletheia-77/     → worktree for issue #77
~/Projects/Aletheia-80/     → worktree for issue #80
```

### Creating a Worktree
```bash
# From main, create a new worktree + branch based on main
git worktree add ../Aletheia-80 -b 80-wire-agent main

# Or attach to an existing branch
git worktree add ../Aletheia-77 77-action-feedback

# Or attach to an existing remote branch
git fetch
git worktree add ../Aletheia-80 origin/80-wire-agent
```

### Managing Worktrees
```bash
# List all worktrees
git worktree list

# Remove a worktree when done (from main directory)
git worktree remove ../Aletheia-80

# Prune stale worktree references
git worktree prune
```

### Complete Cleanup After Merge
After merging a PR for a worktree-based branch, perform BOTH cleanup steps:

```bash
# 1. Remove the worktree directory
git worktree remove ../Aletheia-80

# 2. Delete the local branch (from main worktree)
cd /c/Users/mcwiz/Projects/Aletheia  # Return to main worktree
git checkout main && git pull
git branch -d 80-wire-agent

# 3. Delete the remote branch
git push origin --delete 80-wire-agent
```

**Critical:** Removing the worktree does NOT delete the branch (local or remote). You must explicitly delete both to prevent zombie branches.

### Benefits
- Main always clean for quick lookups and reviews
- Multiple agents can work in parallel (each in own directory)
- Compare feature vs main side-by-side
- Never accidentally commit to wrong branch

### Rules
- Never checkout the same branch in two worktrees
- Remove worktrees after PR merge to avoid clutter
- Delete both local AND remote branches after removing worktree
- Run `git worktree list` periodically to audit

## 7. Session Log Management

Session logs live in `docs/session-logs/` with weekly files named by Monday date.

### Week Boundary
- **Cutoff:** Monday 3:00 AM CT
- Sunday 11pm work → current week's file
- Monday 9am work → new week's file

### Getting Current Time on Windows
**CORRECT command for Windows:**
```bash
powershell.exe -Command "Get-Date -Format 'yyyy-MM-dd HH:mm'"
```

**WRONG - Do NOT use:**
```bash
TZ='America/Chicago' date   # Returns UTC, not local time
```

**Why:** Git Bash's `date` command doesn't have Windows timezone awareness. It returns UTC regardless of the `TZ` variable. Use PowerShell's `Get-Date` to get actual local time.

**For AI Agents:** If unsure, ASK THE USER what the current time is. Don't assume automated commands work correctly.

**For Orchestrator:** Always verify the week file before agents append. If it's before Monday 3 AM CT, entries go in the CURRENT week's file, not next week's file.

### File Naming
```
docs/session-logs/2025-12-16.md  ← Week of Dec 16-22
docs/session-logs/2025-12-23.md  ← Week of Dec 23-29
```

### Creating a New Week's File
When the week boundary crosses, create the new file:

```bash
# Calculate the Monday date (adjust for your OS)
MONDAY=$(date -d "last monday" +%Y-%m-%d)

# Create the file with header
cat > docs/session-logs/${MONDAY}.md << 'EOF'
# Session Log: Week of ${MONDAY}

Week boundary: Monday 3:00 AM CT to following Monday 2:59 AM CT

---
EOF
```

Or manually:
1. Copy header from previous week's file
2. Update the date in the `# Session Log: Week of` line
3. Clear the entries (keep the `---` separator)

### Orchestrator Checklist (Week Start)
- [ ] Check if new session log file needed (Monday mornings)
- [ ] If agents worked over the weekend, verify entries went to correct week
- [ ] Commit new week's file before assigning work

### Edge Cases
| Situation | Action |
|:----------|:-------|
| Agent starts session, no file exists | Agent creates file with header |
| Late Sunday session crosses midnight | Entry goes in prior week's file (until 3am Mon) |
| Extended session spans week boundary | Use the session END date's week file |
| Forgot to create file, agent already wrote | Move entry to correct file, commit both |
