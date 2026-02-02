"""
Lambda Function - Naked Python Orchestrator.

Replaces LangGraph/LangChain with pure boto3 for faster cold starts.
See: docs/1113-naked-python-architecture.md

Pipeline: Input → Validate → Denylist → Semantic → Persist → Generate (Buffered)

Updated by Issue #124 to use Digital Etymologist persona with structured JSON output.
See: docs/1124-digital-etymologist.md

Updated by Issue #7 to add X-Ray tracing and CloudWatch metrics.
See: docs/1007-observability.md
"""
import hashlib
import json
import logging
import os
import time
from typing import Any

import boto3
from botocore.exceptions import ClientError

from .etymologist import HAIKU_MODEL_ID, AnalysisResult, analyze_term
from .guardrails.denylist import check_denylist, load_denylist
from .guardrails.semantic import (
    SemanticGuardrail,
    BLOCK_TYPE_HARD,
    BLOCK_TYPE_SOFT,
    BLOCK_TYPE_NONE,
)

# Issue #7: Observability tracing (imported after boto3 so patch_all works)
from .observability import create_subsegment, log_bedrock_metrics, trace_bedrock_call

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuration
DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE", "aletheia-state")
# Issue #124: Use Haiku for <3s latency requirement
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", HAIKU_MODEL_ID)
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# Issue #145: TTL for automatic data expiry (30 days)
TTL_SECONDS = 2592000

# Issue #310: Poetic resonance detection threshold
# When poetic_potential >= this value, "Explore Deeper Meaning" button appears
POETIC_THRESHOLD = 0.6

# Issue #295: Score display threshold and category mapping
SCORE_DISPLAY_THRESHOLD = 0.15
CATEGORY_DISPLAY_NAMES = {
    "None": "General Usage",
    "Archaic": "Archaic",
    "Provocative": "Provocative",
    "Neologism": "Neologism",
    "Hate": "Hate",  # Should never be displayed (403 blocks first)
}


def process_scores_for_display(scores: dict[str, float]) -> list[dict[str, Any]]:
    """
    Issue #295: Process raw scores into display-ready format.

    - Filter: Keep categories with score >= 15%
    - Round: Round to nearest 5%
    - Sort: Descending by score
    - Rename: "None" -> "General Usage"

    Returns list of {category: str, score: int} dicts.
    """
    if not scores:
        return []

    display_list = []
    for category, score in scores.items():
        if score >= SCORE_DISPLAY_THRESHOLD:
            # Round to nearest 5%
            rounded = round(score * 20) * 5  # 0.73 -> 15 -> 75%
            display_name = CATEGORY_DISPLAY_NAMES.get(category, category)
            display_list.append({
                "category": display_name,
                "score": rounded,
            })

    # Sort descending by score (cast for mypy)
    display_list.sort(key=lambda x: x["score"] if isinstance(x["score"], int) else 0, reverse=True)
    return display_list


# Lazy-initialized clients (warm start optimization)
_dynamodb_client = None
_bedrock_client = None
_semantic_guardrail = None


def get_dynamodb_client():
    """Lazy-initialize DynamoDB client.

    Supports DYNAMODB_ENDPOINT env var for local testing with DynamoDB Local.
    Issue #264: DynamoDB integration test fixtures.
    """
    global _dynamodb_client
    if _dynamodb_client is None:
        endpoint = os.environ.get("DYNAMODB_ENDPOINT")
        if endpoint:
            _dynamodb_client = boto3.client(
                "dynamodb", endpoint_url=endpoint, region_name=AWS_REGION
            )
        else:
            _dynamodb_client = boto3.client("dynamodb", region_name=AWS_REGION)
    return _dynamodb_client


def get_bedrock_client():
    """Lazy-initialize Bedrock client."""
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    return _bedrock_client


