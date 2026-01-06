---
description: Agent onboarding (quick/full mode)
argument-hint: "[--help] [--quick | --full]"
---

# Agent Onboarding

**If `$ARGUMENTS` contains `--help`:** Display the Help section below and STOP. Do not execute onboarding.

Onboard yourself to the Aletheia project by reading and understanding the AgentOS documentation.

## Help

```
/onboard - Agent onboarding for Aletheia project

Usage: `/onboard [--help] [--quick | --full]`

Options:
| Flag | Effect |
|------|--------|
| `--help` | Show this help message and exit |
| `--quick` | Read digest only (~$0.02, 30s) - for simple tasks |
| `--full` | Full onboarding (~$0.35, 2min) - for complex work (default) |

Examples:
- `/onboard --help` - show this help
- `/onboard --quick` - quick onboard for status check
- `/onboard --full` - full onboard for feature work
- `/onboard` - same as --full
```

## Modes

| Mode | Cost | Time | Use Case |
|------|------|------|----------|
| `--quick` | ~$0.02 | ~30s | Simple tasks, status checks, quick fixes |
| `--full` (default) | ~$0.35 | ~2min | Complex features, architecture work, audits |

## Quick Mode (`--quick`)

Read only the executive summary:
1. Read `docs/0000b-ONBOARD-DIGEST.md`
2. State the Bash command oath
3. Acknowledge readiness

**Use when:** Task is simple, context is clear, or you're resuming recent work.

## Full Mode (`--full` or no argument)

Complete onboarding per 0000-GUIDE.md:

### Step 1: Core Documentation (parallel reads)
Read these files simultaneously:
- `docs/0000-GUIDE.md` - System philosophy and rules
- `docs/0000a-IMMEDIATE-PLAN.md` - Current sprint focus
- `docs/6000-open-issues.md` - Open issues (scan titles/labels, skip bodies)

### Step 2: Session Context
- Glob `docs/session-logs/Week-starting-*.md`
- Read the most recent session log (last 3 entries only)

### Step 3: Acknowledge

State the **Bash Command Oath**:
> "I have read the Bash command rules. I will not use pipes or && in Bash commands. I will use single commands with absolute paths."

Then report:
1. Current sprint focus (from 0000a)
2. Top 3 priority issues
3. Last session's state on exit
4. Ready for command

## Rules
- Use absolute paths and `git -C` patterns (no cd && chaining)
- Use `--repo martymcenroe/Aletheia` for all gh commands
- Never use forbidden commands (git reset, git push --force, pip install, etc.)
- All code changes require worktrees - NEVER commit directly to main

## Efficiency Notes

The full onboarding reads ~93KB of documentation (~23K tokens). To minimize cost:

1. **Parallel reads** - Read independent files simultaneously
2. **Scan, don't deep-read** - For 6000-open-issues.md, scan titles/labels, skip issue bodies unless relevant
3. **Recent entries only** - For session logs, read last 3 entries, not the entire file
4. **Regenerate digest** - If `0000b-ONBOARD-DIGEST.md` is stale (>24h), regenerate it:
   ```bash
   poetry run python /c/Users/mcwiz/Projects/Aletheia/tools/generate_onboard_digest.py
   ```
