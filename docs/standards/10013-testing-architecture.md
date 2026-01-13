# 0013 - Testing Architecture

## 1. Overview

This document defines Aletheia's testing strategy: test pyramid, tooling choices, coverage requirements, and automation approach.

**Status:** Draft (2026-01-04)
**Related Issues:** #105 (Test Infrastructure), #104 (Age Gate)

---

## 2. Test Pyramid

```
                    ┌───────────┐
                    │    E2E    │  ← Playwright (extension + pages)
                    │   Tests   │     Slow, expensive, high confidence
                   ─┴───────────┴─
                  ┌───────────────┐
                  │  Integration  │  ← pytest + mocked AWS
                  │    Tests      │     Medium speed, real code paths
                 ─┴───────────────┴─
                ┌───────────────────┐
                │    Unit Tests     │  ← pytest (pure functions)
                │                   │     Fast, isolated, high coverage
               ─┴───────────────────┴─
```

### 2.1 Layer Definitions

| Layer | Scope | Tools | Speed | Count |
|-------|-------|-------|-------|-------|
| Unit | Single function/class | pytest | <1s each | Many (100+) |
| Integration | Module interactions | pytest + moto | <5s each | Medium (20-50) |
| E2E | Full user flow | Playwright | <30s each | Few (10-20) |

---

## 3. Test Categories

### 3.1 Backend (Python)

| Category | Location | What It Tests |
|----------|----------|---------------|
| Guardrails | `tests/test_guardrails.py` | Selection check, validators |
| Denylist | `tests/test_denylist.py` | Hash lookup, term blocking |
| Semantic | `tests/test_semantic.py` | LLM classification (mocked) |
| Lambda Handler | `tests/test_lambda_handler.py` | Request/response flow |
| Etymologist | `tests/test_etymologist.py` | JSON response structure |
| Signal Inspector | `tests/test_signal_inspector.py` | Meta tag parsing |
| Denylist Fetcher | `tests/test_fetch_denylist.py` | Wikipedia parsing |

### 3.2 Frontend (Extension)

| Category | Location | What It Tests |
|----------|----------|---------------|
| XSS Prevention | `tests/e2e/xss-protection.spec.js` | textContent vs innerHTML |
| Age Gate | `tests/e2e/age-gate.spec.js` | Rating meta detection |
| Allowlist | `tests/e2e/allowlist.spec.js` | Domain enable/disable |
| Overlay | `tests/e2e/overlay.spec.js` | Positioning, timing, dismiss |
| Badge | `tests/e2e/badge.spec.js` | State transitions |

### 3.3 Security

| Category | Location | What It Tests |
|----------|----------|---------------|
| WAF Integration | `tests/e2e/waf-integration.spec.js` | Rate limiting, headers |
| XSS Payloads | `tests/fixtures/html/test-xss-*.html` | OWASP vectors |

### 3.4 Accessibility (#160)

| Category | Location | What It Tests |
|----------|----------|---------------|
| WCAG A Compliance | `tests/e2e/accessibility.spec.js` | axe-core scan of popup.html |
| WCAG AA Compliance | `tests/e2e/accessibility.spec.js` | Warning-level checks |
| ARIA Attributes | `tests/e2e/accessibility.spec.js` | role, aria-live, aria-label |

**Tools:** @axe-core/playwright

**Thresholds:**
- WCAG Level A violations: CI fails
- WCAG Level AA violations: CI warns (logged)

### 3.5 Performance (#161)

| Category | Location | What It Tests |
|----------|----------|---------------|
| Lambda Latency | `tests/test_lambda_benchmark.py` | Handler response time (mocked) |
| Extension Load | `tests/e2e/benchmark.spec.js` | Time to interactive |
| Click-to-Glass | `tests/e2e/benchmark.spec.js` | User action to overlay visible |

**Tools:** pytest-benchmark, Playwright metrics

**Thresholds:**
- Lambda warm: < 100ms
- Extension click-to-glass: < 200ms
- Regression tolerance: 20%

---

## 4. Test Infrastructure

### 4.1 GitHub Pages Test Sites (#105)

```
https://martymcenroe.github.io/Aletheia/tests/
├── index.html           # QA Sandbox landing page
├── test-adult.html      # rating="adult" meta tag
├── test-rta.html        # RTA pattern meta tag
├── test-mature.html     # rating="mature" (allowed)
├── test-clean.html      # No restrictions
├── test-xss-script.html # <script> in content
├── test-xss-img.html    # <img onerror> in content
└── test-xss-event.html  # Event handler in content
```

### 4.2 Environment Flexibility

```bash
# Default: GitHub Pages
npm run test:e2e

# Local development
TEST_BASE_URL=http://localhost:8080 npm run test:e2e

# Custom domain
TEST_BASE_URL=https://test.aletheia.study npm run test:e2e
```

### 4.3 Playwright Configuration

**File:** `playwright.config.js`

