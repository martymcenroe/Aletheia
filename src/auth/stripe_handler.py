"""Stripe billing handler for subscription management.

Issue #366: Full Billing with Stripe.

Provides:
- POST /create-checkout-session — redirect to Stripe Checkout
- POST /stripe-webhook — handle Stripe webhook events
- GET /subscription-status — return user subscription state
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

import boto3
import stripe
from botocore.exceptions import ClientError

from .jwt_service import get_jwt_secret, validate_jwt, validate_jwt_dual_secret
from .auth_middleware import extract_token
from .stripe_events import (
    handle_checkout_completed,
    handle_invoice_paid,
    handle_invoice_payment_failed,
    handle_subscription_deleted,
    is_event_processed,
    mark_event_processed,
)

logger = logging.getLogger(__name__)

# Table and region
USERS_TABLE = os.environ.get("USERS_TABLE", "aletheia-users")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# Secret names
STRIPE_SECRET_NAME = os.environ.get(
    "STRIPE_SECRET_NAME", "aletheia/stripe-secret-key-test"
)
STRIPE_WEBHOOK_SECRET_NAME = os.environ.get(
    "STRIPE_WEBHOOK_SECRET_NAME", "aletheia/stripe-webhook-secret-test"
)

# URLs
SUCCESS_URL = os.environ.get(
    "STRIPE_SUCCESS_URL", "https://aletheia.study/upgrade-success"
)
CANCEL_URL = os.environ.get(
    "STRIPE_CANCEL_URL", "https://aletheia.study/upgrade-cancel"
)

# Lazy clients
_dynamodb_client = None
_secrets_client = None
_stripe_api_key: str | None = None
_webhook_secret: str | None = None


def _get_dynamodb_client():
    global _dynamodb_client
    if _dynamodb_client is None:
        endpoint = os.environ.get("DYNAMODB_ENDPOINT")
        if endpoint:
            _dynamodb_client = boto3.client(
                "dynamodb", endpoint_url=endpoint, region_name=AWS_REGION
            )
        else:
            _dynamodb_client = boto3.client("dynamodb", region_name=AWS_REGION)
    return _dynamodb_client


def _get_secrets_client():
    global _secrets_client
    if _secrets_client is None:
        _secrets_client = boto3.client("secretsmanager", region_name=AWS_REGION)
    return _secrets_client


def get_stripe_api_key() -> str:
    """Retrieve Stripe API key from Secrets Manager (cached)."""
    global _stripe_api_key
    if _stripe_api_key is not None:
        return _stripe_api_key
    client = _get_secrets_client()
    response = client.get_secret_value(SecretId=STRIPE_SECRET_NAME)
    _stripe_api_key = response["SecretString"]
    return _stripe_api_key


def get_webhook_secret() -> str:
    """Retrieve Stripe webhook signing secret from Secrets Manager (cached)."""
    global _webhook_secret
    if _webhook_secret is not None:
        return _webhook_secret
    client = _get_secrets_client()
    response = client.get_secret_value(SecretId=STRIPE_WEBHOOK_SECRET_NAME)
    _webhook_secret = response["SecretString"]
    return _webhook_secret


def _authenticate(event: dict) -> Any:
    """Authenticate JWT from event, return auth result or None."""
    token = extract_token(event)
    if token is None:
        return None

    try:
        primary_secret = get_jwt_secret()
    except RuntimeError:
        return None

    secondary_secret = os.environ.get("JWT_SECONDARY_SECRET")
    if secondary_secret:
        return validate_jwt_dual_secret(token, primary_secret, secondary_secret)
    return validate_jwt(token, primary_secret)


# --------------------------------------------------------------------------- #
# POST /create-checkout-session
# --------------------------------------------------------------------------- #


def handle_create_checkout(event: dict, context: Any = None) -> dict:
    """Handle POST /create-checkout-session.

    Creates a Stripe Checkout Session and returns the URL.
    Requires JWT authentication.
    """
    auth_result = _authenticate(event)
    if auth_result is None or not auth_result["success"]:
        return _build_response(401, {"error": "Unauthorized"})

    user_id = str(auth_result["user_id"])

    # Get user email from DynamoDB (optional, for pre-fill)
    email = None
    try:
        client = _get_dynamodb_client()
        user_record = client.get_item(
            TableName=USERS_TABLE,
            Key={"user_id": {"S": user_id}},
            ProjectionExpression="email",
        )
        item = user_record.get("Item", {})
        email = item.get("email", {}).get("S")
    except ClientError:
        pass  # Email pre-fill is optional

    try:
        api_key = get_stripe_api_key()
        stripe.api_key = api_key

        session_params: dict[str, Any] = {
            "mode": "subscription",
            "success_url": SUCCESS_URL,
            "cancel_url": CANCEL_URL,
            "metadata": {"user_id": user_id},
        }

        # Use existing price ID from env, or let Stripe use default
        price_id = os.environ.get("STRIPE_PRICE_ID")
        if price_id:
            session_params["line_items"] = [{"price": price_id, "quantity": 1}]

        if email:
            session_params["customer_email"] = email

        session = stripe.checkout.Session.create(**session_params)

        return _build_response(200, {
            "checkout_url": session.url,
            "session_id": session.id,
        })

    except stripe.StripeError as e:
        logger.error(f"Stripe checkout error: {e}")
        return _build_response(500, {"error": "Failed to create checkout session"})


# --------------------------------------------------------------------------- #
# POST /stripe-webhook
# --------------------------------------------------------------------------- #


def handle_webhook(event: dict, context: Any = None) -> dict:
    """Handle POST /stripe-webhook.

    Validates Stripe webhook signature and processes events.
    No JWT auth — uses Stripe signature verification instead.
    """
    # Get raw body for signature verification
    body = event.get("body", "")
    if event.get("isBase64Encoded"):
        import base64
        body = base64.b64decode(body).decode("utf-8")

    headers = event.get("headers", {})
    signature = headers.get("stripe-signature", headers.get("Stripe-Signature", ""))

    if not signature:
        return _build_response(400, {"error": "Missing stripe-signature header"})

    try:
        webhook_secret = get_webhook_secret()
    except Exception as e:
        logger.error(f"Failed to get webhook secret: {e}")
        return _build_response(500, {"error": "Internal error"})

    # Validate signature
    try:
        stripe_event = stripe.Webhook.construct_event(
            body, signature, webhook_secret
        )
    except stripe.SignatureVerificationError:
        logger.warning("Invalid webhook signature")
        return _build_response(400, {"error": "Invalid webhook signature"})
    except ValueError:
        logger.warning("Invalid webhook payload")
        return _build_response(400, {"error": "Invalid payload"})

    event_id = stripe_event["id"]
    event_type = stripe_event["type"]
    event_data = stripe_event["data"]["object"]

    # Extract user_id from metadata
    user_id = None
    metadata = event_data.get("metadata", {})
    user_id = metadata.get("user_id")

    # For invoice/subscription events, look up via customer
    if not user_id and event_data.get("customer"):
        user_id = _lookup_user_by_stripe_customer(event_data["customer"])

    if not user_id:
        logger.warning(f"No user_id found for event {event_id} ({event_type})")
        return _build_response(200, {"status": "ignored", "reason": "No user mapping"})

    # Idempotency check
    client = _get_dynamodb_client()
    if is_event_processed(client, event_id, user_id):
        return _build_response(200, {
            "status": "ignored",
            "reason": "Event already processed",
        })

    # Route by event type
    handlers = {
        "checkout.session.completed": handle_checkout_completed,
        "invoice.paid": handle_invoice_paid,
        "invoice.payment_failed": handle_invoice_payment_failed,
        "customer.subscription.deleted": handle_subscription_deleted,
    }

    handler = handlers.get(event_type)
    if handler:
        try:
            handler(client, event_data, user_id)
            mark_event_processed(client, event_id, user_id)
            logger.info(json.dumps({
                "action": "stripe_event_processed",
                "event_type": event_type,
                "event_id": event_id,
            }))
            return _build_response(200, {"status": "processed"})
        except Exception as e:
            logger.error(f"Error processing {event_type}: {e}")
            return _build_response(500, {"error": "Processing failed"})
    else:
        # Unknown event type — acknowledge to prevent retries
        logger.info(f"Ignoring unknown event type: {event_type}")
        return _build_response(200, {
            "status": "ignored",
            "reason": "Unknown event type",
        })


# --------------------------------------------------------------------------- #
# GET /subscription-status
# --------------------------------------------------------------------------- #


def handle_subscription_status(event: dict, context: Any = None) -> dict:
    """Handle GET /subscription-status.

    Returns current subscription state for authenticated user.
    """
    auth_result = _authenticate(event)
    if auth_result is None or not auth_result["success"]:
        return _build_response(401, {"error": "Unauthorized"})

    user_id = str(auth_result["user_id"])

    try:
        client = _get_dynamodb_client()
        result = client.get_item(
            TableName=USERS_TABLE,
            Key={"user_id": {"S": user_id}},
            ProjectionExpression="tier, grace_period_end, stripe_customer_id",
        )
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return _build_response(500, {"error": "Internal error"})

    item = result.get("Item", {})
    tier = item.get("tier", {}).get("S", "free")
    grace_end = int(item.get("grace_period_end", {}).get("N", "0"))
    now = int(time.time())

    response: dict[str, Any] = {"tier": tier}

    if grace_end > 0 and grace_end > now:
        response["status"] = "grace_period"
        response["grace_period_days_remaining"] = max(
            1, (grace_end - now) // 86400
        )
    elif tier == "premium":
        response["status"] = "active"
    else:
        response["status"] = "none"

    return _build_response(200, response)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _lookup_user_by_stripe_customer(customer_id: str) -> str | None:
    """Look up user_id by Stripe customer ID in DynamoDB.

    Uses scan since we don't have a GSI on stripe_customer_id.
    For production scale, add a GSI.
    """
    try:
        client = _get_dynamodb_client()
        result = client.scan(
            TableName=USERS_TABLE,
            FilterExpression="stripe_customer_id = :cid",
            ExpressionAttributeValues={":cid": {"S": customer_id}},
            ProjectionExpression="user_id",
            Limit=1,
        )
        items = result.get("Items", [])
        if items:
            return items[0]["user_id"]["S"]
    except ClientError as e:
        logger.error(f"Customer lookup error: {e}")
    return None


def _build_response(status_code: int, body: dict) -> dict:
    """Build Lambda response."""
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
