# Implementation Report: Issue #537

## Summary

Fix IAM Bedrock policy to use wildcard region for cross-region AIP invocations, and fix AIP source ARNs for INFERENCE_PROFILE-only models.

## Changes

| File | Change |
|------|--------|
| `provision.sh` | IAM Bedrock resources: `us-east-1` -> `*` for foundation models and inference profiles; AIP source ARNs: Haiku 4.5 / Opus 4.6 use system-defined inference profile, not foundation model |

## Root Cause

US system-defined inference profiles (`us.anthropic.claude-haiku-4-5-*`) route to the nearest US region — either us-east-1 or us-east-2. The IAM policy only allowed us-east-1, causing `AccessDeniedException` when Bedrock routed to us-east-2.

Similarly, Haiku 4.5 and Opus 4.6 are INFERENCE_PROFILE-only models — they cannot be wrapped via foundation model ARN, only via system-defined inference profile ARN.
