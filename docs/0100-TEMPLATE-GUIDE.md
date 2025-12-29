# 0100 - Template Guide

## Purpose
This document indexes all templates in the `01xx` namespace. Templates provide consistent patterns for common artifacts.

## How to Use Templates
1. Find the appropriate template below
2. Copy the template file to the correct location
3. Rename according to conventions (see `0002-coding-standards.md`)
4. Fill in all sections; delete "Future" placeholders if not applicable

---

## Template Index

### 010x: Core Templates
| File | Purpose | Status |
|:-----|:--------|:-------|
| `0100-TEMPLATE-GUIDE.md` | This file. Index of all templates. | Active |
| `0101-TEMPLATE-issue.md` | GitHub Issue template for features | Active |
| `0102-TEMPLATE-feature-lld.md` | Low-Level Design doc for features | Active |
| `0103-TEMPLATE-chore-issue.md` | Lightweight issue for chores/bugs | Future |
| `0104-TEMPLATE-adr.md` | Architecture Decision Record | Future |

### 011x: Testing Templates
| File | Purpose | Status |
|:-----|:--------|:-------|
| `0110-TEMPLATE-test-plan.md` | Test strategy for a feature/release | Future |
| `0111-TEMPLATE-test-script.md` | Generic manual test procedure (basic) | Active |
| `0112-TEMPLATE-browser-extension-test-script.md` | Browser extension test script for non-technical users | Active |
| `0113-TEMPLATE-test-report.md` | Results documentation after test run | Future |

### 012x: Content & Tutorial Templates
| File | Purpose | Status |
|:-----|:--------|:-------|
| `0120-TEMPLATE-tutorial-plan.md` | Outline for a tutorial video/doc | Future |
| `0121-TEMPLATE-tutorial-script.md` | Shot-by-shot script for video recording | Future |
| `0122-TEMPLATE-support-article.md` | FAQ/troubleshooting article format | Future |

### 013x: Release & Operations Templates
| File | Purpose | Status |
|:-----|:--------|:-------|
| `0130-TEMPLATE-release-notes.md` | Changelog format for releases | Future |
| `0131-TEMPLATE-incident-report.md` | Post-mortem for outages/bugs | Future |
| `0132-TEMPLATE-sprint-retro.md` | Mini-sprint retrospective | Future |

### 014x: Style Guides
| File | Purpose | Status |
|:-----|:--------|:-------|
| `0140-STYLE-ui-copy.md` | Tone, voice, terminology for user-facing text | Future |
| `0141-STYLE-error-messages.md` | How to write error messages | Future |
| `0142-STYLE-commit-messages.md` | Expanded commit convention guide | Future |

### 015x-018x: Reserved
| Range | Category | Status |
|:------|:---------|:-------|
| `015x` | Security (threat models, reviews) | Future |
| `016x` | Compliance (privacy, store submission) | Future |
| `017x` | Integration (API docs, webhooks) | Future |
| `018x` | Infrastructure (runbooks, deployment) | Future |

---

## Adding New Templates

1. Choose the appropriate range from above
2. Use the next available number in that range
3. Name format: `01XX-TEMPLATE-{name}.md` or `01XX-STYLE-{name}.md`
4. Update this guide with the new entry
5. Update `0003-file-inventory.md`

## Session Logs

Session logs are stored in `docs/session-logs/` with weekly files using ISO 8601 date format.

**Week boundary:** Monday 3:00 AM CT to following Monday 2:59 AM CT

### ⚠️ CRITICAL: Timestamp Issue on Windows
**Git Bash (MINGW64) timestamp bug:** The command `TZ='America/Chicago' date` on Windows shows **UTC time with a "CT" label**, NOT actual Central Time. It will be 6 hours ahead during CST (winter).

**AI Agents:** Do NOT trust automated timestamp commands on Windows. Ask the user for the current time OR use the time stated by the orchestrator in conversation.

### File Naming
- Format: `Week-starting-YYYY-MM-DD.md` where the date is the Monday that starts the week
- Use ISO 8601 format (YYYY-MM-DD) with zero-padded month and day for proper sorting
- Example: Work done Sunday night 2025-12-21 at 11pm goes in `Week-starting-2025-12-15.md` (prior week)
- Example: Work done Monday 2025-12-22 at 9am goes in `Week-starting-2025-12-22.md` (new week)

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

### Weekly File Header
Each weekly file should start with:
```markdown
# Session Log: Week starting YYYY-MM-DD

**Period:** Monday YYYY-MM-DD 3:00 AM CT → Monday YYYY-MM-DD 2:59 AM CT

---
```

**Entries must be sorted chronologically** (oldest at top, newest at bottom) so the log reads like a story.
