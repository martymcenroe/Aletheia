"""
Root-level pytest fixtures.

Issue #246: Add audit_logger fixture for adversarial test logging.
See: docs/lld/active/1246-adversarial-test-logging.md
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Callable
from unittest.mock import MagicMock

import pytest

# Ensure src/ is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Audit log group for CloudWatch
AUDIT_LOG_GROUP = "/aletheia/adversarial-audit"


@pytest.fixture(scope="session")
def audit_logger() -> Callable[[dict], None]:
    """
    CloudWatch logger for adversarial test audit trail.

    In CI/local: Writes to tmp/adversarial-audit.jsonl (no AWS required)
    In production audit: Writes to CloudWatch Logs

    Usage:
        audit_logger({"action": "adversarial_test", ...})
    """
    use_cloudwatch = os.environ.get("ADVERSARIAL_AUDIT_CLOUDWATCH", "").lower() == "true"

    if use_cloudwatch:
        # Production audit mode: write to CloudWatch
        import boto3

        client = boto3.client(
            "logs", region_name=os.environ.get("AWS_REGION", "us-east-1")
        )

        # Ensure log group exists
        try:
            client.create_log_group(logGroupName=AUDIT_LOG_GROUP)
        except client.exceptions.ResourceAlreadyExistsException:
            pass

        # Create log stream for this run
        stream_name = f"audit-{time.strftime('%Y%m%d-%H%M%S')}"
        client.create_log_stream(
            logGroupName=AUDIT_LOG_GROUP, logStreamName=stream_name
        )

        sequence_token = None

        def log_to_cloudwatch(entry: dict) -> None:
            nonlocal sequence_token
            kwargs = {
                "logGroupName": AUDIT_LOG_GROUP,
                "logStreamName": stream_name,
                "logEvents": [
                    {"timestamp": int(time.time() * 1000), "message": json.dumps(entry)}
                ],
            }
            if sequence_token:
                kwargs["sequenceToken"] = sequence_token
            response = client.put_log_events(**kwargs)
            sequence_token = response.get("nextSequenceToken")

        return log_to_cloudwatch
    else:
        # Local/CI mode: write to file
        log_dir = Path(__file__).parent.parent / "tmp"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "adversarial-audit.jsonl"

        # Clear previous run's log
        if log_file.exists():
            log_file.unlink()

        def log_to_file(entry: dict) -> None:
            entry["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            with open(log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")

        return log_to_file


@pytest.fixture
def lambda_invoker():
    """
    Fixture to invoke Lambda handler directly with mocked context.

    Returns a function that takes (text, dom_context) and returns response dict.
    The Lambda is unaware it is being tested - uses real guardrails.
    """
    from src.lambda_function import lambda_handler

    def invoke(text: str, dom_context: str = "") -> dict:
        """
        Invoke Lambda handler with adversarial payload.

        Args:
            text: The text to analyze (may be adversarial)
            dom_context: Optional DOM context

        Returns:
            Dict with statusCode, body (parsed JSON), and request_id
        """
        # Build Lambda event
        event = {
            "httpMethod": "POST",
            "body": json.dumps({"text": text, "domContext": dom_context}),
            "headers": {"Content-Type": "application/json"},
        }

        # Mock Lambda context
        context = MagicMock()
        context.aws_request_id = f"test-{time.time_ns()}"
        context.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789:function:aletheia-test"
        )

        # Invoke handler - Lambda is unaware it's being tested
        response = lambda_handler(event, context)

        # Parse body if present
        body = {}
        if response.get("body"):
            try:
                body = json.loads(response["body"])
            except json.JSONDecodeError:
                body = {"raw": response["body"]}

        return {
            "statusCode": response.get("statusCode", 500),
            "body": body,
            "request_id": context.aws_request_id,
        }

    return invoke
