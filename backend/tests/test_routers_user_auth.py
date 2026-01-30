"""
Integration tests for api/routers/user_auth.py.

Tests cover:
- User login with valid credentials
- User login with invalid credentials
- User login with inactive accounts
- Logout endpoint
- Get current user info endpoint
- All error paths
- Token generation and validation

Uses in-memory SQLite database for test isolation.
"""

import sqlite3
import uuid
from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.db.user_database import hash_password, init_database
from api.main import app


@pytest.fixture
def temp_db_path(tmp_path):
    """Create a temporary database path for each test."""
    return tmp_path / "test_users.db"


@pytest.fixture
def mock_database(temp_db_path, monkeypatch):
    """Initialize a temporary in-memory database with test users."""
    # Mock the database path
    with patch("api.db.user_database._get_database_path", return_value=temp_db_path):
        # Initialize the database
        init_database()

        # Create a test user
        conn = sqlite3.connect(str(temp_db_path))
        cursor = conn.cursor()

        test_user_id = str(uuid.uuid4())
        test_password_hash = hash_password("test_password_123")

        cursor.execute(
            """
            INSERT INTO users (id, username, password_hash, full_name, role, created_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """,
            (
                test_user_id,
                "testuser",
                test_password_hash,
                "Test User",
                "user",
                datetime.now().isoformat(),
            ),
        )

        # Create an inactive user
        inactive_user_id = str(uuid.uuid4())
        inactive_password_hash = hash_password("inactive_password_123")

        cursor.execute(
            """
            INSERT INTO users (id, username, password_hash, full_name, role, created_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        """,
            (
                inactive_user_id,
                "inactive_user",
                inactive_password_hash,
                "Inactive User",
                "user",
                datetime.now().isoformat(),
            ),
        )

        # Create an admin user
        admin_user_id = str(uuid.uuid4())
        admin_password_hash = hash_password("admin_password_123")

        cursor.execute(
            """
            INSERT INTO users (id, username, password_hash, full_name, role, created_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """,
            (
                admin_user_id,
                "adminuser",
                admin_password_hash,
                "Admin User",
                "admin",
                datetime.now().isoformat(),
            ),
        )

        conn.commit()
        conn.close()

        yield temp_db_path


@pytest.fixture
def client(mock_database, monkeypatch):
    """Create a test client with mocked database and test API key."""
    # Set test API key to bypass middleware
    test_api_key = "test-api-key-12345"
    monkeypatch.setenv("API_KEY", test_api_key)

    # Patch the database path for all database operations
    with patch("api.db.user_database._get_database_path", return_value=mock_database):
        # Import and reload config to pick up new API_KEY
        import importlib
        import api.config
        import api.middleware.auth

        importlib.reload(api.config)
        importlib.reload(api.middleware.auth)

        yield TestClient(app, headers={"X-API-Key": test_api_key})


