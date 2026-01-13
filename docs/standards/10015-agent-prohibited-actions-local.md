# 10015 - Aletheia Agent Prohibited Actions (Local Extension)

> **Extends:** [AgentOS 0003 - Agent Prohibited Actions](C:\Users\mcwiz\Projects\AgentOS\docs\standards\0003-agent-prohibited-actions.md)
>
> This document contains Aletheia-specific prohibited actions that supplement the generic AgentOS rules.

---

## 1. Overview

This document defines actions that AI agents (Claude Code, etc.) are **FORBIDDEN** from performing on the Aletheia project. These are encoded in `.claude/settings.local.json` as deny rules.

**Status:** Active
**Related:** CLAUDE.md, `.claude/settings.local.json`, ADR 0201

---

## 2. Philosophy

**Default: PERMISSIVE within project bounds.**

Agents should be able to work autonomously without constant permission prompts. The deny list is intentionally SHORT - only truly dangerous operations that could cause:
- Irreversible data loss
- Security breaches
- Collaboration disruption

If an operation can be undone with `git revert` or restored from backup, it's probably fine.

---

## 3. Prohibited Actions

### 3.1 Git Destructive Operations

| Action | Why Prohibited | Safe Alternative |
|--------|----------------|------------------|
| `git reset` | Rewrites history, loses commits | `git revert` |
| `git push --force` | Destroys remote history, breaks collaborators | Fix locally, push normally |
| `git push -f` | Same as above | Fix locally, push normally |
| `git clean -fd` | Permanently deletes untracked files | Manual review first |

### 3.2 Package Management

| Action | Why Prohibited | Safe Alternative |
|--------|----------------|------------------|
| `pip install` | Bypasses Poetry lockfile, creates dependency drift | `poetry add <package>` |

### 3.3 Secrets Access

| Action | Why Prohibited | Safe Alternative |
|--------|----------------|------------------|
| `Read(.env)` | Contains secrets | Use documented env var names |
| `Read(.env.*)` | Contains secrets | Use documented env var names |

### 3.4 Deployment Safety

| Action | Why Prohibited | Safe Alternative |
|--------|----------------|------------------|
| Creating dummy/placeholder files to force success | Creates **Silent Failures**. Masks underlying errors (e.g., missing source code) and deploys broken code to production. | **Fail Closed.** If a required file is missing, the script or agent must `exit 1` and report the error immediately. |

**Example of the "Init Bug":**
```python
# WRONG - Agent created this to bypass missing-file error
# lambda_function.py
def lambda_handler(event, context):
    return "Init"  # Placeholder that crashed production
```

```bash
# CORRECT - Script fails fast when source is missing
if [ ! -f "src/lambda_function.py" ]; then
    echo "ERROR: src/lambda_function.py not found. Aborting deployment."
    exit 1
fi
```

### 3.5 Environment-Specific Commands

| Action | Why Prohibited | Safe Alternative |
|--------|----------------|------------------|
| `TZ='America/Chicago' date` | Returns UTC on Windows (Git Bash), not local time | `powershell.exe -Command "Get-Date -Format 'yyyy-MM-dd HH:mm'"` |

### 3.6 Temporary Files

| Action | Why Prohibited | Safe Alternative |
|--------|----------------|------------------|
| `/tmp` or `$TEMP` directories | System temp varies by OS, is shared, and may be cleaned unexpectedly | Use project-local `{project}/tmp/` (ensure `tmp/` is in `.gitignore`) |

---

## 4. Permitted Actions (No Approval Needed)

Agents MAY perform these without asking:

### 4.1 File Operations (within Aletheia project)
- Create, read, edit, delete any file
- Create, delete directories
- Move, copy, rename files

### 4.2 Git Operations (non-destructive)
- All commit operations
- Branch create/delete
- Push/pull (non-force)
- Merge, rebase (interactive excluded)
- Stash operations
- Worktree operations

### 4.3 Build & Test
- Run any Python script
- Run pytest, ruff, mypy
- Run npm, npx, node
- Run Poetry commands
- Run AWS CLI commands
- Run GitHub CLI commands

### 4.4 Web Access
- WebSearch (any query)
- WebFetch (approved domains)

---

## 5. When to Ask for Permission

Agents SHOULD ask before:
- Deleting the entire repository
- Operations outside `/c/Users/mcwiz/Projects/Aletheia*/**`
- Reading system environment variables that might contain passwords
- Any operation not covered by existing permissions

Agents should NOT ask for:
- Normal file operations within the project
- Running tests, lints, builds
- Git operations (except prohibited ones)
- Creating/editing documentation

---

## 6. Adding New Prohibitions

To add a new prohibited action:

1. Document it in this file (Section 3)
2. Add to `.claude/settings.local.json` deny list
3. Add to `tools/policy_check.sh` if automatable
4. Update CLAUDE.md if it's a workflow rule

**Criteria for prohibition:**
- Irreversible without extraordinary effort
- Potential for significant data loss
- Security/secrets exposure
- Collaboration disruption

---

## 7. Technical Implementation

### 7.1 Settings File Location
```
.claude/settings.local.json
```

### 7.2 Permission Format
```json
{
  "permissions": {
    "allow": [
      "Bash(command:*)",           // Prefix match
      "Read(path/pattern/**)",     // Glob pattern
      "WebFetch(domain:example.com)"
    ],
    "deny": [
      "Bash(dangerous command:*)"
    ]
  }
}
```

### 7.3 Priority
Deny rules take precedence over allow rules.

---

## 8. Audit

This document is audited by **0808-audit-permission-permissiveness.md** to ensure:
- Permissions are maximally permissive within safety bounds
- No unnecessary restrictions causing workflow friction
- Deny list remains minimal and justified

---

## 9. References

- CLAUDE.md - Workflow rules
- ADR 0201 - Privacy-First Permissions (extension, not agent)
- `.claude/settings.local.json` - Technical implementation
