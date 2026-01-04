# 0810 - Audit: Privacy

## 1. Purpose

Comprehensive privacy audit covering data protection, user consent, data minimization, and AI-specific privacy concerns. Based on industry frameworks including IAPP, IEEE 7000 Series, NIST Privacy Framework, and browser extension privacy requirements.

**Aletheia Context:**
- Browser extension processing user-selected text
- AWS Lambda backend with DynamoDB state
- AWS Bedrock Claude for text analysis
- No user accounts or authentication

---

## 2. IAPP Privacy Program Framework

### Data Inventory

| Data Type | Collection Point | Storage | Retention | Status |
|-----------|------------------|---------|-----------|--------|
| Selected text | User selection | In-memory only | Request duration | |
| Analysis results | Bedrock response | In-memory only | Display duration | |
| Preferences | Extension settings | localStorage | Until cleared | |
| Rate limit state | Lambda | DynamoDB | TTL auto-expire | |
| CloudWatch logs | Lambda execution | AWS CloudWatch | 30 days | |

### Privacy Principles Checklist

| Principle | Implementation | Status |
|-----------|----------------|--------|
| **Lawfulness** | Legitimate interest (user-initiated) | |
| **Purpose Limitation** | Only bias/slur detection | |
| **Data Minimization** | Only selected text, no context | |
| **Accuracy** | N/A (analysis, not storage) | |
| **Storage Limitation** | In-memory only, no persistence | |
| **Integrity & Confidentiality** | HTTPS, no logging of user content | |
| **Accountability** | This audit, ADRs | |

### Data Subject Rights

| Right | Applicability | Implementation | Status |
|-------|---------------|----------------|--------|
| **Access** | Low (no PII stored) | No persistent user data | |
| **Rectification** | N/A | No persistent data | |
| **Erasure** | Low | Clear localStorage in extension | |
| **Portability** | N/A | No user data to port | |
| **Objection** | N/A | User controls all actions | |
| **Automated Decision** | Partial | Analysis only, no decisions | |

---

## 3. IEEE 7000 Series Alignment

### IEEE 7002-2022: Data Privacy Process

| Requirement | Aletheia Implementation | Status |
|-------------|------------------------|--------|
| Privacy by Design | ADR 0201, minimal permissions | |
| Data agency (user control) | User initiates all actions | |
| Consent mechanisms | Implicit (user action) | |
| Privacy impact assessment | This audit | |

### IEEE 7010-2020: Human Well-Being Impact

| Consideration | Aletheia Approach | Status |
|---------------|-------------------|--------|
| User autonomy | User controls when/what to analyze | |
| Psychological impact | Educational framing, not punitive | |
| Information asymmetry | Transparent about AI limitations | |
| Dignity respect | Analysis of text, not judgment of user | |

### Data Agency Principles

| Principle | Implementation | Status |
|-----------|----------------|--------|
| User controls data collection | Only selected text | |
| User controls data use | Only bias analysis | |
| User controls data sharing | Not shared externally | |
| User can withdraw | Uninstall extension | |

---

## 4. NIST Privacy Framework 1.1 (AI-Enhanced)

### IDENTIFY-P (Privacy Risk Assessment)

| Activity | Aletheia Implementation | Status |
|----------|------------------------|--------|
| Data inventory | §2 Data Inventory table | |
| Privacy risk catalog | Minimal (no PII storage) | |
| AI-specific risks | LLM prompt content | |

### GOVERN-P (Governance)

| Activity | Aletheia Implementation | Status |
|----------|------------------------|--------|
| Privacy policies | ADR 0201, this audit | |
| Roles/responsibilities | Orchestrator protocol | |
| Privacy training | N/A (no team) | |

### CONTROL-P (Data Processing Controls)

| Activity | Aletheia Implementation | Status |
|----------|------------------------|--------|
| Data processing policies | In-memory only | |
| Consent management | User-initiated actions | |
| Data quality | N/A (no storage) | |

### COMMUNICATE-P (Transparency)

| Activity | Aletheia Implementation | Status |
|----------|------------------------|--------|
| Privacy notice | Store listing, README | |
| Data use disclosure | Transparent about Bedrock | |
| Third-party disclosure | AWS only, disclosed | |

### PROTECT-P (Data Security)

| Activity | Aletheia Implementation | Status |
|----------|------------------------|--------|
| Access controls | No user data to protect | |
| Data security | HTTPS, encryption in transit | |
| Data disposal | Automatic (in-memory) | |

---

## 5. Browser Extension Privacy

### Chrome Web Store Requirements

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| Privacy policy link | README link | |
| Data use disclosure | Store listing | |
| Single purpose | Bias/slur detection only | |
| Minimal permissions | ADR 0201 compliance | |
| No `<all_urls>` | PROHIBITED | |

### Permission Privacy Audit

| Permission | Privacy Impact | Justification | Status |
|------------|----------------|---------------|--------|
| `activeTab` | Low - only on user action | Analyze selected text | |
| `contextMenus` | None | UI only | |
| `storage` | Low - local only | User preferences | |