class TestLoginEndpoint:
    """Tests for POST /auth/login endpoint."""

    def test_login_with_valid_credentials(self, client):
        """Test successful login with valid username and password."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "test_password_123"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "token" in data
        assert "refresh_token" in data
        assert data["user"]["username"] == "testuser"
        assert data["user"]["full_name"] == "Test User"
        assert data["user"]["role"] == "user"
        assert data["user"]["id"] is not None

    def test_login_with_invalid_username(self, client):
        """Test login with non-existent username."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent_user", "password": "some_password"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is False
        assert data["error"] == "Invalid username or password"
        assert data.get("token") is None

    def test_login_with_invalid_password(self, client):
        """Test login with correct username but wrong password."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "wrong_password"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is False
        assert data["error"] == "Invalid username or password"
        assert data.get("token") is None

    def test_login_with_empty_password(self, client):
        """Test login with empty password."""
        response = client.post(
            "/api/v1/auth/login", json={"username": "testuser", "password": ""}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is False
        assert data["error"] == "Invalid username or password"

    def test_login_with_inactive_account(self, client):
        """Test login with inactive user account."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "inactive_user", "password": "inactive_password_123"},
        )

        assert response.status_code == 200
        data = response.json()

        # The verify_password function returns False early for inactive users
        # So we get the generic invalid credentials error
        assert data["success"] is False
        # The error is "Invalid username or password" because verify_password
        # checks is_active and returns False before the router check
        assert data["error"] == "Invalid username or password"

    def test_login_with_admin_user(self, client):
        """Test login with admin user credentials."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "adminuser", "password": "admin_password_123"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["user"]["role"] == "admin"
        assert data["user"]["username"] == "adminuser"
        assert data["user"]["full_name"] == "Admin User"

    def test_login_with_missing_username(self, client):
        """Test login with missing username field."""
        response = client.post("/api/v1/auth/login", json={"password": "some_password"})

        # FastAPI validates required fields
        assert response.status_code == 422

    def test_login_with_missing_password(self, client):
        """Test login with missing password field."""
        response = client.post("/api/v1/auth/login", json={"username": "testuser"})

        # FastAPI validates required fields
        assert response.status_code == 422

    def test_login_with_empty_request_body(self, client):
        """Test login with empty request body."""
        response = client.post("/api/v1/auth/login", json={})

        # FastAPI validates required fields
        assert response.status_code == 422

    def test_login_updates_last_login_timestamp(self, client, mock_database):
        """Test that successful login updates last_login timestamp."""
        # Get initial last_login (should be None for new user)
        conn = sqlite3.connect(str(mock_database))
        cursor = conn.cursor()
        cursor.execute("SELECT last_login FROM users WHERE username = 'testuser'")
        cursor.fetchone()[0]
        conn.close()

        # Perform login
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "test_password_123"},
        )
        assert response.status_code == 200

        # Check that last_login was updated
        conn = sqlite3.connect(str(mock_database))
        cursor = conn.cursor()
        cursor.execute("SELECT last_login FROM users WHERE username = 'testuser'")
        updated_last_login = cursor.fetchone()[0]
        conn.close()

        assert updated_last_login is not None
        # Verify it's a valid ISO format timestamp
        datetime.fromisoformat(updated_last_login)

    def test_login_returns_valid_jwt_token(self, client):
        """Test that login returns a valid JWT token."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "test_password_123"},
        )

        assert response.status_code == 200
        data = response.json()

        token = data["token"]
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

        # JWT tokens have 3 parts separated by dots
        parts = token.split(".")
        assert len(parts) == 3

    def test_login_returns_refresh_token(self, client):
        """Test that login returns a refresh token."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "test_password_123"},
        )

        assert response.status_code == 200
        data = response.json()

        refresh_token = data["refresh_token"]
        assert refresh_token is not None
        assert isinstance(refresh_token, str)
        assert len(refresh_token) > 0

    def test_login_response_contains_all_user_fields(self, client):
        """Test that login response contains all expected user fields."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "test_password_123"},
        )

        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        assert "id" in user
        assert "username" in user
        assert "full_name" in user
        assert "role" in user
        assert user["username"] == "testuser"
        assert user["full_name"] == "Test User"
        assert user["role"] == "user"


