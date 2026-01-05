# 1102 - Chore: Reorganize Repository Structure for Professional Appearance

## 1. Context & Goal
* **Issue:** #102
* **Objective:** Reorganize the repository structure for a cleaner, more professional appearance suitable for open source.
* **Status:** Draft
* **Related Issues:** None

### Open Questions
*Questions that need clarification before or during implementation. Remove when resolved.*

- [ ] What specific reorganization is desired? The issue body may have details.
- [ ] Should we consolidate Chrome and Firefox extensions into a single `extensions/` directory?
- [ ] Should tools be reorganized (currently `tools/` is flat)?
- [ ] Are there files in root that should move to subdirectories?
- [x] ~~Should we add standard open-source files (CONTRIBUTING.md, CODE_OF_CONDUCT.md)?~~ **Yes - per Gemini review**
- [ ] What's the target structure? Need explicit before/after.

### Resolved Questions (Gemini Review 2026-01-05)

1. **Q: Should `lambda_function.py` move to `src/lambda/`?**
   **A: NO.** Keep at `src/` root to preserve AWS Lambda handler path (`lambda_function.lambda_handler`). Moving requires either AWS config change OR deploy script modification to flatten the zip. Risk > Benefit.

## 2. Requirements

1. Repository structure follows open-source best practices
2. Clear separation of concerns (src, tests, tools, docs, extensions)
3. README prominently accessible
4. **No breaking changes to AWS Lambda deployment** (CRITICAL)
5. No breaking changes to CI workflows
6. Add standard open-source governance files

## 3. Alternatives Considered

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| Minimal restructure | Low risk | May not achieve "professional" | **Selected** |
| Major restructure (move src/) | Clean result | Breaks Lambda deployment | Rejected |
| Monorepo tools (nx, turborepo) | Scalable | Overkill for this project | Rejected |

**Rationale:** Minimal restructure preserves Lambda deployment while improving organization. Focus on extensions consolidation and adding governance files.

## 4. Data & Fixtures

N/A - Repository structure change.

## 5. Diagram

### Current Structure (Abbreviated)
```
/
├── extension-chrome-V3/
├── extension-firefox-V2/
├── src/
│   ├── lambda_function.py    ← KEEP HERE (Lambda handler)
│   ├── etymologist.py
│   ├── guardrails/
│   └── signal_inspector/
├── tests/
├── tools/
├── docs/
├── .github/
├── CLAUDE.md, GEMINI.md, etc.
└── Various root files
```

### Proposed Structure (Minimal Risk)
```
/
├── extensions/
│   ├── chrome/               ← was extension-chrome-V3/
│   └── firefox/              ← was extension-firefox-V2/
├── src/                      ← NO CHANGES (preserve Lambda paths)
│   ├── lambda_function.py
│   ├── etymologist.py
│   ├── guardrails/
│   └── signal_inspector/
├── tests/
│   ├── e2e/                  ← already exists
│   ├── fixtures/             ← already exists
│   └── (unit tests at root)
├── tools/
│   ├── aws/                  ← already exists
│   ├── print/                ← already exists
│   └── (other tools at root)
├── docs/
├── .github/
├── CONTRIBUTING.md           ← NEW
├── CODE_OF_CONDUCT.md        ← NEW
└── Standard root files
```

## 6. Technical Approach

* **Module:** Repository-wide
* **Dependencies:** Update extension paths in CI, Playwright, docs
* **Pattern:** Standard open-source layout

### 6.1 AWS Lambda Deployment (CRITICAL)

**Current Handler:** `lambda_function.lambda_handler`
**Current Deploy:** `deploy.sh` zips `src/*.py`

**Decision:** DO NOT MOVE `src/lambda_function.py`. The deployment script and AWS Lambda configuration assume handler at root of zip. Changing this risks deployment failures.

### 6.2 Files to Move

| Source | Destination | Rationale |
|--------|-------------|-----------|
| `extension-chrome-V3/` | `extensions/chrome/` | Cleaner naming |
| `extension-firefox-V2/` | `extensions/firefox/` | Cleaner naming |

### 6.3 Files to Add

| File | Purpose |
|------|---------|
| `CONTRIBUTING.md` | Contribution guidelines |
| `CODE_OF_CONDUCT.md` | Community standards |

### 6.4 Files NOT Moving

| File | Reason |
|------|--------|
| `src/lambda_function.py` | AWS Lambda handler path |
| `src/*.py` | Import paths, deployment |
| `tools/*.py` | Already organized |
| `tests/*.py` | pytest discovery |

### 6.5 Git History Preservation

**MANDATORY:** Use `git mv` for ALL moves to preserve blame history.

```bash
# CORRECT - preserves history
git mv extension-chrome-V3 extensions/chrome

# WRONG - loses history
mv extension-chrome-V3 extensions/chrome
git add .
```

### 6.6 CI/CD Path Verification (BLOCKING)

Before committing, verify no old paths remain:

