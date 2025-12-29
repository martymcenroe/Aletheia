# 0203 - ADR: Stateful Serverless Pattern

**Status:** Implemented
**Date:** 2025-12-15
**Categories:** Infrastructure, Data

## 1. Context

Aletheia is a GenAI agent requiring persistent memory (conversation history, user context). AWS Lambda is inherently stateless — each invocation starts fresh. We needed a pattern to maintain agent state across invocations while preserving Lambda's benefits (zero idle cost, auto-scaling).

The challenge: How do we build a stateful agent on stateless infrastructure?

## 2. Decision

**We will use a "Hydration/Dehydration" pattern with DynamoDB for state persistence.**

Each Lambda invocation:
1. **Hydrates:** Loads state from DynamoDB using `thread_id`
2. **Executes:** LangGraph processes with full state context
3. **Dehydrates:** Persists updated state back to DynamoDB

## 3. Alternatives Considered

### Option A: DynamoDB Hydration/Dehydration — SELECTED
**Description:** Store agent state in DynamoDB, load on each invocation.

**Pros:**
- Zero idle cost (no always-on servers)
- Infinite scale (DynamoDB + Lambda both auto-scale)
- Simple key-value pattern (`thread_id` → state)
- Supports TTL for automatic cleanup
- LangGraph has built-in checkpointer support

**Cons:**
- Latency overhead on each invocation (~50-100ms)
- State size limited by DynamoDB item size (400KB)
- Requires careful state serialization

### Option B: ElastiCache (Redis) — Rejected
**Description:** Store state in Redis for faster access.

**Pros:**
- Sub-millisecond latency
- Rich data structures

**Cons:**
- Always-on cost (even when idle)
- Requires VPC configuration
- Overkill for our access patterns
- No built-in persistence (risk of data loss)

### Option C: ECS/Fargate Long-Running Service — Rejected
**Description:** Run agent as persistent service with in-memory state.

**Pros:**
- No hydration overhead
- Simpler state management

**Cons:**
- Always-on cost
- Manual scaling configuration
- Memory limits agent capacity
- State lost on restart

### Option D: S3 for State — Rejected
**Description:** Store state as JSON files in S3.

**Pros:**
- Unlimited state size
- Simple storage

**Cons:**
- Higher latency than DynamoDB
- No conditional updates (race conditions)
- Not designed for frequent small reads/writes

## 4. Rationale

DynamoDB + Lambda is the "serverless native" approach:
- Pay only when processing requests
- Scales automatically to any load
- LangGraph's `DynamoDBSaver` handles serialization
- TTL provides automatic data hygiene

The ~100ms hydration overhead is acceptable for GenAI workloads where Bedrock API latency dominates (1-3 seconds).

## 5. Security Risk Analysis

| Risk | Impact | Likelihood | Severity | Mitigation |
|------|--------|------------|----------|------------|
| State data exposure | High | Low | 3 | IAM policies restrict access; encryption at rest |
| State corruption | Med | Low | 2 | DynamoDB transactions; validation on hydration |
| Race condition (concurrent updates) | Med | Med | 4 | Conditional writes; `thread_id` isolation |
| State size exceeds limit | Low | Low | 1 | Monitor item sizes; compress if needed |

**Residual Risk:** Low. DynamoDB is battle-tested for this pattern.

## 6. Consequences

### Positive
- Zero idle cost (significant savings)
- Infinite agent memory capacity (disk, not RAM)
- Auto-scaling without configuration
- Built-in backup and recovery
- TTL for automatic data cleanup

### Negative
- Hydration latency on each request (~50-100ms)
- State serialization complexity
- DynamoDB costs scale with usage
- Cold starts add to total latency

### Neutral
- State schema must be carefully designed
- Monitoring required for item sizes

## 7. Implementation

- **Related Issues:** #80 (Wire Agent)
- **Related LLDs:** 1080
- **Status:** Complete

DynamoDB table: `aletheia-agent-state`
Partition key: `thread_id`
Checkpointer: `langgraph.checkpoint.dynamodb.DynamoDBSaver`

## 8. References

- [LangGraph Persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- `checkpointer.py` in repository

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2025-12-15 | Gemini | Initial architecture design |
| 2025-12-29 | Claude Opus 4.5 | Extracted to ADR format |
