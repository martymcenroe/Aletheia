import json
import boto3
from pathlib import Path
from typing import Dict, Any

class SemanticGuardrail:
    """
    LLM-based guardrail to filter unsafe semantic content.
    Loads definitions and few-shot examples from resources/taxonomy.json.
    """
    def __init__(self, region_name: str = "us-east-1", model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"):
        self.client = boto3.client("bedrock-runtime", region_name=region_name)
        self.model_id = model_id
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
        Returns: {'is_safe': bool, 'reason': str, 'scores': dict}
        """
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 200,
            "system": self._build_system_prompt(),
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": text}]}
            ]
        }

        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(payload)
            )
            result = json.loads(response['body'].read())
            content_text = result['content'][0]['text']
            
            # Parse the JSON response from the LLM
            data = json.loads(content_text)
            category = data.get("category", "Unknown")
            scores = data.get("scores", {})
            
            # Deterministic Policy Enforcement (Code > LLM)
            # "None" and "Neologism" are Safe. Others are Unsafe.
            unsafe_categories = ["Archaic", "Provocative", "Hate"]
            is_safe = category not in unsafe_categories
            
            return {
                "is_safe": is_safe,
                "reason": category,
                "scores": scores
            }
            
        except Exception as e:
            # Fail closed on infrastructure error
            return {"is_safe": False, "reason": f"Guardrail Error: {str(e)}", "scores": {}}
