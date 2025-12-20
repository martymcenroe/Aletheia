# 0005 - Testing Strategy & Protocols

## 1. Philosophy: "Trust but Verify"

Aletheia operates in a high-liability domain (AI Safety). Testing is not just about functionality; it is about **auditability** and **data hygiene**.

* **Fail Closed:** If a test cannot verify safety, the feature is broken.
* **Data Minimization:** We do not persist toxic artifacts.
* **Live Verification:** We prefer testing against live infrastructure (Bedrock/DynamoDB) over mocks, given our "Stateful Serverless" architecture.

## 2. The Toolbelt

| Tool | File | Purpose |
| --- | --- | --- |
| **The Inspector** | `tools/log_viewer.py` | Read-only verification of the "Last Mile" (DynamoDB). |
| **The Harvester** | `tools/harvest_test_data.py` | Pulls live telemetry to update regression suites. |
| **The Judge** | `verify_holistic.py` | Probabilistic grading of the LLM against Ground Truth. |
| **The Unit** | `pytest` | Deterministic logic checks (Regex, JSON parsing). |

## 3. Test Modules (The Building Blocks)

These modules are the atomic units of verification.

### Module A: Local Logic (L1/L2)

**Goal:** Verify deterministic guardrails (Regex, Hash Lists) work without network calls.

* **Input:** Known patterns (e.g., Email addresses, Blocked Terms).
* **Success:** Immediate rejection.
* **Tool:** `poetry run pytest tests/test_guardrails.py`

### Module B: Semantic Intelligence (L3)

**Goal:** Verify the LLM correctly classifies nuances (e.g., "Kill the process" vs. "Kill the person").

* **Input:** `test_ground_truth.json`.
* **Success:** >90% alignment with human labels.
* **Tool:** `poetry run python verify_holistic.py`

### Module C: End-to-End Trace

**Goal:** Verify the full pipeline: Extension -> Lambda -> Bedrock -> DynamoDB.

* **Action:** User inputs a unique "Trace Token" (e.g., `AletheiaTest_<TIMESTAMP>`) in the browser.
* **Verification:** Use **The Inspector** to find that specific token in the logs.
* **Tool:** `poetry run python tools/log_viewer.py --tail 1`

### Module D: The "Toxic Waste" Check (Hygiene)

**Goal:** Verify that rejected content is **NOT** persisted in the database.

* **Action:** Inject a known "Hate" term (defined in `test_ground_truth.json`).
* **Verification:** Run **The Inspector**.
* **Pass:** The entry is either missing OR recorded as `[REDACTED]`.
* **Fail:** The hate term is visible in the logs.



## 4. Operational Sequences (SOPs)

Combine modules to create training scripts or release checklists.

### Sequence 1: The "Daily Standup" (Smoke Test)

*Target: Rapid confidence.*

1. **Run Module A** (Unit Tests): `poetry run pytest`
2. **Run Module C** (Trace): Send "Hello World", verify in Inspector.

### Sequence 2: The "Safety Release" (Regression)

*Target: Zero regression on safety.*

1. **Run Module B** (Holistic): Ensure AI hasn't drifted.
2. **Run Module D** (Toxic Waste): Confirm privacy barriers are holding.

### Sequence 3: The "Ground Truth" Calibration

*Target: Improving the AI.*

1. **Run Inspector:** Identify new/novel user queries.
2. **Run Harvester:** Import interesting edge cases.
3. **Manual Labeling:** Update `test_ground_truth.json`.
4. **Run Module B:** Verify the new baseline.