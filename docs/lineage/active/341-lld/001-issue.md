# Issue #341: feat: Add JWT authentication to analysis endpoint with daily token cap

## Problem Statement

The main analysis Lambda does not validate authentication. Anyone can call the API directly with any userId, bypassing the extension and potentially:
- Avoiding future rate limits
- Impersonating other users
- Running up Bedrock costs via botnet

## Solution

1. Auth Lambda issues JWT after LinkedIn validation (24h expiry)
2. Main Lambda validates JWT locally (no LinkedIn call per request)
3. Daily token cap limits total tokens issued per day (default: 20)
4. Admin tool to adjust the cap without redeployment

## Acceptance Criteria

- Request without Authorization header returns 401 Unauthorized
- Request with invalid/expired JWT returns 401 Unauthorized
- Request with valid JWT proceeds to analysis
- User receives JWT after successful LinkedIn login
- JWT contains user_id and exp (24h from issuance)
- 21st token issuance of the day receives 503 Service Unavailable
- Admin can adjust daily cap via CLI tool
- All auth failures logged with action: auth_failed and reason

Labels: enhancement, security, cost-control
