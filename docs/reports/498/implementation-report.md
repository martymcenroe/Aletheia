# Implementation Report: #498 Store LinkedIn Profile Data

## Changes
- `src/lambda_auth_function.py`: `get_or_create_user()` now stores `email` and `picture` from LinkedIn OIDC userinfo response
  - On CREATE: adds email/picture to DynamoDB Item if present
  - On UPDATE: updates email/picture on each login (profile data may change)
  - Gracefully handles missing fields (no error if LinkedIn doesn't return them)

## Tests Added
- `test_get_or_create_user_stores_email_and_picture_on_create`
- `test_get_or_create_user_updates_email_and_picture_on_login`
- `test_get_or_create_user_no_email_picture_no_error`

All 7 TestUserManagement tests pass.
