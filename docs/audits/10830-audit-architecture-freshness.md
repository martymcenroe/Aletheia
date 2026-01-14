# 0830 - Architecture Freshness Audit

**Purpose:** Ensure architecture documentation remains current and complete as the system evolves.

**Frequency:** Monthly + on significant changes

**Trigger:** `/audit`, `/cleanup --full`

**Distinct From:** [0806 Architecture Audit](0806-architecture-audit.md) (Drift Detector) checks code-vs-docs alignment. This audit checks documentation completeness and currency.

---

## 1. Component Coverage

Verify all system components appear in architecture documentation.

### 1.1 Landing Page Components

Check `0001-architecture.md` Components table includes:

| Component | In 0001? | Notes |
|-----------|----------|-------|
| Extension | [ ] | Chrome MV3 / Firefox MV2 (single entry, not separate) |
| Lambda Service | [ ] | |
| Defense Funnel | [ ] | |
| Digital Etymologist | [ ] | |

**Note:** Infrastructure (DynamoDB, API Gateway, Bedrock) belongs in Deployment View (0001f), not the landing page.

**Pass Criteria:** All 4 core components listed with accurate descriptions.

### 1.2 Container View Completeness

Check `0001b-container-view.md` covers:

- [ ] Extension container with all subcomponents
- [ ] Lambda container with all modules
- [ ] Infrastructure container with all AWS services
- [ ] Key files table is accurate

**Verification:**
```bash
# Check extension files exist
ls extensions/chrome/manifest.json
ls extensions/chrome/overlay.js
ls extensions/chrome/service-worker.js

# Check Lambda files exist
ls src/lambda_function.py
ls src/guardrails/
ls src/etymologist.py
```

### 1.3 Diagram Quality Audit

**Rule:** Architecture diagrams must be readable, simple, and well-rendered.

#### 1.3.1 Simplification Check

When a diagram shows multiple components that do the same thing (e.g., "Chrome Extension" and "Firefox Extension"), they SHOULD be collapsed into a single conceptual node (e.g., "Extension") unless their interactions differ.

**Verification:** Review each diagram for redundant parallel nodes.

#### 1.3.2 Visual Rendering Check

Manually inspect each diagram in GitHub for:

| Check | Pass Criteria |
|-------|---------------|
| No touching elements | All boxes have visible gaps |
| No hidden lines | All arrows fully visible, not behind boxes |
| Readable labels | No truncation, font size adequate |
| Clear flow | Direction obvious (TB or LR consistent) |

#### 1.3.3 Diagram-Table Consistency (Relaxed)

When a document has both a diagram and a Components table:
- Diagram MAY use higher-level abstractions (e.g., "Extension" instead of "Chrome Extension, Firefox Extension")
- Table provides detail; diagram provides overview
- Every diagram node SHOULD correspond to one or more table rows

**Pass Criteria:** Diagram is readable, simple, and all elements trace to table entries.

**Failure Action:** Simplify diagram per 0006 §8.1, or fix rendering issues per 0006 §8.2-8.3.

---

## 2. ADR Synchronization

Verify `0001d-adr-digest.md` matches actual ADRs.

### 2.1 Count Check

```bash
# Count ADR files
ls docs/02*-ADR-*.md | wc -l

# Count entries in digest (grep for table rows)
grep -c "^\| \[02" docs/0001d-adr-digest.md
```

**Pass Criteria:** Counts match.

### 2.2 Status Accuracy

For each ADR in digest, verify status matches the source file:

| ADR | Digest Status | File Status | Match? |
|-----|---------------|-------------|--------|
| 0201 | | | [ ] |
| 0202 | | | [ ] |
| ... | | | [ ] |

### 2.3 New ADRs

Check for ADRs created since last audit that aren't in digest:

```bash
# Find ADRs modified in last 30 days
find docs -name "02*-ADR-*.md" -mtime -30
```

**Action:** Add any new ADRs to digest with accurate one-liner.

---

## 3. Glossary Completeness

Verify `0001g-glossary.md` includes all key terms.

### 3.1 Required Terms

| Term | In Glossary? | Accurate? |
|------|--------------|-----------|
| Defense Funnel | [ ] | [ ] |
| Digital Etymologist | [ ] | [ ] |
| Hydration/Dehydration | [ ] | [ ] |
| Museum Label | [ ] | [ ] |
| Naked Python | [ ] | [ ] |
| Stateful Serverless | [ ] | [ ] |
| AgentOS | [ ] | [ ] |
| Shadow DOM | [ ] | [ ] |
| Denylist | [ ] | [ ] |

