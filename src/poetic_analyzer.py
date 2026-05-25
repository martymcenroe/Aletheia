"""
Poetic Resonance Analyzer - Opus-powered deep meaning extraction.

Issue #310: Enables detection and explanation of layered/poetic meanings
where a term's deeper connotations resonate with surrounding context.

This module provides:
- analyze_poetic_resonance(): Main entry point for deep analysis
- Uses Opus model for rich, multi-dimensional analysis
- Returns synthesis explaining how word meaning interacts with context

See: docs/lld/active/1310-poetic-resonance.md
"""

import json
import logging
import os
import time
from typing import Literal, TypedDict

logger = logging.getLogger(__name__)

# Issue #535: Opus model from env var (AIP ARN) with fallback to raw model ID
OPUS_MODEL_ID = os.environ.get(
    "ALETHEIA_AIP_OPUS", "anthropic.claude-opus-4-6-v1"
)

# Maximum tokens for Opus response
MAX_TOKENS = 1000

# Valid dimension labels
VALID_DIMENSIONS = frozenset(
    [
        "religious",
        "literary",
        "architectural",
        "artistic",
        "political",
        "scientific",
    ]
)


class DimensionAnalysis(TypedDict):
    """Analysis of a single dimension of meaning."""

    dimension: str
    explanation: str


class PoeticAnalysisResult(TypedDict):
    """Result from poetic resonance analysis."""

    status: Literal["success", "error"]
    synthesis: str  # Multi-paragraph explanation of layered meaning
    dimensions: list[DimensionAnalysis]  # Per-dimension explanations
    resonance_strength: float  # 0.0-1.0 confidence in resonance
    latency_ms: int


# Fallback result for errors
FALLBACK_RESULT: PoeticAnalysisResult = {
    "status": "error",
    "synthesis": "",
    "dimensions": [],
    "resonance_strength": 0.0,
    "latency_ms": 0,
}


POETIC_SYSTEM_PROMPT = """You are a literary analyst specializing in detecting layered meanings and poetic resonance in language.

Given a word, its etymology, and the surrounding context, analyze how the word's deeper connotations interact with the context to create meaning beyond the literal.

You MUST respond with ONLY a JSON object (no markdown, no preamble) containing:
- "synthesis": A 2-3 paragraph explanation of the layered meaning (200 words max). Focus on how the word's history and connotations CREATE meaning in this specific context. Be specific - cite actual context elements that create resonance.
- "dimensions": Array of objects, each with:
  - "dimension": One of ["religious", "literary", "architectural", "artistic", "political", "scientific"] or "novel:{description}" for emergent dimensions
  - "explanation": 1-2 sentences explaining how this dimension resonates with the context
- "resonance_strength": A score from 0.0 to 1.0 indicating how strongly the word resonates with context:
  - 0.0-0.3: Weak or no resonance (word is mostly literal in context)
  - 0.4-0.6: Moderate resonance (some layered meaning activated)
  - 0.7-0.9: Strong resonance (multiple dimensions clearly activated)
  - 1.0: Exceptional resonance (word choice is deeply poetic/intentional)

CRITICAL RULES:
1. Focus on how etymology and connotations CREATE meaning in THIS SPECIFIC context
2. Do NOT include personal names from the context in your synthesis
3. If no genuine resonance exists, say so honestly and give resonance_strength < 0.3
4. Be specific about which context elements activate which dimensions
5. Respond with ONLY the JSON object - no markdown code fences, no explanation

Example output:
{"synthesis": "The word 'ascension' carries profound dual resonance in this context...", "dimensions": [{"dimension": "religious", "explanation": "The word evokes spiritual transcendence, echoing the passage from mortal life."}], "resonance_strength": 0.82}"""


def build_poetic_prompt(
    word: str,
    etymology: dict,
    page_context: str,
    dimensions: list[str],
) -> dict:
    """
    Build Opus prompt for poetic resonance analysis.

    Args:
        word: The term being analyzed.
        etymology: Dict with signal, gem, context from initial analysis.
        page_context: Surrounding text from the page (truncated to 5000 chars).
        dimensions: Initial dimension hints from Nova Micro.

    Returns:
        Dict formatted for Bedrock Claude API.
    """
    # Truncate page context to prevent excessive token usage
    truncated_context = page_context[:5000] if page_context else ""

    user_message = f"""Analyze the poetic resonance of this word:

<word>{word}</word>

<etymology>
Signal: {etymology.get("signal", "Unknown")}
Summary: {etymology.get("gem", "")}
History: {etymology.get("context", "")}
</etymology>

<page_context>
{truncated_context}
</page_context>

<detected_dimensions>
{", ".join(dimensions) if dimensions else "None detected"}
</detected_dimensions>

Explain how this word's deeper meanings interact with the surrounding context to create layered meaning."""

    return {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": MAX_TOKENS,
        "system": POETIC_SYSTEM_PROMPT,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": user_message}],
            }
        ],
    }


