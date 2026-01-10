# [1010] Feature: Semantic Maturity Guardrails

## 1. Context & Goal
* **Issue:** #10
* **Objective:** Analyze text for "Semantic Maturity" using an LLM to detect Archaic, Provocative, or Neologistic content.
* **Placement:** Semantic layer of the Defense Funnel (after Selection Check and Denylist).

## 2. Taxonomy (Probabilistic)
The engine returns a probability distribution (0.0 - 1.0) for:
1.  **Archaic:** Outdated/Pejorative terms (e.g., "consumptive").
2.  **Provocative:** Sexual double entendres (e.g., "size matters").
3.  **Neologism:** Recent internet slang (< 2 years old).
4.  **None:** Standard language.

*Note: "Hate" is primarily handled by the Denylist (deterministic), but the LLM retains a "Hate" category as a fail-safe.*

## 3. Technical Approach
* **Module:** `src/guardrails/semantic.py`
* **Configuration:** `src/guardrails/resources/taxonomy.json` (Taxonomy & Few-Shot Examples).
* **Model:** Claude 3 Haiku (AWS Bedrock).
* **Performance Budget:** ~800ms (Network I/O).

## 4. Logic & Policy
* **Separation of Concerns:** The LLM provides *classification scores*. The Python code applies the *policy*.
* **Scoring:** The system passes raw probability scores to the client for granular UI warnings (e.g., "85% Provocative").

## 5. Verification
* **Test Harness:** `verify_holistic.py`
* **Dataset:** `test_ground_truth.json`
* **Success Criteria:** * Correctly classifies "Size Matters" as Provocative.
    * Correctly classifies "stupidogenic" as Neologism (Safe).
    * Returns valid `scores` dictionary.
