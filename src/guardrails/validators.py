"""
Individual guardrail validator functions.
Each validator returns an error message string if the check fails,
and None if it passes.
"""
from typing import Optional
import math

def validate_length(input_text: str) -> Optional[str]:
    """Reject if word < 2 chars or > 50 chars."""
    if not 2 <= len(input_text) <= 50:
        return f"Input length ({len(input_text)}) is outside the allowed range (2-50)."
    return None

def validate_entropy(input_text: str) -> Optional[str]:
    """
    Reject if the input is repetitive (e.g., "aaaaa").
    This is a simple entropy check based on character frequency.
    """
    if not input_text:
        return "Input is empty."
    
    # Calculate Shannon entropy
    freq_map = {char: input_text.count(char) / len(input_text) for char in set(input_text)}
    entropy = -sum(p * math.log2(p) for p in freq_map.values())
    
    # Heuristic threshold: < 1.5 usually indicates repetitive nonsense like "asdfasdf"
    if entropy < 1.5:
        return f"Input has low entropy ({entropy:.2f}), suggesting it is repetitive."
    return None
