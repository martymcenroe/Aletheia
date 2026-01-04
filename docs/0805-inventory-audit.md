# 0805 - File Inventory Drift Audit

## Purpose

Detect discrepancies between `docs/0003-file-inventory.md` and the actual filesystem. Catches:
- Files that exist but aren't in inventory
- Inventory entries for deleted files
- Incorrect status or metadata

## Trigger

- Weekly (part of 0009 Full Mode §F9)
- After any file creation, deletion, or move
- After major refactoring

## Procedure

### Step 1: Find Files Not in Inventory

```bash
# Python files
find src tests tools -name "*.py" -type f | while read f; do
  grep -q "$(basename $f)" docs/0003-file-inventory.md || echo "NOT IN INVENTORY: $f"
done

# Shell scripts
find . -maxdepth 1 -name "*.sh" -type f | while read f; do
  grep -q "$(basename $f)" docs/0003-file-inventory.md || echo "NOT IN INVENTORY: $f"
done

# Docs
find docs -name "*.md" -type f | while read f; do
  grep -q "$(basename $f)" docs/0003-file-inventory.md || echo "NOT IN INVENTORY: $f"
done
```

### Step 2: Find Inventory Entries for Deleted Files

```bash
# Extract file paths from inventory and check existence
grep -oP '\| `[^`]+`' docs/0003-file-inventory.md |
  sed 's/| `//;s/`//' |
  while read f; do
    [ ! -e "$f" ] && echo "DELETED: $f (still in inventory)"
  done
```

### Step 3: Check for Moved Files

Common moves to check:
- Root → src/ (lambda files)
- docs/ → docs/legacy/ (deprecated docs)
- tools/ restructuring

```bash
# Check if inventory paths are current
grep "lambda_function.py" docs/0003-file-inventory.md  # Should show src/
grep "1119-rsdb" docs/0003-file-inventory.md           # Should show legacy/
```

### Step 4: Verify Status Accuracy

For files marked 🟢 **Stable**:
- Should have tests
- Should have documentation
- Should not have TODO/FIXME comments

For files marked 🟠 **In-Progress**:
- Should have linked issue
- Should be actively worked on

### Step 5: Remediation

| Finding | Action |
|---------|--------|
| File not in inventory | Add entry with appropriate status |
| Deleted file in inventory | Remove entry |
| Wrong path | Update path |
| Wrong status | Update status with note |
| Missing linked issue | Add issue reference or N/A |

## Quick Commands

```bash
# Count files by location
echo "=== File counts ==="
echo "src/: $(find src -name '*.py' | wc -l)"
echo "tests/: $(find tests -name '*.py' | wc -l)"
echo "tools/: $(find tools -name '*.py' | wc -l)"
echo "docs/: $(find docs -name '*.md' | wc -l)"

# Inventory entry count (approximate)
echo "Inventory entries: $(grep -c '| `' docs/0003-file-inventory.md)"
```

## Output Format

```markdown
## File Inventory Audit - {DATE}

### Summary
- Files checked: {N}
- Not in inventory: {N}
- Deleted but listed: {N}
- Wrong path: {N}

### Additions Needed
| File | Suggested Status | Description |
|------|------------------|-------------|
| `tools/new_script.py` | 🟡 Beta | New utility |

### Removals Needed
| Entry | Reason |
|-------|--------|
| `tests/test_rsdb_download.py` | Deleted (superseded by test_fetch_denylist.py) |

### Path Corrections
| Old Path | New Path |
|----------|----------|
| `lambda_function.py` | `src/lambda_function.py` |
```

## Integration

- Referenced by `docs/0009-session-closeout-protocol.md` §F9 (Full Mode)
- Run as part of 0009 Full Mode closeout
