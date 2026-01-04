# 0012 - DevOps Architecture

## 1. Overview

This document defines Aletheia's DevOps infrastructure: CI/CD pipelines, deployment processes, environment management, and quality gates.

**Status:** Implemented (2026-01-04)
**Related Issues:** #105 (Test Infrastructure), Architecture Review Session

---

## 2. CI/CD Pipeline

### 2.1 GitHub Actions Workflow

**File:** `.github/workflows/ci.yml`

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions CI                        │
├─────────────────────────────────────────────────────────────┤
│  Trigger: push to main, pull_request to main                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Job: test                                          │   │
│  │  ├── Checkout                                       │   │
│  │  ├── Setup Python 3.12                              │   │
│  │  ├── Install Poetry                                 │   │
│  │  ├── Install dependencies                           │   │
│  │  ├── Ruff lint (src/, tests/)                       │   │
│  │  ├── Mypy type check (src/)                         │   │
│  │  ├── Pytest with coverage                           │   │
│  │  └── Upload coverage to Codecov                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Job: extension-lint                                │   │
│  │  ├── Checkout                                       │   │
│  │  ├── ESLint Chrome extension                        │   │
│  │  └── ESLint Firefox extension                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Job: e2e (Future - #105)                           │   │
│  │  ├── Setup Playwright                               │   │
│  │  ├── Load Chrome extension                          │   │
│  │  └── Run E2E tests against GitHub Pages             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Quality Gates

| Gate | Tool | Threshold | Blocking? |
|------|------|-----------|-----------|
| Linting (Python) | Ruff | Zero errors | Yes |
| Type Checking | Mypy | Zero errors | Yes |
| Unit Tests | Pytest | 100% pass | Yes |
| Coverage | pytest-cov | 70% minimum | Yes |
| Linting (JS) | ESLint | Zero errors | Yes |
| E2E Tests | Playwright | 100% pass | Yes (future) |

### 2.3 Pre-commit Hooks

**File:** `.pre-commit-config.yaml`

Local quality gates run before every commit:

| Hook | Purpose |
|------|---------|
| trailing-whitespace | Remove trailing whitespace |
| end-of-file-fixer | Ensure files end with newline |
| check-yaml | Validate YAML syntax |
| check-json | Validate JSON syntax |
| check-added-large-files | Prevent accidental large file commits |
| detect-private-key | Prevent secret leakage |
| ruff | Python linting with auto-fix |
| mypy | Python type checking |
| gitleaks | Secret scanning |

**Installation:**
```bash
poetry add --group dev pre-commit
poetry run pre-commit install
```

---

## 3. Deployment Pipeline

### 3.1 Lambda Deployment

**Script:** `deploy.sh`

```
┌─────────────────────────────────────────────────────────────┐
│                    Lambda Deployment                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Package Source                                          │
│     └── Zip src/*.py (Naked Python - no dependencies)       │
│                                                             │
│  2. Upload to AWS                                           │
│     └── aws lambda update-function-code                     │
│                                                             │
│  3. Verify Deployment                                       │
│     └── aws lambda get-function (check LastModified)        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Key Design Decision (ADR 0211):** Lambda uses "Naked Python" architecture - no pip dependencies bundled. Only boto3 (pre-installed in Lambda runtime) is used. This keeps deployment zip under 1MB and cold starts fast.

### 3.2 Extension Deployment

**Script:** `tools/build_release.py`

Creates release ZIPs for browser stores:
- `aletheia-chrome-v{version}.zip`
- `aletheia-firefox-v{version}.zip`

### 3.3 Infrastructure Provisioning

**Script:** `provision.sh`

Creates AWS resources:
- DynamoDB table (AletheiaState)
- IAM Role (aletheia-lambda-role)
- Lambda function (aletheia-handler)
- CloudFront distribution (with WAF)

---

## 4. Environment Management

### 4.1 Environments

| Environment | Purpose | Lambda State |
|-------------|---------|--------------|
| Production | Live users | Concurrency enabled |
| Development | Local testing | Concurrency = 0 (disabled) |

### 4.2 Lambda Cost Control

**Scripts:** `tools/aws/lambda-*.sh`

```bash
./tools/aws/lambda-on.sh      # Enable Lambda (remove concurrency limit)
./tools/aws/lambda-off.sh     # Disable Lambda (set concurrency=0)
./tools/aws/lambda-status.sh  # Check current state
```

**Rule:** Lambda should be OFF when not actively testing to prevent unexpected Bedrock costs.

### 4.3 Environment Variables

| Variable | Purpose | Where Set |
|----------|---------|-----------|
| `AWS_REGION` | AWS region | Lambda config |
| `DYNAMODB_TABLE` | State table name | Lambda config |
| `TEST_BASE_URL` | E2E test target | GitHub Actions / local |

---

## 5. Monitoring & Observability

### 5.1 Current State

| Capability | Status | Tool |
|------------|--------|------|
| CI/CD status | ✅ Implemented | GitHub Actions badges |
| Code coverage | ✅ Implemented | Codecov |
| Lambda logs | ✅ Available | CloudWatch Logs |
| Request tracing | ⚪ Planned | X-Ray (#7) |
| Cost monitoring | ⚪ Planned | CloudWatch Billing |

### 5.2 Badges (README.md)

```markdown
![CI](https://github.com/martymcenroe/Aletheia/actions/workflows/ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/martymcenroe/Aletheia/branch/main/graph/badge.svg)](https://codecov.io/gh/martymcenroe/Aletheia)
```

---

## 6. Security

### 6.1 Supply Chain

| Control | Implementation |
|---------|----------------|
| Dependency pinning | Poetry lockfile |
| Vulnerability scanning | Dependabot (planned) |
| Secret scanning | Gitleaks pre-commit hook |

### 6.2 Deployment Security

| Control | Implementation |
|---------|----------------|
| IAM least privilege | aletheia-lambda-role scoped to DynamoDB + Bedrock |
| No secrets in code | Environment variables only |
| WAF protection | CloudFront + AWS WAF (#95) |

---

## 7. Tooling Summary

| Category | Tool | Version |
|----------|------|---------|
| Package Manager | Poetry | 1.7+ |
| Linter (Python) | Ruff | 0.1.9+ |
| Type Checker | Mypy | 1.8+ |
| Test Runner | Pytest | 8.0+ |
| Coverage | pytest-cov | 4.0+ |
| Linter (JS) | ESLint | 8.0+ |
| E2E Testing | Playwright | 1.40+ |
| Pre-commit | pre-commit | 3.6+ |
| Secret Scanning | Gitleaks | 8.18+ |

---

## 8. Future Enhancements (Tier 2/3)

| Enhancement | Priority | Issue |
|-------------|----------|-------|
| Dependabot auto-updates | High | TBD |
| Allure test reporting | Medium | TBD |
| Visual regression testing | Medium | TBD |
| Lambda cold start benchmarks | Medium | #137 |
| Contract testing (Pact) | Low | TBD |
| Mutation testing | Low | TBD |

---

## 9. References

- ADR 0211: Naked Python Architecture
- Issue #95: Security Hardening (WAF)
- Issue #105: Test Infrastructure
- Architecture Review: 2026-01-04 Session Log
