import json
import sys
import os
from src.guardrails.semantic import SemanticGuardrail

def run_holistic_test():
    print("=== Holistic Semantic Guardrail Test (Probabilistic) ===")

    if not os.path.exists("test_ground_truth.json"):
        print("[FATAL] 'test_ground_truth.json' not found.")
        sys.exit(1)

    with open("test_ground_truth.json", "r") as f:
        test_data = json.load(f)

    try:
        guard = SemanticGuardrail()
    except Exception as e:
        print(f"[FATAL] Initialization Failed: {e}")
        sys.exit(1)

    # Counters
    pass_count = 0

    # Header: Input | Arch | Prov | Hate | Neo | None | Category | Status
    header = f"{'INPUT':<18} | {'ARCH':<4} | {'PROV':<4} | {'HATE':<4} | {'NEO':<4} | {'NONE':<4} | {'ACT.CAT':<11} | {'STS'}"
    print(header)
    print("-" * len(header))

    for item in test_data:
        text = item.get("text")
        exp_safe = item.get("expected_safe")
        exp_cat = item.get("expected_category", "None")

        # Invoke
        try:
            res = guard.check_safety(text)
            _act_safe = res["is_safe"]  # noqa: F841 - extracted for debugging
            act_cat = res["reason"]
            scores = res.get("scores", {})
        except Exception:
            _act_safe = False  # noqa: F841
            act_cat = "Error"
            scores = {}

        # Extract Scores (Default to 0.0)
        s_arch = scores.get("Archaic", 0.0)
        s_prov = scores.get("Provocative", 0.0)
        s_hate = scores.get("Hate", 0.0)
        s_neo  = scores.get("Neologism", 0.0)
        s_none = scores.get("None", 0.0)

        # Status Logic (Category Match)
        # We Pass if the Category matches Expected OR if we expected Safe and got Neologism (which is safe)
        is_pass = False
        if exp_cat.lower() == act_cat.lower():
            is_pass = True
        elif exp_safe and act_cat == "Neologism":
            # Neologisms are technically "Safe" in our policy, so this is a pass
            is_pass = True

        status = "PASS" if is_pass else "FAIL"
        if is_pass:
            pass_count += 1

        # Format scores as .XX (e.g. .99)
        def fmt(v): return f"{v:.2f}"[-3:] # .99

        print(f"{text[:18]:<18} | {fmt(s_arch):<4} | {fmt(s_prov):<4} | {fmt(s_hate):<4} | {fmt(s_neo):<4} | {fmt(s_none):<4} | {act_cat[:11]:<11} | {status}")

    print("-" * len(header))
    print(f"Overall Score: {pass_count}/{len(test_data)} ({(pass_count/len(test_data))*100:.1f}%)")

if __name__ == "__main__":
    run_holistic_test()
