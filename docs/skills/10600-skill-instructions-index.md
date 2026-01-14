# 10600 - Skill Instructions Index

## Purpose

This document indexes all skill instructions in the `106xx` namespace. Skill instructions are prompts and procedures that agents follow to perform specific tasks. Unlike templates (which are filled in), skill instructions are executed as-is.

## Distinction from Templates

| Type | Namespace | Purpose | How Used |
|------|-----------|---------|----------|
| **Templates** | `101xx` | Patterns to fill in | Copy, rename, customize |
| **Skill Instructions** | `106xx` | Procedures to execute | Read and follow verbatim |

**Examples:**
- Template: `docs/templates/10102-TEMPLATE-feature-lld.md` - Copy and fill in for your feature
- Skill: `docs/skills/10601-skill-gemini-lld-review.md` - Gemini follows this to review LLDs

---

## Skill Instructions Index

### 1060x: Review & Quality Skills

| File | Purpose | Target Agent | Status |
|:-----|:--------|:-------------|:-------|
| [10600-skill-instructions-index.md](10600-skill-instructions-index.md) | This file. Index of all skills. | Any | Active |
| [10601-skill-gemini-lld-review.md](10601-skill-gemini-lld-review.md) | LLD review procedure with priority tiers | Gemini | Active |
| [10602-skill-gemini-dual-review.md](10602-skill-gemini-dual-review.md) | Claude-Gemini dual review automation for LLD, implementation, and issue filing with model verification | Claude + Gemini | Planned |

### 1061x: Audit Skills

| File | Purpose | Target Agent | Status |
|:-----|:--------|:-------------|:-------|
| Reserved for audit execution procedures | | | Future |

### 1062x: Maintenance Skills

| File | Purpose | Target Agent | Status |
|:-----|:--------|:-------------|:-------|
| Reserved for cleanup, migration procedures | | | Future |

---

## Adding New Skills

1. Choose the appropriate range from above
2. Use the next available number in that range
3. Name format: `106XX-skill-{name}.md`
4. Include:
   - Clear purpose statement
   - Target agent (which model should execute)
   - Step-by-step procedure
   - Expected output format
5. Update this index
6. Update `docs/standards/10003-file-inventory.md`

---

## Relationship to Slash Commands

Skill instructions may be invoked via slash commands in `.claude/commands/`. The relationship:

| Skill Doc | Slash Command | Notes |
|-----------|---------------|-------|
| `10601-skill-gemini-lld-review.md` | N/A | Manually assigned by orchestrator |
| Future audit skills | `/audit` | Could be linked |

---

## History

| Date | Change |
|------|--------|
| 2026-01-08 | Created. Moved 0109-gemini-lld-review-procedure.md to 10601. |
| 2026-01-09 | Added 10602-skill-gemini-dual-review.md (Claude-Gemini dual review automation). Issue #222. |
| 2026-01-14 | Updated to 10xxx naming scheme for Aletheia project. |
