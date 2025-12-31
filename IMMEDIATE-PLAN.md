# Immediate Plan: Issue #45 (Denylist) - First Willison Protocol Feature

**Updated:** 2025-12-31 (post-Gemini review)
**Goal:** Implement deterministic hate speech filter with full test automation

---

## Kick-off Prompt for New Session

Read `docs/0000-GUIDE.md`, then `docs/1045-deterministic-hate-filter.md` (the LLD).

**Task:** Implement Issue #45 (Denylist).

**Required reading before coding:**
1. `docs/1045-deterministic-hate-filter.md` - Full LLD (Gemini-reviewed, approved)
2. `docs/0005-testing-strategy-and-protocols.md` Section 5 - Willison Protocol
3. `docs/0004-orchestration-protocol.md` Section 8 - Feature Development Lifecycle

**Critical implementation notes from Gemini review:**
- Use `re.findall(r'\w+', text)` for tokenization (NOT `split()`)
- Use `unicodedata.normalize('NFKC', text)` for unicode bypass prevention
- Mock `load_denylist()` in tests with safe terms like `{"test_block_term"}` - NO real slurs in test files

**Workflow:**
1. Create worktree: `git worktree add ../Aletheia-45 -b 45-denylist`
2. Push immediately: `git push -u origin HEAD`
3. Write code per LLD Section 6
4. Write tests per LLD Section 10 (mock the denylist!)
5. Verify Willison Protocol: tests FAIL on revert, PASS with implementation
6. Create Implementation Report (`docs/reports/45/implementation-report.md`)
7. Create Test Report (`docs/reports/45/test-report.md`)
8. Create PR with proof artifacts

Questions before starting?

---

## Context Summary

### What Changed (2025-12-31)
- **LLD 1045:** Reviewed by Gemini 3.0 Pro, all findings addressed
- **Tokenization:** Fixed `split()` → `re.findall(r'\w+')` for punctuation handling
- **Security:** Added NFKC unicode normalization (standard library)
- **Partial matching:** Deferred to future (incompatible with O(1))
- **Test hygiene:** Must mock denylist - no real slurs in Git history

### Critical Path
1. **#45 (Denylist)** ← YOU ARE HERE
2. **#113 (Naked Python)** - Wire the full pipeline
3. **#51/#53 (Store)** - Chrome Web Store submission
4. **#100 (Firefox)** - Firefox Add-ons compatibility

### Key Documentation
| Doc | Purpose |
|-----|---------|
| `docs/1045` | Denylist LLD (Gemini-approved) |
| `docs/0005` Section 5 | Willison Protocol |
| `docs/0004` Section 8 | Feature Development Lifecycle |
| `docs/0103` | Implementation Report template |
| `docs/0113` | Test Report template |

---

## Files to Create

```
src/guardrails/denylist.py              # Implementation
src/guardrails/resources/denylist.json  # Term list from RSDB
tests/test_denylist.py                  # Automated tests (MOCKED data)
docs/reports/45/implementation-report.md
docs/reports/45/test-report.md
```

## Function Signatures (from LLD 6.2)

```python
def load_denylist(path: str = "src/guardrails/resources/denylist.json") -> set[str]:
    """Load denylist from JSON file into memory. Called once on cold start."""

def normalize_text(text: str) -> str:
    """Normalize input: NFKC unicode, lowercase, strip whitespace."""

def check_denylist(text: str, denylist: set[str]) -> DenylistResult:
    """Check if any token in text matches the denylist. O(1) per token."""
```

## Test Scenarios (from LLD 10.1)

| ID | Scenario | Input | Expected |
|----|----------|-------|----------|
| 010 | Known term blocked | Term from mock denylist | `{blocked: True}` |
| 020 | Clean word passes | "hello world" | `{blocked: False}` |
| 030 | Empty input | "" | `{blocked: False}` |
| 040 | Whitespace only | "   " | `{blocked: False}` |
| 050 | Case insensitive | "BADTERM" | `{blocked: True}` |
| 060 | Mixed clean/bad | "hello [badterm] world" | `{blocked: True}` |
| 070 | Performance | 1000 lookups | < 5ms total |
| 080 | Missing file | No file | Fail open + log |
| 090 | Malformed JSON | Invalid JSON | Fail open + log |

## Definition of Done

### Code
- [ ] `src/guardrails/denylist.py` implemented
- [ ] `src/guardrails/resources/denylist.json` created
- [ ] Uses `re.findall()` and `unicodedata.normalize()`

### Tests (Willison Protocol)
- [ ] `tests/test_denylist.py` covers 9 scenarios
- [ ] Tests use MOCKED denylist (no real slurs)
- [ ] Tests FAIL when implementation reverted (verified)
- [ ] Terminal output captured

### Documentation
- [ ] Implementation Report created
- [ ] Test Report created with proof artifacts
- [ ] LLD updated if any deviations

### Review
- [ ] PR created with proof artifacts
- [ ] Orchestrator verified test proof
- [ ] Issue #45 closed with PR reference
