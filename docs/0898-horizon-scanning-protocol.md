# 0898 - Horizon Scanning Protocol

## 1. Purpose

Systematic discovery of emerging AI governance frameworks, standards, and threats that should be reflected in the AgentOS audit suite. Transforms the audit system from reactive (validating existing audits) to proactive (surfacing what's missing).

**Core Question:** "What should we be auditing that we're not?"

**Relationship to Other Audits:**
- **0898 (this):** Discovers gaps, tracks frameworks, triggers new audit creation
- **0899:** Validates existing audits are executed correctly
- **0800:** Index of all audits

---

## 2. Framework Version Tracking

### 2.1 Active Framework Registry

Track current versions of frameworks that inform our audit suite:

| Framework | Current Version | Last Checked | Our Coverage | Status |
|-----------|-----------------|--------------|--------------|--------|
| **OWASP LLM Top 10** | 2025 | | 0809 Security | |
| **OWASP Agentic Top 10** | 2026 | | 0821 Agentic | |
| **ISO/IEC 42001** | 2023 | | 0818 AIMS | |
| **EU AI Act** | 2024 (effective 2025-2027) | | 0809, 0820 | |
| **NIST AI RMF** | 1.0 (2023) | | 0818, 0823 | |
| **ASVS** | 4.0.3 | | 0809 §4 | |
| **CWE Top 25** | 2024 | | 0809 §2 | |
| **SPDX AI Profile** | 3.0 | | 0819 AIBOM | |

### 2.2 Version Check Procedure

**Quarterly (or on trigger):**

```bash
# Check OWASP updates
🤖 Search: "OWASP LLM Top 10" site:owasp.org
🤖 Search: "OWASP Agentic" site:genai.owasp.org

# Check ISO updates
🤖 Search: "ISO 42001" updates site:iso.org

# Check NIST updates
🤖 Search: "NIST AI RMF" updates site:nist.gov

# Check EU AI Act implementation
🤖 Search: "EU AI Act" implementation guidance
```

### 2.3 Version Change Response

| Change Type | Response |
|-------------|----------|
| Minor update (clarification) | Note in registry, review relevant audit |
| Major update (new controls) | Gap analysis, update audit or create new |
| New framework published | Triage per §4 |
| Framework deprecated | Review for replacement |

---

## 3. Quarterly Research Protocol

### 3.1 Research Questions

Every quarter, systematically investigate:

| Category | Questions |
|----------|-----------|
| **Standards Bodies** | What new ISO/IEC AI standards published? What's in draft? |
| **OWASP** | Any updates to LLM Top 10? New guidance documents? |
| **Regulatory** | EU AI Act implementation updates? US state AI laws? |
| **Big 4 / Analysts** | What are Deloitte, KPMG, Gartner publishing on AI governance? |
| **Academic** | Major AI safety/security papers with practical implications? |
| **Industry** | What are Microsoft, Google, AWS publishing on responsible AI? |
| **Incidents** | Notable AI incidents that reveal new risk categories? |

### 3.2 Research Sources

| Source | URL | Focus |
|--------|-----|-------|
| OWASP GenAI | genai.owasp.org | LLM/Agentic security |
| ISO | iso.org/ics/35.020 | AI standards |
| NIST AI | nist.gov/artificial-intelligence | US framework |
| EU AI Act | artificialintelligenceact.eu | Regulation |
| Partnership on AI | partnershiponai.org | Industry practices |
| AI Incident Database | incidentdatabase.ai | Failure patterns |
| CSA | cloudsecurityalliance.org | Cloud AI security |
| ISACA | isaca.org | Audit guidance |
| IEEE | ieee.org | Technical standards |

### 3.3 Research Log

| Date | Researcher | Findings | Action Taken |
|------|------------|----------|--------------|
| | | | |

---

## 4. New Framework Triage

### 4.1 Triage Template

When a new framework, standard, or guidance is identified:

```markdown
## Framework Triage: [Name]

**Source:** [Organization]
**Published:** [Date]
**URL:** [Link]

### Relevance Assessment (1-5)

| Factor | Score | Notes |
|--------|-------|-------|
| Applies to our tech stack | | |
| Applies to our risk profile | | |
| Industry adoption momentum | | |
| Regulatory weight | | |
| **Total** | /20 | |

### Gap Analysis

| Framework Requirement | Current Coverage | Gap? |
|-----------------------|------------------|------|
| [Requirement 1] | [Audit 08xx §X] | |
| [Requirement 2] | None | Yes |

### Decision

- [ ] **Adopt** - Create/update audit to incorporate
- [ ] **Monitor** - Track for future adoption
- [ ] **Ignore** - Not relevant to AgentOS

### If Adopting

- Target audit: 08xx
- Effort estimate: [hours]
- Priority: P1/P2/P3
- Issue created: #xxx
```

### 4.2 Triage Criteria

| Score | Interpretation |
|-------|----------------|
| 16-20 | High relevance - prioritize adoption |
| 11-15 | Medium relevance - plan adoption |
| 6-10 | Low relevance - monitor only |
| 1-5 | Not relevant - document decision and ignore |

---

## 5. Trigger Pattern Library

### 5.1 External Triggers

Events that should trigger immediate horizon scanning:

| Trigger | Response | Owner |
|---------|----------|-------|
| OWASP publishes new guidance | Run §3 research protocol for OWASP | Developer |
| ISO publishes AI standard | Triage per §4 | Developer |
| Major AI incident reported | Check if new risk category | Developer |
| EU AI Act deadline approaching | Compliance review | Developer |
| Anthropic policy change | Review Claude Code governance | Developer |
| AWS Bedrock update | Review supply chain, security | Developer |

### 5.2 Internal Triggers

Patterns in our own system that suggest audit gaps:

| Pattern | Indicates | Response |
|---------|-----------|----------|
| Same issue found repeatedly | Audit not preventing | Strengthen audit |
| Issue found in production, not audit | Detection gap | Add test case |
| Agent asks permission too often | Over-restriction | Run 0808 |
| Agent does unexpected action | Under-restriction | Run 0821 |
| User reports false positive | Guardrail tuning needed | Run 0822 |
| User reports harmful content | Safety gap | Run 0809, 0823 |

### 5.3 Regulatory Triggers

| Trigger | Date | Response |
|---------|------|----------|
| EU AI Act - Prohibited practices | Feb 2025 | ✅ Review complete |
| EU AI Act - GPAI obligations | Aug 2025 | Review needed |
| EU AI Act - High-risk obligations | Aug 2026 | Plan compliance review |
| EU AI Act - Legacy systems | Aug 2027 | Plan legacy review |

---

## 6. Emerging Risk Radar

### 6.1 Risk Categories Under Watch

Risks not yet fully addressed in current audits:

| Risk Category | Relevance | Current Coverage | Watch Priority |
|---------------|-----------|------------------|----------------|
| **Model collapse** (training on AI output) | Low (use Bedrock) | None | Low |
| **Agentic swarms** | Low (single agent) | None | Monitor |
| **AI-generated malware** | Medium | 0809 | Monitor |
| **Deepfake integration** | Low | None | Low |
| **Autonomous goal-seeking** | Medium | 0821 | Active |
| **Supply chain poisoning** | Medium | 0819 | Active |
| **Regulatory fragmentation** | Medium | Multiple | Active |

### 6.2 Technology Watch

| Technology | Status | Implication for Audits |
|------------|--------|------------------------|
| Claude 4 / GPT-5 | Expected 2026 | Model upgrade procedures |
| Multi-agent frameworks | Emerging | 0821 expansion needed |
| AI agents in browsers | Emerging | Extension security |
| On-device LLMs | Emerging | Architecture change |
| Federated AI | Research | Privacy implications |

---

## 7. Audit Suite Gap Analysis

### 7.1 Current Coverage Map

| Domain | Audit(s) | Coverage Level |
|--------|----------|----------------|
| Security | 0809 | High |
| Privacy | 0810 | High |
| Code quality | 0811, 0812, 0813, 0814 | High |
| Dependencies | 0816 | Medium |
| Agent governance | 0808, 0815, 0821 | High |
| AI management | 0818 | Medium (new) |
| Supply chain | 0819 | Medium (new) |
| Explainability | 0820 | Low (new) |
| Bias/fairness | 0822 | Low (new) |
| Incident response | 0823 | Medium (new) |
| Meta/discovery | 0898, 0899 | High |

### 7.2 Identified Gaps

| Gap | Severity | Proposed Solution | Status |
|-----|----------|-------------------|--------|
| Continuous compliance automation | Medium | Add to 0899 | Planned |
| Audit effectiveness metrics | Medium | Add to 0899 | Planned |
| Multi-agent governance | Low | Future 0821 update | Monitor |
| Real-time monitoring | Low | Future consideration | Monitor |

---

## 8. Continuous Compliance Integration

### 8.1 Compliance as Code Vision

Long-term goal: audits generate from CI/CD artifacts, not manual checklists.

| Audit | Automation Potential | Current State | Target State |
|-------|----------------------|---------------|--------------|
| 0809 Security | High | Manual | CI security scans |
| 0811 Linting | High | Automated | ✅ Complete |
| 0812 Type checking | High | Automated | ✅ Complete |
| 0813 Test coverage | High | Automated | ✅ Complete |
| 0816 Dependencies | High | Semi-auto | Dependabot + alerts |
| 0819 Supply chain | Medium | Manual | SBOM generation |
| 0821 Agent governance | Low | Manual | Manual (complex) |

### 8.2 Automation Roadmap

| Phase | Target | Audits |
|-------|--------|--------|
| Current | Manual with CLI verification | Most |
| Near-term | CI generates evidence | 0811-0814, 0816 |
| Mid-term | Automated SBOM/AIBOM | 0819 |
| Long-term | Policy-as-code | 0809, 0821 |

---

## 9. Execution Schedule

### 9.1 Quarterly Cycle

| Month | Activity |
|-------|----------|
| **Q Start** | Full horizon scan (§3) |
| **Q Start + 2w** | Triage new frameworks (§4) |
| **Q Mid** | Update Framework Registry (§2) |
| **Q End** | Gap analysis review (§7) |

### 9.2 Event-Driven

| Event | Immediate Action |
|-------|------------------|
| Major framework release | Triage within 1 week |
| Security incident (industry) | Review within 48 hours |
| Regulatory deadline < 6 months | Compliance review |

---

## 10. Audit Record

| Date | Activity | Findings | Actions |
|------|----------|----------|---------|
| 2026-01-06 | Initial creation | 6 new audits identified | Created 0818-0823 |

---

## 11. References

### Horizon Scanning
- [UK Government Horizon Scanning](https://www.gov.uk/government/groups/horizon-scanning-programme-team)
- [OECD AI Policy Observatory](https://oecd.ai/)

### Framework Sources
- [OWASP GenAI](https://genai.owasp.org/)
- [ISO AI Standards](https://www.iso.org/committee/6794475/x/catalogue/)
- [NIST AI](https://www.nist.gov/artificial-intelligence)
- [EU AI Act](https://artificialintelligenceact.eu/)

### Internal
- docs/0899-meta-audit.md - Audit validation
- docs/0800-audit-index.md - Audit suite index

---

## 12. History

| Date | Change |
|------|--------|
| 2026-01-06 | Created. Extracted discovery/horizon scanning from 0899 into dedicated protocol. |