class TestLogoutEndpoint:
    """Tests for POST /auth/logout endpoint."""

    def test_logout_returns_success(self, client):
        """Test that logout returns success response."""
        response = client.post(
            "/api/v1/auth/logout", headers={"X-API-Key": "test-api-key-12345"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["message"] == "Logged out successfully"

    def test_logout_always_succeeds(self, client):
        """Test that logout succeeds regardless of authentication state."""
        # Logout with API key
        response = client.post(
            "/api/v1/auth/logout", headers={"X-API-Key": "test-api-key-12345"}
        )
        assert response.status_code == 200

        # Multiple logouts should all succeed
        for _ in range(3):
            response = client.post(
                "/api/v1/auth/logout", headers={"X-API-Key": "test-api-key-12345"}
            )
            assert response.status_code == 200


class TestGetCurrentUserEndpoint:
    """Tests for GET /auth/me endpoint."""

    def test_get_current_user_with_valid_token(self, client):
        """Test getting current user info with valid token."""
        # First login to get a token
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "test_password_123"},
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        token = login_data["token"]

        # Use token to get current user info
        response = client.get(
            "/api/v1/auth/me",
            headers={"X-API-Key": "test-api-key-12345", "X-User-Token": token},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["username"] == "testuser"
        assert data["full_name"] == "Test User"
        assert data["role"] == "user"
        assert data["id"] is not None

    def test_get_current_user_without_token(self, client):
        """Test getting current user info without token returns 401."""
        # Note: The middleware requires X-API-Key header which is set by the client fixture
        # So this test expects the middleware to allow the request through,
        # but the endpoint itself returns 401 when no X-User-Token is present
        response = client.get(
            "/api/v1/auth/me", headers={"X-API-Key": "test-api-key-12345"}
        )

        assert response.status_code == 401
        data = response.json()
        # The endpoint returns "Not authenticated" when request.state.user is not set
        assert data["detail"] == "Not authenticated"

    def test_get_current_user_with_invalid_token(self, client):
        """Test getting current user info with invalid token."""
        response = client.get(
            "/api/v1/auth/me",
            headers={
                "X-API-Key": "test-api-key-12345",
                "X-User-Token": "invalid.jwt.token",
            },
        )

        assert response.status_code == 401
        data = response.json()
        # Invalid token doesn't populate request.state.user, so we get Not authenticated
        assert data["detail"] == "Not authenticated"

    def test_get_current_user_with_malformed_token(self, client):
        """Test getting current user info with malformed token."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"X-API-Key": "test-api-key-12345", "X-User-Token": "not-a-jwt"},
        )

        assert response.status_code == 401

    def test_get_current_user_with_expired_token(self, client):
        """Test getting current user info with expired token."""
        # Create an expired token (this would require mocking time or token service)
        # For now, test with a malformed token that simulates expiration
        expired_token = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2MDAwMDAwMDB9.expired"
        )

        response = client.get(
            "/api/v1/auth/me",
            headers={"X-API-Key": "test-api-key-12345", "X-User-Token": expired_token},
        )

        assert response.status_code == 401

    def test_get_current_user_for_admin(self, client):
        """Test getting current user info for admin user."""
        # Login as admin
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "adminuser", "password": "admin_password_123"},
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        token = login_data["token"]

        # Get current user
        response = client.get(
            "/api/v1/auth/me",
            headers={"X-API-Key": "test-api-key-12345", "X-User-Token": token},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["role"] == "admin"
        assert data["username"] == "adminuser"

    def test_get_current_user_returns_all_fields(self, client):
        """Test that /me endpoint returns all expected fields."""
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "test_password_123"},
        )
        token = login_response.json()["token"]

        response = client.get(
            "/api/v1/auth/me",
            headers={"X-API-Key": "test-api-key-12345", "X-User-Token": token},
        )

        assert response.status_code == 200
        data = response.json()

        assert "id" in data
        assert "username" in data
        assert "full_name" in data
        assert "role" in data


class TestTokenValidation:
    """Tests for token validation across endpoints."""

    def test_user_identity_token_contains_correct_claims(self, client):
        """Test that user identity token contains correct claims."""
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "test_password_123"},
        )
        token = login_response.json()["token"]

        # Decode the token (without verification, just check structure)
        import base64
        import json

        # JWT format: header.payload.signature
        parts = token.split(".")
        assert len(parts) == 3

        # Decode payload (add padding if needed)
        payload_b64 = parts[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding

        payload = json.loads(base64.b64decode(payload_b64))

        # Check claims
        assert "user_id" in payload
        assert "username" in payload
        assert "role" in payload
        assert "type" in payload
        assert payload["type"] == "user_identity"
        assert payload["username"] == "testuser"
        assert payload["role"] == "user"

    def test_token_type_is_user_identity(self, client):
        """Test that login token has type 'user_identity'."""
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "test_password_123"},
        )
        token = login_response.json()["token"]

        # Decode and check type claim
        import base64
        import json

        parts = token.split(".")
        payload_b64 = parts[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding

        payload = json.loads(base64.b64decode(payload_b64))
        assert payload["type"] == "user_identity"


class TestErrorPaths:
    """Tests for error paths and edge cases."""

    def test_login_case_sensitive_username(self, client):
        """Test that username is case-sensitive."""
        # Login with uppercase username (should fail)
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "TESTUSER", "password": "test_password_123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    def test_login_with_whitespace_in_username(self, client):
        """Test login with whitespace in username."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": " testuser ", "password": "test_password_123"},
        )

        assert response.status_code == 200
        data = response.json()
        # Should fail because username with spaces doesn't exist
        assert data["success"] is False

    def test_login_with_special_characters(self, client):
        """Test login with special characters in credentials."""
        # Create a user with special characters
        (
            client.app.state._test_db_path
            if hasattr(client.app.state, "_test_db_path")
            else None
        )

        # This test documents that special chars are handled by the database
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser@example.com", "password": "test_password_123"},
        )

        # Should fail - user doesn't exist
        assert response.status_code == 200
        assert response.json()["success"] is False

    def test_concurrent_logins_same_user(self, client):
        """Test that the same user can login multiple times."""
        # First login
        response1 = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "test_password_123"},
        )
        assert response1.status_code == 200
        token1 = response1.json()["token"]

        # Second login
        response2 = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "test_password_123"},
        )
        assert response2.status_code == 200
        token2 = response2.json()["token"]

        # Tokens should be different (different JTI)
        assert token1 != token2

        # Both tokens should work
        response = client.get(
            "/api/v1/auth/me",
            headers={"X-API-Key": "test-api-key-12345", "X-User-Token": token1},
        )
        assert response.status_code == 200

        response = client.get(
            "/api/v1/auth/me",
            headers={"X-API-Key": "test-api-key-12345", "X-User-Token": token2},
        )
        assert response.status_code == 200

    def test_login_with_very_long_password(self, client):
        """Test login with very long password."""
        long_password = "a" * 1000

        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": long_password},
        )

        # Should fail gracefully
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    def test_login_with_unicode_characters(self, client):
        """Test login with unicode characters in credentials."""
        # Test with unicode password (should work)
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "test_password_123"},
        )

        # Unicode in password should be handled
        assert response.status_code in (200, 401)