### 3.2 New Terms

Search for undefined terms in recent docs:

```bash
# Find capitalized terms that might need glossary entries
grep -rh "\*\*[A-Z][a-z]*\*\*" docs/lld/active/ | sort | uniq
```

**Action:** Add any frequently-used terms not in glossary.

---

## 4. Quality Attributes Currency

Verify `0001e-quality-attributes.md` reflects current reality.

### 4.1 Metrics Validation

| Attribute | Documented Value | Actual Value | Source |
|-----------|------------------|--------------|--------|
| Latency (e2e) | | | CloudWatch |
| Cold start | | | CloudWatch |
| Error rate | | | CloudWatch |

### 4.2 Evidence Links

Check all audit links in quality attributes resolve:

```bash
# Verify linked audits exist
ls AgentOS:audits/0801-security-audit
ls AgentOS:audits/0802-privacy-audit
ls AgentOS:audits/0804-accessibility-audit
ls docs/0812-audit-performance.md
```

---

## 5. Cross-Reference Integrity

Verify all internal links resolve.

### 5.1 Link Validation

```bash
# Find all markdown links in 0001* files
grep -roh "\[.*\](.*\.md)" docs/0001*.md | sort | uniq

# Check each link resolves (manual or script)
```

### 5.2 Orphaned References

Check for references to old `0001-system-architecture.md`:

```bash
grep -r "0001-system-architecture" docs/
```

**Pass Criteria:** Only the redirect stub file should match.

---

## 6. Diagram Graduation Review

Check recent LLDs for diagrams that should be promoted to architecture docs.

### 6.1 Recent LLDs with Diagrams

```bash
# Find mermaid blocks in recent LLDs
grep -l "```mermaid" docs/lld/done/*.md | head -10
```

### 6.2 Graduation Criteria

A diagram should be promoted if it:
- [ ] Shows cross-component interaction
- [ ] Illustrates a reusable pattern
- [ ] Explains something frequently asked about

**Action:** For qualifying diagrams, add to appropriate 0001x doc and update LLD to reference it.

---

## 7. Audit Record

| Date | Auditor | Findings | Issues Created |
|------|---------|----------|----------------|
| | | | |

### Finding Categories

- **PASS:** All checks passed
- **FAIL:** Missing component/ADR/term - requires immediate update
- **WARN:** Stale metric or broken link - create issue

---

## 8. Auto-Fix (Default Behavior)

**This audit auto-fixes freshness issues rather than just reporting them.**

### 8.1 Auto-Fixable Items

| Finding | Auto-Fix Action |
|---------|-----------------|
| Missing ADR in digest | Extract title from file, add row to 0001d-adr-digest.md |
| Missing term in glossary | Add term with placeholder definition, flag for review |
| Broken internal link | Update to correct path if target exists |
| Orphaned old file reference | Update to new canonical path |
| Stale count mismatch | Update count to match reality |

### 8.2 Auto-Fix Procedure

```markdown
For each auto-fixable finding:
1. Identify the target file and location
2. Generate the fix:
   - ADR: `| [XXXX](02XX-ADR-name.md) | {title from file} | Final |`
   - Glossary: `| **Term** | [Definition needed] | - |`
   - Link: Update path to resolved location
3. Apply the edit
4. Log: "Auto-fixed: {description}"
```

### 8.3 Manual Review Required

| Finding | Reason |
|---------|--------|
| Missing component in 0001b | Requires accurate description |
| Diagram quality issues | Requires visual judgment |
| Quality attribute values | Requires CloudWatch/metrics verification |
| Diagram graduation | Requires architectural judgment |
| Major restructuring | Requires design discussion |

### 8.4 Fallback Workflow

When auto-fix cannot resolve:

1. **Minor updates** (typos, broken links): Fix in current session
2. **Missing components**: Add to relevant 0001x document
3. **New ADRs**: Add one-liner to 0001d-adr-digest.md
4. **New terms**: Add to 0001g-glossary.md
5. **Major restructuring**: Create issue for dedicated work

---

## 9. Integration

This audit is triggered by:

- `/audit` command (runs all audits including this)
- `/cleanup --full` (comprehensive cleanup)
- Monthly schedule per [0800-audit-index.md](AgentOS:audits/0800-audit-index)

---

*Created as part of the Architectural Depth Model (ADM) - Issue #308*
