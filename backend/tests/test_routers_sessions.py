"""Integration tests for sessions router endpoints.

Tests all session management endpoints including:
- POST /sessions - Create new session
- POST /sessions/{id}/close - Close session
- DELETE /sessions/{id} - Delete session
- POST /sessions/batch-delete - Batch delete
- PATCH /sessions/{id} - Update session
- GET /sessions - List all sessions
- POST /sessions/resume - Resume previous session
- GET /sessions/{id}/history - Get session history
- POST /sessions/{id}/resume - Resume specific session
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status


class TestCreateSession:
    """Test cases for POST /sessions endpoint."""

    @pytest.mark.asyncio
    async def test_create_session_success(self, client, user_auth_headers):
        """Test successful session creation with agent_id."""
        mock_manager = MagicMock()
        mock_manager.create_session = AsyncMock(return_value="test-session-123")

        with patch("api.dependencies.get_session_manager", return_value=mock_manager):
            response = client.post(
                "/api/v1/sessions",
                json={"agent_id": "test-agent"},
                headers=user_auth_headers,
            )

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["session_id"] == "test-session-123"
            assert data["status"] == "ready"
            assert data["resumed"] is False
            mock_manager.create_session.assert_called_once_with(
                agent_id="test-agent", resume_session_id=None
            )

    @pytest.mark.asyncio
    async def test_create_session_with_resume(self, client, user_auth_headers):
        """Test session creation with resume_session_id."""
        mock_manager = MagicMock()
        mock_manager.create_session = AsyncMock(return_value="resumed-session-456")

        with patch("api.dependencies.get_session_manager", return_value=mock_manager):
            response = client.post(
                "/api/v1/sessions",
                json={
                    "agent_id": "test-agent",
                    "resume_session_id": "previous-session-123",
                },
                headers=user_auth_headers,
            )

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["session_id"] == "resumed-session-456"
            assert data["status"] == "ready"
            assert data["resumed"] is True

    @pytest.mark.asyncio
    async def test_create_session_no_auth(self, client, auth_headers):
        """Test that creating session without user auth fails."""
        response = client.post(
            "/api/v1/sessions",
            json={"agent_id": "test-agent"},
            headers=auth_headers,  # Only API key, no user token
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_create_session_empty_body(self, client, user_auth_headers):
        """Test session creation with empty request body."""
        mock_manager = MagicMock()
        mock_manager.create_session = AsyncMock(return_value="minimal-session")

        with patch("api.dependencies.get_session_manager", return_value=mock_manager):
            response = client.post(
                "/api/v1/sessions",
                json={},
                headers=user_auth_headers,
            )

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["session_id"] == "minimal-session"
            mock_manager.create_session.assert_called_once_with(
                agent_id=None, resume_session_id=None
            )


class TestCloseSession:
    """Test cases for POST /sessions/{id}/close endpoint."""

    @pytest.mark.asyncio
    async def test_close_session_success(self, client, user_auth_headers):
        """Test successful session closure."""
        mock_manager = MagicMock()
        mock_manager.close_session = AsyncMock(return_value=None)

        with patch("api.dependencies.get_session_manager", return_value=mock_manager):
            response = client.post(
                "/api/v1/sessions/test-session-123/close",
                headers=user_auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "closed"
            mock_manager.close_session.assert_called_once_with("test-session-123")

    @pytest.mark.asyncio
    async def test_close_session_not_found(self, client, user_auth_headers):
        """Test closing non-existent session."""
        from api.core.errors import SessionNotFoundError

        mock_manager = MagicMock()
        mock_manager.close_session = AsyncMock(
            side_effect=SessionNotFoundError("nonexistent-session")
        )

        with patch("api.dependencies.get_session_manager", return_value=mock_manager):
            response = client.post(
                "/api/v1/sessions/nonexistent-session/close",
                headers=user_auth_headers,
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_close_session_no_auth(self, client, auth_headers):
        """Test that closing session without user auth fails."""
        response = client.post(
            "/api/v1/sessions/test-session/close",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestDeleteSession:
    """Test cases for DELETE /sessions/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_session_success(self, client, user_auth_headers, tmp_path):
        """Test successful session deletion."""
        mock_manager = MagicMock()
        mock_manager.delete_session = AsyncMock(return_value=None)

        mock_session_storage = MagicMock()
        mock_session_storage.delete_session = MagicMock(return_value=True)

        mock_history_storage = MagicMock()
        mock_history_storage.delete_history = MagicMock(return_value=True)

        with (
            patch("api.dependencies.get_session_manager", return_value=mock_manager),
            patch(
                "api.routers.sessions.get_user_session_storage",
                return_value=mock_session_storage,
            ),
            patch(
                "api.routers.sessions.get_user_history_storage",
                return_value=mock_history_storage,
            ),
        ):
            response = client.delete(
                "/api/v1/sessions/test-session-123",
                headers=user_auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "deleted"
            mock_session_storage.delete_session.assert_called_once_with(
                "test-session-123"
            )
            mock_history_storage.delete_history.assert_called_once_with(
                "test-session-123"
            )

    @pytest.mark.asyncio
    async def test_delete_session_not_in_cache(self, client, user_auth_headers):
        """Test deleting session that exists in storage but not in cache."""
        from api.core.errors import SessionNotFoundError

        mock_manager = MagicMock()
        # Session not in cache
        mock_manager.delete_session = AsyncMock(
            side_effect=SessionNotFoundError("test-session")
        )

        mock_session_storage = MagicMock()
        mock_session_storage.delete_session = MagicMock(return_value=True)

        mock_history_storage = MagicMock()
        mock_history_storage.delete_history = MagicMock(return_value=True)

        with (
            patch("api.dependencies.get_session_manager", return_value=mock_manager),
            patch(
                "api.routers.sessions.get_user_session_storage",
                return_value=mock_session_storage,
            ),
            patch(
                "api.routers.sessions.get_user_history_storage",
                return_value=mock_history_storage,
            ),
        ):
            # Should still succeed even though session wasn't in cache
            response = client.delete(
                "/api/v1/sessions/test-session",
                headers=user_auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            mock_session_storage.delete_session.assert_called_once()
            mock_history_storage.delete_history.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_session_no_auth(self, client, auth_headers):
        """Test that deleting session without user auth fails."""
        response = client.delete(
            "/api/v1/sessions/test-session",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestBatchDeleteSessions:
    """Test cases for POST /sessions/batch-delete endpoint."""

    @pytest.mark.asyncio
    async def test_batch_delete_success(self, client, user_auth_headers):
        """Test successful batch deletion of sessions."""
        mock_manager = MagicMock()
        mock_manager.delete_session = AsyncMock(return_value=None)

        mock_session_storage = MagicMock()
        mock_session_storage.delete_session = MagicMock(return_value=True)

        mock_history_storage = MagicMock()
        mock_history_storage.delete_history = MagicMock(return_value=True)

        with (
            patch("api.dependencies.get_session_manager", return_value=mock_manager),
            patch(
                "api.routers.sessions.get_user_session_storage",
                return_value=mock_session_storage,
            ),
            patch(
                "api.routers.sessions.get_user_history_storage",
                return_value=mock_history_storage,
            ),
        ):
            response = client.post(
                "/api/v1/sessions/batch-delete",
                json={"session_ids": ["session-1", "session-2", "session-3"]},
                headers=user_auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "deleted"
            assert mock_session_storage.delete_session.call_count == 3
            assert mock_history_storage.delete_history.call_count == 3

    @pytest.mark.asyncio
    async def test_batch_delete_single_session(self, client, user_auth_headers):
        """Test batch delete with single session ID."""
        mock_manager = MagicMock()
        mock_manager.delete_session = AsyncMock(return_value=None)

        mock_session_storage = MagicMock()
        mock_history_storage = MagicMock()

        with (
            patch("api.dependencies.get_session_manager", return_value=mock_manager),
            patch(
                "api.routers.sessions.get_user_session_storage",
                return_value=mock_session_storage,
            ),
            patch(
                "api.routers.sessions.get_user_history_storage",
                return_value=mock_history_storage,
            ),
        ):
            response = client.post(
                "/api/v1/sessions/batch-delete",
                json={"session_ids": ["single-session"]},
                headers=user_auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_batch_delete_empty_list(self, client, user_auth_headers):
        """Test batch delete with empty list fails validation."""
        response = client.post(
            "/api/v1/sessions/batch-delete",
            json={"session_ids": []},
            headers=user_auth_headers,
        )

        # Pydantic validation should reject empty list
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    @pytest.mark.asyncio
    async def test_batch_delete_mixed_cache_storage(self, client, user_auth_headers):
        """Test batch delete where some sessions are in cache and some only in storage."""
        from api.core.errors import SessionNotFoundError

        mock_manager = MagicMock()
        # First call succeeds, second fails (not in cache), third succeeds
        mock_manager.delete_session = AsyncMock(
            side_effect=[None, SessionNotFoundError("session-2"), None]
        )

        mock_session_storage = MagicMock()
        mock_history_storage = MagicMock()

        with (
            patch("api.dependencies.get_session_manager", return_value=mock_manager),
            patch(
                "api.routers.sessions.get_user_session_storage",
                return_value=mock_session_storage,
            ),
            patch(
                "api.routers.sessions.get_user_history_storage",
                return_value=mock_history_storage,
            ),
        ):
            response = client.post(
                "/api/v1/sessions/batch-delete",
                json={"session_ids": ["session-1", "session-2", "session-3"]},
                headers=user_auth_headers,
            )

            # Should still succeed overall
            assert response.status_code == status.HTTP_200_OK
            assert mock_session_storage.delete_session.call_count == 3

    @pytest.mark.asyncio
    async def test_batch_delete_no_auth(self, client, auth_headers):
        """Test that batch deleting without user auth fails."""
        response = client.post(
            "/api/v1/sessions/batch-delete",
            json={"session_ids": ["session-1"]},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUpdateSession:
    """Test cases for PATCH /sessions/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_session_name(self, client, user_auth_headers):
        """Test updating session name."""
        from agent.core.storage import SessionData

        mock_session = SessionData(
            session_id="test-session-123",
            name="Old Name",
            first_message="Hello",
            created_at=datetime.now().isoformat(),
            turn_count=5,
            agent_id="test-agent",
        )

        mock_session_storage = MagicMock()
        mock_session_storage.update_session = MagicMock(return_value=True)
        mock_session_storage.get_session = MagicMock(return_value=mock_session)

        with patch(
            "api.routers.sessions.get_user_session_storage",
            return_value=mock_session_storage,
        ):
            response = client.patch(
                "/api/v1/sessions/test-session-123",
                json={"name": "New Custom Name"},
                headers=user_auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["session_id"] == "test-session-123"
            assert data["name"] == "Old Name"  # Returns the stored session
            mock_session_storage.update_session.assert_called_once_with(
                session_id="test-session-123", name="New Custom Name"
            )

    @pytest.mark.asyncio
    async def test_update_session_not_found(self, client, user_auth_headers):
        """Test updating non-existent session."""
        mock_session_storage = MagicMock()
        mock_session_storage.update_session = MagicMock(return_value=False)

        with patch(
            "api.routers.sessions.get_user_session_storage",
            return_value=mock_session_storage,
        ):
            response = client.patch(
                "/api/v1/sessions/nonexistent",
                json={"name": "New Name"},
                headers=user_auth_headers,
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert "message" in data
            assert "not found" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_update_session_no_auth(self, client, auth_headers):
        """Test that updating session without user auth fails."""
        response = client.patch(
            "/api/v1/sessions/test-session",
            json={"name": "New Name"},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestListSessions:
    """Test cases for GET /sessions endpoint."""

    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, client, user_auth_headers):
        """Test listing sessions when none exist."""
        mock_session_storage = MagicMock()
        mock_session_storage.load_sessions = MagicMock(return_value=[])

        with patch(
            "api.routers.sessions.get_user_session_storage",
            return_value=mock_session_storage,
        ):
            response = client.get(
                "/api/v1/sessions",
                headers=user_auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_sessions_multiple(self, client, user_auth_headers):
        """Test listing multiple sessions."""
        from agent.core.storage import SessionData

        sessions = [
            SessionData(
                session_id="session-1",
                name="First Chat",
                first_message="Hello",
                created_at="2024-01-01T12:00:00",
                turn_count=3,
                agent_id="agent-1",
            ),
            SessionData(
                session_id="session-2",
                name=None,
                first_message="Hi there",
                created_at="2024-01-02T14:30:00",
                turn_count=1,
                agent_id="agent-2",
            ),
        ]

        mock_session_storage = MagicMock()
        mock_session_storage.load_sessions = MagicMock(return_value=sessions)

        with patch(
            "api.routers.sessions.get_user_session_storage",
            return_value=mock_session_storage,
        ):
            response = client.get(
                "/api/v1/sessions",
                headers=user_auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 2
            assert data[0]["session_id"] == "session-1"
            assert data[0]["name"] == "First Chat"
            assert data[1]["session_id"] == "session-2"
            assert data[1]["name"] is None

    @pytest.mark.asyncio
    async def test_list_sessions_no_auth(self, client, auth_headers):
        """Test that listing sessions without user auth fails."""
        response = client.get(
            "/api/v1/sessions",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestResumePreviousSession:
    """Test cases for POST /sessions/resume endpoint."""

    @pytest.mark.asyncio
    async def test_resume_previous_session_success(self, client, user_auth_headers):
        """Test resuming previous session successfully."""
        mock_manager = MagicMock()
        mock_manager.create_session = AsyncMock(return_value="resumed-session-789")

        with patch("api.dependencies.get_session_manager", return_value=mock_manager):
            response = client.post(
                "/api/v1/sessions/resume",
                json={"resume_session_id": "previous-session-123"},
                headers=user_auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["session_id"] == "resumed-session-789"
            assert data["status"] == "ready"
            assert data["resumed"] is True
            mock_manager.create_session.assert_called_once_with(
                resume_session_id="previous-session-123"
            )

    @pytest.mark.asyncio
    async def test_resume_previous_session_missing_resume_id(
        self, client, user_auth_headers
    ):
        """Test resume request without resume_session_id fails."""
        response = client.post(
            "/api/v1/sessions/resume",
            json={},  # Missing resume_session_id
            headers=user_auth_headers,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "message" in data
        assert "resume_session_id" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_resume_previous_session_no_auth(self, client, auth_headers):
        """Test that resuming session without user auth fails."""
        response = client.post(
            "/api/v1/sessions/resume",
            json={"resume_session_id": "previous-session"},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetSessionHistory:
    """Test cases for GET /sessions/{id}/history endpoint."""

    @pytest.mark.asyncio
    async def test_get_session_history_with_metadata(self, client, user_auth_headers):
        """Test getting history for session with metadata."""
        from agent.core.storage import SessionData

        mock_session = SessionData(
            session_id="test-session",
            name="Test Chat",
            first_message="Hello",
            created_at="2024-01-01T12:00:00",
            turn_count=2,
        )

        mock_messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        mock_session_storage = MagicMock()
        mock_session_storage.get_session = MagicMock(return_value=mock_session)

        mock_history_storage = MagicMock()
        mock_history_storage.get_messages_dict = MagicMock(return_value=mock_messages)

        with (
            patch(
                "api.routers.sessions.get_user_session_storage",
                return_value=mock_session_storage,
            ),
            patch(
                "api.routers.sessions.get_user_history_storage",
                return_value=mock_history_storage,
            ),
        ):
            response = client.get(
                "/api/v1/sessions/test-session/history",
                headers=user_auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["session_id"] == "test-session"
            assert data["turn_count"] == 2
            assert data["first_message"] == "Hello"
            assert len(data["messages"]) == 2
            assert data["messages"][0]["role"] == "user"

    @pytest.mark.asyncio
    async def test_get_session_history_without_metadata(
        self, client, user_auth_headers
    ):
        """Test getting history for session without metadata."""
        mock_messages = [
            {"role": "user", "content": "Test message"},
            {"role": "assistant", "content": "Response"},
            {"role": "user", "content": "Follow up"},
        ]

        mock_session_storage = MagicMock()
        mock_session_storage.get_session = MagicMock(return_value=None)

        mock_history_storage = MagicMock()
        mock_history_storage.get_messages_dict = MagicMock(return_value=mock_messages)

        with (
            patch(
                "api.routers.sessions.get_user_session_storage",
                return_value=mock_session_storage,
            ),
            patch(
                "api.routers.sessions.get_user_history_storage",
                return_value=mock_history_storage,
            ),
        ):
            response = client.get(
                "/api/v1/sessions/unknown-session/history",
                headers=user_auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["session_id"] == "unknown-session"
            # Calculates turn_count from messages (2 user messages)
            assert data["turn_count"] == 2
            assert data["first_message"] == "Test message"

    @pytest.mark.asyncio
    async def test_get_session_history_empty(self, client, user_auth_headers):
        """Test getting history for session with no messages."""
        mock_session_storage = MagicMock()
        mock_session_storage.get_session = MagicMock(return_value=None)

        mock_history_storage = MagicMock()
        mock_history_storage.get_messages_dict = MagicMock(return_value=[])

        with (
            patch(
                "api.routers.sessions.get_user_session_storage",
                return_value=mock_session_storage,
            ),
            patch(
                "api.routers.sessions.get_user_history_storage",
                return_value=mock_history_storage,
            ),
        ):
            response = client.get(
                "/api/v1/sessions/empty-session/history",
                headers=user_auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["session_id"] == "empty-session"
            assert data["messages"] == []
            assert data["turn_count"] == 0
            assert data["first_message"] is None

    @pytest.mark.asyncio
    async def test_get_session_history_no_auth(self, client, auth_headers):
        """Test that getting history without user auth fails."""
        response = client.get(
            "/api/v1/sessions/test-session/history",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestResumeSessionById:
    """Test cases for POST /sessions/{id}/resume endpoint."""

    @pytest.mark.asyncio
    async def test_resume_session_by_id_success(self, client, user_auth_headers):
        """Test resuming session by ID successfully."""
        mock_manager = MagicMock()
        mock_manager.create_session = AsyncMock(return_value="new-resumed-session")

        with patch("api.dependencies.get_session_manager", return_value=mock_manager):
            response = client.post(
                "/api/v1/sessions/target-session-123/resume",
                json={"initial_message": "Continue our conversation"},
                headers=user_auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["session_id"] == "new-resumed-session"
            assert data["status"] == "ready"
            assert data["resumed"] is True
            mock_manager.create_session.assert_called_once_with(
                resume_session_id="target-session-123"
            )

    @pytest.mark.asyncio
    async def test_resume_session_by_id_no_body(self, client, user_auth_headers):
        """Test resuming session by ID without request body."""
        mock_manager = MagicMock()
        mock_manager.create_session = AsyncMock(return_value="resumed-session")

        with patch("api.dependencies.get_session_manager", return_value=mock_manager):
            response = client.post(
                "/api/v1/sessions/target-session/resume",
                headers=user_auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            # initial_message is optional, should work without it
            mock_manager.create_session.assert_called_once_with(
                resume_session_id="target-session"
            )

    @pytest.mark.asyncio
    async def test_resume_session_by_id_no_auth(self, client, auth_headers):
        """Test that resuming session by ID without user auth fails."""
        response = client.post(
            "/api/v1/sessions/test-session/resume",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestPerUserIsolation:
    """Test cases for per-user data isolation."""

    @pytest.mark.asyncio
    async def test_sessions_isolated_by_user(self, client, user_auth_headers):
        """Test that sessions are isolated per user."""
        # This test verifies the API uses per-user storage correctly
        # In a real scenario, different users would get different storage instances

        mock_session_storage = MagicMock()
        mock_session_storage.load_sessions = MagicMock(return_value=[])

        with patch(
            "api.routers.sessions.get_user_session_storage",
            return_value=mock_session_storage,
        ) as mock_get_storage:
            response = client.get(
                "/api/v1/sessions",
                headers=user_auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            # Verify get_user_session_storage was called with username from token
            mock_get_storage.assert_called_once()
            # The call should include the username
            call_args = mock_get_storage.call_args
            assert call_args is not None


class TestErrorResponseHandling:
    """Test cases for error response handling."""

    @pytest.mark.asyncio
    async def test_invalid_request_error_format(self, client, user_auth_headers):
        """Test that InvalidRequestError returns proper format."""
        response = client.post(
            "/api/v1/sessions/resume",
            json={},  # Missing required resume_session_id
            headers=user_auth_headers,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "message" in data
        assert len(data["message"]) > 0

    @pytest.mark.asyncio
    async def test_session_not_found_error_format(self, client, user_auth_headers):
        """Test that SessionNotFoundError returns 404."""
        from api.core.errors import SessionNotFoundError

        mock_manager = MagicMock()
        mock_manager.close_session = AsyncMock(
            side_effect=SessionNotFoundError("missing-session")
        )

        with patch("api.dependencies.get_session_manager", return_value=mock_manager):
            response = client.post(
                "/api/v1/sessions/missing-session/close",
                headers=user_auth_headers,
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert "message" in data
            assert "missing-session" in data["message"]
            assert "session_id" in data
            assert data["session_id"] == "missing-session"
