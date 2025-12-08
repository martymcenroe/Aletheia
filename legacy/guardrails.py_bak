from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_aws import ChatBedrockConverse
from pydantic import BaseModel, Field

# 1. Output Schema
class SafetyAssessment(BaseModel):
    status: Literal["SAFE", "ARCHAIC", "PROVOCATIVE", "UNSAFE"] = Field(
        ..., 
        description="Classify the text. ARCHAIC=outdated/insensitive. PROVOCATIVE=sexual/locker-room. UNSAFE=slurs/hate."
    )
    reasoning: str = Field(..., description="Brief explanation of why the text was flagged.")

# 2. Model (Haiku is fast and cheap for this)
llm = ChatBedrockConverse(
    model_id="anthropic.claude-3-haiku-20240307-v1:0", 
    temperature=0,
    region_name="us-east-1"
)

# 3. Guardrail Prompt
system_prompt = """You are a Semantic Safety Guardrail. Analyze the text for subtle, context-dependent issues.

Taxonomy:
- ARCHAIC: Terms valid in the past but offensive now (e.g., 'deaf-mute', 'oriental').
- PROVOCATIVE: Sexual double entendres or 'locker room' talk (e.g., 'size matters').
- UNSAFE: Slurs, hate speech, explicit profanity.
- SAFE: Standard language.

Return the result as JSON matching the SafetyAssessment schema.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", "Analyze this text: {text}")
])

# 4. Runnable Chain
guardrail_chain = prompt | llm.with_structured_output(SafetyAssessment)

def check_safety(text: str) -> SafetyAssessment:
    """Synchronous wrapper for the guardrail check."""
    return guardrail_chain.invoke({"text": text})
