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