```javascript
module.exports = {
  testDir: './tests/e2e',
  use: {
    baseURL: process.env.TEST_BASE_URL ||
             'https://martymcenroe.github.io/Aletheia/tests',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chrome-extension',
      use: {
        browserName: 'chromium',
        launchOptions: {
          args: [
            `--disable-extensions-except=${extensionPath}`,
            `--load-extension=${extensionPath}`
          ]
        }
      }
    }
  ]
};
```

---

## 5. Coverage Requirements

### 5.1 Thresholds

| Metric | Threshold | Enforcement |
|--------|-----------|-------------|
| Line Coverage | 70% | CI fails below |
| Branch Coverage | 60% | Warning below |
| Critical Paths | 100% | Manual review |

### 5.2 Critical Paths (Must Be 100%)

- Denylist blocking logic
- XSS prevention (textContent usage)
- Age gate detection
- Rate limiting enforcement
- WCAG Level A accessibility (popup, overlay)

### 5.3 Configuration

**File:** `pyproject.toml`

```toml
[tool.coverage.run]
source = ["src"]
omit = ["tests/*", "*/__init__.py"]

[tool.coverage.report]
fail_under = 70
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

---

## 6. Willison Protocol

*"Your job is to deliver code you have proven to work."*

### 6.1 Requirements

Every PR must include:

1. **Automated tests** that exercise the change
2. **Proof tests fail on revert:**
   ```bash
   git stash           # Remove implementation
   pytest              # Tests MUST fail
   git stash pop       # Restore implementation
   pytest              # Tests MUST pass
   ```
3. **Evidence** in PR description or test report

### 6.2 Test Report Location

```
docs/reports/{IssueID}/
├── implementation-report.md
├── test-report.md
└── test-output.log (optional)
```

---

## 7. Mocking Strategy

### 7.1 AWS Services

| Service | Mock Tool | When to Use |
|---------|-----------|-------------|
| DynamoDB | moto | Unit/Integration tests |
| Bedrock | unittest.mock | Unit tests |
| Bedrock | Real API | Integration tests (marked `@pytest.mark.live`) |

### 7.2 External Services

| Service | Strategy |
|---------|----------|
| GitHub Pages | Real (test sites are ours) |
| LinkedIn OAuth | Mock in tests |
| Web pages | Fixtures in `tests/fixtures/html/` |

### 7.3 Test Markers

```python
@pytest.mark.unit       # Fast, no external deps
@pytest.mark.integration # May use mocked AWS
@pytest.mark.live       # Hits real services (slow)
@pytest.mark.e2e        # Browser automation
@pytest.mark.benchmark  # Performance tests (pytest-benchmark)
@pytest.mark.a11y       # Accessibility tests (axe-core)
```

**Running subsets:**
```bash
pytest -m "unit"                    # Fast feedback
pytest -m "not live"                # CI-safe
pytest -m "live" --run-live         # Manual verification
pytest -m "benchmark" --benchmark-only  # Performance tests
npx playwright test --grep a11y    # Accessibility tests
```

---

## 8. Test Data Management

### 8.1 Golden Sets

| File | Purpose |
|------|---------|
| `tests/data/etymology_golden_set.json` | Known-good etymologist responses |
| `test_ground_truth.json` | Guardrail classification ground truth |

### 8.2 Fixtures

| Directory | Contents |
|-----------|----------|
| `tests/fixtures/html/` | Test HTML pages |
| `tests/fixtures/signal_inspector/` | robots.txt, meta tag samples |

### 8.3 Data Hygiene

**Never commit:**
- Real slurs or hate speech (use hashes or placeholders)
- PII from real users
- API keys or secrets

---

## 9. CI Integration

### 9.1 Current Pipeline

```yaml
# .github/workflows/ci.yml
- name: Run tests with coverage
  run: poetry run pytest tests/ -v --cov=src --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v4
```

### 9.2 Future: E2E in CI

```yaml
# After #105 implementation
- name: Install Playwright
  run: npx playwright install chromium

- name: Run E2E tests
  run: npm run test:e2e
  env:
    TEST_BASE_URL: https://martymcenroe.github.io/Aletheia/tests
```

---

## 10. Local Development

### 10.1 Quick Commands

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=term-missing

# Run specific test file
poetry run pytest tests/test_denylist.py -v

# Run only fast tests
poetry run pytest -m "not live" -x

# Run E2E tests
npm run test:e2e
```

### 10.2 Debugging Failed Tests

```bash
# Verbose output
pytest -vvs tests/test_failing.py

# Drop into debugger on failure
pytest --pdb tests/test_failing.py

# Show local variables on failure
pytest -l tests/test_failing.py
```

---

## 11. References

- 0005-testing-strategy-and-protocols.md (philosophy)
- 0012-devops-architecture.md (CI/CD integration)
- 1105-test-site-infrastructure.md (E2E test pages)
- Willison Protocol: https://simonwillison.net/2025/Dec/18/your-job-is-to-deliver-code/
