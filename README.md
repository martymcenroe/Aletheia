# Aletheia: Stateful AI Agent on AWS Serverless

A production-grade backend for a Chrome Extension that delivers context-aware text analysis. It solves the "Stateless Lambda" problem by using **LangGraph** with a custom **DynamoDB Checkpointer** to persist agent state across execution turns.

## 🏗️ Architecture

The system is designed as a **Stateful Graph** running on **Stateless Compute**.

* **Runtime:** AWS Lambda (Python 3.12) with Response Streaming (SSE).
* **Orchestration:** LangGraph (StateGraph).
* **Persistence:** Amazon DynamoDB (Thread-level check-pointing).
* **AI Model:** Amazon Bedrock (Claude 3.5 Sonnet).

### The "Stateful Serverless" Pattern
Standard Lambdas forget context after execution. Aletheia overrides this:
1.  **Load:** Lambda initializes -> fetches `thread_id` -> loads State Snapshot from DynamoDB.
2.  **Reason:** Agent processes input -> determines next step (LLM or Tool).
3.  **Persist:** Agent saves new State Snapshot -> DynamoDB.
4.  **Stream:** Token-by-token response is streamed to the client via `awslambda.streamify_response`.

## 🛠️ Technology Stack

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Compute** | AWS Lambda | Zero-scale cost, event-driven. |
| **Database** | DynamoDB | Low-latency state/checkpoint storage. |
| **Agent Framework** | LangGraph | Cyclic graph flows (Looping capability). |
| **LLM** | Claude 3.5 Sonnet | High reasoning capability for linguistic nuances. |
| **Interface** | SSE (Server-Sent Events) | Real-time UX for the browser extension. |

## 🚀 Key Features

* **Streaming Response:** Uses `awslambda.streamify_response` to reduce Time-To-First-Byte (TTFB).
* **Persistence Layer:** Custom `DynamoDBSaver` class implementing LangGraph's `BaseCheckpointSaver`.
* **Tooling:** Extensible tool node structure (currently implements `lookup_definition`).

## 📂 Repository Structure

* `lambda_function.py`: Entry point. Handles SSE streaming and async execution loop.
* `agent.py`: Defines the `StateGraph`, Nodes, and Bedrock binding.
* `checkpointer.py`: Custom infrastructure adapter for DynamoDB persistence.

## 🔮 Roadmap

* **RAG Integration:** Connect to Vector Store for long-term document recall.
* **Observability:** Implement AWS X-Ray/LangSmith tracing.
* **Testing:** Add unit tests for graph transitions.
