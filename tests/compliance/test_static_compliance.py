"""Static compliance tests for Issue #148: Bedrock No-Training Verification.

These tests run on every PR (no AWS credentials required).
They verify our codebase doesn't contain forbidden Bedrock training APIs
and that our privacy documentation is accurate.
"""

import re
from pathlib import Path

# Forbidden Bedrock API calls that would enable model training/customization
FORBIDDEN_BEDROCK_APIS = [
    "CreateCustomModel",
    "CreateModelCustomizationJob",
    "PutModelInvocationLoggingConfiguration",
]


class TestStaticCompliance:
    """Static compliance tests that grep the codebase for policy violations."""

    def test_no_bedrock_training_apis_in_src(self) -> None:
        """Verify src/ contains no Bedrock training/customization API calls.

        If this test fails, it means someone added code that could train
        models on user data, violating our privacy commitment.
        """
        src_dir = Path(__file__).parent.parent.parent / "src"
        assert src_dir.exists(), f"src/ directory not found at {src_dir}"

        violations: list[str] = []
        for py_file in src_dir.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            for api in FORBIDDEN_BEDROCK_APIS:
                if api in content:
                    violations.append(f"{py_file.relative_to(src_dir)}: contains {api}")

        assert not violations, (
            "COMPLIANCE VIOLATION: Forbidden Bedrock APIs found:\n"
            + "\n".join(f"  - {v}" for v in violations)
        )

    def test_no_bedrock_training_apis_in_extensions(self) -> None:
        """Verify extensions/ contains no Bedrock training/customization API calls.

        Extension code shouldn't call AWS directly, but this test ensures
        no accidental backend code leaks into the frontend.
        """
        extensions_dir = Path(__file__).parent.parent.parent / "extensions"
        assert extensions_dir.exists(), "extensions/ directory not found"

        violations: list[str] = []
        for js_file in extensions_dir.rglob("*.js"):
            content = js_file.read_text(encoding="utf-8")
            for api in FORBIDDEN_BEDROCK_APIS:
                if api in content:
                    violations.append(
                        f"{js_file.relative_to(extensions_dir)}: contains {api}"
                    )

        assert not violations, (
            "COMPLIANCE VIOLATION: Forbidden Bedrock APIs found:\n"
            + "\n".join(f"  - {v}" for v in violations)
        )

    def test_privacy_docs_contain_no_training_statement(self) -> None:
        """Verify index.html contains the AWS Bedrock no-training statement.

        Our privacy policy MUST state that AWS Bedrock does not train on user data.
        """
        index_html = Path(__file__).parent.parent.parent / "web" / "index.html"
        assert index_html.exists(), "index.html not found at web/index.html"

        content = index_html.read_text(encoding="utf-8")

        # Match various phrasings of the no-training commitment
        # e.g., "AWS Bedrock does not train on your prompts"
        # e.g., "AWS Bedrock does not use your data to train"
        pattern = re.compile(
            r"AWS\s+Bedrock\s+does\s+not\s+(train|use.*train)", re.IGNORECASE
        )

        assert pattern.search(content), (
            "COMPLIANCE VIOLATION: index.html must contain statement that "
            "'AWS Bedrock does not train on your data' or similar. "
            "Current privacy policy is missing this required disclosure."
        )
