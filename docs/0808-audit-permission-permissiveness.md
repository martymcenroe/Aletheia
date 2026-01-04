# 0808 - Audit: Permission Permissiveness

## 1. Purpose

Ensure agent permissions are maximally permissive within safety bounds. Overly restrictive permissions create workflow friction and slow development.

**Philosophy:** If an operation isn't destructive or a security risk, the agent should be able to do it without asking.

---

## 2. Audit Checklist

### 2.1 Allow List Completeness

| Category | Expected Permissions | Status |
|----------|---------------------|--------|
| **File Operations** | Read, Write, Edit for Aletheia project paths | |
| **Shell Basics** | cat, ls, mkdir, rm, cp, mv, chmod, touch, ln | |
| **Text Processing** | grep, rg, head, tail, wc, sort, uniq, cut, awk, sed, jq | |
| **File Search** | find, fd, which, where, tree, file, stat | |
| **Archiving** | tar, zip, unzip, gzip | |
| **Networking** | curl, wget | |
| **Git (all non-destructive)** | git (blanket, with denies for destructive) | |
| **GitHub CLI** | gh (all operations) | |
| **AWS CLI** | aws, sam | |
| **Python Toolchain** | python, poetry, pytest, ruff, mypy, pre-commit | |
| **Node Toolchain** | node, npm, npx, yarn, pnpm | |
| **Shell/Environment** | bash, sh, env, source, export, eval | |
| **Windows Shell** | powershell.exe, pwsh, cmd | |
| **Project Scripts** | ./tools/*, ./tests/* | |
| **Web Access** | WebSearch, WebFetch (unrestricted domains) | |

### 2.2 Deny List Minimality

The deny list should be SHORT. Each item requires justification:

| Denied Action | Justification | Verdict |
|---------------|---------------|---------|
| `Read(.env)` | Contains secrets | ✅ Keep |
| `Read(.env.*)` | Contains secrets | ✅ Keep |
| `Read(~/.aws/credentials)` | Contains AWS secrets | ✅ Keep |
| `git reset` | Rewrites history | ✅ Keep |
| `git push --force` | Destroys remote history | ✅ Keep |
| `git push -f` | Same as above | ✅ Keep |
| `git clean -fd` | Permanent file deletion | ✅ Keep |
| `pip install` | Bypasses Poetry | ✅ Keep |
| `rm -rf /` | System destruction | ✅ Keep |
| `rm -rf ~` | Home directory destruction | ✅ Keep |
| `dd if=` | Disk operations | ✅ Keep |
| `mkfs` | Filesystem operations | ✅ Keep |
| `format` | Disk formatting | ✅ Keep |

### 2.3 Friction Points

Check recent sessions for patterns of:
- Agent asking permission for routine operations
- Repeated permission grants for same command types
- User frustration with permission prompts

**Finding:** [Document any friction points here]

**Remediation:** Add missing permissions to allow list.

---

## 3. Audit Procedure

1. Read `.claude/settings.local.json`
2. Check allow list against §2.1 categories
3. Check deny list against §2.2 justifications
4. Review recent session logs for permission friction
5. Update settings file if gaps found
6. Document findings in audit record

---

## 4. Audit Record

| Date | Auditor | Finding | Remediation |
|------|---------|---------|-------------|
| 2026-01-04 | Claude Opus 4.5 | Initial audit - expanded allow list significantly, added comprehensive bash commands | Created 0015-agent-prohibited-actions.md |

---

## 5. References

- docs/0015-agent-prohibited-actions.md - Policy document
- .claude/settings.local.json - Implementation
- CLAUDE.md - Workflow rules
