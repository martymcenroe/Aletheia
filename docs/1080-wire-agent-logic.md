# 1080 - Fix: Wire Agent to Defense Funnel

## 1. Context & Goal
* **Issue:** #80
* **Objective:** Enforce the "Defense in Depth" architecture by wiring the `guardrails` and `summarizer` modules into the `agent.py` LangGraph.
* **Status:** Draft
* **Strategy:** "Operation Glass House" (Ref: `docs/0007`).
    * **Guardrails:** Full Implementation (L1/L2/L3).
    * **Summarizer:** **Pass-Through (No-Op)** for this issue. (Logic implementation deferred to Issue #85).

## 2. Requirements
1. **Fail Fast:** If Guardrails fail, the chain must stop immediately. Agent NOT invoked.
2. **Architecture:** `Start -> Guardrails -> Summarizer -> Agent -> End`.
3. **State Management:** The graph state must track `safety_status` and `signals`.

## 3. Diagram

```mermaid
graph TD
    START --> GuardrailsNode
    GuardrailsNode -->|Safe?| CHECK_SAFETY
    
    CHECK_SAFETY -->|No (Block)| END
    CHECK_SAFETY -->|Yes| SummarizerNode
    
    SummarizerNode --> AgentNode
    AgentNode --> END

    subgraph "The Gauntlet"
    GuardrailsNode[Run L1, L2, L3]
    SummarizerNode[Summarizer (Pass-Through)]
    end
    
    subgraph "The Brain"
    AgentNode[Bedrock Agent]
    end

```

## 4. Technical Approach

* **Module:** `agent.py`
* **Dependencies:** `src.guardrails.engine`
* **Graph Changes:**
* **New Nodes:** `guardrails_node`, `summarizer_node`.
* **New Edge:** Conditional edge `should_continue`.



## 5. Implementation Details

### 5.1 State Schema Update

```python
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    thread_id: str
    raw_selection: str          # Input text
    signals: dict               # {noarchive: bool, ...}
    guardrail_result: dict      # {passed: bool, reason: str}

```

### 5.2 Node Logic

**A. `guardrails_node(state)` (Real Logic)**

* Calls `guardrails_engine.validate(state['raw_selection'])`.
* Returns `{"guardrail_result": result}`.
* If blocked, appends a system message: `"BLOCKED: {reason}"`.

**B. `summarizer_node(state)` (No-Op / Pass-Through)**

* **Current Behavior:** Returns state as-is.
* **Future Behavior (Issue #85):** Will check `state['signals']` and potentially summarize.

```python
def summarizer_node(state):
    # TODO (Issue #85): Implement 'noarchive' summarization logic here.
    # For now, we respect the "Glass House" default: Transparency.
    return {} 

```

**C. `agent_node(state)**`

* Receives the messages (which might contain the original raw text OR a summary from the future node).
* Invokes Bedrock.

## 6. Verification & Testing

### 6.1 Test Modules

* **Module:** `tests/test_agent_wiring.py`

### 6.2 Test Scenarios

| Scenario | Input | Expected Output | Pass Criteria |
| --- | --- | --- | --- |
| **Guardrail Block** | "Valid Input" | Guardrail Mock = `False` | Graph stops at GuardrailsNode. Agent NOT called. |
| **Pass Through** | "Valid Input" | Guardrail Mock = `True` | Graph traverses `Summarizer` and hits `Agent`. |

**Note:** "Summarization Logic" tests are **Out of Scope** for this issue (Defer to #85).

## 7. Definition of Done

* [ ] `agent.py` imports `guardrails`
* [ ] Graph structure matches the Mermaid diagram
* [ ] Conditional edge `should_continue` functions correctly
* [ ] `summarizer_node` exists (even if empty) to reserve the architectural slot
* [ ] Unit tests pass for Blocking and Passing flows
