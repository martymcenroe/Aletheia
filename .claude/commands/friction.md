---
description: Analyze session logs for permission friction (15-30 min)
argument-hint: "[--help] [--sessions N] [--since YYYY-MM-DD] [--file PATH]"
---

# Permission Friction Analysis (0824)

**If `$ARGUMENTS` contains `--help`:** Display the Help section below and STOP.

---

## Help

Usage: `/friction [--help] [--sessions N] [--since YYYY-MM-DD] [--file PATH]`

| Argument | Description |
|----------|-------------|
| `--help` | Show this help message and exit |
| `--sessions N` | Analyze last N session entries (default: 5) |
| `--since YYYY-MM-DD` | Analyze entries since date |
| `--file PATH` | Analyze specific log file |

**Examples:**
- `/friction --help` - show this help
- `/friction` - analyze last 5 session entries
- `/friction --sessions 10` - analyze last 10 entries
- `/friction --since 2026-01-01` - analyze all entries since Jan 1
- `/friction --file docs/session-logs/Week-starting-2026-01-05.md` - analyze specific file

**What it does:**
1. Searches session logs for permission friction (approval prompts, MSYS issues, pattern failures)
2. Categorizes findings (MISSING, MSYS, PATTERN, ENV_PREFIX, NEW_TOOL)
3. Generates remediation plan with specific fixes
4. Outputs report with proposed settings.local.json changes

**Time:** ~15-30 minutes depending on scope

---

## Execution

Analyze session logs to identify commands that caused approval prompts or workflow friction.

**Ref:** `docs/0824-audit-permission-friction.md`

## Arguments

| Arg | Effect | Default |
|-----|--------|---------|
| `--sessions N` | Analyze last N session entries | 5 |
| `--since YYYY-MM-DD` | Analyze entries since date | (none) |
| `--file PATH` | Analyze specific log file | (none) |

**Examples:**
- `/friction` - analyze last 5 session entries
- `/friction --sessions 10` - analyze last 10 entries
- `/friction --since 2026-01-01` - analyze all entries since Jan 1
- `/friction --file docs/session-logs/Week-starting-2026-01-05.md` - analyze specific file

---

## Procedure

### Step 1: List Session Logs

```bash
ls -la /c/Users/mcwiz/Projects/Aletheia/docs/session-logs/
```

Determine which logs to analyze based on arguments.

### Step 2: Search for Friction Patterns

For each session log in scope, search for these patterns:

**Permission mentions:**
```
grep -in "permission\|approval\|confirm\|prompted" {log}
```

**MSYS path conversion:**
```
grep -in "MSYS_NO_PATHCONV\|path conversion\|/aws/" {log}
```

**Pattern matching failures:**
```
grep -in "cd &&\|doesn't match\|pattern match" {log}
```

**Retry/workaround patterns:**
```
grep -in "retry\|workaround\|instead of" {log}
```

### Step 3: Read Current Permissions

```bash
cat /c/Users/mcwiz/Projects/Aletheia/.claude/settings.local.json
```

### Step 4: Categorize Findings

Classify each friction instance:

| Category | Description |
|----------|-------------|
| **MISSING** | Command should be in allowlist but isn't |
| **MSYS** | Windows path conversion issue |
| **PATTERN** | Command structure doesn't match patterns |
| **ENV_PREFIX** | Env var prefix not in allowlist |
| **NEW_TOOL** | New tool not yet permitted |

### Step 5: Generate Remediation Plan

For each finding, determine:
1. **Remediation type:** Add permission, change command pattern, update docs
2. **Priority:** HIGH (frequent), MEDIUM (occasional), LOW (rare)
3. **Action:** Specific change to make

---

## Output Format

Produce a report following this template:

```markdown
## Permission Friction Analysis - YYYY-MM-DD

**Scope:** [description of what was analyzed]

### Findings Summary

| Category | Count | Priority |
|----------|-------|----------|
| MISSING | N | ... |
| MSYS | N | ... |
| PATTERN | N | ... |

### Detailed Findings

#### [Category]: [Command/Pattern]
- **Session:** [log file and approximate date]
- **Context:** [what was being done]
- **Friction:** [what happened]
- **Remediation:** [specific fix]

### Remediation Actions

#### Immediate (settings.local.json)
```json
// Add to allow list:
"Bash(new-pattern:*)",
```

#### Documentation Updates (CLAUDE.md)
- [Any command pattern changes needed]

#### No Action Needed
- [Patterns that are intentionally blocked]
```

---

## Rules

- Use absolute paths and `git -C` patterns (no cd && chaining)
- **Evidence-based:** Only report friction found in logs, don't guess
- **Actionable output:** Every finding must have a specific remediation
- Produce the report, then ask user which remediations to apply
- Do NOT auto-modify settings.local.json without approval

---

## Quick Reference: Common Remediations

| Friction Type | Fix |
|--------------|-----|
| AWS commands fail on Windows | Add `Bash(MSYS_NO_PATHCONV=1 aws:*)` |
| `cd /path && git` blocked | Use `git -C /path` instead |
| Tool not in allowlist | Add `Bash(tool-name:*)` |
| Env prefix not matched | Add `Bash(VAR=value cmd:*)` |
| Glob too shallow | Change `*` to `**` in pattern |
