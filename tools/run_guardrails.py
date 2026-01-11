#!/usr/bin/env python
"""
Integration test script for the GuardrailsEngine.

This script loads test data from `test_holistic_data.json` and runs
each 'word' through the guardrails engine, printing the result.
"""
import json
from src.guardrails.engine import GuardrailsEngine


def main():
    """Load data, run validations, and print results."""
    print("=== Running Guardrails Verification ===")
    engine = GuardrailsEngine()

    try:
        with open("test_holistic_data.json", "r", encoding="utf-8") as f:
            records = json.load(f)
    except FileNotFoundError:
        print("Error: `test_holistic_data.json` not found. Please run from the project root.")
        return

    for record in records:
        word = record.get("word", "")
        result = engine.validate_input(word)
        status = "PASS" if result.is_valid else f"FAIL ({result.reason})"
        print(f"- Word: '{word}' -> {status}")

    print("=== Verification Complete ===")


if __name__ == "__main__":
    main()
