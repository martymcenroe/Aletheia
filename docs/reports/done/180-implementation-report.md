# 80 - Implementation Report: Wire Agent to Defense Funnel (ABANDONED)

## 1. Metadata

| Field | Value |
|-------|-------|
| **Issue** | #80 |
| **LLD** | `docs/legacy/1080-wire-agent-logic-langgraph.md` |
| **Test Report** | N/A - Implementation abandoned before testing |
| **Implementer** | Claude Opus 4.5 via Claude Code |
| **Date** | 2025-12-29 |
| **PR** | N/A - Branch deleted |
| **Outcome** | **ABANDONED** - Superseded by Issue #113 |

## 2. Summary

Attempted to wire the LangGraph-based agent to the Defense Funnel (guardrails pipeline). Implementation was completed per LLD but could not be tested due to fundamental infrastructure gaps. Investigation revealed the LangGraph/LangChain architecture was overengineered for Aletheia's actual requirements.

**This implementation failure led directly to ADR 0211 (Naked Python Architecture).**

## 3. Files Created

| File | Description |
|------|-------------|
| `agent.py` | LangGraph agent with guardrails_node, summarizer_node, routing logic |
| `tests/test_agent_wiring.py` | 7 test scenarios for agent wiring |

*Note: All files were deleted as part of the architectural pivot.*

## 4. Files Modified

| File | Changes | Description |
|------|---------|-------------|
| `src/guardrails/engine.py` | Refactored | Integrated SemanticGuardrail with Defense Funnel pattern |
| `lambda_function.py` | Updated | New state structure for LangGraph |

*Note: All changes were reverted.*

## 5. Deviations from LLD

| Deviation | Reason | Impact |
|-----------|--------|--------|
| Implementation abandoned | Architectural mismatch discovered | Complete pivot to new approach |

**Root Cause Analysis:**

The implementation proceeded per LLD but testing revealed:

1. **Deployment pipeline incomplete:** Current `deploy.sh` only deploys harvester function without dependencies
2. **Binary incompatibility:** Windows development environment couldn't produce Lambda-compatible binaries for LangChain dependencies
3. **No Lambda layers configured:** AWS Lambda had no layers attached for LangGraph dependencies

More significantly, investigation prompted a requirements review:

| Aletheia's Actual Flow | LangGraph/LangChain Purpose |
|------------------------|----------------------------|
| Validate input (if-else) | Multi-turn agent conversations |
| Call Bedrock once | Complex tool orchestration |
| Return response | Iterative refinement loops |

**Conclusion:** The orchestration framework solved problems Aletheia doesn't have.

## 6. Test Harness

- **Test file:** `tests/test_agent_wiring.py` (deleted)
- **Scenarios:** 7 test cases covering happy path, edge cases, error handling
- **Status:** Could not execute - `ImportError` for langgraph components

## 7. Test Coverage

| Area | Coverage | Notes |
|------|----------|-------|
| Unit tests | Written | Could not run due to missing dependencies |
| Integration tests | Not attempted | Blocked by unit test failures |
| E2E tests | Not attempted | Infrastructure not ready |

**Willison Protocol Compliance:** FAILED - Could not prove code works

## 8. Lessons Learned

1. **Test early, test often:** We wrote all the code before attempting to run tests. Should have verified test infrastructure first.

2. **Framework bloat is real:** LangGraph/LangChain added ~200MB of dependencies for what is essentially `if/else` logic.

3. **Question the architecture:** The original LangGraph decision (ADR 0205) was made based on anticipated complexity that never materialized. "Resume Driven Development" created unnecessary overhead.

4. **Deployment friction is a signal:** When deployment becomes complex, question whether the architecture is appropriate for the constraints.

5. **MVP discipline:** Chrome Web Store submission needs working software, not sophisticated infrastructure.

## 9. Open Issues

| Issue | Type | Description |
|-------|------|-------------|
| #113 | Replacement | Naked Python Architecture - the correct approach |
| ADR 0211 | Decision | Documents the pivot and rationale |

## 10. Orchestrator Review Notes

**Reviewer:** Marty McEnroe
**Date:** 2025-12-29

### In-Scope Observations
- Implementation was technically correct per LLD
- Failure was infrastructure/architectural, not code quality

### New-Scope Observations
- Created: #113 - Naked Python Architecture (replacement approach)
- Created: ADR 0211 - Documents the decision to abandon LangGraph

### Meta Observations
- **Process improvement:** Should have validated deployment pipeline before investing in implementation
- **Architecture review:** Complex frameworks need justification against actual requirements, not anticipated future needs
- **Session management insight:** This failure highlighted the challenge of maintaining context across multiple LLM sessions with different agents. The CMS philosophy was reinforced: everything needed for context must be in documentation, not in human memory.

### Approval
- [x] Code reviewed (before abandonment)
- [ ] Manual tests passed - N/A (not testable)
- [x] Decision to abandon was correct
