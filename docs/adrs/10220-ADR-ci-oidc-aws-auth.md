# 10220 - ADR: CI-to-AWS Authentication via GitHub OIDC

**Status:** Implemented
**Date:** 2026-07-08
**Categories:** Security, Infrastructure, Authentication

## 1. Context

Two CI jobs in `.github/workflows/ci.yml` needed to call AWS:

- **`compliance-audit`** (push + nightly cron) — read-only Bedrock/STS calls that verify model configuration.
- **`deploy-infra`** (formerly on push-to-main) — ran `provision.sh`, requiring broad write access.

Both authenticated with **static IAM access keys** stored as the GitHub Actions secrets `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`. Those keys belonged to the `aletheia-developer` IAM user, which holds **`AdministratorAccess`**. Three problems followed:

1. **Long-lived, high-blast-radius credentials in a public repo's secrets.** Admin keys that never expire are the worst-case secret to leak; Aletheia is a public repository.
2. **Silent breakage.** When the keys expired/were rotated, every run's `Configure AWS Credentials` step failed, turning the `main` badge red on every nightly run (#773) — an interviewer flagged the red badge.
3. **CI held deploy power it should not have.** `deploy-infra` auto-ran `provision.sh` on merge, contradicting the standing rule that deploys are manual (`provision.sh` is run locally; merging to main does not deploy).

GitHub Actions supports OpenID Connect (OIDC): a workflow can request a short-lived, signed identity token and exchange it for temporary AWS credentials via `sts:AssumeRoleWithWebIdentity`, with no stored secret. This is the current GitHub- and AWS-recommended pattern for CI-to-cloud auth.

## 2. Decision

**CI authenticates to AWS via GitHub OIDC using short-lived federated tokens and least-privilege IAM roles scoped to this repository. No long-lived AWS access keys live in CI. CI is read-only; deploys remain a manual, human-run action (`provision.sh`).**

Concretely:

1. **One GitHub OIDC identity provider** in account `383687041805`: URL `token.actions.githubusercontent.com`, audience `sts.amazonaws.com`.
2. **Per-purpose least-privilege IAM roles**, each with a trust policy that permits only `sts:AssumeRoleWithWebIdentity` from this repo:
   ```json
   "Condition": {
     "StringEquals": { "token.actions.githubusercontent.com:aud": "sts.amazonaws.com" },
     "StringLike":   { "token.actions.githubusercontent.com:sub": "repo:martymcenroe/Aletheia:*" }
   }
   ```
   Reference implementation: **`AletheiaCIAuditRole`** — trust as above, permission policy limited to exactly the three read-only actions the audit tests call (`bedrock:GetModelInvocationLoggingConfiguration`, `bedrock:ListCustomModels`, `bedrock:ListModelCustomizationJobs`). `sts:GetCallerIdentity` needs no grant.
