# 10006 - Feature: RAG Vector Store

## 1. Context & Goal
* **Issue:** #6
* **Objective:** Implement Retrieval Augmented Generation with vector storage.
* **Status:** **DEFERRED TO POST-MVP (v2.0)**

### Orchestrator Decision (2026-01-06)

**Verdict: DEFER**

**Reasoning:** Adding a vector database (Pinecone/Chroma) now would:
1. Delay launch by weeks
2. Complicate our privacy policy (storing user thoughts indefinitely)
3. Exceed cost budget for free tier

**Action:** Leave in Backlog. Do not implement before Chrome Store submission.

---

### Resolved Questions (Orchestrator 2026-01-06)

#### Architecture Questions
- [x] **Q1:** What data goes into the vector store?
  - **Answer:** User Queries + Approved Reference Docs (when implemented)

- [x] **Q2:** What's the embedding model?
  - **Answer:** AWS Titan Embeddings v2 (stay in Bedrock/AWS ecosystem)

- [x] **Q3:** Where is the vector store hosted?
  - **Answer:** AWS OpenSearch Serverless OR Bedrock Knowledge Bases (no new vendors like Pinecone)

- [x] **Q4:** What's the data lifecycle?
  - **Answer:** 30-day TTL (strict privacy alignment with #145)

#### Integration Questions
- [ ] **Q5:** How does RAG integrate with the current Lambda flow?
  - **Deferred** - Design when implementing

- [ ] **Q6:** What similarity threshold determines "relevant" context?
  - **Deferred** - Tune during implementation

- [ ] **Q7:** How do we handle cold starts if vector store requires initialization?
  - **Deferred** - Design when implementing

#### Privacy Questions
- [x] **Q8:** Do we store user query embeddings?
  - **Answer: CRITICAL** - Cannot store user query embeddings without explicit "Cloud Sync" opt-in. **Default must be OFF.**

- [ ] **Q9:** How does RAG interact with noarchive signals?
  - **Deferred** - Design when implementing

- [ ] **Q10:** Is user consent required for adding queries to knowledge base?
  - **Answer:** Yes - Requires explicit opt-in (per Q8)

#### Cost Questions
- [ ] **Q11:** What's the estimated monthly cost?
  - **Deferred** - Calculate when planning v2.0

- [x] **Q12:** Is this feature viable for free tier?
  - **Answer:** No - Too high for MVP free tier. May require paid tier in v2.0.

---

## 2. Requirements (Post-MVP)

| ID | Requirement | Notes |
|----|-------------|-------|
| R1 | AWS-native solution | Titan Embeddings + OpenSearch/Knowledge Bases |
| R2 | 30-day TTL | Privacy alignment |
| R3 | Explicit opt-in | "Cloud Sync" toggle, default OFF |
| R4 | No PII storage | User consent required |

## 3. Technical Approach (Outline for v2.0)

* **Module:** `src/rag/`
* **Dependencies:**
  - AWS Titan Embeddings v2
  - AWS OpenSearch Serverless OR Bedrock Knowledge Bases
  - aws-xray-sdk (for tracing)
* **Performance Budget:** TBD

### 3.1 Preferred Architecture (v2.0)

```
User Query ──embed──► Titan Embeddings ──search──► OpenSearch Serverless
                                                          │
                                                          ▼
                                            Retrieved context + Query
                                                          │
                                                          ▼
                                                   Bedrock (Sonnet)
                                                          │
                                                          ▼
                                                   Enhanced response
```

## 4. Implementation Details
Deferred to v2.0 planning phase.

## 5. Verification & Testing

### 5.1 Test Commands
```bash
# Unit tests (when implemented)
poetry run pytest tests/test_rag.py -v
```

### 5.2 Test Scenarios
| Scenario | Input | Expected Output | Pass Criteria |
|:---------|:------|:----------------|:--------------|
| Deferred | Deferred | Deferred | Deferred |

## 6. Definition of Done
- [ ] v2.0 planning complete
- [ ] Cost analysis approved
- [ ] Privacy policy updated for "Cloud Sync"
- [ ] User consent UI implemented
- [ ] Code complete and linted
- [ ] Unit tests pass
- [ ] PR merged to main

---

## Appendix: Review History

| Date | Reviewer | Verdict |
|------|----------|---------|
| 2026-01-05 | Gemini 3 Pro | DEFER (stub) |
| 2026-01-06 | Orchestrator | **DEFER to Post-MVP** |
