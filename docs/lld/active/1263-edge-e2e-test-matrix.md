# 1263 - Test: Add Edge/Chromium Browser E2E Test Matrix

## 1. Context & Goal
* **Issue:** #263
* **Objective:** Add Microsoft Edge to the Playwright E2E test matrix to verify Chrome extension compatibility.
* **Status:** Draft
* **Related Issues:** #160 (accessibility CI), #161 (performance benchmarks)

### Open Questions
*Questions that need clarification before or during implementation. Remove when resolved.*

- [ ] Should Edge tests run on every PR or only on schedule (weekly)?
- [ ] Block PRs on Edge failures, or warn-only initially?
- [ ] Do we need Edge-specific test fixtures, or do Chrome fixtures work?

## 2. Requirements

Per Test Gap Analysis 2026-01-10:
1. Playwright config includes Edge channel
2. E2E tests run against Edge in CI
3. Extension loads correctly in Edge
4. All existing E2E specs pass in Edge
5. CI workflow updated to include Edge runs

## 3. Alternatives Considered

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| Separate Edge workflow job | Parallel execution, clear isolation | More CI config, duplicate setup | **Selected** |
| Same job, matrix strategy | Single workflow file | Longer total time, all-or-nothing | Consider if job isolation fails |
| Manual Edge testing only | No CI cost | Regression risk, human error | Rejected |
| BrowserStack/Sauce Labs | Real browsers, more coverage | Cost, external dependency | Future consideration |

**Rationale:** Separate job provides isolation - Edge failures don't block Chrome tests. Can be run in parallel for same total CI time.

## 4. Data & Fixtures

### 4.1 Test Reuse

All existing E2E specs should run unchanged:
- `tests/e2e/age-gate.spec.js`
- `tests/e2e/museum-label.spec.js`
- `tests/e2e/xss-protection.spec.js`
- `tests/e2e/shadow-dom-security.spec.js`
- `tests/e2e/accessibility.spec.js`
- `tests/e2e/waf-integration.spec.js`

### 4.2 Edge-Specific Considerations

| Concern | Mitigation |
|---------|------------|
| Edge uses different extension path | Same as Chrome (Chromium-based) |
| Edge DevTools protocol | Same as Chrome (Chromium-based) |
| Edge installation in CI | Use `channel: 'msedge'` in Playwright |

## 5. Diagram

```mermaid
flowchart TD
    A[PR Push] --> B[CI Workflow]
    B --> C[Job: test-chrome]
    B --> D[Job: test-edge]

    C --> E[Install Chrome]
    C --> F[Load Extension]
    C --> G[Run E2E Specs]
    C --> H{Pass?}

    D --> I[Install Edge]
    D --> J[Load Extension]
    D --> K[Run E2E Specs]
    D --> L{Pass?}

    H -->|Yes| M[Chrome OK]
    H -->|No| N[Block PR]

    L -->|Yes| O[Edge OK]
    L -->|No| P[Warn or Block]

    Note over P: Start with Warn<br/>Promote to Block after baseline
```

## 6. Technical Approach

### 6.1 Playwright Configuration

Update `playwright.config.js`:

```javascript
projects: [
  {
    name: 'chromium',
    use: { ...devices['Desktop Chrome'] },
  },
  {
    name: 'edge',
    use: {
      channel: 'msedge',
      // Extension loading uses same path as Chrome
    },
  },
],
```

### 6.2 CI Workflow

Add to `.github/workflows/test.yml`:

```yaml
jobs:
  test-edge:
    runs-on: windows-latest  # Edge pre-installed on Windows runners
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npx playwright install msedge
      - run: npx playwright test --project=edge
```

### 6.3 Extension Loading

Playwright loads Chrome extensions via `--load-extension` flag. Edge (Chromium) uses identical mechanism:

```javascript
const context = await chromium.launchPersistentContext('', {
  headless: false,
  channel: 'msedge',
  args: [
    `--disable-extensions-except=${extensionPath}`,
    `--load-extension=${extensionPath}`,
  ],
});
```

## 7. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Edge not available in CI | Low | High | Windows runner has Edge pre-installed |
| Extension manifest incompatibility | Very Low | Medium | MV3 is cross-browser standard |
| Flaky tests in Edge | Medium | Low | Start with warn-only mode |
| Increased CI time | Medium | Low | Parallel job execution |

## 8. Acceptance Criteria

- [ ] `playwright.config.js` includes Edge project
- [ ] CI workflow has Edge test job
- [ ] All 7 E2E spec files pass in Edge
- [ ] Edge failures produce clear error output
- [ ] Documentation updated (README test section)

## 9. Out of Scope

- Firefox E2E tests (different extension, tracked separately)
- Safari testing (no extension support)
- Mobile browser testing
- Visual regression comparison Chrome vs Edge