3. **Workflow jobs** that touch AWS declare `permissions: id-token: write` and use `aws-actions/configure-aws-credentials@v6` with `role-to-assume: <role-arn>` (no `aws-access-key-id` inputs).
4. **No deploy role in CI.** Deploys stay manual. `deploy-infra`/`post-deploy-smoke` were removed from CI (#775); if CI deploy is ever wanted, it gets its own ADR and a scoped deploy role — never the admin identity.

Implemented across #773 (compliance-audit → OIDC) and #775 (remove the static-key deploy jobs). The static-key secrets are to be deleted once unreferenced.

## 3. Alternatives Considered

### Option A: GitHub OIDC + least-privilege per-repo roles — SELECTED

Short-lived tokens, no stored secrets, per-job least privilege, repo-scoped trust.

**Pros:** No long-lived credentials to leak or expire; least privilege per job; auditable (CloudTrail shows `AssumeRoleWithWebIdentity` with the GitHub subject); no rotation toil; strong story for a security review.
**Cons:** Requires an OIDC provider + IAM role per purpose (one-time provisioning); a too-broad `sub` condition would let other repos assume the role (mitigated below).

### Option B: Refresh the static access keys — REJECTED

Set new `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` secrets.

**Cons:** Keeps long-lived admin credentials in a public repo's secrets; the same expiry breaks CI again on a schedule; no least privilege; rotation is manual and recurring. This is the exact failure mode #773 documents.

### Option C: OIDC with a broad deploy role in CI — REJECTED

Give CI an OIDC role able to run `provision.sh` (Lambda/IAM/AIP writes).

**Cons:** A CI-assumable role with deploy/IAM-write power is a large attack surface — anyone able to push a workflow change (or compromise an Action) could rewrite production infrastructure. Deploys are deliberately manual; CI does not need this. Rejected in favor of read-only CI.

## 4. Security Risk Analysis

| Risk | Impact | Likelihood | Severity | Mitigation |
|------|--------|------------|----------|------------|
| Trust-policy `sub` too broad (e.g. `repo:*`) lets another repo assume the role | Med (unauthorized read of Bedrock config) | Low | 2 - Low | `sub` pinned to `repo:martymcenroe/Aletheia:*`; review trust policy on every new role. Can tighten to a specific branch/environment if a role's scope warrants. |
| Permission creep — a role accrues write actions over time | Med | Med | 2 - Low | Roles start with the exact actions a job calls (3 read-only for the audit role); additions require a PR touching the role's inline policy, visible at review. |
| Admin static keys still exist on `aletheia-developer` (used locally) | High if leaked | Low | 2 - Low | Out of CI now; tracked for rotation. CI no longer references them (secrets to be deleted). |
| `provision.sh` re-applies env and could clobber a verified secret on deploy | High (silent origin-lockdown bypass) | Low | 3 - Low | Tracked in #779 (fail-fast on empty secret + post-deploy assertion). Independent of OIDC but part of the same secrets-hygiene posture. |
| Workflow-file change needed to wire/adjust OIDC can't be pushed by the agent PAT | None (by design) | n/a | 1 | The fine-grained PAT deliberately lacks `workflow` scope (AZ ADR-0216 §1); such changes land via the gpg-gated classic-PAT Contents-API path — a human checkpoint for CI-auth changes, which is desirable. |

**Residual Risk:** Minimal. The remaining long-lived credential (the `aletheia-developer` key, used only for local tooling) is outside CI and slated for rotation.

## 5. Consequences

### Positive
- No long-lived AWS credentials anywhere in CI; nothing to rotate or expire.
- Least privilege per job; CI is read-only and cannot deploy.
- Auditable via CloudTrail (`AssumeRoleWithWebIdentity` carries the GitHub `sub`).
- Removes the recurring red-badge failure mode (#773) at the root.
- Concrete, demonstrable control for a security/CISO review.

### Negative
- Each AWS-touching purpose needs an OIDC role provisioned once (IAM change).
- Workflow-file edits that wire OIDC require the classic-PAT landing path (AZ ADR-0216), i.e. a human passphrase — deliberate, not incidental.

### Neutral
- Deploys are unchanged: still manual via `provision.sh`. This ADR does not grant CI deploy power.
- Verification of the deployed posture is covered by the `aletheia_verify_config.sh` (maintained in a private tooling repo) checks (origin secret, AUTH_ENABLED, budget/kill-switch).

## 6. References

- #773 — nightly CI red badge; compliance-audit → OIDC.
- #775 — remove `deploy-infra`/`post-deploy-smoke` (retire the last static-key path).
- #779 — provision.sh env re-apply / origin-secret clobber hardening.
- ADR-10216 — CloudFlare migration + origin shared-secret (adjacent edge-auth posture).
- AssemblyZero ADR-0216 — in-process classic-PAT decryption (why workflow-file changes are human-gated).
- `aws-actions/configure-aws-credentials` OIDC docs; GitHub "Configuring OpenID Connect in Amazon Web Services".