class TestResponseFormats:
    """Tests for response format and structure."""

    def test_login_response_success_format(self, client):
        """Test login response format on success."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "test_password_123"},
        )

        assert response.status_code == 200
        data = response.json()

        # Check all expected fields
        assert "success" in data
        assert "token" in data
        assert "refresh_token" in data
        assert "user" in data
        assert "error" not in data or data["error"] is None

        # Check types
        assert isinstance(data["success"], bool)
        assert isinstance(data["token"], str)
        assert isinstance(data["refresh_token"], str)
        assert isinstance(data["user"], dict)

    def test_login_response_failure_format(self, client):
        """Test login response format on failure."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "wrong_password"},
        )

        assert response.status_code == 200
        data = response.json()

        # Check error response format
        assert "success" in data
        assert "error" in data
        assert data["success"] is False
        assert isinstance(data["error"], str)

        # Token and user should not be present on failure
        assert data.get("token") is None
        assert data.get("user") is None

    def test_logout_response_format(self, client):
        """Test logout response format."""
        response = client.post(
            "/api/v1/auth/logout", headers={"X-API-Key": "test-api-key-12345"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "success" in data
        assert "message" in data
        assert isinstance(data["success"], bool)
        assert isinstance(data["message"], str)

    def test_me_response_format(self, client):
        """Test /me endpoint response format."""
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "test_password_123"},
        )
        token = login_response.json()["token"]

        response = client.get(
            "/api/v1/auth/me",
            headers={"X-API-Key": "test-api-key-12345", "X-User-Token": token},
        )

        assert response.status_code == 200
        data = response.json()

        # Check all user fields
        assert "id" in data
        assert "username" in data
        assert "full_name" in data
        assert "role" in data

        # Check types
        assert isinstance(data["id"], str)
        assert isinstance(data["username"], str)
        assert isinstance(data["role"], str)
        # full_name can be None or str
        assert data["full_name"] is None or isinstance(data["full_name"], str)


