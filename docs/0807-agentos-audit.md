# 0807 - AgentOS Health Check

## Purpose

Verify the documentation system (Agent Operating System) itself is healthy and internally consistent. Unlike other audits that check code/product, this audit checks the operating system that agents run on.

## Trigger

- Monthly (system maintenance)
- When onboarding new agents
- After major documentation reorganization
- When agents report confusion or broken workflows

## Philosophy

> "The operating system must be debuggable."

If an agent can't execute a protocol because of broken references, unclear instructions, or conflicting guidance, the AOS has a bug.

## Procedure

### Step 1: Cross-Reference Validation

**Check for broken internal references:**
```bash
# Find all doc references and verify targets exist
grep -roh "docs/[0-9]\{4\}[^.]*\.md" docs/*.md | sort -u | while read ref; do
  if [ ! -f "$ref" ]; then
    echo "BROKEN: $ref"
  fi
done

# Find references to deleted docs (common after renumbering)
grep -r "0011" docs/*.md --include="*.md" | grep -v session-logs
```

**Check for orphaned docs (not referenced anywhere):**
```bash
for f in docs/0*.md; do
  basename="$(basename $f)"
  refs=$(grep -r "$basename" docs/*.md --include="*.md" -l | wc -l)
  if [ "$refs" -eq 0 ]; then
    echo "ORPHAN: $f (not referenced)"
  fi
done
```

### Step 2: CLAUDE.md / 0000-GUIDE.md Alignment

These two files must be consistent. Check:

| Check | CLAUDE.md | 0000-GUIDE.md |
|-------|-----------|---------------|
| Forbidden commands | Listed | Referenced |
| Workflow rules | Detailed | Summarized |
| Session log format | Referenced | Template in 0100 |
| Worktree protocol | Mandated | Explained |

```bash
# Quick diff of key sections
grep -A5 "Forbidden" CLAUDE.md
grep -A5 "Forbidden" docs/0000-GUIDE.md
```

### Step 3: Template Consistency

**Verify templates match their usage:**
```bash
# List all templates
ls docs/01*TEMPLATE*.md

# Check a sample report against template structure
# (Manual: compare docs/reports/*/implementation-report.md against 0103)
```

**Check template index (0100) lists all templates:**
```bash
for t in docs/01*TEMPLATE*.md; do
  basename="$(basename $t)"
  grep -q "$basename" docs/0100-TEMPLATE-GUIDE.md || echo "NOT IN INDEX: $t"
done
```

### Step 4: Protocol Executability

For each protocol (0009, 0004, etc.), verify:
- [ ] Steps are numbered and unambiguous
- [ ] Commands are copy-pasteable
- [ ] Expected outputs are documented
- [ ] Failure conditions are handled

**Quick check for incomplete protocols:**
```bash
# Protocols should have "## Procedure" or numbered steps
for p in docs/000[4-9]*.md docs/08*.md; do
  if ! grep -q -E "(## Procedure|### Step|### [SF][0-9])" "$p"; then
    echo "NO STEPS: $p"
  fi
done
```

### Step 5: Session Log Format Consistency

```bash
# Check recent session logs follow format
grep -c "^## [0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}" docs/session-logs/*.md
```

### Step 6: Inventory Self-Check

```bash
# Verify 0003 lists itself and key system docs
for doc in 0000-GUIDE.md 0003-file-inventory.md CLAUDE.md; do
  grep -q "$doc" docs/0003-file-inventory.md || echo "NOT IN INVENTORY: $doc"
done
```

### Step 7: 0000-GUIDE Filing System Accuracy

**Verify all files listed in 0000-GUIDE.md §3 (Filing System) actually exist:**
```bash
# Extract filenames from 0000-GUIDE.md and check they exist
grep -oE '\`[0-9]{4}[a-z]?-[^`]+\.md\`' docs/0000-GUIDE.md | tr -d '\`' | while read f; do
  if [ ! -f "docs/$f" ] && [ ! -f "$f" ]; then
    echo "LISTED BUT MISSING: $f"
  fi
done
```

**Verify all 00xx/01xx docs are listed in 0000-GUIDE.md:**
```bash
# Check for undocumented standards
for f in docs/00[0-1][0-9]*.md; do
  basename="$(basename $f)"
  grep -q "$basename" docs/0000-GUIDE.md || echo "EXISTS BUT NOT LISTED: $basename"
done
```

**Action:** Update 0000-GUIDE.md §3 to include all current files.

## Output Format

```markdown
## AgentOS Health Check - YYYY-MM-DD

### Broken References
- [ ] `docs/XXXX.md` references deleted `docs/YYYY.md`

### Alignment Issues
- [ ] CLAUDE.md says X, 0000-GUIDE.md says Y

### Template Drift
- [ ] Template 0103 has section X, but reports lack it

### Protocol Issues
- [ ] Protocol 0009 step S3 has unclear expected output

### Recommendations
1. Fix broken reference in X
2. Align Y with Z
```

## Integration

- Run as part of monthly maintenance
- Run before onboarding new AI agents
- Results feed into system improvement issues

## Common Findings

| Finding | Cause | Fix |
|---------|-------|-----|
| Broken doc reference | Renumbering without updating refs | grep + sed |
| Template drift | Template updated, old reports not | Accept drift in old reports |
| Conflicting guidance | Multiple authors, no review | Consolidate into one source |
| Unclear protocol step | Written for expert, not novice | Add expected output |

## History

| Date | Change |
|------|--------|
| 2026-01-04 | Created. |
