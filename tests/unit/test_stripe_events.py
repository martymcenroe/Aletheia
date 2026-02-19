"""Tests for Stripe event processing.

Issue #366: Full Billing with Stripe.
"""

import time
from unittest.mock import MagicMock

from src.auth.stripe_events import (
    GRACE_PERIOD_SECONDS,
    calculate_grace_period_end,
    handle_checkout_completed,
    handle_invoice_paid,
    handle_invoice_payment_failed,
    handle_subscription_deleted,
    is_event_processed,
    mark_event_processed,
)


# --------------------------------------------------------------------------- #
# Event Handler Tests
# --------------------------------------------------------------------------- #


class TestCheckoutCompleted:
    """T040: checkout.session.completed → tier upgrade."""

    def test_upgrades_tier_to_premium(self):
        """T040: User tier becomes premium after checkout."""
        client = MagicMock()
        event_data = {
            "customer": "cus_test_xyz",
            "subscription": "sub_test_456",
            "metadata": {"user_id": "user-123"},
        }

        handle_checkout_completed(client, event_data, "user-123")

        client.update_item.assert_called_once()
        call_kwargs = client.update_item.call_args.kwargs
        assert ":tier" in call_kwargs["ExpressionAttributeValues"]
        assert call_kwargs["ExpressionAttributeValues"][":tier"]["S"] == "premium"

    def test_stores_stripe_customer_id(self):
        """Stores stripe_customer_id on user record."""
        client = MagicMock()
        event_data = {
            "customer": "cus_test_xyz",
            "subscription": "sub_test_456",
        }

        handle_checkout_completed(client, event_data, "user-123")

        call_kwargs = client.update_item.call_args.kwargs
        assert ":cid" in call_kwargs["ExpressionAttributeValues"]
        assert call_kwargs["ExpressionAttributeValues"][":cid"]["S"] == "cus_test_xyz"

    def test_stores_stripe_subscription_id(self):
        """Stores stripe_subscription_id on user record."""
        client = MagicMock()
        event_data = {
            "customer": "cus_test_xyz",
            "subscription": "sub_test_456",
        }

        handle_checkout_completed(client, event_data, "user-123")

        call_kwargs = client.update_item.call_args.kwargs
        assert ":sid" in call_kwargs["ExpressionAttributeValues"]
        assert call_kwargs["ExpressionAttributeValues"][":sid"]["S"] == "sub_test_456"


class TestInvoicePaid:
    """T050: invoice.paid → clear grace period."""

    def test_clears_grace_period(self):
        """T050: Grace period removed after payment success."""
        client = MagicMock()
        event_data = {"customer": "cus_test_xyz"}

        handle_invoice_paid(client, event_data, "user-123")

        client.update_item.assert_called_once()
        call_kwargs = client.update_item.call_args.kwargs
        assert "REMOVE grace_period_end" in call_kwargs["UpdateExpression"]


class TestInvoicePaymentFailed:
    """T060: invoice.payment_failed → set grace period."""

    def test_sets_grace_period(self):
        """T060: Grace period set to now + 7 days."""
        client = MagicMock()
        event_data = {"customer": "cus_test_xyz"}
        before = int(time.time())

        handle_invoice_payment_failed(client, event_data, "user-123")

        client.update_item.assert_called_once()
        call_kwargs = client.update_item.call_args.kwargs
        grace_end = int(call_kwargs["ExpressionAttributeValues"][":end"]["N"])

        # Should be approximately 7 days from now
        expected_min = before + GRACE_PERIOD_SECONDS
        expected_max = expected_min + 5  # 5 second tolerance
        assert expected_min <= grace_end <= expected_max


class TestSubscriptionDeleted:
    """T070: customer.subscription.deleted → downgrade."""

    def test_downgrades_to_free(self):
        """T070: User tier becomes free after subscription deletion."""
        client = MagicMock()
        event_data = {"customer": "cus_test_xyz"}

        handle_subscription_deleted(client, event_data, "user-123")

        client.update_item.assert_called_once()
        call_kwargs = client.update_item.call_args.kwargs
        assert call_kwargs["ExpressionAttributeValues"][":tier"]["S"] == "free"

    def test_removes_grace_period_and_subscription_id(self):
        """Removes grace_period_end and stripe_subscription_id on delete."""
        client = MagicMock()
        event_data = {"customer": "cus_test_xyz"}

        handle_subscription_deleted(client, event_data, "user-123")

        call_kwargs = client.update_item.call_args.kwargs
        assert "REMOVE" in call_kwargs["UpdateExpression"]
        assert "grace_period_end" in call_kwargs["UpdateExpression"]
        assert "stripe_subscription_id" in call_kwargs["UpdateExpression"]


# --------------------------------------------------------------------------- #
# Idempotency Tests
# --------------------------------------------------------------------------- #


class TestIdempotency:
    """T080, T140: Event deduplication."""

    def test_unprocessed_event_returns_false(self):
        """New event is not yet processed."""
        client = MagicMock()
        client.get_item.return_value = {"Item": {}}

        assert is_event_processed(client, "evt_new", "user-123") is False

    def test_processed_event_returns_true(self):
        """T140: Previously processed event detected."""
        client = MagicMock()
        client.get_item.return_value = {
            "Item": {
                "processed_events": {"SS": ["evt_old_1", "evt_old_2"]}
            }
        }

        assert is_event_processed(client, "evt_old_1", "user-123") is True

    def test_no_processed_events_field(self):
        """User record without processed_events returns False."""
        client = MagicMock()
        client.get_item.return_value = {
            "Item": {"user_id": {"S": "user-123"}}
        }

        assert is_event_processed(client, "evt_new", "user-123") is False

    def test_mark_event_adds_to_set(self):
        """mark_event_processed adds event ID to StringSet."""
        client = MagicMock()

        mark_event_processed(client, "evt_123", "user-123")

        client.update_item.assert_called_once()
        call_kwargs = client.update_item.call_args.kwargs
        assert "ADD processed_events" in call_kwargs["UpdateExpression"]
        assert "evt_123" in call_kwargs["ExpressionAttributeValues"][":eid"]["SS"]

    def test_dynamodb_error_returns_false(self):
        """DynamoDB error on idempotency check returns False (fail-open)."""
        from botocore.exceptions import ClientError

        client = MagicMock()
        client.get_item.side_effect = ClientError(
            {"Error": {"Code": "InternalServerError", "Message": ""}},
            "GetItem",
        )

        assert is_event_processed(client, "evt_123", "user-123") is False


# --------------------------------------------------------------------------- #
# Grace Period Calculation
# --------------------------------------------------------------------------- #


class TestGracePeriod:
    """Grace period calculation tests."""

    def test_grace_period_7_days_from_now(self):
        """Grace period end is 7 days from now."""
        before = int(time.time())
        result = calculate_grace_period_end()
        after = int(time.time())

        assert before + GRACE_PERIOD_SECONDS <= result <= after + GRACE_PERIOD_SECONDS
