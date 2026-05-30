# 10263 - Test: Add Edge/Chromium Browser E2E Test Matrix

> **SUPERSEDED 2026-05-30 by Aletheia #697 and follow-up #705.** The Edge E2E test matrix this LLD designed is no longer maintained. Aletheia is not distributed through Edge Add-ons and the FAQ (`Aletheia.wiki/FAQ.md:20`) explicitly disclaims Edge support: *"Edge and other Chromium-based browsers may work but are not officially supported."* The CI job that ran this matrix (`.github/workflows/e2e-edge.yml`) was deleted in PR #698; the `edge` Playwright project block was removed in the PR closing #705. This file is preserved for historical reference only — do not treat its design as live.

## 1. Context & Goal
* **Issue:** #263
* **Objective:** Add Microsoft Edge to the Playwright E2E test matrix to verify Chrome extension compatibility.
* **Status:** Draft
* **Related Issues:** #160 (accessibility CI), #161 (performance benchmarks), #272 (Shadow DOM patch), #306 (Chrome E2E CI gate - **DEPENDENCY**)

### Open Questions
*Questions that need clarification before or during implementation. Remove when resolved.*

- [x] Should Edge tests run on every PR or only on schedule? **Every PR (parallel job)**
- [x] Block PRs on Edge failures, or warn-only initially? **Warn-only initially, promote to blocking after baseline**
- [x] Do we need Edge-specific test fixtures? **No - Chrome fixtures work (Chromium-based)**

## 2. Requirements

Per Test Gap Analysis 2026-01-10:

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| R1 | Playwright config includes Edge | `projects` array has Edge entry |
| R2 | E2E tests run against Edge in CI | GitHub Actions job for Edge |
| R3 | Extension loads in Edge | Extension ID logged on startup |
| R4 | All E2E specs pass in Edge | 0 failures in Edge project |
| R5 | CI workflow created | `.github/workflows/e2e-edge.yml` created for Edge tests |

## 3. Alternatives Considered

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| Separate Edge workflow job | Parallel execution, clear isolation | More CI config | **Selected** |
| Same job, matrix strategy | Single workflow file | Longer total time, all-or-nothing | Rejected |
| Manual Edge testing only | No CI cost | Regression risk, human error | Rejected |
| BrowserStack/Sauce Labs | Real browsers | Cost, external dependency | Future consideration |

**Rationale:** Separate job provides isolation - Edge failures don't block Chrome tests. Can be run in parallel for same total CI time.

## 4. Data & Fixtures

### 4.1 Data Sources

| Attribute | Value |
|-----------|-------|
| Source | Existing Chrome E2E test fixtures |
| Format | HTML test pages, extension build |
| Size | ~50KB extension, ~10 test files |
| Refresh | Per CI run |
| Copyright/License | MIT (project code) |

### 4.2 Data Pipeline

```
Extension build ──load──► Edge browser ──execute──► Playwright specs ──report──► CI
```

### 4.3 Test Fixtures

| Fixture | Source | Notes |
|---------|--------|-------|
| Extension source | `extensions/chrome/` | Unpacked extension (no build step) |
| Test HTML pages | `tests/e2e/fixtures/` | Reused |
| Mock responses | Playwright route handlers | Reused |

### 4.4 Deployment Pipeline

CI only - no production deployment changes.

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
    L -->|No| P[Warn - Do Not Block]

    Note over P: Start with Warn<br/>Promote to Block after baseline
```

## 6. Technical Approach

* **Module:**
  - `playwright.config.js` - Add Edge project
  - `.github/workflows/e2e-edge.yml` - NEW file for Edge CI job
* **Dependencies:** Playwright, Microsoft Edge (CI has it pre-installed)
* **Pattern:** Browser matrix testing

### 6.1 Playwright Configuration

Add Edge project to existing CommonJS config:

```javascript
// playwright.config.js - ADD edge project to existing projects array
const { defineConfig, devices } = require("@playwright/test");

