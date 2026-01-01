"""
Lambda Function - Naked Python Orchestrator.

Replaces LangGraph/LangChain with pure boto3 for faster cold starts.
See: docs/1113-naked-python-architecture.md

Pipeline: Input → Validate → Denylist → Semantic → Persist → Generate → Stream
"""
import hashlib
import json
import logging
import os
import time
from typing import Any, Iterator

import boto3
from botocore.exceptions import ClientError

from .guardrails.denylist import check_denylist, load_denylist
from .guardrails.semantic import SemanticGuardrail

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuration
DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE", "aletheia-state")
BEDROCK_MODEL_ID = os.environ.get(
    "BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0"
)
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# Lazy-initialized clients (warm start optimization)
_dynamodb_client = None
_bedrock_client = None
_semantic_guardrail = None


def get_dynamodb_client():
    """Lazy-initialize DynamoDB client."""
    global _dynamodb_client
    if _dynamodb_client is None:
        _dynamodb_client = boto3.client("dynamodb", region_name=AWS_REGION)
    return _dynamodb_client


def get_bedrock_client():
    """Lazy-initialize Bedrock client."""
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    return _bedrock_client


def get_semantic_guardrail():
    """Lazy-initialize SemanticGuardrail."""
    global _semantic_guardrail
    if _semantic_guardrail is None:
        _semantic_guardrail = SemanticGuardrail(region_name=AWS_REGION)
    return _semantic_guardrail


def validate_input(event: dict) -> tuple[bool, str | None]:
    """
    Validate event payload. Returns (is_valid, error_message).

    See: docs/1113-naked-python-architecture.md Section 8.1
    """
    # Existence
    if "text" not in event:
        return False, "Missing required field: text"

    # Type
    if not isinstance(event["text"], str):
        return False, "Field 'text' must be string"

    # Empty/whitespace (Aletheia should not process empty inputs)
    if not event["text"].strip():
        return False, "Field 'text' cannot be empty"

    # Length (prevent payload attacks)
    if len(event["text"]) > 20_000:
        event["text"] = event["text"][:20_000]  # Truncate silently

    # Encoding (reject malformed)
    try:
        event["text"].encode("utf-8")
    except UnicodeError:
        return False, "Invalid text encoding"

    return True, None


def generate_thread_id(event: dict) -> str:
    """
    Generate a thread ID for DynamoDB persistence.

    TODO: Issue #116 - Replace with authenticated user ID from LinkedIn Auth.

    Current strategy: hash of URL + text prefix for session-based identity.
    """
    url = event.get("url", "unknown")
    text_prefix = event.get("text", "")[:50]
    raw = f"{url}:{text_prefix}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def save_state(thread_id: str, data: dict) -> None:
    """
    Persist context to DynamoDB.

    See: docs/1113-naked-python-architecture.md Section 7.2
    """
    client = get_dynamodb_client()
    timestamp = str(int(time.time() * 1000))

    item = {
        "thread_id": {"S": thread_id},
        "checkpoint_id": {"S": timestamp},
        "input": {"S": data.get("text", "")},
        "url": {"S": data.get("url", "")},
        "safety_score": {"S": json.dumps(data.get("safety_score", {}))},
    }

    # TODO: Issue #116 - Add user_id when LinkedIn Auth is implemented
    if data.get("userId"):
        item["user_id"] = {"S": data["userId"]}

    try:
        client.put_item(TableName=DYNAMODB_TABLE, Item=item)
        logger.info(f"Saved state: thread_id={thread_id}")
    except ClientError as e:
        # Log but don't fail the request - persistence is not critical path
        logger.error(f"DynamoDB error: {e.response['Error']['Code']}")
        raise


