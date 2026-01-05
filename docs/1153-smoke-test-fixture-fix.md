# 1153 - Bug: Fix smoke_test.py pytest Fixture Errors

## 1. Context & Goal
* **Issue:** #153
* **Objective:** Fix the 5 pytest fixture errors caused by missing `url` fixture in smoke_test.py.
* **Status:** Draft
* **Related Issues:** None

### Open Questions
*Questions that need clarification before or during implementation. Remove when resolved.*

- [ ] What is the intended purpose of these test functions? Are they pytest tests or manual invocation functions?
- [ ] If they're manual functions, should they be renamed to not start with `test_` to avoid pytest collection?
- [ ] If they're pytest tests, what URL fixture should be provided? A local test server? GitHub Pages test site?
- [ ] Should these tests use the test site infrastructure from #105?

## 2. Requirements

1. Eliminate the 5 "fixture 'url' not found" errors from pytest runs
2. Either convert functions to proper pytest tests OR exclude from pytest collection
3. Maintain any existing functionality for manual invocation if needed

## 3. Alternatives Considered

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| Rename to not start with `test_` | Quick fix, keeps manual usage | Loses test coverage | Consider |
| Create URL fixture in conftest.py | Proper pytest integration | Need to determine correct URL | Consider |
| Parametrize with test URLs | Full test coverage | More complex | Consider |
| Delete file entirely | Clean codebase | Lose smoke test capability | Rejected |

**Rationale:** TBD - depends on intended purpose of these functions.

## 4. Data & Fixtures

N/A - This is a test infrastructure fix.

## 5. Diagram

N/A

## 6. Technical Approach

* **Module:** `tools/smoke_test.py`
* **Dependencies:** pytest, requests
* **Pattern:** Fixture injection or function renaming

### Option A: Create fixture in conftest.py

```python
# tests/conftest.py or tools/conftest.py
import pytest

@pytest.fixture
def url():
    """Provide test URL for smoke tests."""
    return os.environ.get("TEST_BASE_URL", "https://martymcenroe.github.io/Aletheia/tests/")
```

### Option B: Rename functions

```python
# Rename test_valid_input to smoke_valid_input
# Will not be collected by pytest
```

### Option C: Mark as not a test

```python
# Add pytest.mark.skip or move to different module
```

## 7. Interface Specification

### Current Broken Functions
```python
def test_valid_input(url: str) -> dict:  # url fixture not found
def test_blocked_input(url: str) -> dict:
def test_empty_input(url: str) -> dict:
def test_prompt_injection(url: str) -> dict:
def test_tone_neutrality(url: str) -> dict:
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
# Verify no more fixture errors
poetry run pytest --collect-only 2>&1 | grep -c "fixture 'url' not found"
# Should return 0

# Full test run
poetry run pytest -v
```

## 12. Definition of Done

### Code
- [ ] No more "fixture 'url' not found" errors
- [ ] Smoke test functionality preserved

### Tests
- [ ] pytest runs without collection errors
- [ ] All legitimate tests pass
