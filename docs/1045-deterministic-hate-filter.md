# [1012] Feature: Deterministic Hate Speech Filter (Layer 2)

## 1. Context & Goal
* **Issue:** #45
* **Objective:** Block hate speech deterministically using a known "Denylist" before engaging the LLM.
* **Why:**
    * **Liability:** Shifts responsibility to an external database (RSDB).
    * **Cost/Latency:** Fails fast (O(1) lookup) without incurring LLM costs.
    * **Safety:** Prevents toxic tokens from even entering the inference pipeline.

## 2. Technical Approach
* **Module:** `src/guardrails/hate.py` (Planned).
* **Data Source:** `src/guardrails/resources/denylist.json` (Harvested from `rsdb.org`).
* **Mechanism:**
    * Load JSON set into memory on Lambda Cold Start.
    * Perform O(1) hash lookup during `check_safety`.
* **Performance Budget:** < 5ms latency.

## 3. Policy
* **Action:** Immediate Rejection.
* **Feedback:** Return generic "Blocked" message with a link to the external source.
* **Privacy:** Do not ship this list to the client (Browser Extension).

## 4. Maintenance
* **Tooling:** A local harvester script (`tools/harvest_rsdb.py`) will be created to scrape and update the JSON list periodically.

## 5. Future Work: Automation (Ref #9001)
* **Trigger Mechanism:** Define a trigger for the `harvest_rsdb.py` script.
    * *Option A (Reactive):* Triggered automatically via EventBridge when a term is blocked by Layer 3 (Semantic) as "Hate" but missed by Layer 2.
    * *Option B (Scheduled):* Monthly Cron job to scrape RSDB for updates.
* **Storage Promotion:** If the list exceeds Lambda memory limits or requires frequent updates, migrate from local `denylist.json` to S3 + DynamoDB (Global Table).