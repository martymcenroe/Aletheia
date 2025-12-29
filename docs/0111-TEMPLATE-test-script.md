# 0111 - Template: Manual Test Script

## Usage
Copy this template when creating a reproducible manual test procedure.
Target Location: `docs/tests/` (create if missing) or `tests/manual/`.

---

## Template

# Test Script: {Feature Name}

**ID:** {TS-XXX}
**Feature Ref:** {Issue #ID}
**Date:** {YYYY-MM-DD}

## 1. Objective
{Brief one-sentence description of what we are verifying.}

## 2. Prerequisites
- [ ] **Environment:** {e.g., Local, Dev, Prod}
- [ ] **State:** {e.g., User logged in, Database empty}
- [ ] **Config:** {e.g., Lambda Concurrency set to 1}

## 3. Execution

### Scenario A: {Happy Path}
| Step | Action | Expected Behavior | Check |
|:--- |:--- |:--- |:--- |
| 1 | {User Action} | {System Response} | [ ] |
| 2 | {User Action} | {System Response} | [ ] |
| 3 | {User Action} | {System Response} | [ ] |

### Scenario B: {Error/Edge Case}
| Step | Action | Expected Behavior | Check |
|:--- |:--- |:--- |:--- |
| 1 | {Force Failure} | {UI shows Error State} | [ ] |
| 2 | {Retry} | {System recovers} | [ ] |

## 4. Post-Condition Verification
- [ ] {Database record exists?}
- [ ] {Logs show expected error code?}

## 5. Notes / Observations
- {Log any oddities here}
