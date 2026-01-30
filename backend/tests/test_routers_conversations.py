"""Comprehensive integration tests for conversations router.

Tests all conversation endpoints including SSE streaming with authentication,
session management, and error handling.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sse_starlette.sse import EventSourceResponse

from api.constants import EventType
from api.models.requests import CreateConversationRequest, SendMessageRequest
from api.models.user_auth import UserTokenPayload


class TestCreateConversationEndpoint:
    """Test POST /conversations endpoint."""

    @pytest.mark.asyncio
    async def test_returns_event_source_response(self):
        """Test that endpoint returns EventSourceResponse."""
        from api.routers.conversations import create_conversation
        from api.services.session_manager import SessionManager

        mock_manager = MagicMock(spec=SessionManager)
        mock_user = UserTokenPayload(
            user_id="test-user-id", username="testuser", role="user"
        )
        request = CreateConversationRequest(content="Hello, world!")

        with patch(
            "api.routers.conversations._stream_conversation_events",
            return_value=AsyncMock(),
        ):
            result = await create_conversation(request, mock_manager, mock_user)

        assert isinstance(result, EventSourceResponse)

    @pytest.mark.asyncio
    async def test_passes_generated_session_id_when_not_provided(self):
        """Test that session_id is generated when not in request."""
        from api.routers.conversations import create_conversation
        from api.services.session_manager import SessionManager

        mock_manager = MagicMock(spec=SessionManager)
        mock_user = UserTokenPayload(
            user_id="test-user-id", username="testuser", role="user"
        )
        request = CreateConversationRequest(content="Hello", session_id=None)

        with patch(
            "api.routers.conversations._stream_conversation_events",
            return_value=AsyncMock(),
        ) as mock_stream:
            await create_conversation(request, mock_manager, mock_user)

            # Should generate a UUID session_id
            call_args = mock_stream.call_args
            assert call_args is not None
            session_id = call_args[0][0]
            assert session_id is not None
            assert len(session_id) == 36  # UUID format

    @pytest.mark.asyncio
    async def test_uses_provided_session_id(self):
        """Test that provided session_id is used."""
        from api.routers.conversations import create_conversation
        from api.services.session_manager import SessionManager

        mock_manager = MagicMock(spec=SessionManager)
        mock_user = UserTokenPayload(
            user_id="test-user-id", username="testuser", role="user"
        )
        custom_session_id = "my-custom-session-123"
        request = CreateConversationRequest(
            content="Hello", session_id=custom_session_id
        )

        with patch(
            "api.routers.conversations._stream_conversation_events",
            return_value=AsyncMock(),
        ) as mock_stream:
            await create_conversation(request, mock_manager, mock_user)

            call_args = mock_stream.call_args
            assert call_args[0][0] == custom_session_id

    @pytest.mark.asyncio
    async def test_passes_agent_id_to_stream(self):
        """Test that agent_id is passed to stream function."""
        from api.routers.conversations import create_conversation
        from api.services.session_manager import SessionManager

        mock_manager = MagicMock(spec=SessionManager)
        mock_user = UserTokenPayload(
            user_id="test-user-id", username="testuser", role="user"
        )
        agent_id = "agent-test-456"
        request = CreateConversationRequest(content="Hello", agent_id=agent_id)

        with patch(
            "api.routers.conversations._stream_conversation_events",
            return_value=AsyncMock(),
        ) as mock_stream:
            await create_conversation(request, mock_manager, mock_user)

            call_args = mock_stream.call_args
            assert call_args[0][3] == agent_id  # 4th positional arg is agent_id

    @pytest.mark.asyncio
    async def test_passes_username_to_stream(self):
        """Test that username is passed to stream function."""
        from api.routers.conversations import create_conversation
        from api.services.session_manager import SessionManager

        mock_manager = MagicMock(spec=SessionManager)
        mock_user = UserTokenPayload(
            user_id="test-user-id", username="testuser", role="user"
        )
        request = CreateConversationRequest(content="Hello")

        with patch(
            "api.routers.conversations._stream_conversation_events",
            return_value=AsyncMock(),
        ) as mock_stream:
            await create_conversation(request, mock_manager, mock_user)

            call_args = mock_stream.call_args
            assert call_args[0][4] == "testuser"  # 5th positional arg is username


class TestStreamConversationEndpoint:
    """Test POST /conversations/{session_id}/stream endpoint."""

    @pytest.mark.asyncio
    async def test_returns_event_source_response(self):
        """Test that endpoint returns EventSourceResponse."""
        from api.routers.conversations import stream_conversation
        from api.services.session_manager import SessionManager

        mock_manager = MagicMock(spec=SessionManager)
        mock_user = UserTokenPayload(
            user_id="test-user-id", username="testuser", role="user"
        )
        session_id = "test-session-123"
        request = SendMessageRequest(content="What is 2+2?")

        with patch(
            "api.routers.conversations._stream_conversation_events",
            return_value=AsyncMock(),
        ):
            result = await stream_conversation(
                session_id, request, mock_manager, mock_user
            )

        assert isinstance(result, EventSourceResponse)

    @pytest.mark.asyncio
    async def test_passes_session_id_to_stream(self):
        """Test that session_id from path is passed to stream."""
        from api.routers.conversations import stream_conversation
        from api.services.session_manager import SessionManager

        mock_manager = MagicMock(spec=SessionManager)
        mock_user = UserTokenPayload(
            user_id="test-user-id", username="testuser", role="user"
        )
        session_id = "path-session-456"
        request = SendMessageRequest(content="Hello again")

        with patch(
            "api.routers.conversations._stream_conversation_events",
            return_value=AsyncMock(),
        ) as mock_stream:
            await stream_conversation(session_id, request, mock_manager, mock_user)

            call_args = mock_stream.call_args
            assert call_args[0][0] == session_id

    @pytest.mark.asyncio
    async def test_passes_content_to_stream(self):
        """Test that message content is passed to stream."""
        from api.routers.conversations import stream_conversation
        from api.services.session_manager import SessionManager

        mock_manager = MagicMock(spec=SessionManager)
        mock_user = UserTokenPayload(
            user_id="test-user-id", username="testuser", role="user"
        )
        content = "Test message content"
        request = SendMessageRequest(content=content)

        with patch(
            "api.routers.conversations._stream_conversation_events",
            return_value=AsyncMock(),
        ) as mock_stream:
            await stream_conversation("session-id", request, mock_manager, mock_user)

            call_args = mock_stream.call_args
            assert call_args[0][1] == content

    @pytest.mark.asyncio
    async def test_passes_username_to_stream(self):
        """Test that username is passed to stream function."""
        from api.routers.conversations import stream_conversation
        from api.services.session_manager import SessionManager

        mock_manager = MagicMock(spec=SessionManager)
        mock_user = UserTokenPayload(
            user_id="test-user-id", username="testuser", role="user"
        )
        request = SendMessageRequest(content="Hello")

        with patch(
            "api.routers.conversations._stream_conversation_events"
        ) as mock_stream:
            # Create a mock async generator
            async def mock_gen():
                return
                yield

            mock_stream.return_value = mock_gen()

            await stream_conversation(
                "session-id", request, mock_manager, mock_user
            )

            # Verify the stream function was called with correct arguments
            mock_stream.assert_called_once()
            call_args = mock_stream.call_args
            # The function is called with args: session_id, content, manager
            # and username as keyword argument
            assert call_args[0][0] == "session-id"
            assert call_args[0][1] == "Hello"
            assert call_args[0][2] is mock_manager
            # username is passed as keyword argument
            kwargs = call_args[1]
            assert "username" in kwargs, f"Expected 'username' in kwargs: {kwargs}"
            assert kwargs["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_manager_is_passed_to_stream(self):
        """Test that SessionManager is passed to stream function."""
        from api.routers.conversations import stream_conversation
        from api.services.session_manager import SessionManager

        mock_manager = MagicMock(spec=SessionManager)
        mock_user = UserTokenPayload(
            user_id="test-user-id", username="testuser", role="user"
        )
        request = SendMessageRequest(content="Test")

        with patch(
            "api.routers.conversations._stream_conversation_events",
            return_value=AsyncMock(),
        ) as mock_stream:
            await stream_conversation("session-id", request, mock_manager, mock_user)

            call_args = mock_stream.call_args
            assert call_args[0][2] is mock_manager


class TestStreamConversationEvents:
    """Test _stream_conversation_events async generator."""

    @pytest.mark.asyncio
    async def test_yields_session_id_event_first(self):
        """Test that session_id event is yielded first."""
        from api.routers.conversations import _stream_conversation_events
        from api.services.session_manager import SessionManager

        mock_manager = MagicMock(spec=SessionManager)
        mock_session = AsyncMock()
        mock_session.send_query = AsyncMock(return_value=iter([]))

        mock_manager.get_or_create_conversation_session = AsyncMock(
            return_value=(mock_session, "resolved-id-123", False)
        )

        events = _stream_conversation_events(
            "pending-id", "Hello", mock_manager, agent_id=None, username="testuser"
        )

        first_event = await events.__anext__()

        assert first_event["event"] == EventType.SESSION_ID
        data = json.loads(first_event["data"])
        assert data["session_id"] == "resolved-id-123"
        assert data["found_in_cache"] is False

    @pytest.mark.asyncio
    async def test_calls_get_or_create_conversation_session(self):
        """Test that manager's get_or_create is called."""
        from api.routers.conversations import _stream_conversation_events
        from api.services.session_manager import SessionManager

        mock_manager = MagicMock(spec=SessionManager)
        mock_session = AsyncMock()
        mock_session.send_query = AsyncMock(return_value=iter([]))

        mock_manager.get_or_create_conversation_session = AsyncMock(
            return_value=(mock_session, "resolved-id", True)
        )

        events = _stream_conversation_events("test-id", "Test content", mock_manager)

        # Consume first event to trigger call
        await events.__anext__()

        mock_manager.get_or_create_conversation_session.assert_called_once_with(
            "test-id", None
        )

    @pytest.mark.asyncio
    async def test_passes_agent_id_to_get_or_create(self):
        """Test that agent_id is passed to get_or_create."""
        from api.routers.conversations import _stream_conversation_events
        from api.services.session_manager import SessionManager

        mock_manager = MagicMock(spec=SessionManager)
        mock_session = AsyncMock()
        mock_session.send_query = AsyncMock(return_value=iter([]))

        mock_manager.get_or_create_conversation_session = AsyncMock(
            return_value=(mock_session, "resolved-id", False)
        )

        agent_id = "test-agent-789"

        events = _stream_conversation_events(
            "test-id", "Test", mock_manager, agent_id=agent_id
        )

        await events.__anext__()

        mock_manager.get_or_create_conversation_session.assert_called_once_with(
            "test-id", agent_id
        )

    @pytest.mark.asyncio
    async def test_saves_user_message_to_history(self):
        """Test that user message is saved via HistoryTracker."""
        from api.routers.conversations import _stream_conversation_events
        from api.services.session_manager import SessionManager
        from unittest.mock import MagicMock

        mock_manager = MagicMock(spec=SessionManager)
        mock_session = AsyncMock()

        # Create an async generator for send_query
        async def empty_async_gen():
            return
            yield

        mock_session.send_query = AsyncMock(return_value=empty_async_gen())

        mock_manager.get_or_create_conversation_session = AsyncMock(
            return_value=(mock_session, "resolved-id", False)
        )

        content = "Test user message"

        with patch(
            "api.routers.conversations.get_user_history_storage"
        ) as mock_storage:
            mock_history = MagicMock()
            mock_storage.return_value = mock_history

            events = _stream_conversation_events(
                "test-id", content, mock_manager, agent_id=None, username="testuser"
            )

            # Consume all events to ensure save_user_message is called
            async for _ in events:
                pass

            mock_storage.assert_called_once_with("testuser")
            mock_history.append_message.assert_called_once()
            call_kwargs = mock_history.append_message.call_args[1]
            assert call_kwargs["session_id"] == "resolved-id"
            assert call_kwargs["role"] == "user"
            assert call_kwargs["content"] == content

    @pytest.mark.asyncio
    async def test_creates_history_tracker_with_username(self):
        """Test HistoryTracker is created with correct params."""
        from api.routers.conversations import _stream_conversation_events
        from api.services.session_manager import SessionManager

        mock_manager = MagicMock(spec=SessionManager)
        mock_session = AsyncMock()
        mock_session.send_query = AsyncMock(return_value=iter([]))

        mock_manager.get_or_create_conversation_session = AsyncMock(
            return_value=(mock_session, "resolved-id-xyz", False)
        )

        with patch("api.routers.conversations.HistoryTracker") as mock_tracker_class:
            with patch(
                "api.routers.conversations.get_user_history_storage"
            ) as mock_storage:
                events = _stream_conversation_events(
                    "test-id", "Test", mock_manager, agent_id=None, username="alice"
                )

                await events.__anext__()

                mock_tracker_class.assert_called_once()
                call_kwargs = mock_tracker_class.call_args[1]
                assert call_kwargs["session_id"] == "resolved-id-xyz"
                mock_storage.assert_called_once_with("alice")

    @pytest.mark.asyncio
    async def test_processes_sse_events_from_send_query(self):
        """Test that events from send_query are converted to SSE."""
        from api.routers.conversations import _stream_conversation_events
        from api.services.session_manager import SessionManager

        mock_manager = MagicMock(spec=SessionManager)
        mock_session = AsyncMock()

        # Mock a ResultMessage with all required fields
        mock_result = MagicMock()
        mock_result.__class__.__name__ = "ResultMessage"

        async def mock_send_query(content):
            yield mock_result

        mock_session.send_query = mock_send_query

        mock_manager.get_or_create_conversation_session = AsyncMock(
            return_value=(mock_session, "resolved-id", False)
        )

        with patch(
            "api.routers.conversations.get_user_history_storage"
        ) as mock_storage:
            mock_history = MagicMock()
            mock_storage.return_value = mock_history

            with patch(
                "api.routers.conversations.convert_messages_to_sse"
            ) as mock_convert:
                # Mock the conversion to return a done event
                mock_convert.return_value = [
                    {
                        "event": EventType.DONE,
                        "data": json.dumps({"turn_count": 1, "total_cost_usd": 0.001}),
                    }
                ]

                events = _stream_conversation_events(
                    "test-id", "Test", mock_manager, agent_id=None, username=None
                )

                # Skip session_id event
                await events.__anext__()

                # Get the done event
                done_event = await events.__anext__()

                assert done_event["event"] == EventType.DONE
                mock_convert.assert_called()

    @pytest.mark.asyncio
    async def test_handles_sdk_session_id_event(self):
        """Test handling of SDK session_id events."""
        from api.routers.conversations import _stream_conversation_events
        from api.services.session_manager import SessionManager

        mock_manager = MagicMock(spec=SessionManager)
        mock_session = AsyncMock()
        mock_session.sdk_session_id = None

        # Create a mock message that will be processed
        mock_msg = MagicMock()
        mock_msg.__class__.__name__ = "SystemMessage"

        async def mock_send_query(content):
            yield mock_msg

        mock_session.send_query = mock_send_query

        mock_manager.get_or_create_conversation_session = AsyncMock(
            return_value=(mock_session, "pending-123", False)
        )

        with patch(
            "api.routers.conversations.get_user_history_storage"
        ) as mock_storage:
            mock_history = MagicMock()
            mock_storage.return_value = mock_history

            with patch(
                "api.routers.conversations.convert_messages_to_sse"
            ) as mock_convert:
                mock_convert.return_value = [
                    {
                        "event": EventType.SESSION_ID,
                        "data": json.dumps({"session_id": "sdk-session-abc"}),
                    }
                ]

                events = _stream_conversation_events(
                    "test-id", "Test", mock_manager, agent_id=None, username=None
                )

                # Skip initial session_id event
                await events.__anext__()

                # Get sdk_session_id event
                sdk_event = await events.__anext__()

                assert sdk_event["event"] == "sdk_session_id"
                data = json.loads(sdk_event["data"])
                assert data["sdk_session_id"] == "sdk-session-abc"

    @pytest.mark.asyncio
    async def test_registers_sdk_session_id_mapping(self):
        """Test that SDK session ID is registered with manager."""
        from api.routers.conversations import _stream_conversation_events
        from api.services.session_manager import SessionManager

        mock_manager = MagicMock(spec=SessionManager)
        mock_session = AsyncMock()
        mock_session.sdk_session_id = None

        mock_manager.get_or_create_conversation_session = AsyncMock(
            return_value=(mock_session, "pending-456", False)
        )

        with patch(
            "api.routers.conversations.get_user_history_storage"
        ) as mock_storage:
            mock_history = MagicMock()
            mock_storage.return_value = mock_history

            with patch(
                "api.routers.conversations.convert_messages_to_sse"
            ) as mock_convert:
                mock_convert.return_value = [
                    {
                        "event": EventType.SESSION_ID,
                        "data": json.dumps({"session_id": "sdk-id-xyz"}),
                    }
                ]

                # Create a mock message that will be yielded
                mock_msg = MagicMock()

                async def message_gen(content):
                    yield mock_msg

                mock_session.send_query = message_gen

                events = _stream_conversation_events(
                    "test-id", "Test", mock_manager, agent_id=None, username="testuser"
                )

                # Skip initial session_id
                await events.__anext__()

                # Get sdk_session_id event
                sdk_event = await events.__anext__()

                assert sdk_event["event"] == "sdk_session_id"

                mock_manager.register_sdk_session_id.assert_called_once_with(
                    "pending-456", "sdk-id-xyz"
                )

    @pytest.mark.asyncio
    async def test_processes_events_through_history_tracker(self):
        """Test that events are processed by HistoryTracker."""
        from api.routers.conversations import _stream_conversation_events
        from api.services.session_manager import SessionManager

        mock_manager = MagicMock(spec=SessionManager)
        mock_session = AsyncMock()

        mock_manager.get_or_create_conversation_session = AsyncMock(
            return_value=(mock_session, "resolved-id", False)
        )

        with patch(
            "api.routers.conversations.get_user_history_storage"
        ) as mock_storage:
            mock_history = MagicMock()
            mock_storage.return_value = mock_history

            with patch(
                "api.routers.conversations.convert_messages_to_sse"
            ) as mock_convert:
                mock_convert.return_value = [
                    {
                        "event": EventType.TEXT_DELTA,
                        "data": json.dumps({"text": "Hello"}),
                    }
                ]

                async def empty_gen():
                    return
                    yield

                mock_session.send_query = lambda content: empty_gen()

                events = _stream_conversation_events(
                    "test-id", "Test", mock_manager, agent_id=None, username="testuser"
                )

                # Skip session_id
                await events.__anext__()

                # Process text delta
                try:
                    await events.__anext__()
                except StopAsyncIteration:
                    pass

                # Verify history storage was called for user message
                assert mock_history.append_message.call_count >= 1

    @pytest.mark.asyncio
    async def test_handles_exception_during_streaming(self):
        """Test error handling during streaming."""
        from api.routers.conversations import _stream_conversation_events
        from api.services.session_manager import SessionManager

        mock_manager = MagicMock(spec=SessionManager)
        mock_session = AsyncMock()

        async def error_stream(content):
            raise RuntimeError("Stream error")
            yield

        mock_session.send_query = error_stream

        mock_manager.get_or_create_conversation_session = AsyncMock(
            return_value=(mock_session, "resolved-id", False)
        )

        with patch("api.routers.conversations.HistoryTracker") as mock_tracker_class:
            mock_tracker = MagicMock()
            mock_tracker.has_accumulated_text.return_value = False
            mock_tracker_class.return_value = mock_tracker

            events = _stream_conversation_events(
                "test-id", "Test", mock_manager, agent_id=None, username="testuser"
            )

            # Skip session_id
            await events.__anext__()

            # Get error event
            error_event = await events.__anext__()

            assert error_event["event"] == EventType.ERROR
            data = json.loads(error_event["data"])
            assert "Stream error" in data["error"]
            assert data["type"] == "RuntimeError"

    @pytest.mark.asyncio
    async def test_finalizes_accumulated_text_on_error(self):
        """Test that accumulated text is finalized on error."""
        from api.routers.conversations import _stream_conversation_events
        from api.services.session_manager import SessionManager

        mock_manager = MagicMock(spec=SessionManager)
        mock_session = AsyncMock()

        async def error_stream(content):
            raise ValueError("Test error")
            yield

        mock_session.send_query = error_stream

        mock_manager.get_or_create_conversation_session = AsyncMock(
            return_value=(mock_session, "resolved-id", False)
        )

        with patch("api.routers.conversations.HistoryTracker") as mock_tracker_class:
            mock_tracker = MagicMock()
            mock_tracker.has_accumulated_text.return_value = True
            mock_tracker_class.return_value = mock_tracker

            events = _stream_conversation_events(
                "test-id", "Test", mock_manager, agent_id=None, username="testuser"
            )

            # Skip session_id
            await events.__anext__()

            # Get error event
            await events.__anext__()

            mock_tracker.finalize_assistant_response.assert_called_once_with(
                metadata={"error": "Test error"}
            )


