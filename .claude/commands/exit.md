---
description: Exit session with mandatory session log (project) (project)
argument-hint: "[--quick] [--summary 'text'] [--created '#XX'] [--closed '#YY']"
---

# Exit Session

**If `$ARGUMENTS` contains `--help`:** Display the Help section below and STOP.

---

## Help

Usage: `/exit [--help] [--quick] [--summary 'text'] [--created '#XX'] [--closed '#YY']`

| Argument | Description |
|----------|-------------|
| `--help` | Show this help message and exit |
| `--quick` | Quick exit with auto-generated summary (no prompt) |
| `--summary 'text'` | Session summary (auto-generated if not provided) |
| `--created '#XX'` | Issues created this session (default: None) |
| `--closed '#YY'` | Issues closed this session (default: None) |

**Examples:**
- `/exit` - Auto-generates summary from session context
- `/exit --quick` - Same as `/exit` (explicit quick mode)
- `/exit --summary "Fixed bug in auth flow"` - Exit with custom summary
- `/exit --summary "Implemented feature X" --closed "#123"` - Exit with issue tracking

**What this does:**
1. Auto-generates session summary from context (or uses provided summary)
2. Appends session log entry to current week's file
3. Stages and commits the session log
4. Pushes to remote
5. Confirms clean exit

---

## Execution

### Step 1: Gather Information

Parse `$ARGUMENTS` for:
- `--summary` - If provided, use it. Otherwise, AUTO-GENERATE from session context:
  - If only onboarding occurred: "Full onboarding, no work performed"
  - If issues were worked: Summarize based on tools used and files changed
  - NEVER ask the user - just generate a reasonable summary
- `--created` - Default to "None" if not provided
- `--closed` - Default to "None" if not provided

### Step 2: Write Session Log

Run the append script:
```bash
poetry run python /c/Users/mcwiz/Projects/Aletheia/tools/append_session_log.py \
    --model "Claude Opus 4.5" \
    --summary "[SUMMARY]" \
    --created "[CREATED]" \
    --closed "[CLOSED]" \
    --next "Per user direction"
```

### Step 3: Stage and Commit

```bash
git -C /c/Users/mcwiz/Projects/Aletheia add docs/session-logs/
```

```bash
git -C /c/Users/mcwiz/Projects/Aletheia commit -m "docs: session log $(powershell.exe -Command "Get-Date -Format 'yyyy-MM-dd HH:mm'")"
```

### Step 4: Push

```bash
git -C /c/Users/mcwiz/Projects/Aletheia push
```

### Step 5: Confirm Exit

Display:
```
✅ Session log written and pushed.
   File: docs/session-logs/Week-starting-YYYY-MM-DD.md

Safe to close this session (Marty affirms).
```

---

## Rules

- Use absolute paths with `git -C /c/Users/mcwiz/Projects/Aletheia`
- NO pipes (`|`) or chain operators (`&&`) - one command per Bash call
- If the session log script fails, manually append using the template from `docs/0100-TEMPLATE-GUIDE.md`
- Do NOT run `/cleanup` - this is a lightweight exit, not a full cleanup
