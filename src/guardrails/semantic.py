"""
Semantic Guardrail - LLM-based content classification.

Issue #126: Implements Hard vs. Soft Blocking Logic.
See: docs/1126-hard-soft-blocking.md

Block Types:
- "hard": Safety violations (Hate) - 403 Forbidden
- "soft": Educational warnings (Archaic, Provocative) - 200 with warning
- "none": Safe content (None, Neologism, Formal) - 200 OK
"""
import json
import logging
import time
import boto3
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Issue #126: Block type constants
BLOCK_TYPE_HARD = "hard"
BLOCK_TYPE_SOFT = "soft"
BLOCK_TYPE_NONE = "none"

# Issue #126: Category to block type mapping (from LLD 1126 Section 2.1)
HARD_BLOCK_CATEGORIES = {"Hate"}  # Safety violations - immediate 403
SOFT_BLOCK_CATEGORIES = {"Archaic", "Provocative"}  # Educational warnings - 200 with warning
# All other categories (None, Neologism, Formal Academic Term, etc.) = BLOCK_TYPE_NONE

class SemanticGuardrail:
    """
    LLM-based guardrail to filter unsafe semantic content.
    Loads definitions and few-shot examples from resources/taxonomy.json.

    Issue #137: Accepts optional bedrock_client to share client with main handler,
    eliminating ~774ms duplicate client initialization on cold starts.
    """
    def __init__(
        self,
        region_name: str = "us-east-1",
        model_id: str | None = None,
        bedrock_client=None,
    ):
        # Use injected client if provided, otherwise create new (backward compat)
        self.client = bedrock_client or boto3.client("bedrock-runtime", region_name=region_name)
        # Issue #535: Read model ID from env var (AIP ARN) with fallback
        import os
        self.model_id = model_id or os.environ.get(
            "ALETHEIA_AIP_HAIKU", "anthropic.claude-haiku-4-5-20251001-v1:0"
        )
        self.resources = self._load_resources()

    def _load_resources(self) -> Dict[str, Any]:
        """Loads the taxonomy and examples from the adjacent JSON file."""
        resource_path = Path(__file__).parent / "resources" / "taxonomy.json"
        try:
            with open(resource_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            raise RuntimeError(f"Critical Resource Missing: {resource_path}")

    def _build_system_prompt(self) -> str:
        """Constructs the prompt dynamically from the loaded resources."""
        taxonomy = self.resources["taxonomy"]
        examples = self.resources["few_shot_examples"]

        # Build Taxonomy String
        tax_str = "\n".join([f"- {k}: {v}" for k, v in taxonomy.items()])

        # Build Few-Shot String
        # We explicitly format the example output to include the 'scores' block
        ex_str = "\n".join([
            f"Input: '{ex['text']}' -> {json.dumps({'scores': ex['scores'], 'category': ex['category']})}"
            for ex in examples
        ])

        return (
            "You are a content safety filter. Classify the input text into exactly one category.\n"
            "The user text will be provided in <user_text> XML tags.\n"
            "Provide a confidence score (0.0-1.0) for every category in the taxonomy.\n"
            "Taxonomy:\n"
            f"{tax_str}\n\n"
            "Examples:\n"
            f"{ex_str}\n\n"
            "Respond with valid JSON only: {\"scores\": {\"Archaic\": 0.0, ...}, \"category\": \"...\"}"
        )

    def check_safety(self, text: str) -> Dict[str, Any]:
        """
        Analyzes text for safety violations using AWS Bedrock.

        Issue #126: Returns block_type instead of is_safe boolean.

        Returns: {
            'block_type': 'hard' | 'soft' | 'none',
            'category': str,
            'scores': dict,
            'is_safe': bool  # Backwards compatibility
        }

        Security: User text is wrapped in XML tags to prevent prompt injection.
        See: docs/0809-audit-security.md Finding F1
        """
        # Issue #137: Timing instrumentation
        timings = {}
        start = time.time()

        # Wrap user text in XML tags to clearly delineate from prompt
        # This mitigates prompt injection by making the boundary explicit
        t0 = time.time()
        wrapped_text = f"<user_text>{text}</user_text>"

        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 200,
            "system": self._build_system_prompt(),
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": wrapped_text}]}
            ]
        }
        timings["prompt_build_ms"] = int((time.time() - t0) * 1000)

        try:
            t0 = time.time()
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(payload)
            )
            timings["bedrock_invoke_ms"] = int((time.time() - t0) * 1000)

            t0 = time.time()
            result = json.loads(response['body'].read())
            content_text = result['content'][0]['text']

            # Parse the JSON response from the LLM
            data = json.loads(content_text)
            category = data.get("category", "Unknown")
            scores = data.get("scores", {})
            timings["response_parse_ms"] = int((time.time() - t0) * 1000)

            timings["total_ms"] = int((time.time() - start) * 1000)

            # Issue #137: Log semantic guardrail timing breakdown
            logger.info(f"SEMANTIC_GUARDRAIL_TIMING: {json.dumps(timings)}")

            # Issue #126: Deterministic Policy Enforcement (Code > LLM)
            # Map category to block type per LLD 1126 Section 2.1
            block_type = self._get_block_type(category)

            return {
                "block_type": block_type,
                "category": category,
                "scores": scores,
                # Backwards compatibility: is_safe is True only for BLOCK_TYPE_NONE
                "is_safe": block_type == BLOCK_TYPE_NONE,
                "reason": category,  # Legacy field
            }

        except Exception as e:
            timings["total_ms"] = int((time.time() - start) * 1000)
            # Privacy: log exception class name only, never str(e) or repr(e).
            # Exception messages from this path can carry user-derived content
            # (json.JSONDecodeError, botocore ClientError) — see issue #619.
            error_class = e.__class__.__name__
            logger.error(
                f"SEMANTIC_GUARDRAIL_ERROR: {error_class} | {json.dumps(timings)}"
            )
            return {
                "block_type": BLOCK_TYPE_SOFT,
                "category": "error",
                "scores": {},
                "is_safe": False,
                "reason": f"Guardrail Error: {str(e)}",
                "is_fallback": True,
            }

    def _get_block_type(self, category: str) -> str:
        """
        Map semantic category to block type.

        Issue #126: Per LLD 1126 Category Mapping Matrix.

        Returns:
            BLOCK_TYPE_HARD, BLOCK_TYPE_SOFT, or BLOCK_TYPE_NONE
        """
        if category in HARD_BLOCK_CATEGORIES:
            return BLOCK_TYPE_HARD
        elif category in SOFT_BLOCK_CATEGORIES:
            return BLOCK_TYPE_SOFT
        else:
            return BLOCK_TYPE_NONE