class TestConversationsRouterIntegration:
    """Integration tests using FastAPI TestClient."""

    def test_create_conversation_requires_auth(self, client):
        """Test that create_conversation requires authentication."""
        response = client.post("/api/v1/conversations", json={"content": "Hello"})

        assert response.status_code == 401

    def test_create_conversation_with_api_key_only_rejected(self, client, auth_headers):
        """Test that API key alone is not sufficient (need JWT)."""
        response = client.post(
            "/api/v1/conversations", json={"content": "Hello"}, headers=auth_headers
        )

        # Should return 401 if no JWT token
        assert response.status_code == 401

    def test_create_conversation_with_valid_auth(self, client, user_auth_headers):
        """Test create_conversation with valid authentication."""
        response = client.post(
            "/api/v1/conversations",
            json={"content": "Hello, agent!"},
            headers=user_auth_headers,
        )

        # EventSourceResponse should be returned
        assert response.status_code == 200
        assert response.headers.get("content-type", "").startswith("text/event-stream")

    def test_stream_conversation_requires_auth(self, client):
        """Test that stream endpoint requires authentication."""
        response = client.post(
            "/api/v1/conversations/session-123/stream", json={"content": "What is 2+2?"}
        )

        assert response.status_code == 401

    def test_stream_conversation_with_valid_auth(self, client, user_auth_headers):
        """Test stream endpoint with valid authentication."""
        response = client.post(
            "/api/v1/conversations/test-session-456/stream",
            json={"content": "Tell me a joke"},
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        assert response.headers.get("content-type", "").startswith("text/event-stream")

    def test_create_conversation_with_session_id(self, client, user_auth_headers):
        """Test creating conversation with existing session_id."""
        session_id = "existing-session-789"

        response = client.post(
            "/api/v1/conversations",
            json={"content": "Continue our conversation", "session_id": session_id},
            headers=user_auth_headers,
        )

        assert response.status_code == 200

    def test_create_conversation_with_agent_id(self, client, user_auth_headers):
        """Test creating conversation with specific agent."""
        response = client.post(
            "/api/v1/conversations",
            json={"content": "Hello", "agent_id": "agent-xyz-123"},
            headers=user_auth_headers,
        )

        assert response.status_code == 200

    def test_create_conversation_validates_content_required(
        self, client, user_auth_headers
    ):
        """Test that content field is required."""
        response = client.post(
            "/api/v1/conversations", json={}, headers=user_auth_headers
        )

        # Should get validation error
        assert response.status_code == 422

    def test_create_conversation_validates_content_not_empty(
        self, client, user_auth_headers
    ):
        """Test that content cannot be empty."""
        response = client.post(
            "/api/v1/conversations", json={"content": ""}, headers=user_auth_headers
        )

        assert response.status_code == 422

    def test_stream_conversation_validates_content(self, client, user_auth_headers):
        """Test that stream endpoint validates content."""
        response = client.post(
            "/api/v1/conversations/session-123/stream",
            json={},
            headers=user_auth_headers,
        )

        assert response.status_code == 422


class TestSSEEventFormat:
    """Test SSE event format and structure."""

    @pytest.mark.asyncio
    async def test_session_id_event_format(self):
        """Test session_id event has correct format."""
        from api.routers.conversations import _stream_conversation_events
        from api.services.session_manager import SessionManager

        mock_manager = MagicMock(spec=SessionManager)
        mock_session = AsyncMock()
        mock_session.send_query = AsyncMock(return_value=iter([]))

        mock_manager.get_or_create_conversation_session = AsyncMock(
            return_value=(mock_session, "test-session-xyz", False)
        )

        events = _stream_conversation_events(
            "pending-id", "Test", mock_manager, agent_id=None, username=None
        )

        event = await events.__anext__()

        # Verify SSE structure
        assert "event" in event
        assert "data" in event
        assert event["event"] == EventType.SESSION_ID

        # Verify data is valid JSON
        data = json.loads(event["data"])
        assert "session_id" in data
        assert "found_in_cache" in data

    @pytest.mark.asyncio
    async def test_error_event_format(self):
        """Test error event has correct format."""
        from api.routers.conversations import _stream_conversation_events
        from api.services.session_manager import SessionManager

        mock_manager = MagicMock(spec=SessionManager)
        mock_session = AsyncMock()

        async def error_stream(content):
            raise ValueError("Test error")
            yield

        mock_session.send_query = error_stream

        mock_manager.get_or_create_conversation_session = AsyncMock(
            return_value=(mock_session, "resolved-id", False)
        )

        with patch("api.routers.conversations.HistoryTracker") as mock_tracker_class:
            mock_tracker = MagicMock()
            mock_tracker.has_accumulated_text.return_value = False
            mock_tracker_class.return_value = mock_tracker

            events = _stream_conversation_events(
                "test-id", "Test", mock_manager, agent_id=None, username="testuser"
            )

            # Skip session_id
            await events.__anext__()

            error_event = await events.__anext__()

            assert error_event["event"] == EventType.ERROR
            data = json.loads(error_event["data"])
            assert "error" in data
            assert "type" in data
            assert data["type"] == "ValueError"


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_empty_message_stream(self):
        """Test handling of empty message stream."""
        from api.routers.conversations import _stream_conversation_events
        from api.services.session_manager import SessionManager

        mock_manager = MagicMock(spec=SessionManager)
        mock_session = AsyncMock()

        async def empty_stream(content):
            return
            yield

        mock_session.send_query = empty_stream

        mock_manager.get_or_create_conversation_session = AsyncMock(
            return_value=(mock_session, "resolved-id", False)
        )

        with patch(
            "api.routers.conversations.get_user_history_storage"
        ) as mock_storage:
            mock_history = MagicMock()
            mock_storage.return_value = mock_history

            events = _stream_conversation_events(
                "test-id", "Test", mock_manager, agent_id=None, username="testuser"
            )

            # Should get session_id event
            event = await events.__anext__()
            assert event["event"] == EventType.SESSION_ID

            # No more events
            try:
                await events.__anext__()
                assert False, "Should have raised StopAsyncIteration"
            except StopAsyncIteration:
                pass

    @pytest.mark.asyncio
    async def test_none_username_passed_correctly(self):
        """Test that None username is handled correctly."""
        from api.routers.conversations import _stream_conversation_events
        from api.services.session_manager import SessionManager

        mock_manager = MagicMock(spec=SessionManager)
        mock_session = AsyncMock()
        mock_session.send_query = AsyncMock(return_value=iter([]))

        mock_manager.get_or_create_conversation_session = AsyncMock(
            return_value=(mock_session, "resolved-id", False)
        )

        events = _stream_conversation_events(
            "test-id", "Test", mock_manager, agent_id=None, username=None
        )

        event = await events.__anext__()
        assert event["event"] == EventType.SESSION_ID

    @pytest.mark.asyncio
    async def test_converts_messages_to_sse_correctly(self):
        """Test that convert_messages_to_sse is called correctly."""
        from api.routers.conversations import _stream_conversation_events
        from api.services.session_manager import SessionManager
        from claude_agent_sdk.types import StreamEvent

        mock_manager = MagicMock(spec=SessionManager)
        mock_session = AsyncMock()

        # Create a mock StreamEvent
        mock_stream_event = MagicMock(spec=StreamEvent)
        mock_stream_event.event = {"delta": {"type": "text_delta", "text": "Hello"}}

        async def mock_send_query(content):
            yield mock_stream_event

        mock_session.send_query = mock_send_query

        mock_manager.get_or_create_conversation_session = AsyncMock(
            return_value=(mock_session, "resolved-id", False)
        )

        with patch(
            "api.routers.conversations.get_user_history_storage"
        ) as mock_storage:
            mock_history = MagicMock()
            mock_storage.return_value = mock_history

            with patch(
                "api.routers.conversations.convert_messages_to_sse"
            ) as mock_convert:
                mock_convert.return_value = [
                    {
                        "event": EventType.TEXT_DELTA,
                        "data": json.dumps({"text": "Hello"}),
                    }
                ]

                events = _stream_conversation_events(
                    "test-id", "Test", mock_manager, agent_id=None, username=None
                )

                # Skip session_id
                await events.__anext__()

                # Get text delta event
                text_event = await events.__anext__()

                assert text_event["event"] == EventType.TEXT_DELTA
                mock_convert.assert_called()
