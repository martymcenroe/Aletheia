"""
The GuardrailsEngine runs a series of validators against an input string.
"""
from dataclasses import dataclass, field
from typing import List, Callable, Optional
from src.guardrails import validators

@dataclass
class GuardrailResult:
    is_valid: bool
    reason: str
    metadata: dict = field(default_factory=dict)

class GuardrailsEngine:
    """A simple engine to run a chain of validators."""
    def __init__(self):
        self.validators: List[Callable[[str], Optional[str]]] = [
            validators.validate_length,
            validators.validate_entropy,
        ]

    def validate_input(self, input_text: str) -> GuardrailResult:
        """
        Runs all active validators against the input.
        Returns the first failure, or success if all pass.
        """
        for validator in self.validators:
            reason = validator(input_text)
            if reason:
                return GuardrailResult(is_valid=False, reason=reason)
        return GuardrailResult(is_valid=True, reason="Valid")
