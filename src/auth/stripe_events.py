"""Stripe event handlers for subscription lifecycle.

Issue #366: Full Billing with Stripe.

Handles:
- checkout.session.completed → tier upgrade + store Stripe IDs
- invoice.paid → clear grace period
- invoice.payment_failed → set 7-day grace period
- customer.subscription.deleted → downgrade to free
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

USERS_TABLE = os.environ.get("USERS_TABLE", "aletheia-users")
GRACE_PERIOD_DAYS = 7
GRACE_PERIOD_SECONDS = GRACE_PERIOD_DAYS * 86400


def handle_checkout_completed(
    client: Any, event_data: dict, user_id: str
) -> None:
    """Handle checkout.session.completed — upgrade tier and store Stripe IDs."""
    customer_id = event_data.get("customer", "")
    subscription_id = event_data.get("subscription", "")

    update_expr = "SET tier = :tier"
    expr_values: dict[str, Any] = {":tier": {"S": "premium"}}

    if customer_id:
        update_expr += ", stripe_customer_id = :cid"
        expr_values[":cid"] = {"S": customer_id}

    if subscription_id:
        update_expr += ", stripe_subscription_id = :sid"
        expr_values[":sid"] = {"S": subscription_id}

    client.update_item(
        TableName=USERS_TABLE,
        Key={"user_id": {"S": user_id}},
        UpdateExpression=update_expr,
        ExpressionAttributeValues=expr_values,
    )

    logger.info(f"User {user_id} upgraded to premium via Stripe checkout")


def handle_invoice_paid(
    client: Any, event_data: dict, user_id: str
) -> None:
    """Handle invoice.paid — clear grace period if set."""
    client.update_item(
        TableName=USERS_TABLE,
        Key={"user_id": {"S": user_id}},
        UpdateExpression="REMOVE grace_period_end",
    )

    logger.info(f"Grace period cleared for user {user_id}")


def handle_invoice_payment_failed(
    client: Any, event_data: dict, user_id: str
) -> None:
    """Handle invoice.payment_failed — set 7-day grace period."""
    grace_end = calculate_grace_period_end()

    client.update_item(
        TableName=USERS_TABLE,
        Key={"user_id": {"S": user_id}},
        UpdateExpression="SET grace_period_end = :end",
        ExpressionAttributeValues={":end": {"N": str(grace_end)}},
    )

    logger.info(f"Grace period set for user {user_id}, ends at {grace_end}")


def handle_subscription_deleted(
    client: Any, event_data: dict, user_id: str
) -> None:
    """Handle customer.subscription.deleted — downgrade to free."""
    client.update_item(
        TableName=USERS_TABLE,
        Key={"user_id": {"S": user_id}},
        UpdateExpression=(
            "SET tier = :tier "
            "REMOVE grace_period_end, stripe_subscription_id"
        ),
        ExpressionAttributeValues={":tier": {"S": "free"}},
    )

    logger.info(f"User {user_id} downgraded to free (subscription deleted)")


def is_event_processed(
    client: Any, event_id: str, user_id: str
) -> bool:
    """Check if a Stripe event has already been processed (idempotency)."""
    try:
        result = client.get_item(
            TableName=USERS_TABLE,
            Key={"user_id": {"S": user_id}},
            ProjectionExpression="processed_events",
        )
        item = result.get("Item", {})
        processed = item.get("processed_events", {}).get("SS", [])
        return event_id in processed
    except ClientError:
        return False


def mark_event_processed(
    client: Any, event_id: str, user_id: str
) -> None:
    """Mark a Stripe event as processed in the user record."""
    client.update_item(
        TableName=USERS_TABLE,
        Key={"user_id": {"S": user_id}},
        UpdateExpression="ADD processed_events :eid",
        ExpressionAttributeValues={":eid": {"SS": [event_id]}},
    )


def calculate_grace_period_end() -> int:
    """Calculate grace period end timestamp (now + 7 days)."""
    return int(time.time()) + GRACE_PERIOD_SECONDS
