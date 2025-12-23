# Aletheia: Architecture & Design Decisions

## 1. The "Stateful Serverless" Pattern
* **Challenge:** AWS Lambda is stateless. Complex GenAI agents require persistent memory.
* **Architecture:** **"Hydration/Dehydration" Cycle**.
    * **Load:** Retrieve state from DynamoDB (`thread_id`).
    * **Execute:** LangGraph processes state.
    * **Persist:** Write updated state back to DynamoDB.
* **Benefit:** Infinite-scale agent memory with zero idle cost.

### 1.1 Component Diagram (Physical Layout)
```mermaid
graph TD
    subgraph Client [Chrome Browser]
        Ext[Extension UI]
        CS[Content Script]
    end

    subgraph Cloud [AWS Cloud]
        LB[Lambda Function]
        DDB[(DynamoDB State)]

        subgraph Logic [The Funnel]
            L1[L1: Regex]
            L2[L2: Hate List]
            L3[L3: Semantic AI]
            Comp[Compliance Engine]
        end

        Brain[Bedrock Agent]
    end

    Ext -->|POST /analyze| LB
    LB <-->|Hydrate/Persist| DDB
    LB --> L1
    L1 --> L2
    L2 --> L3
    L3 -->|Safe?| Comp
    Comp -->|Summary| Brain
    Brain -->|SSE Stream| Ext
```

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

## 5. Architecture Decision Records (ADRs)

### ADR-001: Privacy-First Extension Permissions
**Date:** 2025-12-21  
**Status:** Final — Do not revisit.

**Decision:** Aletheia will NEVER request `host_permissions: ["<all_urls>"]`.

**Context:**
Chrome extensions requesting broad host permissions trigger a scary warning: "Read and change all your data on all websites." This erodes user trust and delays Chrome Web Store review.

**Rationale:**
- `activeTab` permission grants temporary per-site access only on user interaction (click, right-click)
- Users explicitly enable sites via the allowlist popup
- No background surveillance of browsing activity

**Tradeoffs Accepted:**
- Toolbar icon remains static (cannot change color/badge per-site without user action)
- Cannot inject scripts proactively — requires user-initiated context menu or popup click
- Badge feedback (setBadgeText/setBadgeBackgroundColor) is the only dynamic toolbar indicator

**Consequences:**
- Issue #77 uses badge text/color instead of icon swapping for feedback
- Allowlist status shown only inside popup UI, never on toolbar icon
- 
### ADR-002: Shadow DOM for Injected UI
**Date:** 2025-12-22  
**Status:** Final

**Decision:** All UI elements injected into host pages MUST use Shadow DOM (`element.attachShadow({mode: 'closed'})`).

**Context:**
Content scripts can inject DOM elements into host pages. Without isolation, host page CSS affects our UI and vice versa, causing "broken UI" reports and unprofessional appearance.

**Rationale:**
- Prevents style "bleed" from host page CSS resets
- Prevents our styles from breaking host page layout
- `mode: 'closed'` prevents host page JavaScript from accessing our shadow tree
- Required for Chrome Web Store approval on complex sites (WSJ, NYT, etc.)

**Consequences:**
- Overlay implementations must create a shadow root before appending styled content
- Slightly more complex code, but required for professional UX across all websites