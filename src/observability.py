"""
Observability Module - AWS X-Ray Tracing and CloudWatch Metrics.

Issue #7: Add observability and tracing to Lambda functions.
Issue #369: Add EMF structured logging for CloudWatch Usage Dashboard.
See: docs/1007-observability.md

PRIVACY RULES (STRICT):
- NEVER log prompt or completion text
- NEVER log user input or URLs
- ONLY log: tokens_used, model_id, latency_ms, status_code, error_type
- NEVER put user_id in metric dimensions (REQ-18)

Safe metadata:
- tokens_used (int)
- model_id (str)
- latency_ms (int)
- status_code (int)
- error_type (str, if applicable)
"""

import json as _json
import logging
import os
import time
from typing import Any

# X-Ray SDK imports
try:
    from aws_xray_sdk.core import patch_all, xray_recorder

    XRAY_AVAILABLE = True
except ImportError:
    XRAY_AVAILABLE = False
    xray_recorder = None  # type: ignore

# CloudWatch client (lazy-initialized)
_cloudwatch_client = None

logger = logging.getLogger(__name__)

# Sampling configuration (5% per LLD)
XRAY_SAMPLING_RATE = 0.05

# CloudWatch namespace for custom metrics
CLOUDWATCH_NAMESPACE = "Aletheia"


def init_xray() -> None:
    """
    Initialize X-Ray SDK with boto3 patching.

    Call this at module load time (cold start) to enable automatic
    tracing of AWS SDK calls.

    Per LLD: patch_all() wraps boto3 clients for automatic tracing.
    """
    if not XRAY_AVAILABLE:
        logger.warning("aws-xray-sdk not available, tracing disabled")
        return

    # Patch all supported libraries (boto3, requests, etc.)
    patch_all()

    # Configure sampling (5% per LLD requirement)
    # Note: Active tracing is set at Lambda config level,
    # SDK sampling is additional layer
    xray_recorder.configure(sampling=True)

    logger.info("X-Ray tracing initialized")


def trace_bedrock_call(
    model_id: str,
    tokens_used: int | None = None,
    latency_ms: int | None = None,
    status: str = "success",
    error_type: str | None = None,
) -> None:
    """
    Add safe annotations to current X-Ray subsegment for Bedrock calls.

    PRIVACY: Only logs safe metadata. NEVER logs prompt or completion text.

    Args:
        model_id: The Bedrock model ID used.
        tokens_used: Total tokens consumed (if available).
        latency_ms: Time taken for the Bedrock call.
        status: "success", "error", or "fallback".
        error_type: Type of error if status is "error".
    """
    if not XRAY_AVAILABLE or xray_recorder is None:
        return

    try:
        # Get current subsegment (created by patch_all() for boto3 calls)
        # If no subsegment exists, annotations are silently ignored
        segment = xray_recorder.current_subsegment()
        if segment is None:
            return

        # Safe annotations (indexed, searchable in X-Ray console)
        segment.put_annotation("model_id", model_id)
        segment.put_annotation("status", status)

        # Safe metadata (not indexed, but visible in trace)
        if tokens_used is not None:
            segment.put_metadata("tokens_used", tokens_used, namespace="bedrock")

        if latency_ms is not None:
            segment.put_metadata("latency_ms", latency_ms, namespace="bedrock")

        if error_type:
            segment.put_annotation("error_type", error_type)

        # STRICT BAN: These are FORBIDDEN
        # segment.put_metadata('prompt', prompt)  # NEVER
        # segment.put_metadata('response', response)  # NEVER
        # segment.put_metadata('input', input)  # NEVER
        # segment.put_annotation('text', text)  # NEVER

    except Exception as e:
        # Tracing should never break the main flow
        logger.debug(f"X-Ray annotation failed (non-fatal): {e.__class__.__name__}")


def create_subsegment(name: str) -> Any:
    """
    Create a named subsegment for detailed tracing.

    Usage:
        with create_subsegment('guardrails_check') as subseg:
            result = run_guardrails(text)
            if subseg:
                subseg.put_annotation('layer', result['layer'])

    Returns a context manager that yields the subsegment (or None if unavailable).
    """
    if not XRAY_AVAILABLE or xray_recorder is None:
        # Return a no-op context manager
        from contextlib import nullcontext

        return nullcontext()

    return xray_recorder.in_subsegment(name)


