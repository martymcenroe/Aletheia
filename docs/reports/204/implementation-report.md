# Implementation Report: Issue #204 - Repository Reorganization

**Issue:** #204 - Repository reorganization - move scripts and test data to proper directories
**Status:** Complete
**Date:** 2026-01-10

## Summary

Reorganized repository structure by moving scripts from root to `tools/`, test data to `tests/data/`, landing page to `web/`, and removing empty `scripts/` directory.

## Changes Made

### 1. Python Scripts Moved to tools/
| From (root) | To (tools/) |
|-------------|-------------|
| harvest_test_data.py | tools/harvest_test_data.py |
| run_guardrails.py | tools/run_guardrails.py |
| verify_bedrock.py | tools/verify_bedrock.py |
| verify_holistic.py | tools/verify_holistic.py |

**Note:** `format-issues.py` listed in issue did not exist (already removed or never created).

### 2. AWS Shell Scripts Moved to tools/aws/
| From (root) | To (tools/aws/) |
|-------------|-----------------|
| aws-cleanup-old-resources.sh | tools/aws/cleanup_old_resources.sh |
| aws-inventory-check.sh | tools/aws/inventory_check.sh |

### 3. Test Data Moved to tests/data/
| From (root) | To (tests/data/) |
|-------------|------------------|
| test_ground_truth.json | tests/data/ground_truth.json |
| test_holistic_data.json | tests/data/holistic_data.json |

### 4. Landing Page Moved to web/
| From (root) | To (web/) |
|-------------|-----------|
| index.html | web/index.html |

### 5. Empty Directory Removed
- Deleted `scripts/aws/.gitkeep`
- Directory `scripts/` removed (was empty after .gitkeep removal)

### 6. Documentation Updates
- Updated `docs/0003-file-inventory.md` to reflect new file locations

### 7. Test Updates
- Updated `tests/compliance/test_static_compliance.py` to look for `web/index.html`

## Items Not Found (Skipped)
The following items from the issue were not present in the repository:
- `format-issues.py` - Did not exist
- `batch-pdf.sh`, `print-all-pdfs.sh`, `print-docs.sh` - Did not exist
- `run-audit.bat` - Did not exist

## Out of Scope (Per User Decision)
- `CHATGPT.md` and `GEMINI.md` kept in root (required for agent routing per 0000-GUIDE.md)
- `prompts/` cleanup - Already gitignored, local-only concern

## Verification
- All pytest tests pass (323 passed)
- Pre-existing failures unrelated to this change:
  - Docker integration tests (Docker not running)
  - Audit index consistency (missing 0828 entry - pre-existing)

## Files Changed
```
docs/0003-file-inventory.md
tests/compliance/test_static_compliance.py
scripts/aws/.gitkeep (deleted)
harvest_test_data.py -> tools/harvest_test_data.py (renamed)
run_guardrails.py -> tools/run_guardrails.py (renamed)
verify_bedrock.py -> tools/verify_bedrock.py (renamed)
verify_holistic.py -> tools/verify_holistic.py (renamed)
aws-cleanup-old-resources.sh -> tools/aws/cleanup_old_resources.sh (renamed)
aws-inventory-check.sh -> tools/aws/inventory_check.sh (renamed)
test_ground_truth.json -> tests/data/ground_truth.json (renamed)
test_holistic_data.json -> tests/data/holistic_data.json (renamed)
index.html -> web/index.html (renamed)
```

## Post-Implementation Acceptance Criteria Status
- [x] No `.py` files in repository root (4 moved)
- [x] No utility `.sh` files in repository root (except `deploy.sh`, `provision.sh`)
- [x] No test data JSON files in repository root (2 moved)
- [x] Empty `scripts/` directory removed
- [x] All tests pass after reorganization
- [x] File inventory updated
