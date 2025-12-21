# 0102 - Template: Feature Low-Level Design (LLD)

## Usage
Copy this template to `docs/1{IssueID}-{short-description}.md` when starting implementation of a feature.

---

## Template

```markdown
# 1{IssueID} - Feature: {Title}

## 1. Context & Goal
* **Issue:** #{IssueID}
* **Objective:** {One sentence}
* **Status:** Draft | In Progress | Complete

## 2. Requirements
{What must be true when this is done - copy from issue or expand}

## 3. Technical Approach
* **Module:** `src/...` or `extension/...`
* **Dependencies:** {packages, APIs, Chrome permissions}
* **Performance Budget:** {if applicable}

## 4. Implementation Details

### 4.1 Data Structures
{Key data structures, state shape, storage schema}

### 4.2 Function Signatures
{Main functions/methods with parameters and return types}

### 4.3 Logic Flow
{Pseudocode or step-by-step algorithm}

## 5. Security Considerations
{If applicable: permissions rationale, data handling, sandboxing}

## 6. Verification & Testing
*Ref: [0005-testing-strategy-and-protocols.md](0005-testing-strategy-and-protocols.md)*

### 6.1 Test Modules (Select relevant from 0005)
* **Module A (Unit):** `poetry run pytest tests/test_{module}.py -v`
* **Module B (Semantic):** {Applicable? Yes/No}
* **Module C (Trace):** {Applicable? Yes/No}

### 6.2 Test Scenarios
| Scenario | Input | Expected Output | Pass Criteria |
|:---------|:------|:----------------|:--------------|
| {name} | {input} | {output} | {how to verify} |

### 6.3 Manual Smoke Test
1. {Step 1}
2. {Step 2}
3. {Expected result}

### 6.4 How to Force Error States
{Instructions for testing error handling - e.g., DevTools offline mode}

## 7. Definition of Done
- [ ] Code complete and linted
- [ ] Unit tests pass
- [ ] Integration test pass (if applicable)
- [ ] Doc updated with actual test results
- [ ] `0003-file-inventory.md` updated
- [ ] PR merged to main
```

---

## Tips for Good LLDs

1. **Section 4 is the meat:** This is where the AI coder will look for implementation guidance.
2. **Be specific:** "Use chrome.storage.local" not "persist data somewhere."
3. **Include error handling:** What happens when things fail?
4. **Test scenarios:** Write these BEFORE coding. They clarify requirements.
5. **Update when done:** Change Status to Complete, check off Definition of Done.
