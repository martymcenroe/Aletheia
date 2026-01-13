# 0001c - Runtime View

Key flows illustrated as sequence diagrams.

## Happy Path: Text Analysis

```mermaid
sequenceDiagram
    participant U as User
    participant CS as Content Script
    participant SW as Service Worker
    participant L as Lambda
    participant DF as Defense Funnel
    participant E as Etymologist
    participant B as Bedrock

    U->>CS: Select text
    CS->>CS: Check allowlist
    CS->>SW: analyzeText(word, context)
    SW->>L: POST /analyze

    L->>DF: Selection Check
    DF-->>L: PASS
    L->>DF: Denylist Check
    DF-->>L: PASS
    L->>DF: Semantic Check
    DF->>B: classify(word)
    B-->>DF: {safe: true}
    DF-->>L: PASS

    L->>E: analyze(word, context)
    E->>B: invoke_model(prompt)
    B-->>E: JSON response
    E-->>L: {signal, gem, context}

    L-->>SW: SSE stream
    SW-->>CS: response
    CS->>CS: Render overlay
```

## Blocked by Denylist

```mermaid
sequenceDiagram
    participant U as User
    participant CS as Content Script
    participant SW as Service Worker
    participant L as Lambda
    participant DF as Defense Funnel

    U->>CS: Select blocked term
    CS->>SW: analyzeText(word)
    SW->>L: POST /analyze

    L->>DF: Selection Check
    DF-->>L: PASS
    L->>DF: Denylist Check
    Note over DF: Hash match found
    DF-->>L: BLOCK (denylist)

    L-->>SW: 200 {blocked: true, reason: "denylist"}
    SW-->>CS: blocked response
    CS->>CS: Show blocked indicator
```

## Rate Limited

```mermaid
sequenceDiagram
    participant U as User
    participant CS as Content Script
    participant SW as Service Worker
    participant AG as API Gateway
    participant WAF as AWS WAF

    U->>CS: Select text (rapid requests)
    CS->>SW: analyzeText(word)
    SW->>AG: POST /analyze

    AG->>WAF: Check rate limit
    Note over WAF: Rate exceeded
    WAF-->>AG: 429 Too Many Requests
    AG-->>SW: 429
    SW-->>CS: rate limited
    CS->>CS: Show rate limit message
```

## Cold Start

```mermaid
sequenceDiagram
    participant AG as API Gateway
    participant L as Lambda Runtime
    participant H as Handler
    participant D as Denylist

    AG->>L: Invoke (cold)
    Note over L: Initialize runtime (~200ms)
    L->>H: Load handler
    H->>D: Load denylist.json
    Note over D: 803 terms into memory
    D-->>H: Ready
    H-->>L: Handler ready
    Note over L: Total cold start ~800ms
    L->>H: Execute request
```

## State Lifecycle (Hydration/Dehydration)

```mermaid
sequenceDiagram
    participant L as Lambda
    participant DDB as DynamoDB
    participant E as Etymologist

    Note over L,DDB: HYDRATION
    L->>DDB: GetItem(thread_id)
    DDB-->>L: Previous state (or empty)

    Note over L,E: EXECUTION
    L->>E: Process with context
    E-->>L: New response

    Note over L,DDB: DEHYDRATION
    L->>DDB: PutItem(thread_id, state, ttl)
    Note over DDB: TTL = now + 24h
    DDB-->>L: OK
```

---

[← Container View](0001b-container-view.md) | [Back to Architecture](0001-architecture.md) | [ADR Digest →](0001d-adr-digest.md)