```bash
# MUST return empty results
grep -r "extension-chrome-V3" .github/
grep -r "extension-firefox-V2" .github/
grep -r "extension-chrome-V3" playwright.config.js
grep -r "extension-chrome-V3" docs/
```

### Migration Script

```bash
#!/bin/bash
set -e  # Exit on error

# 1. Create new directory structure
mkdir -p extensions

# 2. Move extensions (preserves git history)
git mv extension-chrome-V3 extensions/chrome
git mv extension-firefox-V2 extensions/firefox

# 3. Update CI workflows
sed -i 's|extension-chrome-V3|extensions/chrome|g' .github/workflows/*.yml
sed -i 's|extension-firefox-V2|extensions/firefox|g' .github/workflows/*.yml

# 4. Update Playwright config
sed -i 's|extension-chrome-V3|extensions/chrome|g' playwright.config.js

# 5. Verify no old paths remain
echo "Checking for old paths..."
if grep -r "extension-chrome-V3" .github/ playwright.config.js 2>/dev/null; then
    echo "ERROR: Old paths still exist!"
    exit 1
fi

echo "Migration complete. Run tests before committing."
```

## 7. Interface Specification

N/A - No code interfaces change.

## 8. Security Considerations

| Concern | Mitigation | Status |
|---------|------------|--------|
| Sensitive files exposed | Audit .gitignore after move | TODO |
| Permission changes lost | Use git mv exclusively | TODO |

**Fail Mode:** N/A

## 9. Performance Considerations

N/A - Structure change only.

## 10. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Break Lambda deployment | **CRITICAL** | Low | DO NOT move src/lambda_function.py |
| Break CI workflows | High | Med | sed replacement + verification grep |
| Break Playwright tests | High | Med | Update playwright.config.js |
| Break import paths | High | Low | Not moving src/ structure |
| Documentation drift | Med | High | Update all doc references |
| Lose git history | Med | Low | Mandatory git mv |

## 11. Verification & Testing

### 11.1 Test Scenarios

| ID | Scenario | Type | Input | Expected Output | Pass Criteria |
|----|----------|------|-------|-----------------|---------------|
| 010 | CI passes after restructure | Auto | Push branch | Green CI | All checks pass |
| 020 | Python imports still work | Auto | pytest | Tests pass | No import errors |
| 030 | Extension build works | Auto | build_release.py | ZIPs created | No errors |
| 040 | Playwright finds extension | Auto | npm test | Tests run | Extension loads |
| 050 | Lambda deploy works | Manual | deploy.sh | Function updated | No errors |
| 060 | No old paths in CI | Auto | grep check | Empty result | Zero matches |

### 11.2 Test Commands

```bash
# After restructure, verify everything still works
poetry run pytest
npm run lint

# Build extension (verifies new paths)
python tools/build_release.py

# Run E2E tests (verifies Playwright config)
npm run test:e2e

# CRITICAL: Check for broken references
grep -r "extension-chrome-V3" .github/ docs/ playwright.config.js
# Must return NO results

# Verify Lambda deployment (staging)
./deploy.sh
```

### 11.3 Python Import Verification

Check `pyproject.toml` package discovery after changes:

```bash
# Verify pytest can still find tests
poetry run pytest --collect-only

# Verify package structure
poetry run python -c "from src.lambda_function import lambda_handler; print('OK')"
```

## 12. Definition of Done

### Prerequisites
- [x] Target structure agreed upon (minimal restructure)
- [x] Lambda deployment strategy confirmed (no move)
- [ ] Migration plan documented

### Code
- [ ] Extensions moved to `extensions/` directory
- [ ] CONTRIBUTING.md added
- [ ] CODE_OF_CONDUCT.md added
- [ ] CI workflows updated with new paths
- [ ] playwright.config.js updated
- [ ] All moves done with `git mv`

### Tests
- [ ] All pytest tests pass
- [ ] All E2E tests pass
- [ ] Extension build works
- [ ] Lambda deploy works (manual verification)
- [ ] `grep` verification passes (no old paths)

### Documentation
- [ ] README updated if needed
- [ ] File inventory (0003) updated
- [ ] All doc references updated (living docs only)

---

## Appendix: Gemini Review Response

**Review Date:** 2026-01-05
**Reviewer:** Gemini 3 Pro

### Tier 1 Issues (BLOCKING) - Addressed

| Issue | Resolution |
|-------|------------|
| AWS Handler Path Mismatch | Decision: DO NOT move lambda_function.py. Keep at src/ root. |
| CI/CD Configuration Drift | Added §6.6 mandatory grep verification before commit |

### Tier 2 Issues (HIGH) - Addressed

| Issue | Resolution |
|-------|------------|
| Python Import Resolution | Added §11.3 verification steps. src/ not moving, so minimal risk. |
| Playwright Config | Added to migration script and verification checklist |

### Tier 3 Issues (SUGGESTIONS) - Addressed

| Issue | Resolution |
|-------|------------|
| Standard Files | Added CONTRIBUTING.md and CODE_OF_CONDUCT.md to plan |
| Git History | Added §6.5 mandatory git mv requirement |
