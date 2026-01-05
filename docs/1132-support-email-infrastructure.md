# 1132 - Chore: Set Up Support Email Infrastructure (Cloudflare Email Routing)

## 1. Context & Goal
* **Issue:** #132
* **Objective:** Set up support@aletheia.study email routing via Cloudflare for user support inquiries.
* **Status:** Draft
* **Related Issues:** #51 (Store Compliance - requires support contact)

### Open Questions
*Questions that need clarification before or during implementation. Remove when resolved.*

- [x] ~~What domain will be used?~~ **aletheia.study** (per Firefox manifest `extension@aletheia.study`)
- [ ] Does `aletheia.study` already have Cloudflare DNS configured?
- [ ] Where should emails be routed to? Personal email? Shared inbox?
- [x] ~~Do we need multiple addresses?~~ **Yes: support@, privacy@, abuse@**
- [ ] Is a ticketing system needed, or just email forwarding?
- [x] ~~What's the expected email volume?~~ **Low (MVP phase)**

### Resolved Questions (Gemini Review 2026-01-05)

1. **Q: What domain?**
   **A: aletheia.study** - Already used in Firefox manifest ID.

2. **Q: Is receive-only acceptable for MVP?**
   **A: Yes** - Replies from personal email acceptable for MVP. Document limitation.

## 2. Requirements

1. `support@aletheia.study` functional (inbound)
2. `privacy@aletheia.study` functional (GDPR contact)
3. `abuse@aletheia.study` functional (standard requirement for stores)
4. Emails forwarded to designated recipient
5. SPF/DKIM configured for deliverability
6. Document reply limitations (outbound)

## 3. Alternatives Considered

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| Cloudflare Email Routing | Free, simple | Inbound only, no SMTP | **Selected (MVP)** |
| Google Workspace | Full email suite, Send As | $6/user/month cost | Post-MVP |
| Fastmail | Privacy-focused, SMTP | Monthly cost | Rejected |
| GitHub Discussions | No email setup | Not traditional support | Complement |

**Rationale:** Cloudflare Email Routing is free and sufficient for low-volume MVP support. Upgrade to Google Workspace if professional replies become necessary.

## 4. Data & Fixtures

N/A - Infrastructure setup, no data.

## 5. Diagram

```mermaid
flowchart LR
    A[User] -->|support@aletheia.study| B[Cloudflare]
    B -->|Forward| C[Personal Email]
    C -.->|Reply from personal| D[User]

    subgraph DNS[aletheia.study DNS]
        E[MX Records]
        F[SPF Record]
        G[DKIM Record]
    end

    style C fill:#ffcc00
    Note[⚠️ Reply exposes personal email]
```

## 6. Technical Approach

* **Module:** Cloudflare Dashboard, DNS configuration
* **Dependencies:** `aletheia.study` domain with Cloudflare DNS
* **Pattern:** Email forwarding (inbound only)

### 6.1 Cloudflare Email Routing Limitation (IMPORTANT)

**Cloudflare Email Routing is INBOUND ONLY.**

| Direction | Supported | Notes |
|-----------|-----------|-------|
| Inbound (receive) | ✅ Yes | User → support@aletheia.study → forwarded |
| Outbound (send) | ❌ No | No SMTP provided |

**Reply Options:**

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| Reply from personal email | Simple | Exposes personal address | **MVP** |
| Gmail "Send As" alias | Professional appearance | Requires verification, SMTP setup | Post-MVP |
| Google Workspace | Full solution | $6/month | Post-MVP |

**MVP Decision:** Accept replies from personal email. Users will see personal address in "From" field. This is acceptable for low-volume MVP.

### 6.2 Email Addresses to Configure

| Address | Purpose | Forward To |
|---------|---------|------------|
| `support@aletheia.study` | User support | Personal email |
| `privacy@aletheia.study` | GDPR/privacy requests | Personal email |
| `abuse@aletheia.study` | Abuse reports (store requirement) | Personal email |

### 6.3 Setup Steps

1. **Verify Cloudflare DNS**
   - Confirm `aletheia.study` is on Cloudflare
   - Dashboard → DNS → Verify nameservers

2. **Enable Email Routing in Cloudflare**
   - Dashboard → Email → Email Routing
   - Verify domain ownership

