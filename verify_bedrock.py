import boto3
from src.guardrails.semantic import SemanticGuardrail

def live_fire_test():
    """
    Directly invokes SemanticGuardrail to test AWS credentials and Model Access.
    """
    print("=== AWS Bedrock Connectivity Test ===")

    # 1. Check Identity
    try:
        sts = boto3.client("sts")
        identity = sts.get_caller_identity()
        print(f"[INFO] Identity: {identity['Arn']}")
    except Exception as e:
        print(f"[FATAL] AWS Credentials Failed: {e}")
        return

    # 2. Initialize Guardrail
    print("[INFO] Initializing Claude 3 Haiku...")
    try:
        guard = SemanticGuardrail()
    except Exception as e:
        print(f"[FATAL] Initialization Failed: {e}")
        return

    # 3. Test Safe Payload
    print("[TEST] Payload: 'Hello World'")
    try:
        res = guard.check_safety("Hello World")
        print(f"[RESULT] {res}")
    except Exception as e:
        print(f"[FAIL] {e}")

    # 4. Test Unsafe Payload (Archaic)
    print("[TEST] Payload: 'Thou art consumptive'")
    try:
        res = guard.check_safety("Thou art consumptive")
        print(f"[RESULT] {res}")
    except Exception as e:
        print(f"[FAIL] {e}")

if __name__ == "__main__":
    live_fire_test()
