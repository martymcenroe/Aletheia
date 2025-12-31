# Tomorrow's Plan: Issue #45 (Denylist) - First Willison Protocol Feature

**Created:** 2025-12-31
**Goal:** Implement deterministic hate speech filter with full test automation

---

## Prompt for Next Session

Read `docs/0000-GUIDE.md`, then `docs/6000-open-issues.md`. Check `docs/session-logs/Week-starting-2025-12-29.md` for recent context.

**Task:** Implement Issue #45 (Denylist).

**Required reading:**
- `docs/1045-deterministic-hate-filter.md` - Full LLD (template-compliant)
- `docs/1113-naked-python-architecture.md` - Pipeline context
- `docs/0211-ADR-naked-python-architecture.md` - Architectural decision

**This is the first Willison Protocol feature.** See `docs/0005-testing-strategy-and-protocols.md` Section 5. You must:
1. Write the code
2. Write automated tests (`tests/test_denylist.py`)
3. Prove tests FAIL on revert, PASS with implementation
4. Include terminal output proof in PR

**Reminder:** Create worktree before coding (`git worktree add ../Aletheia-45 -b 45-denylist`).

Questions before starting?

---

## Context Summary

### What Changed (2025-12-29 to 2025-12-30)
- **ADR 0211:** Abandoned LangGraph in favor of "Naked Python" (boto3 direct)
- **Issue #80:** Closed as superseded by #113
- **Deleted:** agent.py, checkpointer.py, compliance.py (LangChain code)
- **Removed:** langchain, langchain-aws, langgraph from pyproject.toml
- **Closed:** 8 obsolete issues (#5, #14, #25, #85, #88, #109, #110, #112)

### Critical Path
1. **#45 (Denylist)** - Deterministic filter, standalone module
2. **#113 (Naked Python)** - Wire the full pipeline
3. **#51/#53 (Store)** - Chrome Web Store submission
4. **#100 (Firefox)** - Firefox Add-ons compatibility

### Key Documentation
| Doc | Purpose |
|-----|---------|
| `docs/0005` Section 5 | Willison Protocol (test requirements) |
| `docs/1045` | Denylist LLD (fully template-compliant) |
| `docs/1113` | Naked Python pipeline LLD |
| `docs/0211-ADR` | Why we removed LangGraph |

### Willison Protocol Summary
*"Your job is to deliver code you have proven to work."* — Simon Willison

1. **Manual test** - See it work, capture terminal output
2. **Automated test** - Write tests that fail on revert
3. **Include proof** - Paste output in PR

---

## Files to Create

```
src/guardrails/denylist.py          # Implementation
src/guardrails/resources/denylist.json  # Term list from RSDB
tests/test_denylist.py              # Automated tests
```

## Definition of Done (from 1045)

### Code
- [ ] `src/guardrails/denylist.py` implemented
- [ ] `src/guardrails/resources/denylist.json` created
- [ ] Integration with pipeline

### Tests (Willison Protocol)
- [ ] `tests/test_denylist.py` covers 9 scenarios
- [ ] Tests FAIL when implementation reverted
- [ ] Terminal output captured in PR

### Review
- [ ] Orchestrator verified test proof
- [ ] Issue #45 closed with PR reference
