"""User data models.

Issue: #364 - Tiered rate limiting with multi-window caps.
"""

from __future__ import annotations

from typing import TypedDict


class UserRecord(TypedDict):
    """User record from DynamoDB."""

    user_id: str
    tier: str
    billing_anchor_day: int
    created_at: str
