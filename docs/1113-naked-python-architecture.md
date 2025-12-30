# 1113 - Feature: Naked Python Agent Architecture

**Status:** In-Progress
**Feature:** Issue #113
**Supersedes:** Issue #1080

## 1. Overview
This specification defines the "Naked Python" backend for Aletheia. It replaces the LangGraph-based `agent.py` with a lightweight, sequential orchestrator in `lambda_function.py`.

## 2. Architecture: The Defense Funnel
The architecture is a single-pass pipeline. Each layer must pass before the next begins.

### 2.1 The Pipeline (Sequential)
1.  **Input:** API Gateway / Function URL Event.
2.  **Layer 1 (Denylist):** Deterministic check.
3.  **Layer 2 (Semantic):** AI-based check (Haiku).
4.  **Layer 3 (Transform):** Data normalization (e.g., noarchive).
5.  **Persistence:** Save context to DynamoDB.
6.  **Generation:** Invoke Bedrock Agent/Model.
7.  **Output:** Return/Stream response.

### 2.2 Component Map

| Layer | Implementation | Lib |
| :--- | :--- | :--- |
| **Orchestrator** | `lambda_function.lambda_handler` | Pure Python |
| **Guardrails** | `src/guardrails/engine.py` | Pure Python |
| **Semantic** | `src/guardrails/semantic.py` | `boto3.invoke_model` |
| **Storage** | `lambda_function.save_state` | `boto3.dynamodb` |
| **LLM** | `lambda_function.generate` | `boto3.invoke_model` |

## 3. Data Structures

### 3.1 Input Payload
```json
{
  "text": "Selected text",
  "url": "[https://example.com](https://example.com)",
  "domContext": "Surrounding paragraph...",
  "userId": "uuid"
}

```

### 3.2 DynamoDB Schema (Unchanged)

* **PK:** `thread_id` (URL hash or User ID)
* **SK:** `checkpoint_id` (Timestamp)
* **Attributes:** `input`, `response`, `safety_score`

### 3.3 Input Validation (Security Audit)

The Lambda must explicitly validate inputs before processing:

* **Existence:** `event['text']` must exist.
* **Type:** `event['text']` must be a `str`.
* **Length:** Truncate to reasonable limit (e.g., 20k chars) to prevent payload attacks.
* **Action:** If validation fails, return `400 Bad Request` immediately.

## 4. Error Handling (Fail Closed)

**Constraint:** The system must NEVER fall through to the LLM generation if a safety check fails or errors.

### 4.1 The "Global Try/Except"

The `lambda_handler` must wrap the entire guardrail/logic flow in a broad `try/except` block.

```python
try:
    # 1. Validation
    # 2. Guardrails
    if not is_safe: return BLOCKED
    # 3. Logic
except AccessDeniedException:
    # IAM Role misconfiguration
    return {"status": "error", "message": "System Configuration Error"}
except ReadTimeout:
    # Bedrock/Dynamo latency
    return {"status": "error", "message": "Service Timeout"}
except Exception as e:
    # Catch-all to prevent Fail Open
    print(f"CRITICAL: Unhandled failure: {e}")
    return {"status": "error", "message": "Safety check failed"}

```

## 5. Verification Plan

1. **Unit Test:** `pytest` mock of `boto3` to verify logic flow.
2. **Security Test:** Send malformed JSON (missing `text`) -> Expect 400.
3. **Security Test:** Simulate `boto3` exception -> Expect 500/Blocked (NOT generated text).
4. **Manual Test:** Deploy and invoke with "Nazi" (Block) and "Apple" (Allow).
