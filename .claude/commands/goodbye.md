---
description: Quick cleanup + exit session (project)
argument-hint: "[--help]"
---

# Goodbye

**If `$ARGUMENTS` contains `--help`:** Display the Help section below and STOP.

---

## Help

Usage: `/goodbye [--help]`

| Argument | Description |
|----------|-------------|
| `--help` | Show this help message and exit |

**What it does:**
1. Runs `/cleanup --quick` (session log entry, ~2 min)
2. Signals session end

**Examples:**
- `/goodbye` - quick cleanup and exit
- `/goodbye --help` - show this help

**When to use:**
- End of session when you want to ensure cleanup happens
- Prevents forgetting to run cleanup before closing

---

## Execution

This command bundles quick cleanup with session exit.

### Step 1: Run Quick Cleanup

Execute the cleanup skill with `--quick` flag:

```
/cleanup --quick
```

Wait for the cleanup to complete. This will:
- Check git status, branches, and open PRs
- Append a session log entry
- Commit and push documentation changes

### Step 2: Session End

After cleanup completes successfully, inform the user:

```
Session cleanup complete. Goodbye!

Summary:
- Session log entry appended
- Documentation committed and pushed
- Ready to close this conversation
```

**Note:** The user should close the conversation after seeing this message. Claude Code does not have a programmatic "exit" command - the session ends when the user closes the terminal or conversation.
