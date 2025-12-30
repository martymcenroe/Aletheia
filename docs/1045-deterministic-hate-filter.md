# 1045 - Feature: Deterministic Hate Speech Filter (Denylist)

## 1. Context & Goal
* **Issue:** #45
* **Objective:** Block hate speech deterministically using a known "Denylist" before engaging the LLM.
* **Status:** Draft
* **Why:**
  - **Liability:** Shifts responsibility to an external database (RSDB).
  - **Cost/Latency:** Fails fast (O(1) lookup) without incurring LLM costs.
  - **Safety:** Prevents toxic tokens from even entering the inference pipeline.

## 2. Requirements
1. Load denylist on Lambda cold start
2. O(1) hash lookup for every input term
3. Immediate rejection with generic message
4. Do not ship denylist to client (browser extension)

## 3. Technical Approach
* **Module:** `src/guardrails/hate.py` (Planned)
* **Data Source:** `src/guardrails/resources/denylist.json` (Harvested from `rsdb.org`)
* **Dependencies:** None (pure Python set operations)
* **Performance Budget:** < 5ms latency

## 4. Implementation Details
- Load JSON set into memory on Lambda Cold Start
- Perform O(1) hash lookup during `check_safety`
- Return generic "Blocked" message with link to external source

### 4.1 Maintenance
* **Tooling:** `tools/harvest_rsdb.py` to scrape and update the JSON list periodically

### 4.2 Future Work (Ref #9001)
* **Trigger Mechanism:**
  - *Option A (Reactive):* EventBridge trigger when Semantic blocks as "Hate" but Denylist missed
  - *Option B (Scheduled):* Monthly cron job to scrape RSDB
* **Storage Promotion:** Migrate to S3 + DynamoDB if list exceeds Lambda memory

## 5. Verification & Testing

### 5.1 Test Commands
```bash
# Unit tests for hate filter
poetry run pytest tests/test_hate_filter.py -v

# Verify denylist loads without error
python -c "import json; d=json.load(open('src/guardrails/resources/denylist.json')); print(f'Loaded {len(d)} terms')"
```

### 5.2 Test Scenarios
| Scenario | Input | Expected Output | Pass Criteria |
|:---------|:------|:----------------|:--------------|
| Known slur | Term from denylist | Blocked | Returns rejection immediately |
| Clean word | "hello" | Passed | No rejection, continues to Semantic |
| Empty input | "" | Passed | No crash, continues pipeline |
| Performance | 1000 lookups | < 5ms total | Benchmark under budget |

### 5.3 Manual Smoke Test
1. Deploy Lambda with hate filter enabled
2. Send API request with known blocked term
3. Verify immediate rejection (no LLM call made)
4. Send clean term, verify it reaches LLM

## 6. Definition of Done
- [ ] Code complete and linted
- [ ] Unit tests pass
- [ ] Performance benchmark < 5ms
- [ ] Denylist loaded from RSDB
- [ ] Doc updated with actual test results
- [ ] PR merged to main
