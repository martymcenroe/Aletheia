# 0827 - Audit: Infrastructure & Integration

## 1. Purpose

Verify configuration integrity of cloud infrastructure, model versions, and system integrations. Ensures production settings match documented architecture and security requirements.

**Aletheia Context:**
- AWS Lambda with Bedrock integration
- DynamoDB for usage tracking
- Claude Code development workflow
- Extension ↔ API Gateway ↔ Lambda pipeline

---

## 2. Model Version Tracking

### 2.1 Production Model IDs

| Component | Expected Model | Verification Command | Status |
|-----------|----------------|---------------------|--------|
| Etymologist | amazon.nova-micro-v1:0 | `grep NOVA_MICRO_MODEL_ID src/etymologist.py` | |
| Semantic Guard | amazon.nova-micro-v1:0 | `grep MODEL_ID src/guardrails/semantic.py` | |
| Lambda Env Override | BEDROCK_MODEL_ID | `aws lambda get-function-configuration` | |

### 2.2 Model Version Drift Detection

```bash
# Check if Lambda is using expected model
MSYS_NO_PATHCONV=1 aws lambda get-function-configuration \
    --function-name AletheiaAgent \
    --query 'Environment.Variables.BEDROCK_MODEL_ID'

# Compare against documented version
grep -r "nova-micro\|NOVA_MICRO" src/*.py
```

| Check | Requirement | Status |
|-------|-------------|--------|
| Lambda model matches code | Env var = hardcoded fallback | |
| Model version is pinned | Not "latest" or wildcard | |
| Bedrock access verified | Can invoke model | |

---

## 3. Lambda Configuration

### 3.1 Environment Variables

| Variable | Purpose | Should Exist? | Sensitive? | Status |
|----------|---------|---------------|------------|--------|
| BEDROCK_MODEL_ID | Override default model | Optional | No | |
| AWS_REGION | Region for Bedrock | Required | No | |
| DENYLIST_TABLE | DynamoDB table name | Required | No | |

### 3.2 Security Configuration

| Setting | Requirement | Verification | Status |
|---------|-------------|--------------|--------|
| IAM Role | Least privilege | Check attached policies | |
| VPC | Not required (public API) | Verify no VPC config | |
| Secrets | No hardcoded secrets | gitleaks scan | |
| Timeout | Reasonable (< 30s) | Get function config | |
| Memory | Appropriate (128-512MB) | Get function config | |

### 3.3 Verification Commands

```bash
# Lambda configuration
MSYS_NO_PATHCONV=1 aws lambda get-function-configuration \
    --function-name AletheiaAgent \
    --query '{Timeout:Timeout,Memory:MemorySize,Runtime:Runtime}'

# IAM policies (check for least privilege)
MSYS_NO_PATHCONV=1 aws iam list-attached-role-policies \
    --role-name Aletheia-lambda-role
```

---

## 4. DynamoDB Configuration

### 4.1 Table Schema

| Table | Primary Key | Sort Key | Purpose | Status |
|-------|-------------|----------|---------|--------|
| aletheia-usage | user_id | timestamp | Usage tracking | |

### 4.2 Data Handling

| Check | Requirement | Status |
|-------|-------------|--------|
| No PII stored | Only anonymized IDs | |
| TTL configured | Auto-delete old data | |
| Encryption at rest | AWS managed | |

### 4.3 Verification

```bash
# Table configuration
MSYS_NO_PATHCONV=1 aws dynamodb describe-table \
    --table-name aletheia-usage \
    --query 'Table.{KeySchema:KeySchema,TTL:TimeToLiveDescription}'
```

---

## 5. API Gateway Configuration

### 5.1 Endpoint Security

| Check | Requirement | Status |
|-------|-------------|--------|
| WAF enabled | Custom header validation | |
| CORS configured | Extension origins only | |
| Rate limiting | Prevent abuse | |
| HTTPS only | No HTTP endpoints | |

### 5.2 Verification

```bash
# Get API Gateway configuration
MSYS_NO_PATHCONV=1 aws apigateway get-rest-apis
```

---

## 6. Claude Code Integration

### 6.1 Settings Verification

| Setting | Location | Requirement | Status |
|---------|----------|-------------|--------|
| Model version | claude --version | Current stable | |
| Deny list | .claude/settings.local.json | Critical ops blocked | |
| Allow list | .claude/settings.local.json | Common ops allowed | |

### 6.2 Verification Commands

```bash
# Check Claude Code version
claude --version

# Verify deny list contains critical items
grep -A 50 '"deny"' .claude/settings.local.json | head -30
```

---

## 7. Cross-Component Integration

### 7.1 Data Flow Verification

```
Extension → API Gateway → Lambda → Bedrock
    ↓                         ↓
  Storage                  DynamoDB
```

| Integration Point | Verification | Status |
|-------------------|--------------|--------|
| Extension → API Gateway | Test with curl | |
| API Gateway → Lambda | CloudWatch logs | |
| Lambda → Bedrock | X-Ray traces | |
| Lambda → DynamoDB | CloudWatch metrics | |

---

## 8. Audit Procedure

1. Run model version checks (§2)
2. Verify Lambda configuration (§3)
3. Check DynamoDB settings (§4)
4. Validate API Gateway (§5)
5. Confirm Claude Code settings (§6)
6. Test integration points (§7)
7. Document findings

---

## 9. Audit Record

| Date | Auditor | Findings Summary | Issues Created |
|------|---------|------------------|----------------|
| | | | |

---

## 10. References

### Internal
- docs/0001-architecture.md (and 0001a-g views)
- docs/0014-cost-architecture.md
- AgentOS:audits/0810-ai-supply-chain

### AWS
- [Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [DynamoDB Security](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/security.html)

---

## 11. History

| Date | Change |
|------|--------|
| 2026-01-10 | Created per #254 - Infrastructure integration audit |
