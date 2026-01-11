"""
Unit tests for handle_oauth_callback() - Firefox OAuth redirect endpoint.

Issue #262: Lambda OAuth callback endpoint tests.
See: docs/lld/active/1262-lambda-oauth-callback-tests.md
"""

from src.lambda_auth_function import handle_oauth_callback


class TestOAuthCallback:
    """Tests for GET /auth/callback endpoint."""

    def test_valid_code_and_state(self):
        """Happy path: LinkedIn returns code and state."""
        query_params = {"code": "test_auth_code_123", "state": "test_state_abc"}

        response = handle_oauth_callback(query_params)

        assert response["statusCode"] == 200
        assert "text/html" in response["headers"]["Content-Type"]

        body = response["body"]
        assert "Login Successful" in body
        assert 'data-code="test_auth_code_123"' in body
        assert 'data-state="test_state_abc"' in body

    def test_missing_code(self):
        """Code parameter missing - returns success HTML with empty code."""
        query_params = {"state": "test_state_abc"}

        response = handle_oauth_callback(query_params)

        assert response["statusCode"] == 200
        body = response["body"]
        # Empty code still renders (extension handles validation)
        assert 'data-code=""' in body

    def test_missing_state(self):
        """State parameter missing - returns success HTML with empty state."""
        query_params = {"code": "test_auth_code_123"}

        response = handle_oauth_callback(query_params)

        assert response["statusCode"] == 200
        body = response["body"]
        assert 'data-state=""' in body

    def test_empty_params(self):
        """Both parameters missing - returns success HTML with empty values."""
        query_params = {}

        response = handle_oauth_callback(query_params)

        assert response["statusCode"] == 200
        body = response["body"]
        assert 'data-code=""' in body
        assert 'data-state=""' in body

    def test_error_from_linkedin(self):
        """User denied access - LinkedIn returns error."""
        query_params = {
            "error": "access_denied",
            "error_description": "User denied access",
        }

        response = handle_oauth_callback(query_params)

        assert response["statusCode"] == 200
        body = response["body"]
        assert "Login Failed" in body
        assert 'data-error="access_denied"' in body
        assert "User denied access" in body

    def test_error_without_description(self):
        """Error without description - shows error code only."""
        query_params = {"error": "server_error"}

        response = handle_oauth_callback(query_params)

        assert response["statusCode"] == 200
        body = response["body"]
        assert "Login Failed" in body
        assert 'data-error="server_error"' in body

    def test_html_structure_success(self):
        """Verify success HTML has required structure for extension parsing."""
        query_params = {"code": "abc", "state": "xyz"}

        response = handle_oauth_callback(query_params)
        body = response["body"]

        # Required elements for extension
        assert "<title>Aletheia" in body
        assert 'id="oauth-result"' in body
        assert "data-code=" in body
        assert "data-state=" in body

    def test_html_structure_error(self):
        """Verify error HTML has required structure."""
        query_params = {"error": "test_error"}

        response = handle_oauth_callback(query_params)
        body = response["body"]

        assert "<title>Aletheia" in body
        assert 'id="oauth-result"' in body
        assert "data-error=" in body

    def test_xss_prevention_code(self):
        """Code parameter with XSS attempt is HTML-escaped."""
        query_params = {"code": '<script>alert("xss")</script>', "state": "safe"}

        response = handle_oauth_callback(query_params)
        body = response["body"]

        # Raw script tags MUST NOT appear - must be escaped
        assert response["statusCode"] == 200
        assert "<script>" not in body
        assert "&lt;script&gt;" in body  # Escaped version present

    def test_xss_prevention_error(self):
        """Error description with XSS attempt is HTML-escaped."""
        query_params = {
            "error": "test",
            "error_description": '<script>alert("xss")</script>',
        }

        response = handle_oauth_callback(query_params)
        body = response["body"]

        # Raw script tags MUST NOT appear - must be escaped
        assert response["statusCode"] == 200
        assert "<script>" not in body
        assert "&lt;script&gt;" in body  # Escaped version present

    def test_xss_prevention_state(self):
        """State parameter with XSS attempt is HTML-escaped."""
        query_params = {"code": "safe", "state": '"><img src=x onerror=alert(1)>'}

        response = handle_oauth_callback(query_params)
        body = response["body"]

        # Angle brackets must be escaped
        assert response["statusCode"] == 200
        assert "<img" not in body
        assert "&lt;img" in body or "&gt;" in body

    def test_xss_prevention_error_code(self):
        """Error code with XSS attempt is HTML-escaped."""
        query_params = {"error": '<script>bad</script>"}'}

        response = handle_oauth_callback(query_params)
        body = response["body"]

        assert response["statusCode"] == 200
        assert "<script>" not in body
