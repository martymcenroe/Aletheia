"""
Observability Module - AWS X-Ray Tracing and CloudWatch Metrics.

Issue #7: Add observability and tracing to Lambda functions.
See: docs/1007-observability.md

PRIVACY RULES (STRICT):
- NEVER log prompt or completion text
- NEVER log user input or URLs
- ONLY log: tokens_used, model_id, latency_ms, status_code, error_type

Safe metadata:
- tokens_used (int)
- model_id (str)
- latency_ms (int)
- status_code (int)
- error_type (str, if applicable)
"""

import logging
import os
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
        logger.debug(f"X-Ray annotation failed (non-fatal): {e}")


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
        logger.warning(f"Failed to log CloudWatch metrics (non-fatal): {e}")


# Initialize X-Ray on module import (Lambda cold start)
init_xray()
