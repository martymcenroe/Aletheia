import json
import os
import sys
from guardrails import check_safety

DATA_FILE = "test_data.json"

def load_test_data():
    if not os.path.exists(DATA_FILE):
        print(f"Error: {DATA_FILE} not found. Please create it with test cases.")
        sys.exit(1)
    
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def run_tests():
    cases = load_test_data()
    
    print(f"{'INPUT':<40} | {'EXPECTED':<12} | {'ACTUAL':<12} | {'PASS'}")
    print("-" * 80)
    
    failures = 0
    
    for case in cases:
        text = case["text"]
        expected = case["expected"]
        
        # Skip placeholder if user hasn't edited it yet
        if text == "REPLACE_WITH_ACTUAL_SLUR":
            print(f"{'SKIPPING PLACEHOLDER':<40} | {expected:<12} | {'---':<12} | ⚠️")
            continue

        try:
            assessment = check_safety(text)
            actual = assessment.status
            
            is_pass = "✅" if actual == expected else "❌"
            if actual != expected:
                failures += 1
                
            print(f"{text[:37]+'...':<40} | {expected:<12} | {actual:<12} | {is_pass}")
            
            if actual != expected:
                print(f"  > Reasoning: {assessment.reasoning}")
                
        except Exception as e:
            print(f"Error executing test for '{text}': {e}")
            failures += 1

    if failures > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
