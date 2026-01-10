"""
Benchmark tests for Lambda handler performance.

Issue #161: Automated performance benchmarks in CI.
See: docs/lld/active/1161-ci-performance-benchmarks.md

These tests use pytest-benchmark to measure Lambda handler latency
with mocked AWS services (Bedrock, DynamoDB).

Targets (from 0812-audit-performance.md):
- Lambda warm invocation: < 100ms
- Total handler time (mocked): < 50ms baseline (no network I/O)

Run with: poetry run pytest tests/benchmark/ --benchmark-only
"""
import pytest
from unittest.mock import MagicMock, patch


# Mock denylist - safe terms only
MOCK_DENYLIST = {"test_block_term", "forbidden_fruit"}


def create_mock_bedrock_response(text: str) -> dict:
    """Create a mock Bedrock response for testing."""
    return {
        "body": MagicMock(read=lambda: b'{"content": [{"text": "{\\"analysis\\": \\"test\\"}"}]}'),
        "ResponseMetadata": {"HTTPStatusCode": 200},
    }


def create_mock_dynamodb_response() -> dict:
    """Create a mock DynamoDB PutItem response."""
    return {"ResponseMetadata": {"HTTPStatusCode": 200}}


@pytest.fixture
def mock_aws_clients():
    """Fixture to mock all AWS clients for benchmarking."""
    from src.guardrails.semantic import BLOCK_TYPE_NONE
    import json

    with (
        patch("src.lambda_function.get_bedrock_client") as mock_bedrock,
        patch("src.lambda_function.get_dynamodb_client") as mock_dynamo,
        patch("src.lambda_function.get_semantic_guardrail") as mock_semantic,
    ):
        # Configure Bedrock mock - return valid structured JSON response
        mock_response = {
            "body": MagicMock(
                read=MagicMock(
                    return_value=json.dumps({
                        "content": [{
                            "type": "text",
                            "text": '{"signal": "Common Noun", "gem": "Test result.", "context": "Test context."}'
                        }]
                    }).encode()
                )
            )
        }
        bedrock_client = MagicMock()
        bedrock_client.invoke_model.return_value = mock_response
        mock_bedrock.return_value = bedrock_client

        # Configure DynamoDB mock
        dynamo_client = MagicMock()
        dynamo_client.put_item.return_value = create_mock_dynamodb_response()
        mock_dynamo.return_value = dynamo_client

        # Configure semantic guardrail mock (pass through)
        semantic_guard = MagicMock()
        semantic_guard.check_safety.return_value = {
            "block_type": BLOCK_TYPE_NONE,
            "category": "None",
            "is_safe": True,
            "reason": "None",
            "scores": {},
        }
        mock_semantic.return_value = semantic_guard

        yield {
            "bedrock": bedrock_client,
            "dynamodb": dynamo_client,
            "semantic": semantic_guard,
        }


@pytest.mark.benchmark
class TestLambdaHandlerBenchmark:
    """Benchmark tests for Lambda handler latency."""

    def test_lambda_handler_warm_invocation(self, benchmark, mock_aws_clients):
        """
        Benchmark: Lambda handler warm invocation latency.

        Target: < 100ms (from 0812-audit-performance.md)
        Baseline: ~10-30ms with all mocks (no network I/O)

        Uses pytest-benchmark to measure median latency over multiple iterations.
        """
        from src.lambda_function import lambda_handler

        event = {
            "text": "apple",
            "url": "https://example.com",
            "mode": "concise",
        }
        context = MagicMock()

        # Run benchmark - pass empty denylist to avoid file loading
        result = benchmark(lambda_handler, event, context, denylist=set())

        # Verify handler succeeded
        assert result["statusCode"] == 200

    def test_lambda_handler_with_denylist_block(self, benchmark, mock_aws_clients):
        """
        Benchmark: Lambda handler with denylist block (fast path).

        Denylist blocks should be very fast since they skip Bedrock calls.
        Target: < 10ms
        """
        from src.lambda_function import lambda_handler
        import json

        event = {
            "text": "test_block_term",  # In MOCK_DENYLIST
            "url": "https://example.com",
        }
        context = MagicMock()

        # Pass denylist with the blocked term
        result = benchmark(lambda_handler, event, context, denylist=MOCK_DENYLIST)

        # Denylist blocks return 403 with blocked status
        assert result["statusCode"] == 403
        body = json.loads(result["body"])
        assert "blocked" in body

    def test_validate_input_benchmark(self, benchmark):
        """
        Benchmark: Input validation function.

        Target: < 1ms (pure Python, no I/O)
        """
        from src.lambda_function import validate_input

        event = {"text": "apple"}

        valid, error = benchmark(validate_input, event)

        assert valid is True
        assert error is None


@pytest.mark.benchmark
class TestGuardrailBenchmark:
    """Benchmark tests for guardrail functions."""

    def test_denylist_check_benchmark(self, benchmark):
        """
        Benchmark: Denylist lookup performance.

        Target: < 1ms (set membership test)
        """
        from src.guardrails.denylist import check_denylist

        # Use safe term that's not in denylist
        result = benchmark(check_denylist, "apple", MOCK_DENYLIST)

        assert result["blocked"] is False

    def test_denylist_check_blocked_benchmark(self, benchmark):
        """
        Benchmark: Denylist lookup for blocked term.

        Target: < 1ms (set membership test)
        """
        from src.guardrails.denylist import check_denylist

        result = benchmark(check_denylist, "test_block_term", MOCK_DENYLIST)

        assert result["blocked"] is True
