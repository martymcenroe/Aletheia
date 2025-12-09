# [1012] Feature: Deterministic Hate Speech Filter (Layer 2)

## 1. Context & Goal
* **Issue:** #45
* **Objective:** Block hate speech deterministically using a known "Denylist" before engaging the LLM.
* **Why:** * **Liability:** Shifts responsibility to an external database (RSDB).
    * **Cost/Latency:** Fails fast (O(1) lookup) without incurring LLM costs.
    * **Safety:** Prevents toxic tokens from even entering the inference pipeline.

## 2. Technical Approach
* **Module:** `src/guardrails/hate.py` (Planned).
* **Data Source:** `src/guardrails/resources/denylist.json` (Harvested from `rsdb.org`).
* **Mechanism:** * Load JSON set into memory on Lambda Cold Start.
    * Perform O(1) hash lookup during `check_safety`.
* **Performance Budget:** < 5ms latency.

## 3. Policy
* **Action:** Immediate Rejection.
* **Feedback:** Return generic "Blocked" message with a link to the external source.
* **Privacy:** Do not ship this list to the client (Browser Extension).

## 4. Maintenance
* **Tooling:** A local harvester script (`tools/harvest_rsdb.py`) will be created to scrape and update the JSON list periodically.
