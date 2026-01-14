# 10100 - Template Guide

## Purpose
This document indexes all templates in the `101xx` namespace. Templates provide consistent patterns for common artifacts.

## How to Use Templates
1. Find the appropriate template below
2. Copy the template file to the correct location
3. Rename according to conventions (see `AgentOS:standards/0002-coding-standards`)
4. Fill in all sections; write "N/A" for sections that don't apply
5. **Never delete numbered sections** - this breaks cross-document references

---

## Template Index

### 101x: Core Templates
| File | Purpose | Status |
|:-----|:--------|:-------|
| `10100-TEMPLATE-GUIDE.md` | This file. Index of all templates. | Active |
| `10101-TEMPLATE-issue.md` | GitHub Issue template for features | Active |
| `10102-TEMPLATE-feature-lld.md` | Low-Level Design doc for features | Active |
| `10103-TEMPLATE-implementation-report.md` | Post-implementation report for completed features | Active |
| `10104-TEMPLATE-adr.md` | Architecture Decision Record | Active |
| `10105-TEMPLATE-implementation-plan.md` | Implementation plan for process/config changes (not code) | Active |
| `10108-lld-pre-implementation-review.md` | LLD review checklist (run BEFORE coding) | Active |

**Note:** Gemini LLD review procedure moved to `docs/skills/10601-skill-gemini-lld-review.md` (skill instructions series).

### 1011x: Testing Templates
| File | Purpose | Status |
|:-----|:--------|:-------|
| `10110-TEMPLATE-test-plan.md` | Test strategy for a feature/release | Future |
| `10111-TEMPLATE-test-script.md` | Generic manual test procedure (basic) | Active |
| `10112-TEMPLATE-browser-extension-test-script.md` | Browser extension test script for non-technical users | Active |
| `10113-TEMPLATE-test-report.md` | Results documentation after test run | Active |

### 1012x: Content & Tutorial Templates
| File | Purpose | Status |
|:-----|:--------|:-------|
| `10120-TEMPLATE-tutorial-plan.md` | Outline for a tutorial video/doc | Future |
| `10121-TEMPLATE-tutorial-script.md` | Shot-by-shot script for video recording | Future |
| `10122-TEMPLATE-support-article.md` | FAQ/troubleshooting article format | Future |

### 1013x: Release & Operations Templates
| File | Purpose | Status |
|:-----|:--------|:-------|
| `10130-TEMPLATE-release-notes.md` | Changelog format for releases | Future |
| `10131-TEMPLATE-incident-report.md` | Post-mortem for outages/bugs | Future |
| `10132-TEMPLATE-sprint-retro.md` | Mini-sprint retrospective | Future |

### 1014x: Style Guides
| File | Purpose | Status |
|:-----|:--------|:-------|
| `10140-STYLE-ui-copy.md` | Tone, voice, terminology for user-facing text | Future |
| `10141-STYLE-error-messages.md` | How to write error messages | Future |
| `10142-STYLE-commit-messages.md` | Expanded commit convention guide | Future |

### 1015x-1018x: Reserved
| Range | Category | Status |
|:------|:---------|:-------|
| `1015x` | Security (threat models, reviews) | Future |
| `1016x` | Compliance (privacy, store submission) | Future |
| `1017x` | Integration (API docs, webhooks) | Future |
| `1018x` | Infrastructure (runbooks, deployment) | Future |

---

## Adding New Templates

1. Choose the appropriate range from above
2. Use the next available number in that range
3. Name format: `101XX-TEMPLATE-{name}.md` or `101XX-STYLE-{name}.md`
4. Update this guide with the new entry
5. Update `docs/standards/10003-file-inventory.md`

## Session Logs

Session logs are stored in `docs/session-logs/` with daily files using ISO 8601 date format.

**Current format:** Daily files (`YYYY-MM-DD.md`) - This is the standard.

