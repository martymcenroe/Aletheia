# 1113 - Feature: Naked Python Agent Architecture

## 1. Context & Goal

* **Issue:** #113
* **Objective:** Replace LangGraph/LangChain with pure boto3 for faster cold starts and simpler debugging.
* **Status:** In Progress
* **Related Issues:** #80 (superseded), #10 (semantic), #45 (denylist stub)
* **ADR:** [0211-ADR-naked-python-architecture.md](0211-ADR-naked-python-architecture.md)

## 2. Requirements

When this feature is complete:

1. `lambda_function.py` is the sole orchestrator (no `agent.py`)
2. All guardrail checks run sequentially before LLM generation
3. System fails closed on ANY exception (no bypass to LLM)
4. Cold start latency reduced by removing LangChain dependency (~200MB)
5. DynamoDB persistence works without LangGraph checkpointer
6. Streaming response maintained via SSE

## 3. Alternatives Considered

*Full analysis in [ADR 0211](0211-ADR-naked-python-architecture.md)*

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| Naked Python (boto3) | Zero deps, fast cold start, simple | Manual wiring | **Selected** |
| Keep LangGraph | Ready for cycles | 200MB bloat, slow cold start | Rejected |

**Rationale:** Linear pipeline doesn't need graph abstractions. Prioritize latency for browser extension UX.

## 4. Diagram

```mermaid
flowchart LR
    subgraph Lambda["lambda_function.py"]
        direction LR
        A[Input] --> B{Validate}
        B -->|Invalid| X1[400 Bad Request]
        B -->|Valid| C[Denylist]
        C -->|Blocked| X2[403 Blocked]
        C -->|Pass| D[Semantic]
        D -->|Blocked| X2
        D -->|Pass| E[Transform]
        E --> F[Persist]
        F --> G[Generate]
        G --> H[Stream Response]
    end

    style X1 fill:#f66
    style X2 fill:#f66
    style H fill:#6f6
```

## 5. Technical Approach

* **Module:** `lambda_function.py` (orchestrator), `src/guardrails/` (checks)
* **Dependencies:** `boto3` (built into Lambda runtime)
* **Pattern:** Sequential pipeline with early-exit on failure

### 5.1 Component Map

| Layer | Implementation | Lib |
|:------|:---------------|:----|
| **Orchestrator** | `lambda_function.lambda_handler` | Pure Python |
| **Guardrails** | `src/guardrails/engine.py` | Pure Python |
| **Semantic** | `src/guardrails/semantic.py` | `boto3.invoke_model` |
| **Storage** | `lambda_function.save_state` | `boto3.dynamodb` |
| **LLM** | `lambda_function.generate` | `boto3.invoke_model` |

## 6. Interface Specification

### 6.1 Data Structures

**Input Payload:**
```json
{
  "text": "Selected text",
  "url": "https://example.com",
  "domContext": "Surrounding paragraph...",
  "userId": "uuid"
}
```

**DynamoDB Schema (Unchanged):**
* **PK:** `thread_id` (URL hash or User ID)
* **SK:** `checkpoint_id` (Timestamp)
* **Attributes:** `input`, `response`, `safety_score`

### 6.2 Function Signatures

```python
def lambda_handler(event: dict, context: Any) -> dict:
    """Main entry point. Orchestrates validation → guards → persist → generate."""
    ...

def validate_input(event: dict) -> tuple[bool, str | None]:
    """Validate event payload. Returns (is_valid, error_message)."""
    ...

def save_state(thread_id: str, data: dict) -> None:
    """Persist context to DynamoDB."""
    ...

def generate(prompt: str) -> Iterator[str]:
    """Stream response chunks from Bedrock."""
    ...
```

### 6.3 Logic Flow (Pseudocode)

```
1. Receive event from API Gateway / Function URL
2. Validate input (exists, type, length)
   - IF invalid → return 400
3. Run Denylist check
   - IF blocked → return 403 with reason
4. Run Semantic check (Haiku)
   - IF blocked → return 403 with reason
5. Transform (if noarchive flag, summarize)
6. Persist to DynamoDB
7. Generate response via Bedrock
8. Stream chunks back to client
```

## 7. Security Considerations

| Concern | Mitigation | Status |
|---------|------------|--------|
| Missing input fields | Explicit validation with 400 response | TODO |
| Payload size attack | Truncate to 20k chars | TODO |
| Injection via text | Guardrails + prompt sanitization | TODO |
| Fail-open on exception | Global try/except returns error, never generates | TODO |
| CloudWatch log leakage | Never log raw `text` field | TODO |
| IAM over-privilege | Least privilege role (Bedrock, DynamoDB only) | TODO |
| Malformed Unicode/null bytes | Validate string encoding | TODO |

**Fail Mode:** Fail Closed - Any unhandled exception returns error response, never proceeds to LLM generation.

### 7.1 Input Validation

```python
def validate_input(event: dict) -> tuple[bool, str | None]:
    # Existence
    if 'text' not in event:
        return False, "Missing required field: text"

    # Type
    if not isinstance(event['text'], str):
        return False, "Field 'text' must be string"

    # Length (prevent payload attacks)
    if len(event['text']) > 20_000:
        event['text'] = event['text'][:20_000]  # Truncate silently

    # Encoding (reject malformed)
    try:
        event['text'].encode('utf-8')
    except UnicodeError:
        return False, "Invalid text encoding"

    return True, None
```