def get_semantic_guardrail():
    """
    Lazy-initialize SemanticGuardrail with shared Bedrock client.

    Issue #137: Pass shared client to eliminate duplicate client initialization
    (~774ms savings on cold start).
    """
    global _semantic_guardrail
    if _semantic_guardrail is None:
        _semantic_guardrail = SemanticGuardrail(
            region_name=AWS_REGION,
            bedrock_client=get_bedrock_client(),
        )
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

    Current strategy: hash of URL + text prefix for session-based identity.
    Future: Use authenticated user ID when available.
    """
    url = event.get("url", "unknown")
    text_prefix = event.get("text", "")[:50]
    raw = f"{url}:{text_prefix}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def save_state(thread_id: str, data: dict) -> None:
    """
    Persist context to DynamoDB with 30-day TTL.

    See: docs/1113-naked-python-architecture.md Section 7.2
    Issue #145: Added TTL for automatic data expiry.
    Issue #177: Added domContext field for surrounding paragraph storage.
    Issue #178: Added response field for AI etymology output storage.
    """
    client = get_dynamodb_client()
    now = int(time.time())
    timestamp = str(now * 1000)

    item = {
        "thread_id": {"S": thread_id},
        "checkpoint_id": {"S": timestamp},
        "input": {"S": data.get("text", "")},
        "url": {"S": data.get("url", "")},
        "safety_score": {"S": json.dumps(data.get("safety_score", {}))},
        "ttl": {"N": str(now + TTL_SECONDS)},  # Issue #145: Auto-expire after 30 days
    }

    # Issue #177: Store surrounding paragraph (domContext)
    # Default to empty string if missing; truncate to 100KB for DynamoDB safety
    dom_context = data.get("domContext", "") or ""
    item["domContext"] = {"S": dom_context[:100000]}

    # Issue #178: Store AI response (signal, gem, context)
    # May be None if generation failed - serialize as JSON for flexibility
    response_data = data.get("response")
    if response_data is not None:
        item["response"] = {"S": json.dumps(response_data)}
    else:
        item["response"] = {"S": "null"}

    # Store user_id if available from authenticated session
    if data.get("userId"):
        item["user_id"] = {"S": data["userId"]}

    try:
        client.put_item(TableName=DYNAMODB_TABLE, Item=item)
        logger.info(f"Saved state: thread_id={thread_id}")
    except ClientError as e:
        # Log but don't fail the request - persistence is not critical path
        logger.error(f"DynamoDB error: {e.response['Error']['Code']}")
        raise


def generate_etymology(word: str, context: str = "") -> AnalysisResult:
    """
    Generate etymology analysis using Digital Etymologist persona.

    Uses buffered Bedrock invocation (not streaming) for reliable JSON extraction.
    See: docs/1124-digital-etymologist.md

    Issue #7: Now includes X-Ray tracing and CloudWatch metrics.

    Args:
        word: The term to analyze.
        context: Page context for disambiguation.

    Returns:
        AnalysisResult dict with status, response, and metadata.
    """
    client = get_bedrock_client()

    # Issue #7: Trace Bedrock call with subsegment
    with create_subsegment("bedrock_invoke"):
        result = analyze_term(
            word=word,
            context=context,
            bedrock_client=client,
            model_id=BEDROCK_MODEL_ID,
        )

        # Issue #7: Add safe annotations (NO PII - only tokens/model/latency)
        metadata = result.get("metadata", {})
        trace_bedrock_call(
            model_id=metadata.get("model", BEDROCK_MODEL_ID),
            tokens_used=metadata.get("tokens_used"),
            latency_ms=metadata.get("latency_ms"),
            status=result.get("status", "unknown"),
            error_type=metadata.get("error") if result.get("status") == "error" else None,
        )

        # Issue #7: Log CloudWatch metrics for cost tracking
        if metadata.get("tokens_used"):
            log_bedrock_metrics(
                tokens_used=metadata["tokens_used"],
                model_id=metadata.get("model", BEDROCK_MODEL_ID),
                latency_ms=metadata.get("latency_ms"),
            )

    return result


def run_guardrails(
    text: str, denylist: set[str] | None = None
) -> tuple[str, str | None, dict]:
    """
    Run guardrail pipeline: Denylist → Semantic.

    Issue #126: Returns block_type instead of is_safe boolean.
    CRITICAL: Sequential execution is mandatory. See LLD Section 6.

    Args:
        text: Input text to check.
        denylist: Optional denylist for testing (dependency injection).

    Returns:
        (block_type, category, metadata)
        - block_type: "hard", "soft", or "none"
        - category: The semantic category (e.g., "Archaic", "None")
        - metadata: Timing and scoring information
    """
    # Issue #137: Track individual guardrail timings
    guardrail_timings = {}

    # Step 1: Denylist check (fast, deterministic) → ALWAYS hard block
    t0 = time.time()
    denylist_result = check_denylist(text, denylist)
    guardrail_timings["denylist_ms"] = int((time.time() - t0) * 1000)
    if denylist_result["blocked"]:
        return (
            BLOCK_TYPE_HARD,
            "denylist",
            {"layer": "denylist", "timings": guardrail_timings},
        )

    # Step 2: Semantic check (LLM-based, slower)
    # MUST run after denylist, returns block_type for nuanced handling
    t0 = time.time()
    semantic = get_semantic_guardrail()
    guardrail_timings["semantic_init_ms"] = int((time.time() - t0) * 1000)

    t0 = time.time()
    semantic_result = semantic.check_safety(text)
    guardrail_timings["semantic_llm_ms"] = int((time.time() - t0) * 1000)

    # Issue #137: Log guardrail breakdown
    logger.info(f"GUARDRAIL_BREAKDOWN: {json.dumps(guardrail_timings)}")

    # Issue #126: Return block_type from semantic guardrail
    block_type = semantic_result.get("block_type", BLOCK_TYPE_NONE)
    category = semantic_result.get("category", "Unknown")

    return (
        block_type,
        category,
        {
            "layer": "semantic",
            "scores": semantic_result.get("scores", {}),
            "timings": guardrail_timings,
            "is_fallback": semantic_result.get("is_fallback", False),
        },
    )


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
        # Issue #137: Timing instrumentation for latency investigation
        timings = {}
        handler_start = time.time()

        # Parse body if coming from API Gateway
        t0 = time.time()
        if "body" in event:
            body = (
                json.loads(event["body"])
                if isinstance(event["body"], str)
                else event["body"]
            )
        else:
            body = event
        timings["parse_body_ms"] = int((time.time() - t0) * 1000)

        # Issue #310: Handle deep poetic analysis action (separate flow)
        if body.get("action") == "deep_poetic_analysis":
            from .poetic_analyzer import analyze_poetic_resonance

            t0 = time.time()
            poetic_result = analyze_poetic_resonance(
                word=body.get("text", ""),
                etymology=body.get("etymology", {}),
                page_context=body.get("domContext", ""),
                dimensions=body.get("dimensions", []),
                bedrock_client=get_bedrock_client(),
            )
            timings["poetic_analysis_ms"] = int((time.time() - t0) * 1000)
            timings["handler_total_ms"] = int((time.time() - handler_start) * 1000)

            logger.info(f"POETIC_ANALYSIS: {json.dumps(timings)}")

            response_dict = {
                "status": poetic_result["status"],
                "synthesis": poetic_result["synthesis"],
                "dimensions": poetic_result["dimensions"],
                "resonance_strength": poetic_result["resonance_strength"],
                "latency_ms": poetic_result["latency_ms"],
            }

            if os.environ.get("ALETHEIA_ENV") == "dev":
                response_dict["_debug_timings"] = timings

            return {
                "statusCode": 200 if poetic_result["status"] == "success" else 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(response_dict),
            }

        # 1. Validation
        t0 = time.time()
        valid, error = validate_input(body)
        timings["validation_ms"] = int((time.time() - t0) * 1000)
        if not valid:
            return {"statusCode": 400, "body": json.dumps({"error": error})}

        text = body["text"]

        # Issue #106: Determine analysis mode and log for cost monitoring
        full_article = body.get("full_article")
        analysis_mode = "full_article" if full_article else "selection"
        input_text = full_article if full_article else text
        input_chars = len(input_text)

        # Log mode for CloudWatch Insights cost analysis
        logger.info(json.dumps({
            "action": "analysis_request",
            "mode": analysis_mode,
            "input_chars": input_chars,
        }))

        # 2. Guardrails (MUST be sequential: Denylist → Semantic)
        # Issue #126: Returns block_type for nuanced handling
        t0 = time.time()
        block_type, category, metadata = run_guardrails(text, denylist)
        timings["guardrails_total_ms"] = int((time.time() - t0) * 1000)

        # Issue #126: Hard block → 403 Forbidden (no etymology)
        if block_type == BLOCK_TYPE_HARD:
            return {
                "statusCode": 403,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "blocked": True,
                    "reason": category,
                    "message": "Blocked: Content not permitted",
                }),
            }

        # 3. Generate thread ID for persistence
        t0 = time.time()
        thread_id = generate_thread_id(body)
        timings["thread_id_ms"] = int((time.time() - t0) * 1000)

        # Issue #177 + #106: Extract context (prefer full_article, fallback to domContext)
        # Truncate to 100KB for DynamoDB safety
        if full_article:
            # Full article mode - use cleaned, PII-scrubbed article text
            dom_context = full_article[:100000]
        else:
            # Selection mode - use raw domContext
            dom_context = (body.get("domContext", "") or "")[:100000]

        # Issue #162: Extract noarchive signal - skip persistence if publisher requests
        signals = body.get("signals", {})
        skip_persistence = signals.get("noarchive", False)

        # 4. Generate etymology analysis (buffered, not streaming)
        # Issue #124: Digital Etymologist returns structured JSON
        # Issue #178: Wrapped in try/finally to ensure save_state always runs
        response_data = None
        result = None
        generation_error = None

        try:
            t0 = time.time()
            result = generate_etymology(text, dom_context)
            timings["etymology_generation_ms"] = int((time.time() - t0) * 1000)

            # Extract response data for persistence
            response_data = {
                "signal": result["response"]["signal"],
                "gem": result["response"]["gem"],
                "context": result["response"]["context"],
            }
        except Exception as e:
            # Issue #178: Capture error state for debugging
            generation_error = e
            response_data = {
                "signal": "error",
                "gem": str(e),
                "context": "Generation failed",
            }
            logger.error(f"Etymology generation failed: {e}")
        finally:
            # Issue #162: Skip persistence if noarchive signal is present
            if skip_persistence:
                logger.info(
                    f"NOARCHIVE: Skipping persistence for thread_id={thread_id}"
                )
                timings["dynamodb_write_ms"] = 0  # No write performed
            else:
                # Issue #177 & #178: Save state for analysis
                t0 = time.time()
                save_state(
                    thread_id,
                    {
                        "text": text,
                        "domContext": dom_context,  # Issue #177
                        "url": body.get("url", ""),
                        "userId": body.get("userId"),  # May be None pre-#116
                        "safety_score": metadata.get("scores", {}),
                        "response": response_data,  # Issue #178
                    },
                )
                timings["dynamodb_write_ms"] = int((time.time() - t0) * 1000)

        # If generation failed, return 500 after saving state
        if generation_error is not None:
            raise generation_error

        # Type narrowing: if we reach here, generation succeeded and result is set
        assert result is not None, "result should be set if no generation_error"

        # Calculate total handler time
        timings["handler_total_ms"] = int((time.time() - handler_start) * 1000)

        # Issue #137: Log all timings for analysis
        logger.info(f"LATENCY_BREAKDOWN: {json.dumps(timings)}")

        # Issue #295: Get scores from semantic guardrail metadata
        raw_scores = metadata.get("scores", {})
        scores_display = process_scores_for_display(raw_scores)

        # Build response with structured output
        # Issue #295: Include both signal (backward compat) and scores (new)
        # Issue #310: Include poetic resonance fields
        poetic_potential = result["response"].get("poetic_potential", 0.0)
        potential_dimensions = result["response"].get("potential_dimensions", [])

        response_body: dict[str, Any] = {
            "thread_id": thread_id,
            "status": result["status"],
            "signal": result["response"]["signal"],  # Backward compat for old extensions
            "scores": raw_scores,  # Issue #295: Full scores object
            "scores_display": scores_display,  # Issue #295: Pre-processed for display
            "gem": result["response"]["gem"],
            "context": result["response"]["context"],
            # Issue #310: Poetic resonance detection
            "poetic_potential": poetic_potential,
            "potential_dimensions": potential_dimensions,
        }

        # Issue #126 + #295: Add warning flag
        # Warning when: soft block OR provocative >= 50%
        provocative_score = raw_scores.get("Provocative", 0.0)
        if block_type == BLOCK_TYPE_SOFT or provocative_score >= 0.50:
            response_body["warning"] = True
            response_body["warning_category"] = category
            # Include fallback flag if semantic check had an error
            if metadata.get("is_fallback"):
                response_body["fallback"] = True

        # Include latency for monitoring
        if result.get("metadata", {}).get("latency_ms"):
            response_body["latency_ms"] = result["metadata"]["latency_ms"]

        # Issue #137: Include timing breakdown in response only in dev mode
        # CloudWatch logging (above) remains active for production observability
        if os.environ.get("ALETHEIA_ENV") == "dev":
            response_body["_debug_timings"] = timings
            if metadata.get("timings"):
                response_body["_debug_timings"]["guardrails"] = metadata["timings"]

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(response_body),
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
