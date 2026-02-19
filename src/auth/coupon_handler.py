"""Coupon redemption handler for manual subscription upgrades.

Issue #367: Manual Subscriptions with Coupons.

Provides POST /redeem-coupon endpoint with:
- Coupon code validation (16 uppercase alphanumeric)
- Atomic redemption via DynamoDB conditional writes
- Tier upgrade on successful redemption
- Email collection (optional)
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any

import boto3
from botocore.exceptions import ClientError

from .jwt_service import get_jwt_secret, validate_jwt, validate_jwt_dual_secret
from .auth_middleware import extract_token

logger = logging.getLogger(__name__)

# Table names
COUPONS_TABLE = os.environ.get("COUPONS_TABLE", "aletheia-coupons")
USERS_TABLE = os.environ.get("USERS_TABLE", "aletheia-users")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# Validation patterns
_COUPON_CODE_RE = re.compile(r"^[A-Z0-9]{16}$")
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

# Lazy client
_dynamodb_client = None


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


def validate_coupon_code(code: str) -> bool:
    """Validate coupon code format: 16 uppercase alphanumeric chars."""
    return bool(_COUPON_CODE_RE.match(code))


def validate_email(email: str) -> bool:
    """Validate email format per RFC 5322 (simplified)."""
    if not email or len(email) > 254:
        return False
    return bool(_EMAIL_RE.match(email))


def handle_redeem_coupon(event: dict, context: Any = None) -> dict:
    """Handle POST /redeem-coupon request.

    Requires JWT authentication. Validates coupon code, checks validity,
    performs atomic redemption, and upgrades user tier.

    Args:
        event: Lambda event with body containing {code, email?}.
        context: Lambda context.

    Returns:
        Lambda response dict.
    """
    # Step 1: Authenticate
    token = extract_token(event)
    if token is None:
        return _build_response(401, {"error": "Unauthorized"})

    try:
        primary_secret = get_jwt_secret()
    except RuntimeError:
        return _build_response(401, {"error": "Unauthorized"})

    secondary_secret = os.environ.get("JWT_SECONDARY_SECRET")
    if secondary_secret:
        auth_result = validate_jwt_dual_secret(token, primary_secret, secondary_secret)
    else:
        auth_result = validate_jwt(token, primary_secret)

    if not auth_result["success"]:
        return _build_response(401, {"error": "Unauthorized"})

    user_id = str(auth_result["user_id"])

    # Step 2: Parse body
    body = {}
    if event.get("body"):
        body = (
            json.loads(event["body"])
            if isinstance(event["body"], str)
            else event["body"]
        )

    raw_code = body.get("code", "")
    code = raw_code.strip().upper()  # Case-insensitive input
    email = body.get("email", "").strip() if body.get("email") else None

    # Step 3: Validate input
    if not code or not validate_coupon_code(code):
        return _build_response(400, {"error": "Invalid coupon code format"})

    if email and not validate_email(email):
        return _build_response(400, {"error": "Invalid email format"})

    # Step 4: Log attempt
    logger.info(json.dumps({
        "action": "coupon_redeem_attempt",
        "user_id": user_id,
        "code_prefix": code[:4] + "****",  # Log prefix only for debugging
    }))

    # Step 5: Redeem
    client = _get_dynamodb_client()
    result = redeem_coupon(client, code, user_id, email)

    if result["success"]:
        return _build_response(200, {
            "status": "success",
            "tier": result["tier"],
            "message": f"Upgraded to {result['tier']}",
        })
    else:
        status_code = 400 if result["error"] != "internal_error" else 500
        return _build_response(status_code, {"error": result["error"]})


def redeem_coupon(
    client: Any,
    code: str,
    user_id: str,
    email: str | None = None,
) -> dict[str, Any]:
    """Perform atomic coupon redemption.

    Uses DynamoDB conditional writes to prevent race conditions.

    Args:
        client: DynamoDB client.
        code: Coupon code (16 uppercase alphanumeric).
        user_id: Authenticated user ID.
        email: Optional email to save.

    Returns:
        Dict with success, tier, or error fields.
    """
    # Get coupon
    try:
        result = client.get_item(
            TableName=COUPONS_TABLE,
            Key={"code": {"S": code}},
        )
    except ClientError as e:
        logger.error(f"DynamoDB get_item error: {e}")
        return {"success": False, "error": "internal_error"}

    item = result.get("Item")
    if item is None:
        return {"success": False, "error": "invalid_code"}

    # Check revoked (same error as not found — prevents enumeration)
    if item.get("revoked", {}).get("BOOL", False):
        return {"success": False, "error": "invalid_code"}

    # Check expiry
    expiry = int(item.get("expiry", {}).get("N", "0"))
    if expiry > 0 and time.time() > expiry:
        return {"success": False, "error": "code_expired"}

    # Check uses
    max_uses = int(item.get("max_uses", {}).get("N", "1"))
    current_uses = int(item.get("uses", {}).get("N", "0"))
    if current_uses >= max_uses:
        return {"success": False, "error": "code_exhausted"}

    tier = item.get("tier", {}).get("S", "subscriber")

    # Atomic increment + append to redeemed_by
    try:
        client.update_item(
            TableName=COUPONS_TABLE,
            Key={"code": {"S": code}},
            UpdateExpression=(
                "SET uses = uses + :one "
                "ADD redeemed_by :user_set"
            ),
            ConditionExpression=(
                "uses < :max "
                "AND (attribute_not_exists(revoked) OR revoked = :false) "
                "AND (attribute_not_exists(expiry) OR expiry = :zero OR expiry > :now)"
            ),
            ExpressionAttributeValues={
                ":one": {"N": "1"},
                ":user_set": {"SS": [user_id]},
                ":max": {"N": str(max_uses)},
                ":false": {"BOOL": False},
                ":now": {"N": str(int(time.time()))},
                ":zero": {"N": "0"},
            },
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return {"success": False, "error": "code_exhausted"}
        logger.error(f"DynamoDB update_item error: {e}")
        return {"success": False, "error": "internal_error"}

    # Upgrade user tier
    try:
        update_expr = "SET tier = :tier"
        expr_values: dict[str, Any] = {":tier": {"S": tier}}

        if email:
            update_expr += ", email = :email"
            expr_values[":email"] = {"S": email}

        client.update_item(
            TableName=USERS_TABLE,
            Key={"user_id": {"S": user_id}},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values,
        )
    except ClientError as e:
        logger.error(f"Failed to upgrade user tier: {e}")
        # Coupon was consumed but tier upgrade failed — log for manual resolution
        return {"success": False, "error": "internal_error"}

    logger.info(json.dumps({
        "action": "coupon_redeemed",
        "user_id": user_id,
        "tier": tier,
        "code_prefix": code[:4] + "****",
    }))

    return {"success": True, "tier": tier}


def _build_response(status_code: int, body: dict) -> dict:
    """Build Lambda response."""
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
