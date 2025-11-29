from typing import TypedDict, Optional, Literal
from langchain_aws import ChatBedrockConverse
from langchain_core.messages import SystemMessage, HumanMessage

# 1. Schema for the Safe Metadata
class ComplianceReport(TypedDict):
    usage_summary: str      # The "Fair Use" synthetic description
    content_vector: list    # The embedding (simulated for MVP)
    paywall_status: Literal["OPEN", "PAYWALLED", "UNKNOWN"]

# 2. Configuration
# Optimization: Use Haiku for fast, cheap summarization
llm = ChatBedrockConverse(
    model_id="anthropic.claude-3-haiku-20240307-v1:0",
    temperature=0,
    region_name="us-east-1"
)

SYSTEM_PROMPT = """
You are a Compliance Context Engine. 
Your goal is to read the provided text and generate a 'Usage Report' that captures the semantic meaning 
of the target word WITHOUT reproducing the copyrighted text verbatim.
Focus on:
1. How the word is used (Part of Speech, Connotation).
2. The surrounding narrative arc (Intro, Climax, etc.).
3. Any specific cultural nuance.

Output ONLY the summary paragraph.
"""

def analyze_context(word: str, raw_context: str) -> ComplianceReport:
    """
    Ephemeral Processor: Ingests raw text, extracts metadata, discards text.
    """
    
    # 1. Traffic Light Check (Simple Heuristic for MVP)
    # In a real scraper, we would check meta tags before even sending to Lambda.
    paywall_status = "OPEN" # Default assume open if we got here
    
    # 2. Generate Semantic Usage Report (The Transform)
    # We invoke the LLM to 'compress' the text into a summary
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Target Word: {word}\n\nContext:\n{raw_context}")
    ])
    
    usage_summary = response.content.strip()
    
    # 3. Generate Vector (Placeholder for MVP)
    # In production, this would call Bedrock Titan Embeddings
    simulated_vector = [0.0] * 1536 
    
    # 4. Return ONLY the metadata (Raw context is dropped here)
    return {
        "usage_summary": usage_summary,
        "content_vector": simulated_vector,
        "paywall_status": paywall_status
    }
