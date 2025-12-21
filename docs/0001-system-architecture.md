# Aletheia: Architecture & Design Decisions

## 1. The "Stateful Serverless" Pattern
* **Challenge:** AWS Lambda is stateless. Complex GenAI agents require persistent memory.
* **Architecture:** **"Hydration/Dehydration" Cycle**.
    * **Load:** Retrieve state from DynamoDB (`thread_id`).
    * **Execute:** LangGraph processes state.
    * **Persist:** Write updated state back to DynamoDB.
* **Benefit:** Infinite-scale agent memory with zero idle cost.

## 2. The Defense Funnel (Fail Fast)
We enforce a strict, ordered defense pipeline to minimize cost and liability.

### Diagram: The Gauntlet
```mermaid
sequenceDiagram
    participant User
    participant L1_Syntax as L1: Syntax (Regex)
    participant L2_Hate as L2: Hate (Denylist)
    participant L3_Semantic as L3: Semantic (AI)
    participant Compliance as Compliance (Future)
    participant Agent as Agent (DynamoDB)

    Note over User, Agent: The Request Pipeline

    User->>L1_Syntax: 1. Input (Word)
    
    alt is Garbage?
        L1_Syntax--xUser: BLOCK (Invalid Format)
    else is Valid
        L1_Syntax->>L2_Hate: 2. Check Index
    end

    alt is Listed?
        L2_Hate--xUser: BLOCK (Liability Shield)
        Note right of L2_Hate: Store Metadata Only<br/>(Index, URL, Time)
    else is Clean
        L2_Hate->>L3_Semantic: 3. Check Context (Raw)
    end

    alt is Unsafe?
        L3_Semantic--xUser: BLOCK (Provocative/Archaic)
    else is Safe
        L3_Semantic->>Compliance: 4. Verification
    end

    rect rgb(240, 240, 240)
    Note over Compliance: DEFERRED (Copyright Engine)
    Compliance-->>Compliance: Summarize & Vectorize
    end

    Compliance->>Agent: 5. Hydrate & Execute
    Agent-->>User: Streaming Response

```

### 2.1 Layer Definitions

| Layer | Type | Mechanism | Responsibility | Storage Logic |
| --- | --- | --- | --- | --- |
| **L1** | Syntactic | Regex (CPU) | Block gibberish, non-words, scripts. | None (Discard). |
| **L2** | Deterministic | Hash Lookup | Block known hate speech (RSDB). | **Metadata Only:** Store Index ID, Timestamp, URL. *Never store the word.* |
| **L3** | Semantic | LLM (Haiku) | Block provocative/archaic nuance. | Log Rejection Category + Score. |
| **Compliance** | Legal | LLM (Summary) | Strip copyright text before storage. | **Deferred.** (Currently passing Raw Text). |

## 3. Streaming UX (Server-Sent Events)

* **Implementation:** `@awslambda.streamify_response`.
* **Outcome:** Time-To-First-Byte < 500ms.

## 4. Why LangGraph?

* **Resilience:** cyclic graphs (`Agent -> Tool -> Agent`) handle failures better than linear chains.
* **Future Proofing:** Enables dynamic RAG loops.