### 7.2 Global Exception Handler

```python
def lambda_handler(event, context):
    try:
        # 1. Validation
        valid, error = validate_input(event)
        if not valid:
            return {"statusCode": 400, "body": json.dumps({"error": error})}

        # 2. Guardrails
        result = guardrails.check(event['text'])
        if not result.is_safe:
            return {"statusCode": 403, "body": json.dumps({"blocked": result.reason})}

        # 3. Transform, Persist, Generate...

    except ClientError as e:
        # AWS SDK errors (IAM, throttling, etc.)
        print(f"AWS Error: {e.response['Error']['Code']}")
        return {"statusCode": 500, "body": json.dumps({"error": "Service error"})}

    except Exception as e:
        # Catch-all: NEVER proceed to generation
        print(f"CRITICAL: Unhandled exception: {type(e).__name__}")
        return {"statusCode": 500, "body": json.dumps({"error": "Internal error"})}
```

## 8. Performance Considerations

| Metric | Budget | Approach |
|--------|--------|----------|
| Cold Start | < 1s (target: 500ms) | Remove LangChain (~200MB), use built-in boto3 |
| Warm Latency | < 2s total | Sequential pipeline, no graph overhead |
| Memory | 256MB | Minimal deps, stream responses |
| Bedrock Calls | 2 max | 1 Haiku (semantic) + 1 generation |

**Bottlenecks:**
- Bedrock invoke latency (~500ms-2s per call)
- DynamoDB write (~50ms)
- Cold start dominated by import time (target: minimal imports)

**Key Metric:** Time-to-First-Token (TTFT) for streaming - user perception of speed.

## 9. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| boto3 API changes | Med | Low | Pin boto3 version in Lambda layer if needed |
| Bedrock throttling | High | Med | Implement exponential backoff, alert on 429s |
| DynamoDB capacity | Med | Low | On-demand pricing, monitor consumed capacity |
| Loss of LangGraph features | Low | N/A | Current flow is linear; no cycles needed |
| Regression in guardrails | High | Med | Comprehensive test coverage before deploy |

## 10. Verification & Testing

*Ref: [0005-testing-strategy-and-protocols.md](0005-testing-strategy-and-protocols.md)*

### 10.1 Test Scenarios

| ID | Scenario | Type | Input | Expected Output | Pass Criteria |
|----|----------|------|-------|-----------------|---------------|
| 010 | Valid input, safe text | Auto | `{"text": "apple"}` | 200 + response | Response contains explanation |
| 020 | Valid input, blocked text | Auto | `{"text": "Nazi"}` | 403 Blocked | `blocked` in response body |
| 030 | Missing text field | Auto | `{}` | 400 Bad Request | Error mentions "text" |
| 040 | Wrong type for text | Auto | `{"text": 123}` | 400 Bad Request | Error mentions "string" |
| 050 | Oversized payload | Auto | `{"text": "a"*25000}` | 200 (truncated) | Processes first 20k chars |
| 060 | Malformed Unicode | Auto | `{"text": "\xff\xfe"}` | 400 Bad Request | Error mentions "encoding" |
| 070 | boto3 exception | Auto | Mock raise | 500 Error | No LLM output in response |
| 080 | DynamoDB failure | Auto | Mock raise | 500 Error | Logged, no LLM bypass |
| 090 | Bedrock throttle | Auto | Mock 429 | 500 Error | Graceful degradation |
| 100 | Empty string | Auto | `{"text": ""}` | 400 Bad Request | Error mentions "empty" |
| 110 | Streaming works | Manual | Valid input | Chunked SSE | First chunk < 2s |

### 10.2 Test Modules (from 0005)

* **Unit Tests:** `poetry run pytest tests/test_lambda_handler.py -v`
* **Semantic (Module B):** Yes - test Haiku integration with mocks
* **End-to-End (Module C):** Yes - deploy to dev and invoke

### 10.3 Manual Smoke Test

1. Deploy Lambda to dev environment
2. Send valid request: `curl -X POST $URL -d '{"text":"apple"}'`
3. Verify streaming response received
4. Send blocked request: `curl -X POST $URL -d '{"text":"Nazi"}'`
5. Verify 403 response with "blocked" reason
6. Check CloudWatch logs do NOT contain raw text

## 11. Definition of Done

### Code
- [ ] `lambda_function.py` refactored as orchestrator
- [ ] `agent.py` deleted
- [ ] `checkpointer.py` deleted
- [ ] LangChain removed from `pyproject.toml`
- [ ] All imports use only `boto3` and stdlib
- [ ] Code comments reference this LLD

### Tests
- [ ] All scenarios in 10.1 pass
- [ ] Test coverage > 80% for lambda_function.py
- [ ] No regressions in existing guardrail tests

### Documentation
- [ ] This LLD updated with any deviations
- [ ] ADR 0211 status → Implemented
- [ ] Implementation Report (0103) completed

### Deployment
- [ ] Lambda deployed to dev
- [ ] Cold start measured < 1s
- [ ] Manual smoke test passed
- [ ] CloudWatch logs verified (no raw text)

### Review
- [ ] Code review completed
- [ ] User approval before closing issue
