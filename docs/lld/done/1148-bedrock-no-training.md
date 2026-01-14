# 1148 - Bedrock No-Training Verification (Compliance-as-Code)

**Issue:** #148
**Status:** Implemented
**Created:** 2026-01-07

## Overview

Implements continuous verification that our AWS Bedrock configuration complies with our privacy commitment: "AWS Bedrock does not use your data to train AI models."

## Problem Statement

Our privacy policy promises we don't train on user data. We need to:
1. Verify this claim is documented in our privacy policy
2. Verify no training APIs are called in our codebase
3. Verify our Bedrock configuration doesn't enable logging/training

## Solution: Compliance-as-Code

Two-tier test suite integrated into CI:

### Tier 1: Static Tests (Every PR)

No AWS credentials required. Runs on every PR.

| Test | What it Verifies |
|------|------------------|
| `test_no_bedrock_training_apis_in_src` | No `CreateCustomModel`, `CreateModelCustomizationJob`, or `PutModelInvocationLoggingConfiguration` in Python code |
| `test_no_bedrock_training_apis_in_extensions` | No training APIs in extension JavaScript |
| `test_privacy_docs_contain_no_training_statement` | index.html contains "AWS Bedrock does not train" statement |

### Tier 2: Live Audit (Main + Nightly)

Requires AWS credentials. Runs on push to main and nightly schedule.

| Test | What it Verifies |
|------|------------------|
| `test_bedrock_logging_disabled` | Bedrock invocation logging is not enabled |
| `test_bedrock_no_custom_models` | No fine-tuned models exist in the account |
| `test_bedrock_no_active_customization_jobs` | No training jobs are running |

## Implementation

### Files Created

- `tests/compliance/__init__.py` - Package marker
- `tests/compliance/test_static_compliance.py` - Static tests (no creds)
- `tests/compliance/test_live_audit.py` - Live tests (requires creds)

### Files Modified

- `pyproject.toml` - Added `audit` pytest marker
- `.github/workflows/ci.yml` - Added nightly schedule and compliance-audit job

### CI Configuration

```yaml
# PRs: Run all tests EXCEPT audit
poetry run pytest tests/ -v -m "not audit"

# Main + Nightly: Run ONLY audit tests with AWS creds
poetry run pytest tests/compliance/ -v -m audit
```

### Pytest Markers

```toml
[tool.pytest.ini_options]
markers = [
    "audit: compliance tests requiring AWS credentials (runs nightly)",
]
```

## Security Considerations

- AWS secrets are ONLY exposed to the `compliance-audit` job
- `compliance-audit` job ONLY runs on push to main or schedule
- PR jobs NEVER have access to AWS secrets
- Tests skip gracefully if credentials are unavailable

## Testing

```bash
# Run static tests (no creds needed)
poetry run pytest tests/compliance/test_static_compliance.py -v

# Run live tests (needs AWS creds)
poetry run pytest tests/compliance/test_live_audit.py -v

# Run only audit-marked tests
poetry run pytest tests/compliance/ -v -m audit

# Exclude audit tests (PR mode)
poetry run pytest tests/ -v -m "not audit"
```

## References

- [AWS Bedrock FAQ - Security & Privacy](https://aws.amazon.com/bedrock/faqs/#Security_and_Privacy)
- Privacy Audit: `AgentOS:audits/0802-privacy-audit`
