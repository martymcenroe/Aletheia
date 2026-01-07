# Implementation Report: Issue #147 - GDPR Data Erasure

**Issue:** #147 - GDPR: Implement data erasure process (right to be forgotten)
**Date:** 2026-01-06
**Implementer:** Claude Opus 4.5
**Branch:** `147-gdpr-erasure`

---

## 1. Objective

Implement GDPR Article 17 compliant data erasure endpoint allowing authenticated users to delete all their stored data on demand.

## 2. Prerequisites Verified

| Prerequisite | Status | Evidence |
|--------------|--------|----------|
| #116 LinkedIn OAuth complete | ✅ | `src/lambda_auth_function.py` has full OAuth implementation |
| DynamoDB schema has user_id | ✅ | `lambda_function.py:139-141` conditionally stores user_id |
| CloudWatch logging safe | ✅ | Grep audit found no raw event/input logging |

## 3. Implementation Details

### 3.1 GSI on user_id (provision.sh:103-129)

Added Global Secondary Index to AletheiaAgentState table:
- **Index Name:** `user_id-index`
- **Key:** `user_id` (HASH)
- **Projection:** KEYS_ONLY (minimal storage, returns thread_id + checkpoint_id for deletion)

```bash
aws dynamodb update-table \
    --attribute-definitions AttributeName=user_id,AttributeType=S \
    --global-secondary-index-updates '[{
        "Create": {
            "IndexName": "user_id-index",
            "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
            "Projection": {"ProjectionType": "KEYS_ONLY"}
        }
    }]'
```

### 3.2 IAM Policy Update (provision.sh:196-198)

Added GSI access to Lambda role:
```json
"Resource": [
    "arn:aws:dynamodb:*:*:table/AletheiaAgentState",
    "arn:aws:dynamodb:*:*:table/AletheiaAgentState/index/*",
    "arn:aws:dynamodb:*:*:table/aletheia-users"
]
```

### 3.3 Delete Function (lambda_auth_function.py:387-443)

```python
def delete_user_data(user_id: str) -> int:
    """Delete all DynamoDB items for a user from AletheiaAgentState table."""
    # 1. Query GSI by user_id (with pagination support)
    # 2. Delete each item using primary key (thread_id, checkpoint_id)
    # 3. Return count of deleted items
```

**Key design decisions:**
- Uses GSI query (not Scan) for O(1) performance
- Handles pagination for users with many items
- Deletes items individually (DynamoDB requires primary key)
- Logs deletion count for audit trail (no PII logged)

### 3.4 API Endpoint (lambda_auth_function.py:446-493)

```python
def handle_delete_my_data(headers: dict) -> dict:
    """Handle DELETE /my-data - GDPR Article 17 data erasure endpoint."""
    # 1. Validate Bearer token from Authorization header
    # 2. Call LinkedIn userinfo to get user_id
    # 3. Call delete_user_data(user_id)
    # 4. Return success response with count
```

**Route:** `DELETE /my-data`
**Authentication:** Required (Bearer token)
**Response:** `{"success": true, "itemsDeleted": N}`

### 3.5 Lambda Handler Update (lambda_auth_function.py:537-538)

Added route:
```python
elif path == "/my-data" and http_method == "DELETE":
    return handle_delete_my_data(headers)
```

### 3.6 Environment Variable (provision.sh)

Added `AGENT_STATE_TABLE` to Auth Lambda environment:
```bash
--environment "Variables={...,AGENT_STATE_TABLE=$TABLE_NAME}"
```

## 4. Documentation Updates

| Document | Changes |
|----------|---------|
| `docs/1147-gdpr-data-erasure.md` | Status BLOCKED → IMPLEMENTED, DoD updated |
| `docs/0810-audit-privacy.md` | Added #147 audit record, GDPR/CCPA status updated |
| `index.html` | Privacy policy updated with accurate data handling |

## 5. Security Considerations

| Concern | Mitigation |
|---------|------------|
| Unauthorized deletion | Requires valid LinkedIn OAuth token |
| Deletion of others' data | user_id extracted from validated token, not user input |
| Incomplete deletion | Pagination handles large datasets |
| Audit trail | Deletion count logged (no PII) |

## 6. Files Changed

| File | Lines Changed | Purpose |
|------|---------------|---------|
| `src/lambda_auth_function.py` | +115 | DELETE endpoint + delete function |
| `provision.sh` | +33 | GSI creation + IAM update |
| `docs/0810-audit-privacy.md` | +72/-4 | Audit record |
| `docs/1147-gdpr-data-erasure.md` | +20/-49 | Status update |
| `index.html` | +5/-4 | Privacy policy |

## 7. Known Limitations

1. **Legacy data:** Items created before #116 (no user_id) cannot be deleted on-demand; they expire via 30-day TTL
2. **User table not deleted:** This endpoint deletes analysis data, not user account from aletheia-users table (by design - account deletion is separate)
3. **No batch delete:** Items deleted one-by-one (DynamoDB limitation for composite keys)

## 8. Deployment Notes

After merge, run `provision.sh` to:
1. Create GSI `user_id-index` (takes ~5 minutes to become ACTIVE)
2. Update IAM policy
3. Deploy updated Auth Lambda with new endpoint
