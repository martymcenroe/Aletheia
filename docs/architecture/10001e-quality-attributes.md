# 0001e - Quality Attributes

Non-functional requirements with targets, current status, and evidence.

## Latency

| Metric | Target | Current | Evidence |
|--------|--------|---------|----------|
| End-to-end | <2s | ~1.5s | [0812 Performance Audit](0812-audit-performance.md) |
| Time-to-First-Byte | <500ms | ~400ms | Lambda streaming metrics |
| Cold start | <1s | ~800ms | CloudWatch INIT duration |

**How Achieved:**
- Amazon Nova Micro model (optimized for low-latency inference)
- SSE streaming via `@awslambda.streamify_response`
- Shared boto3 client (eliminates duplicate initialization)
- Naked Python architecture (no framework overhead)

**Trade-offs:**
- Chose Nova Micro over larger models for speed over depth
- Sequential LLM calls (semantic + etymology) add ~1s but required for safety

**Deep Dive:** [LLD-1137 Lambda Latency Investigation](lld/done/1137-lambda-latency-investigation.md)

---

## Privacy

| Metric | Target | Current | Evidence |
|--------|--------|---------|----------|
| PII storage | None | None | [0810 Privacy Audit](AgentOS:audits/0802-privacy-audit) |
| Data retention | <48h | 24h TTL | DynamoDB TTL configuration |
| User tracking | None | None | No cookies, no analytics |

**How Achieved:**
- DynamoDB TTL auto-deletes all data within 24-48h
- Hash-based thread_id (no user identification)
- Blocked terms never stored (only hash match)
- User preferences stored client-side only

**Trade-offs:**
- Cannot provide DSAR (Data Subject Access Request) without OAuth
- No usage analytics means no product insights

**Deep Dive:** [LLD-1147 GDPR Data Erasure](lld/done/1147-gdpr-data-erasure.md), [ADR-0208](0208-ADR-client-side-preference-storage.md)

---

## Security

| Metric | Target | Current | Evidence |
|--------|--------|---------|----------|
| OWASP LLM Top 10 | Compliant | Passing | [0809 Security Audit](AgentOS:audits/0801-security-audit) |
| Extension permissions | Minimal | `activeTab` only | [ADR-0201](0201-ADR-privacy-first-permissions.md) |
| Prompt injection | Protected | XML wrapping | [LLD-1124 §6.3](lld/done/1124-digital-etymologist.md) |

**How Achieved:**
- Defense funnel blocks malicious input before LLM
- XML-wrapped user input prevents prompt injection
- Shadow DOM prevents XSS via host page
- WAF rate limiting prevents abuse
- No `<all_urls>` permission (no broad access)

**Trade-offs:**
- Strict permissions limit proactive features
- Rate limiting may frustrate power users

**Deep Dive:** [0825 AI Safety Audit](AgentOS:audits/0808-ai-safety-audit), [LLD-1095 Security Hardening](lld/done/1095-security-hardening.md)

---

## Accessibility

| Metric | Target | Current | Evidence |
|--------|--------|---------|----------|
| WCAG 2.1 | AA | Passing | [0811 Accessibility Audit](AgentOS:audits/0804-accessibility-audit) |
| Keyboard navigation | Full | Implemented | Overlay focusable, Escape closes |
| Screen reader | Compatible | ARIA labels | `aria-live`, `aria-expanded` |

**How Achieved:**
- Semantic HTML in overlay
- ARIA attributes for dynamic content
- Focus management on overlay open/close
- Sufficient color contrast

**Trade-offs:**
- Shadow DOM complicates some assistive tech (mitigated with ARIA)

**Deep Dive:** [LLD-1154 ARIA Accessibility](lld/done/1154-aria-accessibility.md)

---

## Reliability

| Metric | Target | Current | Evidence |
|--------|--------|---------|----------|
| Uptime | 99.9% | ~99.95% | AWS Lambda SLA |
| Error rate | <1% | <0.5% | CloudWatch metrics |
| Graceful degradation | Yes | Fallback responses | Etymologist fallback structure |

**How Achieved:**
- Serverless architecture (AWS manages infrastructure)
- Fallback responses on LLM failure
- Retry logic in extension
- Circuit breaker for rate limits

---

## Cost

| Metric | Target | Current | Evidence |
|--------|--------|---------|----------|
| Per-request | <$0.001 | ~$0.0003 | [0814 Cost Architecture](0014-cost-architecture.md) |
| Monthly (1K users) | <$50 | ~$30 | AWS billing estimates |
| Idle cost | $0 | $0 | Serverless scale-to-zero |

**How Achieved:**
- Lambda pay-per-invocation
- DynamoDB on-demand capacity
- Amazon Nova Micro (cost-effective model)
- No always-on infrastructure

---

[← ADR Digest](0001d-adr-digest.md) | [Back to Architecture](0001-architecture.md) | [Deployment View →](0001f-deployment-view.md)
