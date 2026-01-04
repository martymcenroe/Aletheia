# Aletheia: Architecture & Design Decisions

## 1. The "Stateful Serverless" Pattern
* **Challenge:** AWS Lambda is stateless. Complex GenAI agents require persistent memory.
* **Architecture:** **"Hydration/Dehydration" Cycle**.
    * **Load:** Retrieve state from DynamoDB (`thread_id`).
    * **Execute:** Sequential pipeline processes state (Naked Python).
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
            L1[Selection Check]
            L2[Denylist]
            L3[Semantic]
            Comp[Transform]
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
    participant SelectionCheck as Selection Check
    participant Denylist as Denylist
    participant Semantic as Semantic
    participant Transform as Transform
    participant Agent as Agent (DynamoDB)

    Note over User, Agent: The Request Pipeline

    User->>SelectionCheck: 1. Input (Word)

    alt is Garbage?
        SelectionCheck--xUser: BLOCK (Invalid Format)
    else is Valid
        SelectionCheck->>Denylist: 2. Check Index
    end

    alt is Listed?
        Denylist--xUser: BLOCK (Liability Shield)
        Note right of Denylist: Store Metadata Only<br/>(Index, URL, Time)
    else is Clean
        Denylist->>Semantic: 3. Check Context (Raw)
    end

    alt is Unsafe?
        Semantic--xUser: BLOCK (Provocative/Archaic)
    else is Safe
        Semantic->>Transform: 4. Verification
    end

    rect rgb(240, 240, 240)
    Note over Transform: Summarize if noarchive
    Transform-->>Transform: Summarize & Vectorize
    end

    Transform->>Agent: 5. Hydrate & Execute
    Agent-->>User: Streaming Response

```

### 2.1 Layer Definitions

| Layer | Type | Mechanism | Responsibility | Storage Logic |
| --- | --- | --- | --- | --- |
| **Selection Check** | Syntactic | Regex (CPU) | Block gibberish, non-words, scripts. | None (Discard). |
| **Denylist** | Deterministic | Hash Lookup | Block known hate speech (Wikipedia). | **Metadata Only:** Store Index ID, Timestamp, URL. *Never store the word.* |
| **Semantic** | Semantic | LLM (Haiku) | Block provocative/archaic nuance. | Log Rejection Category + Score. |
| **Transform** | Legal | LLM (Summary) | Summarize if noarchive flag set. | Summary only (raw text discarded). |

## 3. Streaming UX (Server-Sent Events)

* **Implementation:** `@awslambda.streamify_response`.
* **Outcome:** Time-To-First-Byte < 500ms.

## 4. Why Naked Python? (ADR 0211)

* **Simplicity:** Sequential pipeline with direct boto3 calls — no framework overhead.
* **Transparency:** Each layer is a plain function, easily debugged and tested.
* **Cost:** Removed LangGraph/LangChain dependencies (see `docs/0205-ADR-langgraph-orchestration.md` for historical context).

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
