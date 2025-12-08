import json
import boto3
from typing import Dict, Any

class SemanticGuardrail:
    """
    LLM-based guardrail to filter unsafe semantic content.
    Target Categories: Archaic, Provocative, Hate.
    """
    def __init__(self, region_name: str = "us-east-1", model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"):
        self.client = boto3.client("bedrock-runtime", region_name=region_name)
        self.model_id = model_id

    def check_safety(self, text: str) -> Dict[str, Any]:
        """
        Analyzes text for safety violations using AWS Bedrock.
        Returns: {'is_safe': bool, 'reason': str}
        """
        system_prompt = (
            "You are a content safety filter. Analyze the text for: "
            "1. Archaic (Outdated/Pejorative), 2. Provocative (Sexual double entendres), "
            "3. Hate (Slurs). Respond with valid JSON only: "
            "{\"safe\": boolean, \"category\": \"None\"|\"Archaic\"|\"Provocative\"|\"Hate\"}"
        )

        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "system": [{"text": system_prompt}],
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
            return {
                "is_safe": data.get("safe", False),
                "reason": data.get("category", "Unknown")
            }
            
        except Exception as e:
            # Fail closed on infrastructure error
            return {"is_safe": False, "reason": f"Guardrail Error: {str(e)}"}
