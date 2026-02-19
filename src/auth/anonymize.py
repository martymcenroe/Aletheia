"""User ID anonymization for privacy-preserving logging.

Issue #369: CloudWatch Usage Dashboard.

Provides a deterministic hash function that converts user IDs into
12-character hex strings for log correlation without exposing PII.
"""

import hashlib


def anonymize_user_id(user_id: str) -> str:
    """Hash user ID for privacy-preserving logging.

    Returns 12-character hex string derived from SHA-256 hash.
    Used for pattern correlation in logs without exposing PII.

    Args:
        user_id: The raw user ID (e.g., LinkedIn sub claim).

    Returns:
        12-character lowercase hex string.
    """
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]
