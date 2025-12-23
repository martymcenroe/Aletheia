# 0008 - Orchestrator Instructions

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
- If power loss occurs, check `.session-log.md` for last known state

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
1. Have the outgoing agent write to `.session-log.md`
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
| Zombie branches accumulating | Run `git fetch --prune` after every PR merge |
| Issues left open after completion | Use `close #ID` keyword, not `ref #ID` |
| Stash forgotten | Check `git stash list` at session end |
| LLD outdated after implementation | Update status to "Complete" and check DoD items |
| Session-log not updated | Make it the last action before closing |

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

### Benefits
- Main always clean for quick lookups and reviews
- Multiple agents can work in parallel (each in own directory)
- Compare feature vs main side-by-side
- Never accidentally commit to wrong branch

### Rules
- Never checkout the same branch in two worktrees
- Remove worktrees after PR merge to avoid clutter
- Run `git worktree list` periodically to audit
