# 🏗️ Aletheia: Architecture & Design Decisions

## 1. The "Stateful Serverless" Pattern
* **Challenge:** AWS Lambda is stateless. Complex GenAI agents require persistent memory (multi-turn reasoning) which usually requires expensive always-on containers.
* **Architecture:** I implemented a **"Hydration/Dehydration"** cycle:
    * **Load:** Lambda retrieves the latest state snapshot from DynamoDB (Partition Key: `thread_id`).
    * **Execute:** LangGraph processes the state.
    * **Persist:** The updated state is written back to DynamoDB.
* **Benefit:** This architecture allows for **infinite-scale agent memory** with **zero idle cost**.

## 2. Why LangGraph? (vs. Linear Chains)
* **Design Choice:** Linear chains (`Seq -> Seq`) are brittle and cannot handle loops (e.g., "The tool failed, try again").
* **Solution:** I chose **LangGraph** to model the application as a cyclic graph (`Agent -> Tool -> Agent`).
* **Future Proofing:** This graph structure is the required foundation for future RAG (Retrieval Augmented Generation) integration, allowing the agent to dynamically decide when to fetch external data.

## 3. Streaming UX (Server-Sent Events)
* **UX Constraint:** LLM inference is slow. A 5-second pause breaks the user flow.
* **Implementation:** I utilized `@awslambda.streamify_response`.
* **Outcome:** Tokens are piped to the client via **Server-Sent Events (SSE)** as they are generated. This reduces the perceived latency (Time-To-First-Byte) from ~4s to <500ms.

## 4. Guardrail Performance Budget
To maintain the "Stateful Serverless" responsiveness, we enforce a strict latency budget for the 3-layer defense funnel:

| Layer | Type | Mechanism | Budget (Max) | Status |
| :--- | :--- | :--- | :--- | :--- |
| **L1** | Syntactic | Regex/Length (CPU) | < 1ms | Active |
| **L2** | Deterministic | Hash Lookup (Memory) | < 5ms | Planned (Ref #1012) |
| **L3** | Semantic | LLM Inference (Network) | ~800ms | Active (Ref #10) |

**Constraint:** L1 and L2 (The "Pre-Flight" checks) must complete in **< 50ms** combined to avoid perceptible drag before the L3 call.
