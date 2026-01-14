# 10153 - Bug: Fix smoke_test.py pytest Fixture Errors

## 1. Context & Goal
* **Issue:** #153
* **Objective:** Fix the 5 pytest fixture errors caused by missing `url` fixture in smoke_test.py.
* **Status:** Draft
* **Related Issues:** None

### Open Questions
*Questions that need clarification before or during implementation. Remove when resolved.*

- [x] ~~What is the intended purpose of these test functions?~~ **Manual/post-deployment verification, NOT unit tests**
- [x] ~~Should they be renamed?~~ **Yes - rename `test_*` to `verify_*` to exclude from pytest collection**
- [x] ~~Should these tests use the test site infrastructure from #105?~~ **No - smoke tests hit live endpoints**

### Resolved Questions (Gemini Review 2026-01-05)

1. **Q: What is the purpose of these functions?**
   **A: Smoke tests for manual/post-deployment verification.** These are NOT unit tests. They're intended to verify a live deployed endpoint works correctly. They should NOT be collected by pytest during unit test runs.

2. **Q: How to fix the fixture errors?**
   **A: Rename functions from `test_*` to `verify_*`.** This prevents pytest from collecting them while preserving their ability to be called manually or via CLI.

## 2. Requirements

1. Eliminate the 5 "fixture 'url' not found" errors from pytest runs
2. Either convert functions to proper pytest tests OR exclude from pytest collection
3. Maintain any existing functionality for manual invocation if needed

## 3. Alternatives Considered

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **Rename `test_*` to `verify_*`** | Quick fix, preserves manual usage, clear intent | None | **Selected** |
| Create URL fixture in conftest.py | Proper pytest integration | Defeats purpose of smoke tests (which hit live endpoints) | Rejected |
| Parametrize with test URLs | Full test coverage | Wrong abstraction - these aren't unit tests | Rejected |
| Mark with `@pytest.mark.skip` | Quick | Confusing intent, still collected | Rejected |
| Delete file entirely | Clean codebase | Lose smoke test capability | Rejected |

**Rationale:** Smoke tests are for manual/post-deployment verification against live endpoints. They are NOT unit tests. Renaming to `verify_*` clearly communicates intent and excludes them from pytest collection without losing functionality.

## 4. Data & Fixtures

N/A - This is a test infrastructure fix.

## 5. Diagram

N/A

## 6. Technical Approach

* **Module:** `tools/smoke_test.py`
* **Dependencies:** requests (NOT pytest - these are manual scripts)
* **Pattern:** Rename functions to exclude from pytest collection

### 6.1 Rename Functions

Rename all `test_*` functions to `verify_*`:

```python
# BEFORE (collected by pytest, causes fixture errors)
def test_valid_input(url: str) -> dict:
def test_blocked_input(url: str) -> dict:
def test_empty_input(url: str) -> dict:
def test_prompt_injection(url: str) -> dict:
def test_tone_neutrality(url: str) -> dict:

# AFTER (NOT collected by pytest, works as manual script)
def verify_valid_input(url: str) -> dict:
def verify_blocked_input(url: str) -> dict:
def verify_empty_input(url: str) -> dict:
def verify_prompt_injection(url: str) -> dict:
def verify_tone_neutrality(url: str) -> dict:
```

### 6.2 Robust CLI Entry Point

Ensure the `if __name__ == "__main__":` block calls all `verify_*` functions:

```python
if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://your-api-endpoint.com"

    print(f"Running smoke tests against: {url}")
    results = [
        ("valid_input", verify_valid_input(url)),
        ("blocked_input", verify_blocked_input(url)),
        ("empty_input", verify_empty_input(url)),
        ("prompt_injection", verify_prompt_injection(url)),
        ("tone_neutrality", verify_tone_neutrality(url)),
    ]

    for name, result in results:
        status = "✓" if result.get("success") else "✗"
        print(f"  {status} {name}")
```

## 7. Interface Specification

### Current (Broken - Collected by pytest)
```python
def test_valid_input(url: str) -> dict:  # ❌ fixture 'url' not found
def test_blocked_input(url: str) -> dict:
def test_empty_input(url: str) -> dict:
def test_prompt_injection(url: str) -> dict:
def test_tone_neutrality(url: str) -> dict:
```

### After Fix (Not collected by pytest)
```python
def verify_valid_input(url: str) -> dict:  # ✓ Manual invocation only
def verify_blocked_input(url: str) -> dict:
def verify_empty_input(url: str) -> dict:
def verify_prompt_injection(url: str) -> dict:
def verify_tone_neutrality(url: str) -> dict:
```

## 8. Security Considerations

| Concern | Mitigation | Status |
|---------|------------|--------|
| Test URLs in code | Use env var | TODO |

**Fail Mode:** N/A

## 9. Performance Considerations

N/A - Test infrastructure change.

## 10. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Break manual smoke test usage | Low | Med | Preserve CLI invocation path |

## 11. Verification & Testing

### 11.1 Test Scenarios

| ID | Scenario | Type | Input | Expected Output | Pass Criteria |
|----|----------|------|-------|-----------------|---------------|
| 010 | pytest runs clean | Auto | `pytest` | No fixture errors | 0 errors |
| 020 | Smoke tests still work | Manual | Direct invocation | Tests execute | Output valid |

### 11.2 Test Commands

```bash
# Verify no more fixture errors (should return 0)
poetry run pytest --collect-only 2>&1 | grep -c "fixture 'url' not found"

# Verify smoke_test.py NOT collected
poetry run pytest --collect-only | grep smoke_test
# Should return nothing (no output)

# Full test run (should pass without fixture errors)
poetry run pytest -v

# Manual smoke test invocation (still works)
python tools/smoke_test.py https://your-deployed-endpoint.com
```

## 12. Definition of Done

### Code
- [ ] All `test_*` functions renamed to `verify_*` in `tools/smoke_test.py`
- [ ] CLI entry point (`__main__`) updated to call `verify_*` functions
- [ ] No more "fixture 'url' not found" errors

### Tests
- [ ] `pytest --collect-only` does NOT collect `smoke_test.py`
- [ ] `pytest -v` runs without fixture errors
- [ ] Manual invocation `python tools/smoke_test.py <url>` still works

---

## Appendix: Gemini Review Response

**Review Date:** 2026-01-05
**Reviewer:** Gemini 3 Pro

### Tier 2 Issues (HIGH) - Addressed

| Issue | Resolution |
|-------|------------|
| Ambiguous purpose | Clarified: smoke tests are for manual/post-deployment verification, NOT unit tests |
| Multiple options without decision | Selected Option B (rename to `verify_*`) as definitive requirement |

### Tier 3 Issues (SUGGESTIONS) - Addressed

| Issue | Resolution |
|-------|------------|
| CLI Entry Point | Added §6.2 with robust CLI invocation example |
| Alternative pytest marker | Rejected in favor of cleaner rename approach |