**Legacy format:** Weekly files (`Week-starting-YYYY-MM-DD.md`) exist from earlier sessions. Per WORM policy, these are not migrated. They remain as historical record.

**Day boundary:** 3:00 AM CT to following day 2:59 AM CT (work at 2am goes in previous day's log)

### Getting Timestamps on Windows
**CORRECT command for Windows:**
```bash
powershell.exe -Command "Get-Date -Format 'yyyy-MM-dd HH:mm'"
```

**WRONG - Do NOT use:**
```bash
TZ='America/Chicago' date   # Returns UTC, not local time
```

**AI Agents:** On Windows, use PowerShell's `Get-Date` for timestamps. Git Bash's `date` command doesn't support Windows timezones. If unsure, ask the user for the current time.

### File Naming
- Format: `YYYY-MM-DD.md` (daily files)
- Use ISO 8601 format (YYYY-MM-DD) with zero-padded month and day for proper sorting
- Example: Work done at 2am on 2025-12-22 goes in `2025-12-21.md` (previous day, before 3am boundary)
- Example: Work done at 9am on 2025-12-22 goes in `2025-12-22.md` (same day, after 3am boundary)

### Entry Template
```markdown
## YYYY-MM-DD HH:MM CT | Model Name

### Summary
One paragraph describing the session's main accomplishment.

### Feature Work
- Bullet list of shipped features, implementations, bug fixes

### Tooling
- Bullet list of documentation updates, template improvements, process refinements

### Issues
- Created: #XX, #YY
- Closed: #ZZ

### State on Exit
- Branch: `branch-name`
- Last commit: `sha` or message
- Open PRs: N
- Next: What the next session should pick up
```

### File Size Limits

**Maximum file size: 75KB** (~20,000 tokens)

Daily files should rarely hit this limit. If a single day's log approaches 75KB, split it:
1. Create a new file with `-part2` suffix: `YYYY-MM-DD-part2.md`
2. Continue new entries in the part2 file
3. Add a note at the end of part1: `*Continued in YYYY-MM-DD-part2.md*`

**Why:** The Read tool has a 25,000 token limit (~80-90KB). Keeping files under 75KB ensures agents can always read the full file without needing offset/limit parameters.

**Check before appending:**
```bash
wc -c docs/session-logs/YYYY-MM-DD.md
# If over 75000 bytes, create part2 file
```

### Daily File Header
Each daily file should start with:
```markdown
# Session Log: YYYY-MM-DD

**Period:** YYYY-MM-DD 3:00 AM CT → YYYY-MM-DD+1 2:59 AM CT

---
```

**Entries must be sorted chronologically** (oldest at top, newest at bottom) so the log reads like a story.

---

## Slash Commands (`.claude/commands/`)

Slash commands are Markdown files in `.claude/commands/` that Claude Code executes as prompts.

### Required Structure

Every slash command **MUST** support `--help`:

```markdown
---
description: Brief description (shown in /help)
argument-hint: "[--help] [other args]"
---

# Command Name

**If `$ARGUMENTS` contains `--help`:** Display the help section below and stop.

## Help

Usage: `/command [--help] [arguments]`

| Argument | Description |
|----------|-------------|
| `--help` | Show this help message |
| ... | ... |

**Examples:**
- `/command` - default behavior
- `/command --help` - show help
- `/command arg1` - with argument

---

## Execution

[Rest of command logic - only runs if --help not present]
```

### Naming Convention
- File: `.claude/commands/{name}.md`
- Invoke: `/{name}` or `/{name} --help`

### Existing Commands
| Command | File | Purpose |
|---------|------|---------|
| `/audit` | `audit.md` | Full 08xx audit suite |
| `/cleanup` | `cleanup.md` | Session cleanup (quick/normal/full) |
| `/full-cleanup` | `full-cleanup.md` | Comprehensive cleanup (0009 Full Mode) |
| `/friction` | `friction.md` | Permission friction analysis |
| `/onboard` | `onboard.md` | Agent onboarding guide |