module.exports = defineConfig({
  // ... existing config (use block with launchOptions for extension) ...
  projects: [
    // IMPORTANT: Keep existing chromium project to avoid regression
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        headless: false,  // Extensions require headed mode
      },
    },
    // NEW: Add Edge project
    {
      name: 'edge',
      use: {
        channel: 'msedge',
        headless: false,  // Extensions require headed mode
        // Inherits launchOptions from global use block (extension loading)
      },
    },
  ],
});
```

**Note:** Uses CommonJS syntax to match existing project structure. Both chromium and edge projects must be explicitly defined to prevent regression in existing Chrome tests.

### 6.2 CI Workflow

**Action:** Create NEW file `.github/workflows/e2e-edge.yml` (separate from existing `ci.yml`).

```yaml
# .github/workflows/e2e-edge.yml - NEW FILE
name: E2E Tests (Edge)

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test-edge:
    runs-on: ubuntu-latest  # Edge available on Linux via channel
    timeout-minutes: 15  # Prevent stalled browser hangs
    continue-on-error: true  # Warn-only initially
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npx playwright install msedge
      - run: npx playwright install-deps msedge  # Install OS-level browser dependencies
      - run: xvfb-run --auto-servernum --server-args="-screen 0 1280x960x24" npx playwright test --project=edge
      - uses: actions/upload-artifact@v4
        if: always()  # Upload even on failure for debugging
        with:
          name: playwright-report-edge
          path: playwright-report/
          retention-days: 7
