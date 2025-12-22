# 0009 - Session Closeout Protocol

A checklist for ending sessions cleanly, ensuring continuity for tomorrow.

## Philosophy
> "Leave the campsite cleaner than you found it."

A proper closeout takes 5-10 minutes but saves 30+ minutes of confusion in the next session.

## The Closeout Checklist

### 1. Git Hygiene
```bash
# Ensure you're on main with latest
git checkout main
git pull

# Check for uncommitted work
git status                    # Should be clean

# Check for forgotten stashes
git stash list                # Document or drop

# Prune zombie remote refs
git fetch --prune

# Verify branch state
git branch -a                 # Only main should remain locally
```

### 2. Issue Audit
```bash
# List open issues assigned to you or recently touched
gh issue list --state open

# For each completed issue, verify it's closed
gh issue view <ID> --json state
```

### 3. PR Audit
```bash
# No open PRs should remain at session end
gh pr list --state open       # Should be empty

# If PRs exist, either merge or document why deferred
```

### 4. Documentation Sync

| Check | Command/Action |
|:------|:---------------|
| Inventory current? | Review `docs/0003-file-inventory.md` |
| LLD status updated? | Change "Approved" → "Complete" for finished features |
| Lessons captured? | Append to `docs/9000-lessons-learned.md` |
| Journal updated? | Append cross-project lessons to `ENGINEERING-JOURNAL.md` |

### 5. Session Log Entry
Append to `.session-log.md` using the template from `docs/0100-TEMPLATE-GUIDE.md`:

```markdown
## YYYY-MM-DD HH:MM CT | Model Name

### Summary
One paragraph describing the session's main accomplishment.

### Feature Work
- Shipped features, implementations, bug fixes

### Tooling
- Documentation updates, template improvements, process refinements

### Issues
- Created: #XX, #YY
- Closed: #ZZ

### State on Exit
- Branch: main
- Last commit: <sha>
- Open PRs: 0
- Next: What the next session should pick up
```

### 6. Handoff Notes
If work continues in the next session, ensure:
- [ ] Next task is clearly identified
- [ ] Any blockers are documented
- [ ] Relevant file paths are listed for quick context loading

### 7. Final Verification
```bash
# One last check
git status           # Clean
git stash list       # Empty or documented
gh issue list        # No surprises
gh pr list           # Empty
```

## Quick Reference (Copy-Paste Block)

```bash
# Session Closeout Sequence
git checkout main && git pull
git status
git stash list
git fetch --prune
git branch -a
gh issue list --state open
gh pr list --state open
echo "Ready for session-log entry"
```

## Anti-Patterns

| Don't | Do Instead |
|:------|:-----------|
| Close laptop mid-conversation | Complete the turn, write session-log |
| Leave feature branch checked out | Return to main |
| Assume issues auto-closed | Verify with `gh issue view` |
| Skip session-log "just this once" | It's 2 minutes, do it |
| Leave stash entries unexplained | Document or drop them |
