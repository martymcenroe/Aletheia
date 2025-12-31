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

### Module A: Local Logic (Selection Check / Denylist)

**Goal:** Verify deterministic guardrails (Regex, Hash Lists) work without network calls.

* **Input:** Known patterns (e.g., Email addresses, Blocked Terms).
* **Success:** Immediate rejection.
* **Tool:** `poetry run pytest tests/test_guardrails.py`

### Module B: Semantic Intelligence

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

## 5. The Willison Protocol

*"Your job is to deliver code you have proven to work."* — [Simon Willison](https://simonwillison.net/2025/Dec/18/your-job-is-to-deliver-code/)

### 5.1 Core Principle

Almost anyone can prompt an LLM to generate a thousand-line patch. **What's valuable is contributing code that is proven to work.** Both human and AI contributors must provide evidence that their code works before submitting for review.

### 5.2 Requirements for Every PR

**Step 1: Manual Testing (Required)**
- Execute the code yourself and observe it working
- Capture proof: terminal output, screenshots, or screen recording
- Test the happy path AND edge cases
- Include proof in PR description or commit message

**Step 2: Automated Testing (Required)**
- Write tests that exercise the change
- Verify tests FAIL if you revert the implementation:
  ```bash
  git stash                    # Revert implementation
  poetry run pytest -v         # Tests should FAIL
  git stash pop                # Restore implementation
  poetry run pytest -v         # Tests should PASS
  ```
- Follow existing test patterns in the codebase

### 5.3 Agent Implementation

For AI agents (Claude, Gemini, etc.), the protocol is the same:

| Task | Agent Capability | Tool |
|------|------------------|------|
| Run Python tests | ✅ Full | `poetry run pytest` |
| Capture terminal output | ✅ Full | Bash output in PR |
| Verify test fails on revert | ✅ Full | `git stash` workflow |
| Browser UI testing | ⚠️ Limited | See Section 5.4 |
| Take screenshots | ⚠️ Limited | See Section 5.4 |

### 5.4 Overcoming Agent Limitations

For work requiring visual/browser testing, these tools can extend agent capabilities:

| Limitation | Tool | How It Helps |
|------------|------|--------------|
| Can't see browser | **Playwright** | Headless Chrome automation with screenshots |
| Can't test extension | **Playwright + Chrome** | Load extension via `--load-extension` flag |
| Can't take screenshots | **Playwright** | `page.screenshot()` saves to file |
| Visual regression | **Playwright** | Built-in visual comparison (`toHaveScreenshot`) |
| Record interactions | **Playwright** | Video recording of test runs |

**Installation:**
```bash
poetry add --group dev playwright
playwright install chromium
```

**Example: Extension Testing with Screenshots**
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # Launch Chrome with extension loaded
    context = p.chromium.launch_persistent_context(
        user_data_dir="/tmp/test-profile",
        headless=False,  # Extensions require headed mode
        args=[
            f"--load-extension={extension_path}",
            f"--disable-extensions-except={extension_path}"
        ]
    )
    page = context.new_page()
    page.goto("https://example.com")
    page.screenshot(path="proof.png")
```

### 5.5 Proof Artifacts

Every PR should include one or more of:

| Artifact | When to Use | Example |
|----------|-------------|---------|
| Terminal output | CLI tools, pytest | Paste in PR description |
| Screenshot | UI changes | Attach `proof.png` |
| Test file | All code changes | `tests/test_feature.py` |
| Benchmark results | Performance claims | Include timing data |

### 5.6 The Accountability Principle

> "A computer can never be held accountable. That's your job as the human in the loop."

The human orchestrator reviews agent-submitted PRs but should NOT be doing the agent's testing work. If an agent submits untested code, reject the PR and instruct the agent to prove it works first.