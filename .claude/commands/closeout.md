---
description: Quick 5-10 min session closeout (0009 Session Mode)
---

# Session Closeout (0009 Session Mode)

Execute the quick session closeout checklist from @docs/0009-session-closeout-protocol.md

This is **explicit approval** to execute all steps autonomously.

## Rules
- Use absolute paths and `git -C` patterns (no cd && chaining)
- Use `--repo martymcenroe/Aletheia` for all gh commands
- Never modify `.claude/settings.local.json` (HAL clause protection)
- Never use forbidden commands (git reset, git push --force, etc.)

## Steps

### S1. Git Hygiene
```bash
git -C /c/Users/mcwiz/Projects/Aletheia checkout main && git -C /c/Users/mcwiz/Projects/Aletheia pull
git -C /c/Users/mcwiz/Projects/Aletheia status
git -C /c/Users/mcwiz/Projects/Aletheia stash list
git -C /c/Users/mcwiz/Projects/Aletheia branch --list
git -C /c/Users/mcwiz/Projects/Aletheia fetch --prune
```

### S2. Issue & PR Audit
```bash
gh issue list --state open --repo martymcenroe/Aletheia
gh pr list --state open --repo martymcenroe/Aletheia
```
- Open PRs should be 0
- Review issues - any completed but unclosed?

### S3. Documentation Sync
```bash
poetry run python /c/Users/mcwiz/Projects/Aletheia/tools/print/print_most_recent_open_issues.py
git -C /c/Users/mcwiz/Projects/Aletheia add docs/6000-open-issues.md
git -C /c/Users/mcwiz/Projects/Aletheia commit -m "docs: regenerate 6000-open-issues.md" --allow-empty
git -C /c/Users/mcwiz/Projects/Aletheia push
```

### S4. Session Log Entry
```bash
poetry run python /c/Users/mcwiz/Projects/Aletheia/tools/append_session_log.py \
    --model "Claude Opus 4.5" \
    --summary "SESSION_SUMMARY_HERE" \
    --created "None" \
    --closed "None" \
    --next "Per user direction"
```
Then commit and push the session log.

### S5. Final Verification
```bash
git -C /c/Users/mcwiz/Projects/Aletheia status
gh pr list --state open --repo martymcenroe/Aletheia
```

Report results in a summary table.