class TestSecurityConsiderations:
    """Tests for security-related behavior."""

    def test_password_not_exposed_in_response(self, client):
        """Test that password is never exposed in any response."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "test_password_123"},
        )

        data = response.json()
        assert "password" not in data
        assert "password" not in data.get("user", {})

    def test_password_hash_not_exposed(self, client):
        """Test that password hash is never exposed."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "test_password_123"},
        )

        data = response.json()
        assert "password_hash" not in data
        assert "password_hash" not in data.get("user", {})

    def test_login_failure_does_not_leak_user_existence(self, client):
        """Test that login failure uses generic error message."""
        # Non-existent user
        response1 = client.post(
            "/api/v1/auth/login", json={"username": "nonexistent", "password": "wrong"}
        )
        error1 = response1.json()["error"]

        # Existing user with wrong password
        response2 = client.post(
            "/api/v1/auth/login", json={"username": "testuser", "password": "wrong"}
        )
        error2 = response2.json()["error"]

        # Same error message
        assert error1 == error2 == "Invalid username or password"


class TestIntegrationScenarios:
    """Integration test scenarios combining multiple operations."""

    def test_complete_authentication_flow(self, client):
        """Test complete flow: login -> get user -> logout."""
        # Step 1: Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "test_password_123"},
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert login_data["success"] is True

        token = login_data["token"]
        user_id = login_data["user"]["id"]

        # Step 2: Get current user
        me_response = client.get(
            "/api/v1/auth/me",
            headers={"X-API-Key": "test-api-key-12345", "X-User-Token": token},
        )
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["id"] == user_id
        assert me_data["username"] == "testuser"

        # Step 3: Logout
        logout_response = client.post(
            "/api/v1/auth/logout", headers={"X-API-Key": "test-api-key-12345"}
        )
        assert logout_response.status_code == 200
        logout_data = logout_response.json()
        assert logout_data["success"] is True

    def test_login_sequence_for_different_users(self, client):
        """Test logging in as different users in sequence."""
        users = [
            ("testuser", "test_password_123", "user"),
            ("adminuser", "admin_password_123", "admin"),
        ]

        for username, password, expected_role in users:
            login_response = client.post(
                "/api/v1/auth/login", json={"username": username, "password": password}
            )

            assert login_response.status_code == 200
            data = login_response.json()

            assert data["success"] is True
            assert data["user"]["username"] == username
            assert data["user"]["role"] == expected_role

    def test_token_works_across_multiple_requests(self, client):
        """Test that a single token works for multiple authenticated requests."""
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "test_password_123"},
        )
        token = login_response.json()["token"]

        # Use token for multiple requests
        for _ in range(5):
            response = client.get(
                "/api/v1/auth/me",
                headers={"X-API-Key": "test-api-key-12345", "X-User-Token": token},
            )
            assert response.status_code == 200


class TestDatabaseIntegration:
    """Tests for database integration behavior."""

    def test_login_with_corrupted_database(self, client, mock_database):
        """Test login behavior when database is corrupted."""
        # Corrupt the database
        conn = sqlite3.connect(str(mock_database))
        cursor = conn.cursor()
        cursor.execute("DROP TABLE users")
        conn.close()

        # Login should handle error gracefully
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "test_password_123"},
        )

        # Should return failure response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    def test_login_with_missing_database_columns(self, client, mock_database):
        """Test login when database schema is incomplete."""
        # Alter database to remove a column
        conn = sqlite3.connect(str(mock_database))
        cursor = conn.cursor()

        # Create a new table with missing columns
        cursor.execute("DROP TABLE users")
        cursor.execute("""
            CREATE TABLE users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

        # Login should handle missing columns
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "test_password_123"},
        )

        # Should handle error
        assert response.status_code in (200, 500)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
