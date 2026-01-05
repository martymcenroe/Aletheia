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
- [ ] Should we add standard open-source files (CONTRIBUTING.md, CODE_OF_CONDUCT.md)?
- [ ] What's the target structure? Need explicit before/after.

## 2. Requirements

1. Repository structure follows open-source best practices
2. Clear separation of concerns (src, tests, tools, docs, extensions)
3. README prominently accessible
4. No breaking changes to existing workflows

## 3. Alternatives Considered

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| Minimal restructure | Low risk | May not achieve "professional" | Consider |
| Major restructure | Clean result | Breaking changes, effort | Consider |
| Monorepo tools (nx, turborepo) | Scalable | Overkill for this project | Rejected |

**Rationale:** TBD - need to understand current pain points.

## 4. Data & Fixtures

N/A - Repository structure change.

## 5. Diagram

### Current Structure (Abbreviated)
```
/
├── extension-chrome-V3/
├── extension-firefox-V2/
├── src/
├── tests/
├── tools/
├── docs/
├── .github/
├── CLAUDE.md, GEMINI.md, etc.
└── Various root files
```

### Proposed Structure (TBD)
```
/
├── extensions/
│   ├── chrome/
│   └── firefox/
├── src/
│   └── lambda/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── tools/
│   ├── aws/
│   ├── build/
│   └── print/
├── docs/
└── Standard root files
```

## 6. Technical Approach

* **Module:** Repository-wide
* **Dependencies:** Update all import paths, CI workflows
* **Pattern:** Standard open-source layout

### Considerations

1. **Import Path Updates**
   - Python imports in tests
   - CI workflow file paths
   - Documentation references

2. **Git History**
   - Use `git mv` to preserve history
   - May need multiple commits for clean history

3. **CI/CD Impact**
   - GitHub Actions workflow paths
   - Build scripts

### Migration Script (Draft)

```bash
#!/bin/bash
# Example structure changes - TBD based on requirements

# Move extensions to unified directory
mkdir -p extensions
git mv extension-chrome-V3 extensions/chrome
git mv extension-firefox-V2 extensions/firefox

# Reorganize tools
mkdir -p tools/{aws,build,print}
git mv tools/provision.sh tools/aws/
git mv tools/build_release.py tools/build/

# Etc.
```

## 7. Interface Specification

N/A - No code interfaces change.

## 8. Security Considerations

| Concern | Mitigation | Status |
|---------|------------|--------|
| Sensitive files exposed | Audit .gitignore | TODO |
| Permission changes lost | Careful git mv | TODO |

**Fail Mode:** N/A

## 9. Performance Considerations

N/A - Structure change only.

## 10. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Break CI workflows | High | Med | Update all workflow paths |
| Break import paths | High | Med | Update and test thoroughly |
| Documentation drift | Med | High | Update all doc references |
| Developer confusion | Med | Med | Clear commit messages, announce |

## 11. Verification & Testing

### 11.1 Test Scenarios

| ID | Scenario | Type | Input | Expected Output | Pass Criteria |
|----|----------|------|-------|-----------------|---------------|
| 010 | CI passes after restructure | Auto | Push branch | Green CI | All checks pass |
| 020 | Imports still work | Auto | pytest | Tests pass | No import errors |
| 030 | Build scripts work | Auto | Build release | Artifacts created | No errors |

### 11.2 Test Commands

```bash
# After restructure, verify everything still works
poetry run pytest
npm run lint
npm run build

# Check for broken references
grep -r "extension-chrome-V3" docs/  # Should find no results after rename
```

## 12. Definition of Done

### Prerequisites
- [ ] Target structure agreed upon
- [ ] Migration plan documented

### Code
- [ ] Structure reorganized per plan
- [ ] All import paths updated
- [ ] CI workflows updated

### Tests
- [ ] All tests pass
- [ ] Build scripts work
- [ ] CI green

### Documentation
- [ ] README updated if needed
- [ ] File inventory (0003) updated
- [ ] All doc references updated
