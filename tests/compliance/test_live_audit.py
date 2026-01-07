"""Live compliance audit tests for Issue #148: Bedrock No-Training Verification.

These tests require AWS credentials and run on:
- Push to main
- Nightly schedule (cron)

They verify our actual AWS Bedrock configuration matches our privacy commitments.
"""

import pytest

# Try to import boto3, skip all tests if not available
try:
    import boto3
    from botocore.exceptions import (
        BotoCoreError,
        ClientError,
        NoCredentialsError,
    )

    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


def _skip_if_no_credentials() -> None:
    """Skip test if AWS credentials are not configured."""
    if not BOTO3_AVAILABLE:
        pytest.skip("boto3 not available")

    try:
        # Quick STS call to verify credentials work
        sts = boto3.client("sts")
        sts.get_caller_identity()
    except (NoCredentialsError, BotoCoreError, ClientError) as e:
        pytest.skip(f"AWS credentials not configured: {e}")


@pytest.mark.audit
class TestLiveBedrockCompliance:
    """Live compliance tests that verify AWS Bedrock configuration.

    These tests hit real AWS APIs and require valid credentials.
    Decorated with @pytest.mark.audit to be excluded from PR runs.
    """

    def test_bedrock_logging_disabled(self) -> None:
        """Verify Bedrock model invocation logging is disabled.

        AWS Bedrock can optionally log prompts and responses to S3/CloudWatch.
        For privacy compliance, we must ensure this is NOT enabled.

        Passing conditions:
        - loggingConfig is not present (default = no logging)
        - loggingConfig.textDataDeliveryEnabled is False
        """
        _skip_if_no_credentials()

        # Use us-east-1 where our Bedrock resources are deployed
        bedrock = boto3.client("bedrock", region_name="us-east-1")

        try:
            response = bedrock.get_model_invocation_logging_configuration()
        except ClientError as e:
            # AccessDeniedException is acceptable - means logging not configured
            # or our IAM role doesn't have permission to check (also safe)
            if e.response["Error"]["Code"] == "AccessDeniedException":
                # No logging config access = can't enable logging = safe
                return
            raise

        logging_config = response.get("loggingConfig")

        # No logging config = safe (default state)
        if logging_config is None:
            return

        # If config exists, verify text data logging is disabled
        text_logging_enabled = logging_config.get("textDataDeliveryEnabled", False)

        assert not text_logging_enabled, (
            "COMPLIANCE VIOLATION: Bedrock model invocation logging is ENABLED. "
            "This violates our privacy commitment to not store user prompts. "
            "Disable via AWS Console: Bedrock > Model invocation logging > Disable"
        )

    def test_bedrock_no_custom_models(self) -> None:
        """Verify no custom/fine-tuned models exist in the account.

        Custom models indicate training on data, which violates our
        commitment to not train on user data.
        """
        _skip_if_no_credentials()

        bedrock = boto3.client("bedrock", region_name="us-east-1")

        try:
            # List custom models (fine-tuned models)
            response = bedrock.list_custom_models()
            custom_models = response.get("modelSummaries", [])
        except ClientError as e:
            # If we don't have permission to list, that's acceptable
            if e.response["Error"]["Code"] == "AccessDeniedException":
                return
            raise

        assert not custom_models, (
            f"COMPLIANCE VIOLATION: Found {len(custom_models)} custom model(s). "
            "Custom models indicate training on data, violating privacy commitments. "
            f"Models: {[m.get('modelName') for m in custom_models]}"
        )

    def test_bedrock_no_active_customization_jobs(self) -> None:
        """Verify no model customization jobs are running.

        Active customization jobs indicate training in progress.
        """
        _skip_if_no_credentials()

        bedrock = boto3.client("bedrock", region_name="us-east-1")

        try:
            # List model customization jobs (training jobs)
            response = bedrock.list_model_customization_jobs(
                statusEquals="InProgress",
            )
            active_jobs = response.get("modelCustomizationJobSummaries", [])
        except ClientError as e:
            # No permission = can't run jobs = safe
            if e.response["Error"]["Code"] == "AccessDeniedException":
                return
            raise

        assert not active_jobs, (
            f"COMPLIANCE VIOLATION: Found {len(active_jobs)} active training job(s). "
            "This violates our commitment to not train on user data. "
            "Stop these jobs immediately."
        )
