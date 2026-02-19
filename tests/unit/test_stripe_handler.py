"""Tests for Stripe billing handler.

Issue #366: Full Billing with Stripe.
"""

import json
import time
import uuid
from unittest.mock import MagicMock, patch

import jwt
import stripe

from src.auth.stripe_handler import (
    handle_create_checkout,
    handle_subscription_status,
    handle_webhook,
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

JWT_SECRET = "test-secret-key-for-stripe-handler-testing-only-32chars!"


def _make_jwt(tier: str = "free", user_id: str = "user-123") -> str:
    """Create a test JWT with all required fields."""
    payload = {
        "user_id": user_id,
        "tier": tier,
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def _make_event(
    method: str = "POST",
    path: str = "/create-checkout-session",
    token: str | None = None,
    body: str | None = None,
    headers: dict | None = None,
) -> dict:
    """Create a Lambda event."""
    h: dict[str, str] = headers or {}
    if token:
        h["authorization"] = f"Bearer {token}"
    event: dict = {
        "requestContext": {"http": {"method": method, "path": path}},
        "headers": h,
    }
    if body is not None:
        event["body"] = body
    return event


# --------------------------------------------------------------------------- #
# Checkout Tests
# --------------------------------------------------------------------------- #


class TestCreateCheckout:
    """T010, T160: Checkout session creation."""

    @patch("src.auth.stripe_handler.get_jwt_secret", return_value=JWT_SECRET)
    def test_401_no_auth(self, _mock_secret):
        """Returns 401 when not authenticated."""
        event = _make_event(token=None)
        result = handle_create_checkout(event)
        assert result["statusCode"] == 401

    @patch("src.auth.stripe_handler.stripe")
    @patch("src.auth.stripe_handler._get_dynamodb_client")
    @patch("src.auth.stripe_handler.get_stripe_api_key", return_value="sk_test_xxx")
    @patch("src.auth.stripe_handler.get_jwt_secret", return_value=JWT_SECRET)
    def test_checkout_session_created(
        self, _mock_jwt, _mock_stripe_key, mock_ddb, mock_stripe
    ):
        """T010: Returns checkout URL on success."""
        mock_client = MagicMock()
        mock_ddb.return_value = mock_client
        mock_client.get_item.return_value = {"Item": {}}

        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_session.id = "cs_test_123"
        mock_stripe.checkout.Session.create.return_value = mock_session

        token = _make_jwt()
        event = _make_event(token=token)
        result = handle_create_checkout(event)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["checkout_url"] == "https://checkout.stripe.com/test"
        assert body["session_id"] == "cs_test_123"

    @patch("src.auth.stripe_handler.stripe")
    @patch("src.auth.stripe_handler._get_dynamodb_client")
    @patch("src.auth.stripe_handler.get_stripe_api_key", return_value="sk_test_xxx")
    @patch("src.auth.stripe_handler.get_jwt_secret", return_value=JWT_SECRET)
    def test_checkout_with_email(
        self, _mock_jwt, _mock_stripe_key, mock_ddb, mock_stripe
    ):
        """T160: Email pre-filled when available."""
        mock_client = MagicMock()
        mock_ddb.return_value = mock_client
        mock_client.get_item.return_value = {
            "Item": {"email": {"S": "user@example.com"}}
        }

        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_session.id = "cs_test_456"
        mock_stripe.checkout.Session.create.return_value = mock_session

        token = _make_jwt()
        event = _make_event(token=token)
        handle_create_checkout(event)

        create_call = mock_stripe.checkout.Session.create.call_args
        assert create_call.kwargs["customer_email"] == "user@example.com"

    @patch("src.auth.stripe_handler.stripe")
    @patch("src.auth.stripe_handler._get_dynamodb_client")
    @patch("src.auth.stripe_handler.get_stripe_api_key", return_value="sk_test_xxx")
    @patch("src.auth.stripe_handler.get_jwt_secret", return_value=JWT_SECRET)
    def test_checkout_stripe_error(
        self, _mock_jwt, _mock_stripe_key, mock_ddb, mock_stripe
    ):
        """Returns 500 on Stripe API error."""
        mock_client = MagicMock()
        mock_ddb.return_value = mock_client
        mock_client.get_item.return_value = {"Item": {}}
        mock_stripe.checkout.Session.create.side_effect = stripe.StripeError("fail")
        mock_stripe.StripeError = stripe.StripeError

        token = _make_jwt()
        event = _make_event(token=token)
        result = handle_create_checkout(event)

        assert result["statusCode"] == 500


# --------------------------------------------------------------------------- #
# Webhook Tests
# --------------------------------------------------------------------------- #


class TestWebhook:
    """T020-T030, T080, T110, T150: Webhook handling."""

    def test_400_missing_signature(self):
        """T030: Returns 400 when signature header missing."""
        event = _make_event(
            path="/stripe-webhook",
            body='{"test": true}',
            headers={},
        )
        result = handle_webhook(event)
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "Missing" in body["error"]

    @patch("src.auth.stripe_handler.get_webhook_secret", return_value="whsec_test")
    @patch("src.auth.stripe_handler.stripe")
    def test_400_invalid_signature(self, mock_stripe, _mock_secret):
        """T030: Returns 400 on invalid signature."""
        mock_stripe.Webhook.construct_event.side_effect = (
            stripe.SignatureVerificationError("bad sig", "sig_header")
        )
        mock_stripe.SignatureVerificationError = stripe.SignatureVerificationError

        event = _make_event(
            path="/stripe-webhook",
            body='{"test": true}',
            headers={"stripe-signature": "t=123,v1=invalid"},
        )
        result = handle_webhook(event)

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "Invalid webhook signature" in body["error"]

    @patch("src.auth.stripe_handler.mark_event_processed")
    @patch("src.auth.stripe_handler.is_event_processed", return_value=False)
    @patch("src.auth.stripe_handler.handle_checkout_completed")
    @patch("src.auth.stripe_handler._get_dynamodb_client")
    @patch("src.auth.stripe_handler.get_webhook_secret", return_value="whsec_test")
    @patch("src.auth.stripe_handler.stripe")
    def test_valid_checkout_event(
        self,
        mock_stripe,
        _mock_secret,
        mock_ddb,
        mock_checkout_handler,
        mock_is_processed,
        mock_mark_processed,
    ):
        """T020: Valid webhook processes checkout event."""
        mock_stripe.Webhook.construct_event.return_value = {
            "id": "evt_123",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "customer": "cus_test",
                    "subscription": "sub_test",
                    "metadata": {"user_id": "user-123"},
                }
            },
        }
        mock_stripe.SignatureVerificationError = stripe.SignatureVerificationError

        event = _make_event(
            path="/stripe-webhook",
            body='{}',
            headers={"stripe-signature": "t=123,v1=valid"},
        )
        result = handle_webhook(event)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["status"] == "processed"
        mock_checkout_handler.assert_called_once()
        mock_mark_processed.assert_called_once()

    @patch("src.auth.stripe_handler.is_event_processed", return_value=True)
    @patch("src.auth.stripe_handler._get_dynamodb_client")
    @patch("src.auth.stripe_handler.get_webhook_secret", return_value="whsec_test")
    @patch("src.auth.stripe_handler.stripe")
    def test_duplicate_event_ignored(
        self, mock_stripe, _mock_secret, mock_ddb, mock_is_processed
    ):
        """T080: Duplicate event returns 200 but is not reprocessed."""
        mock_stripe.Webhook.construct_event.return_value = {
            "id": "evt_duplicate",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "metadata": {"user_id": "user-123"},
                }
            },
        }
        mock_stripe.SignatureVerificationError = stripe.SignatureVerificationError

        event = _make_event(
            path="/stripe-webhook",
            body='{}',
            headers={"stripe-signature": "t=123,v1=valid"},
        )
        result = handle_webhook(event)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["status"] == "ignored"
        assert "already processed" in body["reason"]

    @patch("src.auth.stripe_handler.is_event_processed", return_value=False)
    @patch("src.auth.stripe_handler._get_dynamodb_client")
    @patch("src.auth.stripe_handler.get_webhook_secret", return_value="whsec_test")
    @patch("src.auth.stripe_handler.stripe")
    def test_unknown_event_returns_200(
        self, mock_stripe, _mock_secret, mock_ddb, mock_is_processed
    ):
        """T110: Unknown event type acknowledged with 200."""
        mock_stripe.Webhook.construct_event.return_value = {
            "id": "evt_unknown",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "metadata": {"user_id": "user-123"},
                }
            },
        }
        mock_stripe.SignatureVerificationError = stripe.SignatureVerificationError

        event = _make_event(
            path="/stripe-webhook",
            body='{}',
            headers={"stripe-signature": "t=123,v1=valid"},
        )
        result = handle_webhook(event)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["status"] == "ignored"
        assert "Unknown event type" in body["reason"]

    @patch("src.auth.stripe_handler.get_webhook_secret")
    def test_secrets_retrieval(self, mock_get_secret):
        """T150: Webhook secret retrieved from Secrets Manager."""
        mock_get_secret.side_effect = Exception("Secrets Manager error")

        event = _make_event(
            path="/stripe-webhook",
            body='{}',
            headers={"stripe-signature": "t=123,v1=test"},
        )
        result = handle_webhook(event)

        assert result["statusCode"] == 500