### Data Flow Privacy

```
User selects text → Extension reads (activeTab)
                  → HTTPS to Lambda (encrypted)
                  → Lambda to Bedrock (AWS internal)
                  → Response to Extension (encrypted)
                  → Display to User
                  → Memory cleared
```

| Stage | Data Exposed | Privacy Control | Status |
|-------|--------------|-----------------|--------|
| Selection | User's selected text | User initiated | |
| Transit to Lambda | Selected text | HTTPS encryption | |
| Lambda processing | Selected text | In-memory only | |
| Bedrock analysis | Selected text | AWS data handling | |
| Response display | Analysis result | Local only | |
| After display | Nothing | Memory cleared | |

---

## 6. AI/LLM Privacy Concerns

### Prompt Privacy

| Concern | Mitigation | Status |
|---------|------------|--------|
| PII in prompts | User controls selection | |
| Prompt logging | Disabled in Bedrock | |
| Prompt training | Bedrock does not train on prompts | |
| Prompt persistence | In-memory only | |

### Model Privacy

| Concern | Mitigation | Status |
|---------|------------|--------|
| Model memorization | Using AWS-managed model | |
| Output hallucination | User reviews output | |
| Inference attacks | Minimal context sent | |

### AWS Bedrock Privacy

| Concern | AWS Commitment | Status |
|---------|----------------|--------|
| Data isolation | Per-account isolation | |
| No training on prompts | Confirmed in TOS | |
| Data residency | US region | |
| Compliance | SOC 2, ISO 27001 | |

---

## 7. Regulatory Awareness

### GDPR (EU Users)

| Requirement | Applicability | Status |
|-------------|---------------|--------|
| Lawful basis | Legitimate interest | |
| Data minimization | ✅ In-memory only | |
| Purpose limitation | ✅ Single purpose | |
| Storage limitation | ✅ No persistence | |
| DPA required | N/A (AWS manages) | |

### CCPA (California Users)

| Requirement | Applicability | Status |
|-------------|---------------|--------|
| Right to know | Store listing disclosure | |
| Right to delete | No data to delete | |
| Right to opt-out | N/A (no selling) | |
| Non-discrimination | N/A | |

### Browser Store Policies

| Platform | Privacy Requirements | Status |
|----------|---------------------|--------|
| Chrome Web Store | Single purpose, minimal permissions | |
| Firefox Add-ons | Privacy policy required | |
| Edge Add-ons | Microsoft privacy compliance | |

---

## 8. Privacy by Design Verification

### Aletheia Design Principles

| Principle | Implementation | Status |
|-----------|----------------|--------|
| **Proactive not reactive** | ADR 0201 written before code | |
| **Privacy as default** | Minimal permissions, no tracking | |
| **Privacy embedded** | Architecture decision, not add-on | |
| **Full functionality** | Privacy doesn't reduce utility | |
| **End-to-end security** | HTTPS, no persistence | |
| **Visibility/transparency** | Open source, this audit | |
| **Respect for user** | User controls all actions | |

---

## 9. Audit Procedure

1. Review Data Inventory (§2) - verify no new data types
2. Check Permission Minimalism (§5) - no permission creep
3. Verify AWS Bedrock settings - no logging of prompts
4. Review CloudWatch logs - no PII present
5. Check store listings - privacy disclosures accurate
6. Document findings in audit record

---

## 10. Audit Record

| Date | Auditor | Findings Summary | Issues Created |
|------|---------|------------------|----------------|
| | | | |

---

## 11. References

### IAPP
- [IAPP Privacy Program Framework](https://iapp.org/resources/article/privacy-program-framework/)
- [Privacy and AI Governance 2025](https://iapp.org/news/video/privacy-ai-governance-and-cybersecurity-law-in-2025/)
- [Built to Scale: Privacy and AI Risk Frameworks](https://iapp.org/resources/article/built-to-scale-privacy-and-ai-risk-frameworks/)

### IEEE
- [IEEE 7000 Series Standards](https://standards.ieee.org/news/ieee-standards-commitment-to-advancing-ai-governance-includes-impactful-contributions-to-new-international-ai-standards-exchange/)
- [Ethically Aligned Design](https://www.paloaltonetworks.com/cyberpedia/ieee-ethically-aligned-design)

### NIST
- [NIST Privacy Framework 1.1](https://www.jonesday.com/en/insights/2025/05/nist-updates-its-privacy-framework-to-address-ai)
- [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework)

### ISC2
- [AI Security and Privacy Best Practices](https://www.isc2.org/Insights/2025/07/ISC2-Launches-AI-Certificate)
- [2025 Cybersecurity Workforce Study](https://www.isc2.org/Insights/2025/12/2025-ISC2-Cybersecurity-Workforce-Study)

### Internal
- ADR 0201 - Privacy-First Extension Permissions
- ADR 0208 - Client-Side Preference Storage
- docs/0809-audit-security.md - Security Audit
