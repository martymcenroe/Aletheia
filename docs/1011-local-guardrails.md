# [1011] Feature: Local Guardrails Test Harness

## 1\. Context & Goal

  * **Issue:** \#11
  * **Objective:** Create a lightweight "Guardrails Engine" to validate user inputs *before* they are sent to the LLM. This saves cost and latency by rejecting garbage inputs locally.
  * **Inputs:** Raw JSON records (from `test_holistic_data.json`).
  * **Outputs:** A `GuardrailResult` object (Pass/Fail + Reason).

## 2\. Technical Approach

We will implement a `GuardrailsEngine` class with a chain of simple validators.

### 2.1. The Check Logic

1.  **Length Check:** Reject if word \< 2 chars or \> 50 chars.
2.  **Entropy Check:** Reject if the input is repetitive (e.g., "aaaaa").
3.  **Allow-list (Optional):** Check against a basic dictionary of valid terms (future scope).

### 2.2. File Structure

  * Create `src/guardrails/` (New module).
  * `src/guardrails/engine.py`: The main logic.
  * `src/guardrails/validators.py`: Individual check functions.
  * `tests/test_guardrails.py`: Unit tests.

## 3\. Detailed Implementation

### Data Structures

```python
@dataclass
class GuardrailResult:
    is_valid: bool
    reason: str  # e.g., "Input too short", "Valid"
    metadata: dict = None
```

### Function Signatures

```python
def validate_input(input_text: str) -> GuardrailResult:
    """
    Runs all active validators against the input.
    Returns the first failure, or success if all pass.
    """
    pass
```

## 4\. Verification Plan

1.  **Unit Tests:** Run `poetry run pytest`.
2.  **Integration:** Create a script `run_guardrails.py` that loads `test_holistic_data.json` and prints the Pass/Fail status for each harvested record.
      * *Expected Output:* The "enthalpy" record should PASS.