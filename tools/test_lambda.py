#!/usr/bin/env python3
"""
Direct Lambda SDK Invocation Tool for Agent Testing.

Bypasses Function URL to invoke Lambda directly, providing:
- Full response including debug timings
- Raw bytes/Unicode codepoint inspection
- noarchive flag to prevent test data pollution

Issue #288: Production Lambda Testing Infrastructure

Usage:
    poetry run python tools/test_lambda.py --term "hello"
    poetry run python tools/test_lambda.py --term "cryptocurrency" --noarchive
    poetry run python tools/test_lambda.py --term "test" --show-codepoints --json
"""

import argparse
import json
import sys
import time
import unicodedata

import boto3


LAMBDA_FUNCTION_NAME = "AletheiaAgent"
REGION = "us-east-1"


def invoke_lambda(term: str, context: str = "", noarchive: bool = False) -> dict:
    """Invoke Lambda directly via boto3 SDK.

    Returns dict with:
    - status_code: HTTP status from Lambda
    - body: Parsed response body
    - raw_payload: Raw Lambda response as string
    - latency_ms: Invocation latency
    - request_id: AWS Request ID for CloudWatch correlation
    """
    client = boto3.client("lambda", region_name=REGION)

    # Build payload matching extension format
    payload = {
        "text": term,
        "domContext": context,
        "url": "https://test.aletheia.local/agent-test",
        "signals": {"noarchive": noarchive},
    }

    lambda_event = {"body": json.dumps(payload)}

    start = time.time()
    response = client.invoke(
        FunctionName=LAMBDA_FUNCTION_NAME, Payload=json.dumps(lambda_event)
    )
    latency = int((time.time() - start) * 1000)

    raw_payload = response["Payload"].read().decode("utf-8")
    parsed = json.loads(raw_payload)

    # Extract body (may be string or dict)
    body = parsed.get("body", {})
    if isinstance(body, str):
        body = json.loads(body)

    return {
        "status_code": parsed.get("statusCode"),
        "body": body,
        "raw_payload": raw_payload,
        "latency_ms": latency,
        "request_id": response.get("ResponseMetadata", {}).get("RequestId", "unknown"),
    }


def show_unicode_codepoints(text: str, label: str = "Text") -> None:
    """Display Unicode codepoints for non-ASCII characters."""
    print(f"\n{label} - Unicode Analysis:")
    print("-" * 60)

    non_ascii = []
    for i, char in enumerate(text):
        codepoint = ord(char)
        if codepoint > 127:
            try:
                name = unicodedata.name(char)
            except ValueError:
                name = "UNKNOWN"
            non_ascii.append((i, codepoint, name, char))

    if non_ascii:
        print(f"Found {len(non_ascii)} non-ASCII characters:")
        for pos, cp, name, char in non_ascii[:20]:
            print(f"  [{pos:4d}] U+{cp:04X} {name:40s} '{char}'")
        if len(non_ascii) > 20:
            print(f"  ... and {len(non_ascii) - 20} more")
    else:
        print("No non-ASCII characters found.")


def main():
    parser = argparse.ArgumentParser(
        description="Direct Lambda SDK invocation for agent testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  poetry run python tools/test_lambda.py --term "hello"
  poetry run python tools/test_lambda.py --term "cryptocurrency" --noarchive
  poetry run python tools/test_lambda.py --term "test" --show-codepoints
  poetry run python tools/test_lambda.py --term "test" --json
        """,
    )
    parser.add_argument("--term", required=True, help="Term to analyze")
    parser.add_argument(
        "--context", default="", help="Page context for disambiguation"
    )
    parser.add_argument(
        "--noarchive", action="store_true", help="Skip DynamoDB persistence"
    )
    parser.add_argument(
        "--show-codepoints",
        action="store_true",
        help="Show Unicode codepoints in response",
    )
    parser.add_argument(
        "--json", action="store_true", help="Output as JSON (for scripting)"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )

    args = parser.parse_args()

    try:
        result = invoke_lambda(args.term, args.context, args.noarchive)
    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}))
        else:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        # Machine-readable output
        output = {
            "status_code": result["status_code"],
            "body": result["body"],
            "latency_ms": result["latency_ms"],
            "request_id": result["request_id"],
        }
        print(json.dumps(output, indent=2))
    else:
        # Human-readable output
        print(f"\n{'='*60}")
        print(f"Term: {args.term}")
        print(f"Request ID: {result['request_id']}")
        print(f"Latency: {result['latency_ms']}ms")
        print(f"Status: {result['status_code']}")
        print(f"{'='*60}")

        body = result["body"]
        print(f"\nStatus: {body.get('status', 'unknown')}")
        print(f"Signal: {body.get('signal', 'N/A')}")
        print(f"Gem: {body.get('gem', 'N/A')}")
        print(f"Context: {body.get('context', 'N/A')}")

        if args.verbose and "_debug_timings" in body:
            print("\nDebug Timings:")
            print(json.dumps(body["_debug_timings"], indent=2))

        # Check for failure indicators
        if body.get("status") == "fallback":
            print("\n*** WARNING: Response is FALLBACK - JSON parsing likely failed ***")
        if body.get("signal") == "Analysis Failed":
            print("\n*** WARNING: Analysis failed - check CloudWatch logs ***")
            print("    Use: aws logs tail /aws/lambda/AletheiaAgent --since 5m")

    if args.show_codepoints:
        # Show codepoints in relevant fields
        for field in ["signal", "gem", "context"]:
            if field in result["body"]:
                show_unicode_codepoints(result["body"][field], field)

    # Exit with appropriate code
    if result["status_code"] != 200:
        sys.exit(1)
    if result["body"].get("status") == "fallback":
        sys.exit(2)


if __name__ == "__main__":
    main()