```

**Notes:**
- Uses `ubuntu-latest` (cheaper than Windows runners)
- Playwright supports Edge on Linux via `channel: 'msedge'`
- `continue-on-error: true` for warn-only mode initially
- Extension is unpacked (loaded from `extensions/chrome/`), no build step needed
- `xvfb-run` required for headed mode (extensions require headed) on Linux CI
- `install-deps` ensures OS-level libraries for Edge are present
- Artifact upload runs `always()` to capture reports even on failure (critical for warn-only debugging)
- `timeout-minutes: 15` prevents stalled jobs from consuming CI minutes

### 6.3 Extension Loading

Extension loading is configured in `playwright.config.js` via `launchOptions` in the global `use` block. The Edge project inherits these settings automatically - no custom helper needed.

## 7. Interface Specification

### 7.1 Data Structures

```typescript
// Playwright project config
interface ProjectConfig {
  name: string;        // "chromium" | "edge"
  use: {
    channel?: string;  // "msedge" for Edge
    ...BrowserConfig;
  };
}
```

### 7.2 Function Signatures

N/A - No custom functions needed. Edge testing uses standard Playwright config.

### 7.3 Logic Flow (Pseudocode)

```
1. CI triggers on PR
2. test-edge job starts on ubuntu-latest
3. Install Edge via Playwright (`npx playwright install msedge`)
4. Build extension
5. Launch Edge with extension loaded
6. Run all E2E specs
7. Report results (warn on failure, don't block)
8. After baseline established: promote to blocking
```

## 8. Security Considerations

| Concern | Mitigation | Status |
|---------|------------|--------|
| Extension permissions in Edge | Same manifest as Chrome | N/A |
| CI secrets exposure | No secrets needed for E2E | N/A |
| Browser sandbox bypass | Playwright defaults secure | Addressed |

**Fail Mode:** N/A - Testing infrastructure only.

## 9. Performance Considerations

| Metric | Budget | Approach |
|--------|--------|----------|
| CI time (Edge job) | < 5 min | Parallel with Chrome |
| Total CI time | Same as before | Parallel execution |
| Runner cost | ~$0.008/min | Ubuntu runner (same as Chrome) |

**Bottlenecks:** Edge installation via Playwright (~30s download).

## 10. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Edge not available in CI | High | Very Low | Playwright installs Edge via `msedge` channel |
| Extension incompatibility | Med | Very Low | MV3 is cross-browser standard |
| Flaky tests in Edge | Med | Med | Start with warn-only, add retries |
| Increased CI time | Low | Low | Parallel job execution |

## 11. Verification & Testing

*Ref: [AgentOS:standards/0007-testing-strategy](AgentOS:standards/0007-testing-strategy)*

**Testing Philosophy:** All testing is automated. This LLD is itself a testing infrastructure change.

### 11.1 Test Scenarios

| ID | Scenario | Type | Input | Expected Output | Pass Criteria |
|----|----------|------|-------|-----------------|---------------|
| 010 | Edge launches with extension | Auto | `npx playwright test --project=edge` | Browser starts | Extension ID in logs |
| 020 | museum-label.spec passes | Auto | Edge + extension | Test passes | 0 failures |
| 030 | age-gate.spec passes | Auto | Edge + extension | Test passes | 0 failures |
| 040 | xss-protection.spec passes | Auto | Edge + extension | Test passes | 0 failures |
| 050 | shadow-dom-security.spec passes | Auto | Edge + extension | Test passes | 0 failures |
| 060 | accessibility.spec passes | Auto | Edge + extension | Test passes | 0 failures |
| 070 | waf-integration.spec passes | Auto | Edge + extension | Test passes | 0 failures |
| 080 | CI job completes | Auto | PR push | Job green | Exit code 0 |

### 11.2 Test Commands

```bash
# Run Edge tests locally (requires Edge installed)
npx playwright test --project=edge

# Run specific spec in Edge
npx playwright test tests/e2e/museum-label.spec.js --project=edge

# Debug mode
npx playwright test --project=edge --debug

# Check Edge is installed
npx playwright install msedge --dry-run
```

### 11.3 Manual Tests

N/A - All scenarios automated.

## 12. Definition of Done

### Code
- [ ] `playwright.config.js` has Edge project (CommonJS syntax)
- [ ] `.github/workflows/e2e-edge.yml` created (NEW file)
- [ ] Edge job uses `continue-on-error: true` initially
- [ ] Edge job uses `ubuntu-latest` runner

### Tests
- [ ] All 7 E2E spec files pass in Edge locally
- [ ] CI job completes (warn-only mode)
- [ ] Baseline established for all specs
- [ ] Verify CI cost/time impact vs Chrome job

### Documentation
- [ ] README test section mentions Edge
- [ ] CI workflow comments explain warn-only mode

### Review
- [ ] Code review completed
- [ ] Gemini review passed

---

## Appendix: Review Log

*Track all review feedback with timestamps and implementation status.*

### Gemini Review #1 (REJECTED)

**Timestamp:** 2026-01-10
**Reviewer:** Gemini 3 Pro Preview
**Verdict:** REJECTED

#### Comments

| ID | Comment | Implemented? |
|----|---------|--------------|
| G1.1 | "[BLOCKING] ESM syntax - should use CommonJS" | ✅ YES - Changed to require/module.exports |
| G1.2 | "[BLOCKING] Manual browser helper conflicts with fixtures" | ✅ YES - Removed, use config only |
| G1.3 | "[BLOCKING] Missing devices import" | ✅ YES - Added to require |
| G1.4 | "[HIGH] CI file should be explicit" | ✅ YES - New file e2e-edge.yml |
| G1.5 | "[HIGH] Use ubuntu-latest not windows-latest" | ✅ YES - Updated all sections |

### Gemini Review #2 (FEEDBACK)

**Timestamp:** 2026-01-10
**Reviewer:** Gemini 3 Pro Preview
**Verdict:** FEEDBACK

#### Comments

| ID | Comment | Implemented? |
|----|---------|--------------|
| G2.1 | "[BLOCKING] Missing headless: false" | ✅ YES - Added to config |
| G2.2 | "Syntax error in require (space)" | ❌ FALSE POSITIVE - File verified correct via grep |

**Note:** Gemini repeatedly reported a space in `require('@playwright/test')` that does not exist in the actual file. Verified via `grep` - line 110 shows correct syntax. This appears to be a parsing artifact in prompt transmission.

### Gemini Review #3 (FEEDBACK)

**Timestamp:** 2026-01-11
**Reviewer:** Gemini 3 Pro Preview
**Verdict:** FEEDBACK

#### Comments

| ID | Comment | Implemented? |
|----|---------|--------------|
| G3.1 | "[BLOCKING] Missing extension build step in CI" | ✅ YES - Added `npm run build:chrome` to workflow |
| G3.2 | "[BLOCKING] Missing xvfb-run for headed mode on Linux" | ✅ YES - Added xvfb-run wrapper and install-deps |
| G3.3 | "[HIGH] Space in require statement" | ❌ FALSE POSITIVE - Re-verified via file read, line 110 is correct |
| G3.4 | "[SUGGESTION] Add CI caching" | ⏳ DEFERRED - Can add in future optimization |

**Note:** The require syntax false positive persists across multiple reviews. The source file has been verified correct multiple times. This appears to be a prompt transmission artifact.

### Gemini Review #4 (FEEDBACK)

**Timestamp:** 2026-01-11
**Reviewer:** Gemini 3 Pro Preview
**Verdict:** FEEDBACK

#### Comments

| ID | Comment | Implemented? |
|----|---------|--------------|
| G4.1 | "[BLOCKING] Missing artifact upload step" | ✅ YES - Added `actions/upload-artifact@v4` with `if: always()` |
| G4.2 | "[HIGH] Space in YAML action versions" | ❌ FALSE POSITIVE - Same transmission artifact as JS require |
| G4.3 | "[HIGH] Playwright config regression risk" | ✅ YES - Added explicit chromium project to example |
| G4.4 | "[SUGGESTION] Matrix strategy instead of separate workflow" | ⏳ DEFERRED - Separate workflow preferred for isolation |
| G4.5 | "[SUGGESTION] Add job timeout" | ✅ YES - Added `timeout-minutes: 15` |

### Gemini Review #5 (FEEDBACK)

**Timestamp:** 2026-01-11
**Reviewer:** Gemini 3 Pro Preview
**Verdict:** FEEDBACK

#### Comments

| ID | Comment | Implemented? |
|----|---------|--------------|
| G5.1 | "[BLOCKING] Invalid `npm run build:chrome` - script doesn't exist" | ✅ YES - Removed build step; extension is unpacked |
| G5.2 | "[HIGH] Existing workflow missing xvfb-run" | ⏳ N/A - LLD specifies correct config, implementation will follow |
| G5.3 | "[HIGH] Artifact path mismatch" | ⏳ N/A - LLD specifies `playwright-report/` which is correct |
| G5.4 | "[SUGGESTION] Update DoD to reflect existing file" | ⏳ NOTED - Implementation will update existing file |

### Review Summary

| Review | Date | Verdict | Key Issue |
|--------|------|---------|-----------|
| Gemini #1 | 2026-01-10 | REJECTED | ESM/CJS mismatch |
| Gemini #2 | 2026-01-10 | FEEDBACK | headless: false needed |
| Gemini #3 | 2026-01-11 | FEEDBACK | Missing build step + xvfb-run |
| Gemini #4 | 2026-01-11 | FEEDBACK | Missing artifact upload |
| Gemini #5 | 2026-01-11 | FEEDBACK | Invalid build:chrome script |

### Gemini Review #6 (APPROVED)

**Timestamp:** 2026-01-11
**Reviewer:** Gemini 3 Pro Preview
**Verdict:** APPROVED

#### Comments

| ID | Comment | Implemented? |
|----|---------|--------------|
| G6.1 | "[SUGGESTION] Use branch protection instead of continue-on-error" | ⏳ DEFERRED |
| G6.2 | "[SUGGESTION] Verify extension ID stability" | ⏳ NOTED |

**Final Status:** APPROVED