def generate(prompt: str, context: str = "") -> Iterator[str]:
    """
    Stream response chunks from Bedrock.

    See: docs/1113-naked-python-architecture.md Section 7.2
    """
    client = get_bedrock_client()

    system_prompt = (
        "You are Aletheia, a helpful assistant that provides context and "
        "historical information about words and phrases. Be educational, "
        "respectful, and avoid reproducing harmful content. "
        "If the term has problematic origins, explain them sensitively."
    )

    if context:
        system_prompt += f"\n\nContext from the page: {context}"

    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Please explain the origin and meaning of: {prompt}",
                    }
                ],
            }
        ],
    }

    response = client.invoke_model_with_response_stream(
        modelId=BEDROCK_MODEL_ID, body=json.dumps(payload)
    )

    for event in response.get("body", []):
        chunk = event.get("chunk")
        if chunk:
            chunk_data = json.loads(chunk.get("bytes", b"{}"))
            if chunk_data.get("type") == "content_block_delta":
                delta = chunk_data.get("delta", {})
                if delta.get("type") == "text_delta":
                    yield delta.get("text", "")


def run_guardrails(
    text: str, denylist: set[str] | None = None
) -> tuple[bool, str | None, dict]:
    """
    Run guardrail pipeline: Denylist → Semantic.

    CRITICAL: Sequential execution is mandatory. See LLD Section 6.

    Args:
        text: Input text to check.
        denylist: Optional denylist for testing (dependency injection).

    Returns:
        (is_safe, block_reason, metadata)
    """
    # Step 1: Denylist check (fast, deterministic)
    denylist_result = check_denylist(text, denylist)
    if denylist_result["blocked"]:
        return False, "Content blocked by safety filter", {"layer": "denylist"}

    # Step 2: Semantic check (LLM-based, slower)
    # MUST run after denylist, MUST block before generation
    semantic = get_semantic_guardrail()
    semantic_result = semantic.check_safety(text)
    if not semantic_result["is_safe"]:
        return (
            False,
            f"Content blocked: {semantic_result['reason']}",
            {"layer": "semantic", "scores": semantic_result.get("scores", {})},
        )

    return True, None, {"layer": "passed", "scores": semantic_result.get("scores", {})}


def lambda_handler(
    event: dict, context: Any, denylist: set[str] | None = None
) -> dict:
    """
    Main entry point. Orchestrates validation → guards → persist → generate.

    See: docs/1113-naked-python-architecture.md

    Args:
        event: Lambda event payload.
        context: Lambda context object.
        denylist: Optional denylist for testing (dependency injection).

    Returns:
        API Gateway response dict.
    """
    try:
        # Parse body if coming from API Gateway
        if "body" in event:
            body = (
                json.loads(event["body"])
                if isinstance(event["body"], str)
                else event["body"]
            )
        else:
            body = event

        # 1. Validation
        valid, error = validate_input(body)
        if not valid:
            return {"statusCode": 400, "body": json.dumps({"error": error})}

        text = body["text"]

        # 2. Guardrails (MUST be sequential: Denylist → Semantic)
        is_safe, block_reason, metadata = run_guardrails(text, denylist)
        if not is_safe:
            return {"statusCode": 403, "body": json.dumps({"blocked": block_reason})}

        # 3. Generate thread ID for persistence
        # TODO: Issue #116 - Use authenticated user ID
        thread_id = generate_thread_id(body)

        # 4. Persist to DynamoDB
        save_state(
            thread_id,
            {
                "text": text,
                "url": body.get("url", ""),
                "userId": body.get("userId"),  # May be None pre-#116
                "safety_score": metadata.get("scores", {}),
            },
        )

        # 5. Generate response
        context_text = body.get("domContext", "")
        response_chunks = []
        for chunk in generate(text, context_text):
            response_chunks.append(chunk)

        full_response = "".join(response_chunks)

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {"response": full_response, "thread_id": thread_id}
            ),
        }

    except ClientError as e:
        # AWS SDK errors (IAM, throttling, etc.)
        error_code = e.response["Error"]["Code"]
        logger.error(f"AWS Error: {error_code}")
        return {"statusCode": 500, "body": json.dumps({"error": "Service error"})}

    except Exception as e:
        # Catch-all: NEVER proceed to generation on unhandled error
        logger.error(f"CRITICAL: Unhandled exception: {type(e).__name__}: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": "Internal error"})}


# Load denylist on cold start
load_denylist()
