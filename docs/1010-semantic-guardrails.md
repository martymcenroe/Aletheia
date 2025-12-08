# [1010] Feature: Semantic Maturity Guardrails

## 1. Context & Goal
* **Issue:** #10
* **Objective:** Prevent "Archaic," "Provocative," or "Hate" speech from reaching the main agent logic using a semantic pre-filter.
* **Why:** Regex is insufficient for context-dependent phrases (e.g., "size matters").

## 2. Taxonomy
1.  **Archaic:** Outdated/Pejorative terms (e.g., "consumptive").
2.  **Provocative:** Sexual double entendres/Locker room talk.
3.  **Hate:** Slurs and discriminatory language.

## 3. Technical Approach
* **Module:** `src/guardrails/semantic.py` (New LLM-based engine).
* **Model:** Claude 3 Haiku (Fast/Cheap) or Bedrock Guard.
* **Integration:**
    * **Node:** `guardrail_node` inserted at the start of the graph.
    * **Edge:** Conditional check. If `UNSAFE` -> End/Error. If `SAFE` -> Proceed to Agent.

## 4. Verification
* **Unit Test:** Mock the LLM response to ensure the parsing logic handles `SAFE` vs `UNSAFE` correctly.
* **Manual Test:** Feed known archaic terms (e.g., from `test_holistic_data.json`) and verify rejection.