# --------------------------------------------------------------------------- #
# Subscription Status Tests
# --------------------------------------------------------------------------- #


class TestSubscriptionStatus:
    """T090-T110: Subscription status endpoint."""

    @patch("src.auth.stripe_handler.get_jwt_secret", return_value=JWT_SECRET)
    def test_401_no_auth(self, _mock_secret):
        """Returns 401 when not authenticated."""
        event = _make_event(method="GET", path="/subscription-status")
        result = handle_subscription_status(event)
        assert result["statusCode"] == 401

    @patch("src.auth.stripe_handler._get_dynamodb_client")
    @patch("src.auth.stripe_handler.get_jwt_secret", return_value=JWT_SECRET)
    def test_free_tier_status(self, _mock_secret, mock_ddb):
        """T090: Free tier user returns status 'none'."""
        mock_client = MagicMock()
        mock_ddb.return_value = mock_client
        mock_client.get_item.return_value = {
            "Item": {"tier": {"S": "free"}}
        }

        token = _make_jwt()
        event = _make_event(method="GET", path="/subscription-status", token=token)
        result = handle_subscription_status(event)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["tier"] == "free"
        assert body["status"] == "none"

    @patch("src.auth.stripe_handler._get_dynamodb_client")
    @patch("src.auth.stripe_handler.get_jwt_secret", return_value=JWT_SECRET)
    def test_premium_active_status(self, _mock_secret, mock_ddb):
        """T100: Premium user returns status 'active'."""
        mock_client = MagicMock()
        mock_ddb.return_value = mock_client
        mock_client.get_item.return_value = {
            "Item": {"tier": {"S": "premium"}}
        }

        token = _make_jwt()
        event = _make_event(method="GET", path="/subscription-status", token=token)
        result = handle_subscription_status(event)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["tier"] == "premium"
        assert body["status"] == "active"

    @patch("src.auth.stripe_handler._get_dynamodb_client")
    @patch("src.auth.stripe_handler.get_jwt_secret", return_value=JWT_SECRET)
    def test_grace_period_status(self, _mock_secret, mock_ddb):
        """T110: User in grace period shows remaining days."""
        mock_client = MagicMock()
        mock_ddb.return_value = mock_client
        grace_end = int(time.time()) + (3 * 86400)  # 3 days from now
        mock_client.get_item.return_value = {
            "Item": {
                "tier": {"S": "premium"},
                "grace_period_end": {"N": str(grace_end)},
            }
        }

        token = _make_jwt()
        event = _make_event(method="GET", path="/subscription-status", token=token)
        result = handle_subscription_status(event)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["status"] == "grace_period"
        assert body["grace_period_days_remaining"] >= 2

    @patch("src.auth.stripe_handler._get_dynamodb_client")
    @patch("src.auth.stripe_handler.get_jwt_secret", return_value=JWT_SECRET)
    def test_expired_grace_period(self, _mock_secret, mock_ddb):
        """Expired grace period shows as active (not in grace)."""
        mock_client = MagicMock()
        mock_ddb.return_value = mock_client
        mock_client.get_item.return_value = {
            "Item": {
                "tier": {"S": "premium"},
                "grace_period_end": {"N": "1000000000"},  # Long past
            }
        }

        token = _make_jwt()
        event = _make_event(method="GET", path="/subscription-status", token=token)
        result = handle_subscription_status(event)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["status"] == "active"
