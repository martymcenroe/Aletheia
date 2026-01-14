# 10275 - Implementation Plan: Eliminate Permission Friction from Spawned Agents

**Issue:** #275
**Status:** Active
**Created:** 2026-01-10
**Author:** Claude Opus 4.5

---

## Problem Statement

When Opus spawns Sonnet agents, those agents run Bash commands that trigger permission prompts despite patterns like `Bash(head:*)` being in the allowlist. The user must approve hundreds of commands per session. This is debilitating.

**Evidence:** `head -660 /c/Users/mcwiz/.claude/path` triggered a prompt even though:
- `Bash(head:*)` is in the allowlist (should match any head command)
- `Bash(head /c/Users/mcwiz/.claude/**:*)` is also in the allowlist (specific for .claude paths)

The specific pattern doesn't allow FLAGS between `head` and the path, so `head -660 /path` doesn't match.

---

## Root Cause Analysis

The spawned agent instructions are incomplete. They cover `&&`, `|`, `;` rules but say NOTHING about:
- Permission pattern syntax and how it works
- How to construct commands that match allowlist patterns
- When to use alternative tools (Read instead of head) to avoid friction
- Path format requirements (Unix vs Windows)

**The MODEL is the problem, not Claude Code.** Agents have access to the allowlist patterns but don't understand how to construct commands that match them.

---

## Solution Strategy

**Same pattern as the && | ; rules:** Comprehensive instructions that spawned agents MUST follow, with visible enforcement.

---

## Implementation Phases

### Phase 1: Update CLAUDE.md Agent Spawning Instructions

**File:** `CLAUDE.md`
**Location:** After the current "Spawning Agents" section (~line 113)

**Add new section:** "PERMISSION FRICTION PREVENTION (SPAWNED AGENTS)"

```markdown
### PERMISSION FRICTION PREVENTION (SPAWNED AGENTS)

**Every permission prompt a spawned agent triggers interrupts the user's workflow. This is unacceptable.**

When spawning to Sonnet/Haiku, ALWAYS include these instructions in the prompt:

---

**PERMISSION-SAFE EXECUTION RULES:**

1. **Prefer dedicated tools over Bash:**
   - Use `Read` instead of `head`, `tail`, `cat`
   - Use `Grep` instead of `grep`, `rg`
   - Use `Glob` instead of `find`, `ls`
   - These tools are ALWAYS auto-approved

2. **For .claude/ paths (session logs, transcripts):**
   - NEVER use `head -n X /path` (flags break pattern matching)
   - USE `Read` tool with `limit` parameter instead
   - If you MUST use Bash: `head /path` (no flags)

3. **Pattern matching is LITERAL:**
   - `Bash(head:*)` matches `head file.txt`
   - `Bash(head:*)` does NOT reliably match `head -660 file.txt`
   - The allowlist pattern expects specific command structure

4. **Safe Bash patterns (known to work):**
   ```
   git -C /absolute/path status          ✓ (matches Bash(git:*))
   git -C /absolute/path push -u origin  ✓ (matches Bash(git:*))
   poetry run python /path/script.py     ✓ (matches Bash(poetry:*))
   npm install --prefix /path            ✓ (matches Bash(npm:*))
   ```

5. **Problematic patterns (avoid):**
   ```
   head -660 /c/Users/.claude/...        ✗ (flags break .claude pattern)
   cd /path && git status                ✗ (&& banned)
   git status | grep main                ✗ (pipe banned)
   ```

6. **When unsure, use alternatives:**
   - Reading file contents? Use `Read` tool
   - Searching file contents? Use `Grep` tool
   - Listing files? Use `Glob` tool
   - Only use Bash for commands that MUST be Bash (git, npm, poetry, etc.)

---

Include this VERBATIM in every agent spawn prompt.
```

---

### Phase 2: Add Friction Risk to Visible Self-Check

**File:** `CLAUDE.md`
**Location:** Modify the existing "Bash Check" block (~line 95)

**Current:**
```markdown
**Bash Check:** `[the command]`
**Scan:** [&&, |, ;, cd at start?] → [CLEAN or VIOLATION]
**Action:** [Execute or Rewrite to: X]
```

**New (expanded):**
```markdown
**Bash Check:** `[the command]`
**Scan:** [&&, |, ;, cd at start?] → [CLEAN or VIOLATION]
**Friction Risk:** [HIGH if .claude path + flags, MEDIUM if unusual pattern, LOW otherwise]
**Action:** [Execute, Rewrite, or Use Read/Grep/Glob instead]
```

**Add friction check table:**

```markdown
#### Friction Risk Assessment

Before issuing Bash commands, assess friction risk:

| Command Pattern | Risk | Alternative |
|-----------------|------|-------------|
| `head -* /c/Users/mcwiz/.claude/**` | HIGH | Use Read tool with limit |
| `tail -* /c/Users/mcwiz/.claude/**` | HIGH | Use Read tool with offset |
| `grep /c/Users/mcwiz/.claude/**` | HIGH | Use Grep tool |
| `cat /c/Users/mcwiz/.claude/**` | HIGH | Use Read tool |
| `head -* /other/path` | LOW | OK, generic pattern allows |
| `git -C /path command` | LOW | OK, pattern allows |

If friction risk is HIGH, use the alternative tool instead of Bash.
```

---

### Phase 3: Fix settings.local.json Patterns

**File:** `.claude/settings.local.json`

**Remove overly-specific patterns (lines 131-133):**
```json
// REMOVE these - they're too narrow and redundant
"Bash(head /c/Users/mcwiz/.claude/**:*)",
"Bash(tail /c/Users/mcwiz/.claude/**:*)",
"Bash(wc /c/Users/mcwiz/.claude/**:*)"
```

**Rationale:** The generic patterns `Bash(head:*)`, `Bash(tail:*)`, `Bash(wc:*)` already exist at lines 37-39. The specific patterns were added thinking they'd help with .claude paths, but they actually BREAK flag support by requiring exact command structure. Removing them lets the generic patterns handle these commands.

**Remove hardcoded worktree path (line 121):**
```json
// REMOVE - breaks when worktree is deleted
"Bash(/c/Users/mcwiz/Projects/Aletheia-137/provision.sh)"
```

---

## Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `CLAUDE.md` | ADD | New "Permission Friction Prevention" section for spawned agents |
| `CLAUDE.md` | MODIFY | Expand Bash Check to include friction risk assessment |
| `.claude/settings.local.json` | REMOVE | Lines 131-133 (narrow .claude patterns) |
| `.claude/settings.local.json` | REMOVE | Line 121 (hardcoded worktree path) |

---

## Verification Plan

### Test 1: Spawned Agent Friction

1. Spawn a Sonnet agent to read .claude session logs
2. Verify it uses Read tool instead of head
3. Count permission prompts (target: 0)

### Test 2: Pattern Validation

1. Run `head /c/Users/mcwiz/.claude/test.jsonl` - should auto-approve
2. Verify generic `Bash(head:*)` pattern works for .claude paths after removing specific patterns

### Test 3: Full Session Test

1. Have agent do a typical task (implementing a feature)
2. Count total permission prompts
3. Target: <10 prompts for a full feature implementation

---

## Success Criteria

- [ ] Spawned agents use Read/Grep/Glob for .claude paths
- [ ] Permission prompts reduced by >90%
- [ ] Pattern matching issues prevented at instruction level

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Generic patterns don't cover .claude paths | Medium | Test before removing specific patterns |
| Spawned agents ignore instructions | Low | Make instructions VERBATIM and prominent |
| Changes break existing workflows | Low | Incremental rollout, test each change |
