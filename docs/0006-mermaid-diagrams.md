# 0006 - Mermaid Diagram Standards

## 1. Philosophy
Visual documentation is code. It must be maintained, versioned, and readable. We use **Mermaid.js** because it renders natively in GitHub and requires no binary assets.

## 2. Standard Diagram Types

### 2.1 Flowcharts (Logic & Process)
* **Type:** `flowchart TD` (Top-Down).
* **Use Case:** User flows, decision logic, system sequences.
* **Constraint:** Do not use `stateDiagram-v2` for complex logic; it lacks layout control and often results in "routing spaghetti."

### 2.2 Sequence Diagrams (Interaction)
* **Type:** `sequenceDiagram`.
* **Use Case:** API calls, message passing between agents.

## 3. The "Router Pattern"
To keep flowcharts clean, avoid connecting every node to every other node directly. Use a central "Router" decision diamond.

**Bad (Spaghetti):**
* Node A -> Node B
* Node A -> Node C
* Node B -> Node A
* Node C -> Node A

**Good (Router):**
* Start -> Router{?}
* Router -->|Condition 1| A[Process A]
* Router -->|Condition 2| B[Process B]
* A --> Router
* B --> Router

## 4. Style & Syntax Guidelines
1.  **Orientation:** Always use `TD` (Top-Down) for vertical scrolling readability.
2.  **Shapes:**
    * `[Rect]`: Standard Process
    * `{Diamond}`: Decision/Router
    * `((Circle))`: Start/Stop
    * `[[Subroutine]]`: Sub-process
3.  **Labels:** Keep arrow labels short.

## 5. Example Snippet

```mermaid
flowchart TD
    Start((Start)) --> Router{Routing Logic}
    
    Router -->|User Input| Process[Process Data]
    Router -->|Error| Handle[Error Handler]
    
    Process --> Router
    Handle --> Stop((End))