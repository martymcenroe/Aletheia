# 0803 - LLD-to-Code Alignment Audit

## Purpose

Verify that implemented code matches the LLD specification, or that deviations are properly documented in the Implementation Report. Catches:
- Implementations that diverged without documentation
- LLDs that weren't updated after changes
- Missing function signatures or interfaces

## Trigger

- Before closing any implementation issue
- After major refactoring of existing features
- When updating an LLD for a new phase

**Note:** This audit applies to **Feature LLDs** (`AgentOS:templates/0102-lld-template`) that produce code. **Implementation Plans** (`AgentOS:templates/0105-implementation-plan-template`) for process/config changes are self-contained and do not require code alignment audits.

## Procedure

### Step 1: Identify LLD and Implementation

```bash
# For issue #121, find:
# LLDs live in docs/lld/active/ (in-progress) or docs/lld/done/ (complete)
LLD="docs/lld/done/1121-wikipedia-denylist.md"
IMPL="tools/fetch_denylist.py"
TESTS="tests/test_fetch_denylist.py"
REPORT="docs/reports/done/1121-implementation-report.md"
```

### Step 2: Extract LLD Promises

From the LLD, extract:
1. **Function signatures** - Names, parameters, return types
2. **Data structures** - JSON schemas, class definitions
3. **Behaviors** - What each function should do
4. **Test scenarios** - IDs and descriptions from Section 10

### Step 3: Compare Against Implementation

For each LLD promise:

| LLD Section | Check | How to Verify |
|-------------|-------|---------------|
| Function signatures | Exact match | `grep "def function_name" impl.py` |
| Parameters | Type hints match | Read function definitions |
| Return types | Match spec | Check return statements |
| Error handling | Documented cases covered | Check except blocks |
| Test scenarios | All have tests | Match test IDs to LLD IDs |

### Step 4: Document Findings

| Finding Type | Action |
|--------------|--------|
| Implementation matches LLD | Note "No deviations" in report |
| Implementation deviates | Document in Implementation Report §5 |
| LLD outdated | Update LLD on main |
| Missing test coverage | Add tests or document gap |

### Step 5: Update Implementation Report

If deviations found, add to `docs/reports/{ID}/implementation-report.md` §5:

```markdown
## 5. Deviations from LLD

| Deviation | Reason | Impact |
|-----------|--------|--------|
| Added seed terms (19) | Category:Profanity contains articles about profanity, not words | Better baseline coverage |
| Rate limiting 1.0s (not 0.5s) | More conservative for API politeness | Slower but safer |
```

## Checklist

For each feature, verify:

- [ ] All function signatures in LLD exist in code
- [ ] Parameter types match
- [ ] Return types match
- [ ] Error handling cases covered
- [ ] Each LLD test scenario has a test function
- [ ] Test IDs in code match LLD IDs
- [ ] Deviations documented in Implementation Report
- [ ] LLD updated if interface changed
- [ ] **LLD moved from `active/` to `done/`** (when issue closes)

## Common Deviations

| Category | Example | Documentation Required |
|----------|---------|------------------------|
| Added parameters | Optional `timeout` parameter | Yes - Implementation Report |
| Changed types | `str` → `Optional[str]` | Yes - Update LLD |
| New error cases | Added rate limit handling | Yes - Both |
| Performance tweaks | Different batch size | Yes - Implementation Report |
| Removed features | Skipped optional enhancement | Yes - Explain why |

## Output Format

```markdown
## LLD-to-Code Alignment Audit - Issue #{ID}

### Files Compared
- **LLD:** `docs/lld/{active|done}/1{ID}-feature.md`
- **Implementation:** `path/to/impl.py`
- **Tests:** `tests/test_feature.py`

### Alignment Status
- Function signatures: ✅ Match
- Parameters: ✅ Match
- Return types: ⚠️ Deviation (documented)
- Test coverage: ✅ 26/26 scenarios

### Deviations Found
| LLD Says | Code Does | Documented? |
|----------|-----------|-------------|
| 0.5s rate limit | 1.0s rate limit | ✅ In Implementation Report |

### Remediation
- [x] Updated Implementation Report §5
- [ ] N/A - LLD update not needed
```

## Step 6: LLD Lifecycle Management

**MANDATORY:** When closing an issue, move its LLD from `active/` to `done/`.

```bash
# For issue #121:
git mv docs/lld/active/1121-feature-name.md docs/lld/done/
```

### Lifecycle States

| Directory | Meaning | When to Use |
|-----------|---------|-------------|
| `docs/lld/active/` | In-progress, Draft, or Placeholder | Issue is OPEN |
| `docs/lld/done/` | Implemented and merged | Issue is CLOSED |

### Quick Audit Check

To find orphaned LLDs (closed issues with LLDs still in active/):

```bash
# List active LLDs
ls docs/lld/active/

# For each, extract issue number (1xxx → #xxx) and check if closed
gh issue view {issue_number} --json state
```

**If LLD is in `active/` but issue is CLOSED:** Move to `done/` immediately.

## Integration

- Run as final step before PR merge
- Required by 0004 §8.6 (Issue Closure Requirements)
- **LLD move to done/ is part of issue closure** - not optional
