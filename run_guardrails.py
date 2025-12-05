#!/usr/bin/env python
"""
Integration test script for the GuardrailsEngine.
Loads test data and runs it through the engine.
"""
import json
import os
from src.guardrails.engine import GuardrailsEngine

def main():
    print("=== Running Guardrails Verification ===")
    engine = GuardrailsEngine()
    
    filename = "test_holistic_data.json"
    if not os.path.exists(filename):
        print(f"Error: `{filename}` not found in {os.getcwd()}")
        return

    with open(filename, "r", encoding="utf-8") as f:
        records = json.load(f)

    for record in records:
        word = record.get("word", "")
        # Handle cases where data might be missing the word
        if not word: 
            continue
            
        result = engine.validate_input(word)
        status = "PASS" if result.is_valid else f"FAIL ({result.reason})"
        print(f"- Word: '{word}' -> {status}")
    print("=== Verification Complete ===")

if __name__ == "__main__":
    main()