def get_cloudwatch_client():
    """Lazy-initialize CloudWatch client."""
    global _cloudwatch_client
    if _cloudwatch_client is None:
        import boto3

        region = os.environ.get("AWS_REGION", "us-east-1")
        _cloudwatch_client = boto3.client("cloudwatch", region_name=region)
    return _cloudwatch_client


def log_bedrock_metrics(
    tokens_used: int,
    model_id: str,
    latency_ms: int | None = None,
) -> None:
    """
    Log custom CloudWatch metrics for Bedrock usage.

    Metrics are used for cost tracking and performance monitoring.
    NO PII is ever included.

    Args:
        tokens_used: Total tokens consumed.
        model_id: The Bedrock model ID used.
        latency_ms: Optional latency in milliseconds.
    """
    try:
        client = get_cloudwatch_client()

        metric_data = [
            {
                "MetricName": "BedrockTokensUsed",
                "Value": tokens_used,
                "Unit": "Count",
                "Dimensions": [{"Name": "ModelId", "Value": model_id}],
            }
        ]

        if latency_ms is not None:
            metric_data.append(
                {
                    "MetricName": "BedrockLatency",
                    "Value": latency_ms,
                    "Unit": "Milliseconds",
                    "Dimensions": [{"Name": "ModelId", "Value": model_id}],
                }
            )

        client.put_metric_data(Namespace=CLOUDWATCH_NAMESPACE, MetricData=metric_data)

        logger.debug(f"Logged metrics: tokens={tokens_used}, model={model_id}")

    except Exception as e:
        # Metrics logging should never break the main flow
        logger.warning(f"Failed to log CloudWatch metrics (non-fatal): {e.__class__.__name__}")


# --------------------------------------------------------------------------- #
# Issue #369: EMF Structured Logging for CloudWatch Usage Dashboard
# --------------------------------------------------------------------------- #

# EMF namespace (separate from the PutMetricData namespace above)
EMF_NAMESPACE = "Aletheia/API"

# Valid tiers for dimension safety (prevents injection)
_VALID_TIERS = {"free", "subscriber", "admin", "pro", "enterprise"}


def _build_emf_payload(
    metrics: list[dict[str, str]],
    dimensions: list[list[str]],
    values: dict[str, Any],
) -> dict[str, Any]:
    """Build a CloudWatch EMF payload.

    Args:
        metrics: List of {"Name": ..., "Unit": ...} metric specs.
        dimensions: List of dimension key groups, e.g. [["Tier"]].
        values: Dict of metric/dimension values to include in payload.

    Returns:
        EMF-formatted dict ready for JSON serialization.
    """
    payload: dict[str, Any] = {
        "_aws": {
            "Timestamp": int(time.time() * 1000),
            "CloudWatchMetrics": [
                {
                    "Namespace": EMF_NAMESPACE,
                    "Dimensions": dimensions,
                    "Metrics": metrics,
                }
            ],
        }
    }
    payload.update(values)
    return payload


def _emit_emf_log(payload: dict[str, Any]) -> None:
    """Write EMF-formatted JSON to stdout for CloudWatch Logs ingestion.

    CloudWatch Logs agent parses the _aws block and extracts metrics
    automatically. No HTTP call required.
    """
    print(_json.dumps(payload, separators=(",", ":")))


def _safe_tier(tier: str) -> str:
    """Validate tier value to prevent dimension injection."""
    return tier if tier in _VALID_TIERS else "unknown"


def emit_request_metric(tier: str) -> None:
    """Emit RequestCount metric via EMF with Tier dimension.

    Issue #369 (REQ-1): Fail-open — catches all exceptions.

    Args:
        tier: User subscription tier (free/subscriber/admin).
    """
    try:
        payload = _build_emf_payload(
            metrics=[{"Name": "RequestCount", "Unit": "Count"}],
            dimensions=[["Tier"]],
            values={"Tier": _safe_tier(tier), "RequestCount": 1},
        )
        _emit_emf_log(payload)
    except Exception as e:
        logger.warning(f"Metric emission failed (non-fatal): {e.__class__.__name__}")