3. **Create Routing Rules**
   ```
   support@aletheia.study → forward to personal email
   privacy@aletheia.study → forward to personal email
   abuse@aletheia.study   → forward to personal email
   ```

4. **Configure DNS Records** (Cloudflare adds automatically)
   ```
   MX    10  route1.mx.cloudflare.net
   MX    20  route2.mx.cloudflare.net
   MX    30  route3.mx.cloudflare.net

   TXT   v=spf1 include:_spf.mx.cloudflare.net ~all
   ```

5. **DKIM Setup**
   - Cloudflare provides DKIM signing for forwarded emails
   - Verify DKIM record exists after setup

## 7. Interface Specification

N/A - Infrastructure, no code interfaces.

## 8. Security Considerations

| Concern | Mitigation | Status |
|---------|------------|--------|
| Spam to support email | Cloudflare spam filtering | Built-in |
| Personal email exposed on INBOUND | Use forwarding, not direct | Addressed |
| Personal email exposed on REPLY | **Known limitation for MVP** | Documented |
| Phishing replies | DKIM/SPF for authenticity | TODO |

**Fail Mode:** Fail Closed - If routing fails, emails bounce (user knows delivery failed).

### 8.1 Reply Exposure Risk

**Current state (MVP):** When replying to forwarded emails from personal Gmail/email, the personal address IS visible to the user in the "From" field.

**Acceptable for MVP because:**
- Low volume expected
- Personal nature of solo developer project
- Professional alias can be added later

**Future mitigation (Post-MVP):**
- Gmail "Send As" with SMTP verification
- Or upgrade to Google Workspace

## 9. Performance Considerations

N/A - Email infrastructure.

## 10. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Email delivery issues | Med | Low | SPF/DKIM properly configured |
| Spam overwhelming inbox | Low | Med | Cloudflare filtering |
| Domain not on Cloudflare | High | Unknown | Verify first |
| Personal email exposed on reply | Low | High | Document as MVP limitation |

## 11. Verification & Testing

### 11.1 Test Scenarios

| ID | Scenario | Type | Input | Expected Output | Pass Criteria |
|----|----------|------|-------|-----------------|---------------|
| 010 | Send to support@ | Manual | Email to support@aletheia.study | Received in inbox | Email arrives |
| 020 | Send to privacy@ | Manual | Email to privacy@aletheia.study | Received in inbox | Email arrives |
| 030 | Send to abuse@ | Manual | Email to abuse@aletheia.study | Received in inbox | Email arrives |
| 040 | SPF check | Auto | mail-tester.com | SPF pass | Score > 8/10 |
| 050 | DKIM check | Auto | mail-tester.com | DKIM pass | Signature valid |

### 11.2 Test Commands

```bash
# Check MX records
dig MX aletheia.study

# Check SPF
dig TXT aletheia.study | grep spf

# Check DKIM (after setup)
dig TXT *._domainkey.aletheia.study

# Send test email (manual)
# Use mail-tester.com for deliverability check
```

## 12. Definition of Done

### Infrastructure
- [ ] Cloudflare DNS verified for aletheia.study
- [ ] Email Routing enabled
- [ ] support@aletheia.study configured
- [ ] privacy@aletheia.study configured
- [ ] abuse@aletheia.study configured
- [ ] MX records verified
- [ ] SPF record configured
- [ ] DKIM configured

### Testing
- [ ] Test emails received at all 3 addresses
- [ ] SPF/DKIM passing on mail-tester.com

### Documentation
- [ ] SECURITY.md updated with security@aletheia.study (or support@)
- [ ] README updated with support contact
- [ ] Privacy policy updated with privacy@ contact
- [ ] Reply limitation documented (personal email visible)

---

## Appendix: Gemini Review Response

**Review Date:** 2026-01-05
**Reviewer:** Gemini 3 Pro

### Tier 2 Issues (HIGH) - Addressed

| Issue | Resolution |
|-------|------------|
| Domain Ambiguity | Confirmed `aletheia.study` from Firefox manifest |
| Reply Exposure Risk | Documented as MVP limitation in §6.1 and §8.1 |

### Tier 3 Issues (SUGGESTIONS) - Addressed

| Issue | Resolution |
|-------|------------|
| Update SECURITY.md/README | Added to Definition of Done |
| Add abuse@ address | Added to §6.2 email addresses |