def _extract_json_from_response(raw_text: str) -> dict | None:
    """
    Extract JSON from Opus response, handling markdown code fences.

    Returns parsed dict or None if extraction fails.
    """
    if not raw_text:
        return None

    text = raw_text.strip()

    # Remove markdown code fences if present
    if text.startswith("```"):
        # Find the end of the opening fence
        first_newline = text.find("\n")
        if first_newline > 0:
            text = text[first_newline + 1 :]
        # Remove closing fence
        if text.endswith("```"):
            text = text[:-3].strip()

    # Find JSON boundaries
    first_brace = text.find("{")
    last_brace = text.rfind("}")

    if first_brace == -1 or last_brace == -1 or last_brace <= first_brace:
        logger.warning(f"No valid JSON boundaries in Opus response: {text[:200]}")
        return None

    json_str = text[first_brace : last_brace + 1]

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON decode failed for Opus response: {e}")
        logger.warning(f"JSON string (first 300 chars): {json_str[:300]}")
        return None


def _validate_poetic_result(parsed: dict) -> tuple[bool, list[str]]:
    """
    Validate parsed Opus response.

    Returns (is_valid, list_of_errors).
    """
    errors = []

    # Check synthesis
    if "synthesis" not in parsed:
        errors.append("Missing field: synthesis")
    elif not isinstance(parsed["synthesis"], str):
        errors.append("Field 'synthesis' must be string")

    # Check dimensions
    if "dimensions" not in parsed:
        errors.append("Missing field: dimensions")
    elif not isinstance(parsed["dimensions"], list):
        errors.append("Field 'dimensions' must be list")
    else:
        for i, dim in enumerate(parsed["dimensions"]):
            if not isinstance(dim, dict):
                errors.append(f"dimensions[{i}] must be dict")
            elif "dimension" not in dim or "explanation" not in dim:
                errors.append(f"dimensions[{i}] missing dimension or explanation")

    # Check resonance_strength
    if "resonance_strength" not in parsed:
        errors.append("Missing field: resonance_strength")
    elif not isinstance(parsed["resonance_strength"], (int, float)):
        errors.append("Field 'resonance_strength' must be number")
    elif parsed["resonance_strength"] < 0.0 or parsed["resonance_strength"] > 1.0:
        errors.append(f"resonance_strength must be 0.0-1.0 (got {parsed['resonance_strength']})")

    return len(errors) == 0, errors


def analyze_poetic_resonance(
    word: str,
    etymology: dict,
    page_context: str,
    dimensions: list[str],
    bedrock_client=None,
) -> PoeticAnalysisResult:
    """
    Analyze poetic resonance using Opus model.

    This function is called when a user clicks "Explore Deeper Meaning"
    after Nova Micro has detected high poetic potential.

    Args:
        word: The term being analyzed.
        etymology: Dict with signal, gem, context from initial Nova analysis.
        page_context: Surrounding text from the page.
        dimensions: Initial dimension hints from Nova Micro's potential_dimensions.
        bedrock_client: boto3 Bedrock runtime client (for dependency injection).

    Returns:
        PoeticAnalysisResult with synthesis, dimensions, and resonance_strength.
    """
    start_time = time.time()

    # Handle missing client
    if bedrock_client is None:
        logger.error("No Bedrock client provided to analyze_poetic_resonance")
        return PoeticAnalysisResult(
            status="error",
            synthesis="",
            dimensions=[],
            resonance_strength=0.0,
            latency_ms=0,
        )

    # Handle empty word
    if not word or not word.strip():
        return PoeticAnalysisResult(
            status="error",
            synthesis="",
            dimensions=[],
            resonance_strength=0.0,
            latency_ms=0,
        )

    try:
        # Build prompt
        prompt = build_poetic_prompt(word, etymology, page_context, dimensions)

        # Call Opus via Bedrock
        response = bedrock_client.invoke_model(
            modelId=OPUS_MODEL_ID,
            body=json.dumps(prompt),
        )

        # Parse response body
        response_body = json.loads(response["body"].read())

        # Extract text from Claude response format
        content = response_body.get("content", [])
        raw_text = ""
        for block in content:
            if block.get("type") == "text":
                raw_text = block.get("text", "")
                break

        # Extract and validate JSON
        parsed = _extract_json_from_response(raw_text)
        if parsed is None:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.error("Failed to extract JSON from Opus response")
            return PoeticAnalysisResult(
                status="error",
                synthesis="",
                dimensions=[],
                resonance_strength=0.0,
                latency_ms=latency_ms,
            )

        # Validate structure
        is_valid, validation_errors = _validate_poetic_result(parsed)
        if not is_valid:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.warning(f"Opus response validation failed: {validation_errors}")
            return PoeticAnalysisResult(
                status="error",
                synthesis="",
                dimensions=[],
                resonance_strength=0.0,
                latency_ms=latency_ms,
            )

        latency_ms = int((time.time() - start_time) * 1000)

        # Return successful result
        return PoeticAnalysisResult(
            status="success",
            synthesis=parsed["synthesis"],
            dimensions=parsed["dimensions"],
            resonance_strength=float(parsed["resonance_strength"]),
            latency_ms=latency_ms,
        )

    except Exception as e:
        # Privacy (#645, audit umbrella #637): class name only — Bedrock errors
        # can carry request-payload echoes. See docs/observability.html.
        latency_ms = int((time.time() - start_time) * 1000)
        logger.error(f"POETIC_ANALYSIS_ERROR: {e.__class__.__name__}")
        return PoeticAnalysisResult(
            status="error",
            synthesis="",
            dimensions=[],
            resonance_strength=0.0,
            latency_ms=latency_ms,
        )