def emit_cap_utilization_metric(
    tier: str, window: str, utilization_percent: float
) -> None:
    """Emit CapUtilization metric via EMF with Tier and Window dimensions.

    Issue #369 (REQ-2): Fail-open — catches all exceptions.

    Args:
        tier: User subscription tier.
        window: Rate limit window (hourly/daily/monthly).
        utilization_percent: Cap usage percentage 0-100.
    """
    try:
        payload = _build_emf_payload(
            metrics=[{"Name": "CapUtilization", "Unit": "Percent"}],
            dimensions=[["Tier", "Window"]],
            values={
                "Tier": _safe_tier(tier),
                "Window": window,
                "CapUtilization": utilization_percent,
            },
        )
        _emit_emf_log(payload)
    except Exception as e:
        logger.warning(f"Metric emission failed (non-fatal): {e.__class__.__name__}")


def emit_cap_denied_metric(tier: str) -> None:
    """Emit CapDenied metric via EMF when request rejected.

    Issue #369 (REQ-3): Fail-open — catches all exceptions.

    Args:
        tier: User subscription tier.
    """
    try:
        payload = _build_emf_payload(
            metrics=[{"Name": "CapDenied", "Unit": "Count"}],
            dimensions=[["Tier"]],
            values={"Tier": _safe_tier(tier), "CapDenied": 1},
        )
        _emit_emf_log(payload)
    except Exception as e:
        logger.warning(f"Metric emission failed (non-fatal): {e.__class__.__name__}")


def emit_bedrock_cost_metric(estimated_cost_usd: float) -> None:
    """Emit BedrockCostEstimate metric via EMF with USD value.

    Issue #369 (REQ-4): Fail-open — catches all exceptions.

    Args:
        estimated_cost_usd: Estimated cost in USD.
    """
    try:
        payload = _build_emf_payload(
            metrics=[{"Name": "BedrockCostEstimate", "Unit": "None"}],
            dimensions=[[]],
            values={"BedrockCostEstimate": estimated_cost_usd},
        )
        _emit_emf_log(payload)
    except Exception as e:
        logger.warning(f"Metric emission failed (non-fatal): {e.__class__.__name__}")


def emit_error_rate_metric(status_code: int) -> None:
    """Emit ErrorRate metric via EMF for 4xx/5xx responses.

    Issue #369 (REQ-5): Fail-open — catches all exceptions.

    Args:
        status_code: HTTP status code (4xx or 5xx).
    """
    try:
        payload = _build_emf_payload(
            metrics=[{"Name": "ErrorRate", "Unit": "Count"}],
            dimensions=[["StatusCode"]],
            values={"StatusCode": status_code, "ErrorRate": 1},
        )
        _emit_emf_log(payload)
    except Exception as e:
        logger.warning(f"Metric emission failed (non-fatal): {e.__class__.__name__}")


def emit_latency_metric(latency_ms: float) -> None:
    """Emit Latency metric via EMF in milliseconds.

    Issue #369 (REQ-6): Fail-open — catches all exceptions.

    Args:
        latency_ms: Response time in milliseconds.
    """
    try:
        payload = _build_emf_payload(
            metrics=[{"Name": "Latency", "Unit": "Milliseconds"}],
            dimensions=[[]],
            values={"Latency": latency_ms},
        )
        _emit_emf_log(payload)
    except Exception as e:
        logger.warning(f"Metric emission failed (non-fatal): {e.__class__.__name__}")


def log_anonymized_user(user_id: str) -> None:
    """Log anonymized user ID to CloudWatch Logs for pattern analysis.

    Issue #369 (REQ-14): Uses 12-char truncated SHA-256 hash.
    Logged as structured JSON for Logs Insights queries.

    Args:
        user_id: Raw user ID to anonymize and log.
    """
    try:
        from .auth.anonymize import anonymize_user_id

        anon_id = anonymize_user_id(user_id)
        logger.info(_json.dumps({"action": "request", "anon_user": anon_id}))
    except Exception as e:
        logger.warning(f"Anonymized user logging failed (non-fatal): {e.__class__.__name__}")


# Initialize X-Ray on module import (Lambda cold start)
init_xray()
