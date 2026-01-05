# 1132 - Chore: Set Up Support Email Infrastructure (Cloudflare Email Routing)

## 1. Context & Goal
* **Issue:** #132
* **Objective:** Set up support@aletheia.example.com (or similar) email routing via Cloudflare for user support inquiries.
* **Status:** Draft
* **Related Issues:** #51 (Store Compliance - may need support contact)

### Open Questions
*Questions that need clarification before or during implementation. Remove when resolved.*

- [ ] What domain will be used? aletheia.app? Other?
- [ ] Does the domain already have Cloudflare DNS configured?
- [ ] Where should emails be routed to? Personal email? Shared inbox?
- [ ] Do we need multiple addresses (support@, privacy@, abuse@)?
- [ ] Is a ticketing system needed, or just email forwarding?
- [ ] What's the expected email volume? (Affects approach)

## 2. Requirements

1. support@{domain} email address functional
2. Emails forwarded to designated recipient
3. Auto-reply configured (optional but recommended)
4. SPF/DKIM configured for deliverability

## 3. Alternatives Considered

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| Cloudflare Email Routing | Free, simple | No inbox, forward only | **Selected** |
| Google Workspace | Full email suite | $6/user/month cost | Rejected |
| Fastmail | Privacy-focused | Monthly cost | Rejected |
| GitHub Discussions | No email setup | Not traditional support | Complement |

**Rationale:** Cloudflare Email Routing is free and sufficient for low-volume support.

## 4. Data & Fixtures

N/A - Infrastructure setup, no data.

## 5. Diagram

```mermaid
flowchart LR
    A[User] -->|support@domain| B[Cloudflare]
    B -->|Forward| C[Personal Email]
    C -->|Reply| D[User]

    subgraph DNS
        E[MX Records]
        F[SPF Record]
        G[DKIM Record]
    end
```

## 6. Technical Approach

* **Module:** Cloudflare Dashboard, DNS configuration
* **Dependencies:** Domain with Cloudflare DNS
* **Pattern:** Email forwarding

### Setup Steps

1. **Enable Email Routing in Cloudflare**
   - Dashboard → Email → Email Routing
   - Verify domain ownership

2. **Create Routing Rules**
   - support@ → forward to personal email
   - Optional: privacy@, abuse@

3. **Configure DNS Records**
   ```
   MX    10  route1.mx.cloudflare.net
   MX    20  route2.mx.cloudflare.net
   MX    30  route3.mx.cloudflare.net

   TXT   v=spf1 include:_spf.mx.cloudflare.net ~all
   ```

4. **DKIM Setup** (optional but recommended)
   - Cloudflare provides DKIM signing for forwarded emails

5. **Auto-Reply** (if supported)
   - "Thank you for contacting Aletheia support. We'll respond within 48 hours."

## 7. Interface Specification

N/A - Infrastructure, no code interfaces.

## 8. Security Considerations

| Concern | Mitigation | Status |
|---------|------------|--------|
| Spam to support email | Cloudflare spam filtering | Built-in |
| Personal email exposed | Use forwarding, not direct | Addressed |
| Phishing replies | DKIM/SPF for authenticity | TODO |

**Fail Mode:** Fail Closed - If routing fails, emails bounce (user knows delivery failed).

## 9. Performance Considerations

N/A - Email infrastructure.

## 10. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Email delivery issues | Med | Low | SPF/DKIM properly configured |
| Spam overwhelming inbox | Low | Med | Cloudflare filtering |
| Domain not on Cloudflare | High | Unknown | Confirm domain setup first |

## 11. Verification & Testing

### 11.1 Test Scenarios

| ID | Scenario | Type | Input | Expected Output | Pass Criteria |
|----|----------|------|-------|-----------------|---------------|
| 010 | Send test email | Manual | Email to support@ | Received in inbox | Email arrives |
| 020 | SPF check | Auto | mail-tester.com | SPF pass | Score > 8/10 |
| 030 | Reply works | Manual | Reply to forwarded email | Sent successfully | Delivery confirmed |

### 11.2 Test Commands

```bash
# Check MX records
dig MX domain.com

# Check SPF
dig TXT domain.com | grep spf

# Send test email (manual)
# Use mail-tester.com for deliverability check
```

## 12. Definition of Done

### Infrastructure
- [ ] Cloudflare Email Routing enabled
- [ ] support@ address configured
- [ ] MX records verified
- [ ] SPF record configured
- [ ] DKIM configured (if available)

### Testing
- [ ] Test email received successfully
- [ ] Reply works correctly
- [ ] SPF/DKIM passing

### Documentation
- [ ] Email address documented in SECURITY.md or README
- [ ] Support contact added to privacy policy
