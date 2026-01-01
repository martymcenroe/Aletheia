#!/usr/bin/env python3
"""
Smoke Test for Aletheia Lambda Deployment.

Verifies the deployed Lambda function is working correctly.
See: docs/1113-naked-python-architecture.md

Usage:
    python tools/smoke_test.py
    python tools/smoke_test.py --url https://your-function-url.lambda-url.us-east-1.on.aws/
"""
import argparse
import json
import subprocess
import sys
import urllib.request
import urllib.error

# Test payloads
VALID_PAYLOAD = {"text": "Hello World", "url": "https://test.example.com"}

def get_blocked_payload() -> dict:
    """Get a blocked payload using a real term from denylist (for smoke testing only)."""
    import os
    import re
    denylist_path = os.path.join(os.path.dirname(__file__), "..", "src", "guardrails", "resources", "denylist.json")
    try:
        with open(denylist_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            terms = data.get("terms", [])
            # Find a single-word term that matches the tokenizer pattern \w+
            for term in terms:
                if re.fullmatch(r"\w+", term):
                    return {"text": term}
    except FileNotFoundError:
        pass
    # Fallback to mock term (will fail but that's expected if denylist not populated)
    return {"text": "test_block_term"}

FUNC_NAME = "AletheiaAgent"
REGION = "us-east-1"


def get_function_url() -> str:
    """Get Lambda Function URL from AWS."""
    try:
        result = subprocess.run(
            [
                "aws", "lambda", "get-function-url-config",
                "--function-name", FUNC_NAME,
                "--region", REGION,
                "--query", "FunctionUrl",
                "--output", "text"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        url = result.stdout.strip()
        if not url or url == "None":
            raise RuntimeError("Function URL not configured")
        return url
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to get function URL: {e.stderr}")
        sys.exit(1)


def send_request(url: str, payload: dict, timeout: int = 30) -> tuple[int, dict]:
    """Send POST request to Lambda and return (status_code, response_body)."""
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except json.JSONDecodeError:
            return e.code, {"raw": body}
    except urllib.error.URLError as e:
        print(f"ERROR: Connection failed: {e}")
        sys.exit(1)


def test_valid_input(url: str) -> bool:
    """Test 1: Valid input should return 200 with response."""
    print("\n[TEST 1] Valid Input (expect 200 OK)")
    print(f"  Payload: {json.dumps(VALID_PAYLOAD)}")

    status, body = send_request(url, VALID_PAYLOAD)

    print(f"  Status:  {status}")
    print(f"  Body:    {json.dumps(body)[:200]}...")

    if status == 200 and "response" in body:
        print("  Result:  PASS")
        return True
    else:
        print(f"  Result:  FAIL (expected 200 with 'response' key)")
        return False


def test_blocked_input(url: str) -> bool:
    """Test 2: Blocked input should return 403."""
    print("\n[TEST 2] Blocked Input (expect 403 Forbidden)")
    blocked_payload = get_blocked_payload()
    # Redact the actual term in output for security
    print(f"  Payload: {{\"text\": \"[REDACTED - denylist term]\"}}")

    status, body = send_request(url, blocked_payload)

    print(f"  Status:  {status}")
    print(f"  Body:    {json.dumps(body)}")

    if status == 403 and "blocked" in body:
        print("  Result:  PASS")
        return True
    else:
        print(f"  Result:  FAIL (expected 403 with 'blocked' key)")
        return False


def test_empty_input(url: str) -> bool:
    """Test 3: Empty input should return 400."""
    print("\n[TEST 3] Empty Input (expect 400 Bad Request)")
    payload = {"text": ""}
    print(f"  Payload: {json.dumps(payload)}")

    status, body = send_request(url, payload)

    print(f"  Status:  {status}")
    print(f"  Body:    {json.dumps(body)}")

    if status == 400 and "error" in body:
        print("  Result:  PASS")
        return True
    else:
        print(f"  Result:  FAIL (expected 400 with 'error' key)")
        return False


def main():
    parser = argparse.ArgumentParser(description="Smoke test for Aletheia Lambda")
    parser.add_argument("--url", help="Override function URL")
    args = parser.parse_args()

    # Get function URL
    if args.url:
        url = args.url
        print(f"Using provided URL: {url}")
    else:
        print("Fetching Function URL from AWS...")
        url = get_function_url()
        print(f"Function URL: {url}")

    print("\n" + "=" * 60)
    print("ALETHEIA SMOKE TEST")
    print("=" * 60)

    # Run tests
    results = []
    results.append(("Valid Input", test_valid_input(url)))
    results.append(("Blocked Input", test_blocked_input(url)))
    results.append(("Empty Input", test_empty_input(url)))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {name}: {status}")

    print(f"\nTotal: {passed}/{total} passed")

    if passed == total:
        print("\nSMOKE TEST PASSED")
        return 0
    else:
        print("\nSMOKE TEST FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
