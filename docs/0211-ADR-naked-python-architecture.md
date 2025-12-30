# 0211 - ADR: Naked Python Architecture

**Status:** Implemented
**Date:** 2025-12-29
**Categories:** Infrastructure, Performance, Cost Optimization
**Supersedes:** [0205-ADR-langgraph-orchestration](0205-ADR-langgraph-orchestration.md)

## 1. Context
We previously selected LangGraph (ADR-0205) to orchestrate the AI Agent.
* **Reality Check:** The actual flow is strictly linear (Guardrails -> Save -> Bedrock). We have no cyclic requirements (loops/reflection).
* **Impact:** LangGraph added ~200MB of dependencies (LangChain, Pydantic, etc.) and increased cold-start latency.
* **Constraint:** As a browser extension backend, user-perceived latency (Time-to-First-Token) is critical.

## 2. Decision
**We will replace the LangGraph/LangChain framework with a "Naked Python" architecture using native AWS `boto3`.**

The "Agent" will be a single Python function in `lambda_function.py` that executes a sequential "Defense Funnel" using standard `if/else` logic.

## 3. Alternatives Considered

### Option A: Naked Python (boto3) — SELECTED
**Pros:**
- **Zero Dependencies:** `boto3` is built into the AWS Lambda runtime.
- **Tiny Deployment:** Deployment package drops from ~250MB to < 1MB.
- **Speed:** Removes framework initialization overhead (faster cold starts).
- **Simplicity:** No graph abstractions to debug.

**Cons:**
- **Manual Wiring:** Must manually handle tool calling loops (if added later).
- **Boilerplate:** Must write raw DynamoDB `put_item` calls instead of using LangGraph checkpointers.

### Option B: Keep LangGraph — Rejected
**Pros:**
- Ready for complex cyclic agents.

**Cons:**
- Bloatware for our current use case.
- "Resume Driven Development" artifact.

## 4. Rationale
The complexity cost of the framework outweighs the benefit for a linear pipeline. We prioritize **Latency** and **Simplicity** for the MVP.

## 5. Security Risk Analysis
| Risk | Impact | Likelihood | Severity | Mitigation |
|------|--------|------------|----------|------------|
| Logic fragmentation | Med | Low | Low | Enforce strictly sequential function calls in `lambda_handler`. |
| AWS SDK updates | Low | Low | Low | `boto3` is managed by AWS; highly stable. |

## 6. Implementation
- **Refactor:** `lambda_function.py` becomes the orchestrator.
- **Delete:** `agent.py`, `checkpointer.py`.
- **Cleanup:** Remove `langchain*` from `pyproject.toml`.
