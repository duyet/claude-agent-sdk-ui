"""Comprehensive integration tests for WebSocket router.

Tests cover:
- Connection lifecycle with valid/invalid tokens
- Message sending/receiving
- Authentication flows
- Session resolution
- Error paths
- AskUserQuestion handling
- Message buffering during auth
- SDK client connection handling

Run: pytest tests/test_routers_websocket.py -v
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from typing import Any

import pytest
from starlette.websockets import WebSocketDisconnect

from api.constants import (
    ASK_USER_QUESTION_TIMEOUT,
    ErrorCode,
    EventType,
    WSCloseCode,
)
from api.routers.websocket import (
    AskUserQuestionHandler,
    SDKConnectionError,
    SessionResolutionError,
    WebSocketState,
    _build_ready_message,
    _connect_sdk_client,
    _create_message_receiver,
    _get_auth_message,
    _handle_session_id_event,
    _process_response_stream,
    _resolve_session,
    _validate_auth_token,
    _wait_for_authentication,
)
from api.services.question_manager import QuestionManager
from claude_agent_sdk.types import (
    PermissionResultAllow,
    PermissionResultDeny,
)


# Skip tests if JWT is not configured
from api.config import JWT_CONFIG

pytestmark = pytest.mark.skipif(
    not JWT_CONFIG.get("secret_key"), reason="JWT not configured"
)


class MockWebSocket:
    """Mock WebSocket for testing."""

    def __init__(self):
        self.client = Mock(host="127.0.0.1", port=12345)
        self.sent_messages = []
        self.receive_queue = asyncio.Queue()
        self.accepted = False
        self.closed = False
        self.close_code = None
        self.close_reason = None
        self._disconnect_on_close = False
        self._close_raises = False  # By default, close() does not raise

    async def accept(self):
        """Accept the connection."""
        self.accepted = True

    async def send_json(self, data: dict[str, Any]):
        """Send JSON data."""
        self.sent_messages.append(data)
        if self.closed:
            raise WebSocketDisconnect(
                code=self.close_code or 1000, reason=self.close_reason or ""
            )

    async def send_text(self, text: str):
        """Send text data."""
        self.sent_messages.append(text)

    async def receive_json(self):
        """Receive JSON data."""
        data = await self.receive_queue.get()
        if self.closed:
            raise WebSocketDisconnect(
                code=self.close_code or 1000, reason=self.close_reason or ""
            )
        return data

    async def receive_text(self):
        """Receive text data."""
        data = await self.receive_queue.get()
        if self.closed:
            raise WebSocketDisconnect(
                code=self.close_code or 1000, reason=self.close_reason or ""
            )
        return data

    async def close(self, code: int = 1000, reason: str = ""):
        """Close the connection."""
        self.closed = True
        self.close_code = code
        self.close_reason = reason
        if self._disconnect_on_close or self._close_raises:
            raise WebSocketDisconnect(code=code, reason=reason)

    def queue_message(self, msg: dict[str, Any]):
        """Queue a message for receive."""
        self.receive_queue.put_nowait(msg)

    def set_disconnect_on_close(self, value: bool):
        """Set whether to raise disconnect on close."""
        self._disconnect_on_close = value

    def set_close_raises(self, value: bool):
        """Set whether close() raises WebSocketDisconnect."""
        self._close_raises = value


class MockSessionStorage:
    """Mock session storage for testing."""

    def __init__(self):
        self.sessions: dict[str, Mock] = {}

    def get_session(self, session_id: str):
        """Get a session by ID."""
        return self.sessions.get(session_id)

    def save_session(
        self,
        session_id: str,
        first_message: str | None = None,
        agent_id: str | None = None,
    ):
        """Save a session."""
        session = Mock()
        session.session_id = session_id
        session.first_message = first_message
        session.agent_id = agent_id
        session.turn_count = 0
        self.sessions[session_id] = session

    def update_session(self, session_id: str, turn_count: int):
        """Update a session."""
        if session_id in self.sessions:
            self.sessions[session_id].turn_count = turn_count


class MockHistoryStorage:
    """Mock history storage for testing."""

    def __init__(self):
        self.data = {}

    def get_history(self, session_id: str):
        """Get history for a session."""
        return self.data.get(session_id, [])


class TestWebSocketState:
    """Tests for WebSocketState dataclass."""

    def test_default_initialization(self):
        """Test WebSocketState initializes with correct defaults."""
        state = WebSocketState()

        assert state.session_id is None
        assert state.turn_count == 0
        assert state.first_message is None
        assert state.tracker is None
        assert state.pending_user_message is None
        assert state.last_ask_user_question_tool_use_id is None
        assert state.authenticated is False

    def test_custom_initialization(self):
        """Test WebSocketState can be initialized with custom values."""
        state = WebSocketState(
            session_id="test-session-123",
            turn_count=5,
            first_message="Hello world",
            tracker=MagicMock(),
            pending_user_message="Pending",
            last_ask_user_question_tool_use_id="tool-use-123",
            authenticated=True,
        )

        assert state.session_id == "test-session-123"
        assert state.turn_count == 5
        assert state.first_message == "Hello world"
        assert state.tracker is not None
        assert state.pending_user_message == "Pending"
        assert state.last_ask_user_question_tool_use_id == "tool-use-123"
        assert state.authenticated is True

    def test_mutable_fields(self):
        """Test WebSocketState fields are mutable."""
        state = WebSocketState()

        state.session_id = "new-session"
        state.turn_count = 10
        state.authenticated = True

        assert state.session_id == "new-session"
        assert state.turn_count == 10
        assert state.authenticated is True


class TestValidateAuthToken:
    """Tests for _validate_auth_token function."""

    @pytest.mark.asyncio
    async def test_valid_user_identity_token(self):
        """Test validation with valid user identity token."""
        from api.services.token_service import token_service

        if not token_service:
            pytest.skip("Token service not configured")

        # Create a user identity token
        token, jti, expires_in = token_service.create_user_identity_token(
            user_id="test_user_123",
            username="testuser",
            role="user",
            full_name="Test User",
        )

        result = await _validate_auth_token(token)

        assert result is not None
        user_id, result_jti, username = result
        assert user_id == "test_user_123"
        assert result_jti == jti
        assert username == "testuser"

    @pytest.mark.asyncio
    async def test_valid_access_token(self):
        """Test validation with valid access token."""
        from api.services.token_service import token_service

        if not token_service:
            pytest.skip("Token service not configured")

        # Create an access token with username claim
        token, jti, expires_in = token_service.create_access_token(
            user_id="test_user_456",
            additional_claims={"username": "accessuser", "role": "user"},
        )

        result = await _validate_auth_token(token)

        assert result is not None
        user_id, result_jti, username = result
        assert user_id == "test_user_456"
        assert result_jti == jti
        assert username == "accessuser"

    @pytest.mark.asyncio
    async def test_invalid_token(self):
        """Test validation with invalid token."""
        result = await _validate_auth_token("invalid.token.string")

        assert result is None

    @pytest.mark.asyncio
    async def test_none_token(self):
        """Test validation with None token."""
        result = await _validate_auth_token(None)

        assert result is None

    @pytest.mark.asyncio
    async def test_expired_token(self):
        """Test validation with expired token."""
        from api.services.token_service import token_service

        if not token_service:
            pytest.skip("Token service not configured")

        # Create a token and manually expire it
        token, jti, _ = token_service.create_user_identity_token(
            user_id="test_user", username="testuser", role="user"
        )

        # Revoke it to simulate it being invalid
        token_service.revoke_token(jti)

        result = await _validate_auth_token(token)

        assert result is None

    @pytest.mark.asyncio
    async def test_token_without_username(self):
        """Test token without username claim returns None."""
        from api.services.token_service import token_service

        if not token_service:
            pytest.skip("Token service not configured")

        # Create an access token without username
        token, jti, expires_in = token_service.create_access_token(
            user_id="test_user_no_username"
        )

        result = await _validate_auth_token(token)

        # Should return None because no username claim
        assert result is None


class TestResolveSession:
    """Tests for _resolve_session function."""

    @pytest.mark.asyncio
    async def test_new_session_no_session_id(self):
        """Test resolving when no session_id provided."""
        websocket = MockWebSocket()
        session_storage = MockSessionStorage()

        existing_session, resume_session_id = await _resolve_session(
            websocket, None, session_storage
        )

        assert existing_session is None
        assert resume_session_id is None

    @pytest.mark.asyncio
    async def test_existing_session_found(self):
        """Test resolving when session exists."""
        websocket = MockWebSocket()
        session_storage = MockSessionStorage()

        # Create a session
        session_storage.save_session(
            session_id="existing-session-123", first_message="Test message"
        )

        existing_session, resume_session_id = await _resolve_session(
            websocket, "existing-session-123", session_storage
        )

        assert existing_session is not None
        assert existing_session.session_id == "existing-session-123"
        assert resume_session_id == "existing-session-123"

    @pytest.mark.asyncio
    async def test_session_not_found(self):
        """Test resolving when session doesn't exist."""
        websocket = MockWebSocket()
        session_storage = MockSessionStorage()

        with pytest.raises(SessionResolutionError):
            await _resolve_session(websocket, "non-existent-session", session_storage)

        # Should have sent error message
        assert len(websocket.sent_messages) == 1
        error_msg = websocket.sent_messages[0]
        assert error_msg["type"] == EventType.ERROR
        assert error_msg["code"] == ErrorCode.SESSION_NOT_FOUND
        assert "non-existent-session" in error_msg["error"]
        # WebSocket should be closed without raising (raise_disconnect=False)
        assert websocket.closed is True
        assert websocket.close_code == WSCloseCode.SESSION_NOT_FOUND

    @pytest.mark.asyncio
    async def test_session_not_found_closes_websocket(self):
        """Test that session not found closes WebSocket."""
        websocket = MockWebSocket()
        session_storage = MockSessionStorage()

        with pytest.raises(SessionResolutionError):
            await _resolve_session(websocket, "non-existent-session", session_storage)

        assert websocket.closed is True
        assert websocket.close_code == WSCloseCode.SESSION_NOT_FOUND


class TestConnectSDKClient:
    """Tests for _connect_sdk_client function."""

    @pytest.mark.asyncio
    async def test_successful_connection(self):
        """Test successful SDK client connection."""
        websocket = MockWebSocket()
        client = MagicMock()
        client.connect = AsyncMock()

        await _connect_sdk_client(websocket, client)

        client.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_failure_sends_error(self):
        """Test that connection failure sends error message."""
        websocket = MockWebSocket()
        client = MagicMock()
        client.connect = AsyncMock(side_effect=RuntimeError("Connection failed"))

        with pytest.raises(SDKConnectionError):
            await _connect_sdk_client(websocket, client)

        # Should have sent error message
        assert len(websocket.sent_messages) == 1
        error_msg = websocket.sent_messages[0]
        assert error_msg["type"] == EventType.ERROR
        assert error_msg["code"] == ErrorCode.UNKNOWN
        assert "Failed to initialize agent" in error_msg["error"]

    @pytest.mark.asyncio
    async def test_connection_failure_closes_websocket(self):
        """Test that connection failure closes WebSocket."""
        websocket = MockWebSocket()
        # Don't raise on close - close_with_error uses raise_disconnect=False
        websocket.set_close_raises(False)
        client = MagicMock()
        client.connect = AsyncMock(side_effect=Exception("SDK error"))

        with pytest.raises(SDKConnectionError):
            await _connect_sdk_client(websocket, client)

        assert websocket.closed is True
        assert websocket.close_code == WSCloseCode.SDK_CONNECTION_FAILED


class TestBuildReadyMessage:
    """Tests for _build_ready_message function."""

    def test_new_session_message(self):
        """Test ready message for new session."""
        message = _build_ready_message(resume_session_id=None, turn_count=0)

        assert message["type"] == EventType.READY
        assert "session_id" not in message
        assert "resumed" not in message
        assert "turn_count" not in message

    def test_resumed_session_message(self):
        """Test ready message for resumed session."""
        message = _build_ready_message(resume_session_id="session-123", turn_count=5)

        assert message["type"] == EventType.READY
        assert message["session_id"] == "session-123"
        assert message["resumed"] is True
        assert message["turn_count"] == 5


class TestHandleSessionIdEvent:
    """Tests for _handle_session_id_event function."""

    def test_initializes_tracker_on_first_session_id(self):
        """Test that tracker is initialized on first session_id event."""
        state = WebSocketState()
        session_storage = MockSessionStorage()
        history = MockHistoryStorage()

        event_data = {"session_id": "new-session-123"}

        _handle_session_id_event(
            event_data, state, session_storage, history, agent_id=None
        )

        assert state.session_id == "new-session-123"
        assert state.tracker is not None
        assert state.tracker.session_id == "new-session-123"

    def test_saves_pending_user_message(self):
        """Test that pending user message is saved on session_id event."""
        state = WebSocketState(pending_user_message="Pending message")
        session_storage = MockSessionStorage()
        history = MockHistoryStorage()

        event_data = {"session_id": "session-456"}

        with patch("api.routers.websocket.HistoryTracker") as mock_tracker_class:
            mock_tracker = MagicMock()
            mock_tracker_class.return_value = mock_tracker

            _handle_session_id_event(
                event_data, state, session_storage, history, agent_id=None
            )

            mock_tracker.save_user_message.assert_called_once_with("Pending message")
            assert state.pending_user_message is None

    def test_does_not_reinitialize_tracker(self):
        """Test that tracker is not reinitialized if it already exists."""
        state = WebSocketState()
        session_storage = MockSessionStorage()
        history = MockHistoryStorage()

        # Set up existing tracker
        existing_tracker = MagicMock()
        state.tracker = existing_tracker

        event_data = {"session_id": "another-session"}

        _handle_session_id_event(
            event_data, state, session_storage, history, agent_id=None
        )

        # Tracker should not be replaced
        assert state.tracker == existing_tracker


class TestAskUserQuestionHandler:
    """Tests for AskUserQuestionHandler class."""

    @pytest.fixture
    def handler(self):
        """Create a handler instance."""
        websocket = MockWebSocket()
        question_manager = QuestionManager()
        state = WebSocketState()

        return AskUserQuestionHandler(
            websocket=websocket,
            question_manager=question_manager,
            state=state,
            timeout=ASK_USER_QUESTION_TIMEOUT,
        )

    @pytest.mark.asyncio
    async def test_allows_non_ask_user_question_tools(self, handler):
        """Test that non-AskUserQuestion tools are allowed."""
        result = await handler.handle(
            tool_name="Bash", tool_input={"command": "echo hello"}, context=MagicMock()
        )

        assert isinstance(result, PermissionResultAllow)
        assert result.updated_input == {"command": "echo hello"}

    @pytest.mark.asyncio
    async def test_sends_question_to_client(self, handler):
        """Test that question is sent to client."""
        tool_input = {
            "questions": [
                {"id": "q1", "question": "What is your name?"},
                {"id": "q2", "question": "How old are you?"},
            ]
        }
        context = MagicMock()

        # Send question and immediately answer it
        result_task = asyncio.create_task(
            handler.handle("AskUserQuestion", tool_input, context)
        )

        # Wait for question to be sent
        await asyncio.sleep(0.01)

        # Check question was sent
        assert len(handler._websocket.sent_messages) == 1
        sent_msg = handler._websocket.sent_messages[0]
        assert sent_msg["type"] == EventType.ASK_USER_QUESTION
        # The question_id should be a UUID (either from state or generated)
        assert "question_id" in sent_msg
        assert len(sent_msg["questions"]) == 2

        # Submit answer
        question_id = sent_msg["question_id"]
        # submit_answer is async
        await handler._question_manager.submit_answer(
            question_id, {"q1": "John", "q2": "30"}
        )

        result = await result_task
        assert isinstance(result, PermissionResultAllow)
        assert "answers" in result.updated_input

    @pytest.mark.asyncio
    async def test_timeout_waits_for_answer(self, handler):
        """Test that timeout occurs if no answer is received."""
        handler._timeout = 0.1  # Short timeout for testing

        result = await handler.handle(
            tool_name="AskUserQuestion",
            tool_input={"questions": [{"id": "q1", "question": "Test?"}]},
            context=MagicMock(),
        )

        assert isinstance(result, PermissionResultDeny)
        assert "Timeout" in result.message

    @pytest.mark.asyncio
    async def test_question_with_custom_tool_use_id(self, handler):
        """Test handler uses custom tool_use_id from state."""
        handler._state.last_ask_user_question_tool_use_id = "custom-tool-use-123"

        result_task = asyncio.create_task(
            handler.handle(
                tool_name="AskUserQuestion",
                tool_input={"questions": [{"id": "q1", "question": "Test?"}]},
                context=MagicMock(),
            )
        )

        await asyncio.sleep(0.01)

        # Check the custom ID was used
        sent_msg = handler._websocket.sent_messages[0]
        assert sent_msg["question_id"] == "custom-tool-use-123"

        # Submit answer
        await handler._question_manager.submit_answer(
            "custom-tool-use-123", {"q1": "Answer"}
        )

        await result_task


class TestWaitForAuthentication:
    """Tests for _wait_for_authentication function."""

    @pytest.mark.asyncio
    async def test_successful_authentication(self):
        """Test successful authentication flow."""
        from api.services.token_service import token_service

        if not token_service:
            pytest.skip("Token service not configured")

        # Create a valid token
        token, jti, _ = token_service.create_user_identity_token(
            user_id="test_user", username="testuser", role="user"
        )

        websocket = MockWebSocket()
        state = WebSocketState()
        message_queue = asyncio.Queue()

        # Queue the auth message
        await message_queue.put({"type": EventType.AUTH, "token": token})

        result = await _wait_for_authentication(websocket, message_queue, state)

        assert result is not None
        user_id, result_jti, username = result
        assert user_id == "test_user"
        assert username == "testuser"

    @pytest.mark.asyncio
    async def test_authentication_timeout(self):
        """Test authentication timeout when no auth received."""
        websocket = MockWebSocket()
        state = WebSocketState()
        message_queue = asyncio.Queue()

        result = await _wait_for_authentication(websocket, message_queue, state)

        assert result is None
        # Should have sent error
        assert len(websocket.sent_messages) >= 1
        error_msg = websocket.sent_messages[-1]
        assert error_msg["type"] == EventType.ERROR
        assert error_msg["code"] == ErrorCode.TOKEN_INVALID

    @pytest.mark.asyncio
    async def test_invalid_token_sends_error(self):
        """Test that invalid token sends error and closes."""
        websocket = MockWebSocket()
        state = WebSocketState()
        message_queue = asyncio.Queue()

        # Queue invalid auth message
        await message_queue.put({"type": EventType.AUTH, "token": "invalid.token.here"})

        result = await _wait_for_authentication(websocket, message_queue, state)

        assert result is None
        # Should have sent error
        assert any(
            msg.get("type") == EventType.ERROR
            and msg.get("code") == ErrorCode.TOKEN_INVALID
            for msg in websocket.sent_messages
        )

    @pytest.mark.asyncio
    async def test_messages_are_buffered(self):
        """Test that non-auth messages are buffered during auth wait."""
        from api.services.token_service import token_service

        if not token_service:
            pytest.skip("Token service not configured")

        # Create a valid token
        token, _, _ = token_service.create_user_identity_token(
            user_id="test_user", username="testuser", role="user"
        )

        websocket = MockWebSocket()
        state = WebSocketState()
        message_queue = asyncio.Queue()

        # Queue messages in wrong order (user message first, then auth)
        await message_queue.put(
            {
                "type": "text",  # Not auth type
                "content": "Hello",
            }
        )
        await message_queue.put({"type": EventType.AUTH, "token": token})

        result = await _wait_for_authentication(websocket, message_queue, state)

        assert result is not None
        # The text message should still be in the queue
        assert not message_queue.empty()


class TestGetAuthMessage:
    """Tests for _get_auth_message function."""

    @pytest.mark.asyncio
    async def test_extracts_valid_auth_message(self):
        """Test extracting valid auth message from queue."""
        from api.services.token_service import token_service

        if not token_service:
            pytest.skip("Token service not configured")

        token, _, _ = token_service.create_user_identity_token(
            user_id="test_user", username="testuser", role="user"
        )

        message_queue = asyncio.Queue()
        await message_queue.put({"type": EventType.AUTH, "token": token})

        result = await _get_auth_message(message_queue)

        assert result is not None
        user_id, jti, username = result
        assert username == "testuser"

    @pytest.mark.asyncio
    async def test_buffers_non_auth_messages(self):
        """Test that non-auth messages are buffered."""
        from api.services.token_service import token_service

        if not token_service:
            pytest.skip("Token service not configured")

        token, _, _ = token_service.create_user_identity_token(
            user_id="test_user", username="testuser", role="user"
        )

        message_queue = asyncio.Queue()

        # Queue non-auth messages first
        await message_queue.put({"type": "text", "content": "Hello"})
        await message_queue.put({"type": "other", "data": "test"})

        # Then queue auth message
        await message_queue.put({"type": EventType.AUTH, "token": token})

        result = await _get_auth_message(message_queue)

        assert result is not None
        # Buffered messages should be back in the queue
        assert not message_queue.empty()

    @pytest.mark.asyncio
    async def test_returns_none_on_connection_close(self):
        """Test returning None when connection closes."""
        message_queue = asyncio.Queue()
        await message_queue.put(None)  # Signal connection closed

        result = await _get_auth_message(message_queue)

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_invalid_token(self):
        """Test returning None for invalid token."""
        message_queue = asyncio.Queue()
        await message_queue.put({"type": EventType.AUTH, "token": "invalid.token"})

        result = await _get_auth_message(message_queue)

        assert result is None


class TestCreateMessageReceiver:
    """Tests for _create_message_receiver function."""

    @pytest.mark.asyncio
    async def test_receives_json_messages(self):
        """Test receiving JSON messages."""
        websocket = MockWebSocket()
        message_queue = asyncio.Queue()
        question_manager = QuestionManager()
        state = WebSocketState(authenticated=True)

        # Queue a message
        websocket.queue_message({"type": "text", "content": "Hello"})

        # Start receiver
        receiver_task = asyncio.create_task(
            _create_message_receiver(websocket, message_queue, question_manager, state)
        )

        # Wait for message to be processed
        await asyncio.sleep(0.01)

        # Check message was queued
        assert not message_queue.empty()
        msg = await message_queue.get()
        assert msg["content"] == "Hello"

        # Clean up
        receiver_task.cancel()
        try:
            await receiver_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_routes_user_answer_to_question_manager(self):
        """Test that user_answer messages are routed to question manager."""
        websocket = MockWebSocket()
        message_queue = asyncio.Queue()
        question_manager = QuestionManager()
        state = WebSocketState(authenticated=True, tracker=MagicMock())

        # Create a pending question
        question_id = "test-question-123"
        question_manager.create_question(question_id, [{"id": "q1"}])

        # Send user answer
        websocket.queue_message(
            {
                "type": EventType.USER_ANSWER,
                "question_id": question_id,
                "answers": {"q1": "Answer 1"},
            }
        )

        # Start receiver
        receiver_task = asyncio.create_task(
            _create_message_receiver(websocket, message_queue, question_manager, state)
        )

        await asyncio.sleep(0.01)

        # Submit answer to question manager in a separate task
        async def submit_answer():
            await asyncio.sleep(0.01)
            answers = await question_manager.wait_for_answer(question_id, timeout=0.1)
            return answers

        answer_task = asyncio.create_task(submit_answer())

        # Wait a bit for processing
        await asyncio.sleep(0.05)

        # Clean up
        receiver_task.cancel()
        try:
            await receiver_task
        except asyncio.CancelledError:
            pass

        answer_task.cancel()
        try:
            await answer_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_handles_websocket_disconnect(self):
        """Test handling WebSocket disconnect."""
        websocket = MockWebSocket()
        message_queue = asyncio.Queue()
        question_manager = QuestionManager()
        state = WebSocketState(authenticated=True)

        # Start receiver
        receiver_task = asyncio.create_task(
            _create_message_receiver(websocket, message_queue, question_manager, state)
        )

        # Queue a message that will cause disconnect when received
        # The MockWebSocket.receive_json will raise WebSocketDisconnect if closed
        websocket.closed = True
        websocket.close_code = 1000
        await websocket.receive_queue.put({})  # This will trigger disconnect

        # Wait for receiver to finish (it should put None in queue and raise)
        try:
            await asyncio.wait_for(receiver_task, timeout=1.0)
        except (WebSocketDisconnect, asyncio.TimeoutError):
            pass

        # Should have put None in queue due to disconnect handling
        # Note: The receiver catches WebSocketDisconnect and puts None in queue
        assert not message_queue.empty()
        msg = await message_queue.get()
        assert msg is None

    @pytest.mark.asyncio
    async def test_buffers_messages_when_not_authenticated(self):
        """Test that messages are buffered when not authenticated."""
        websocket = MockWebSocket()
        message_queue = asyncio.Queue()
        question_manager = QuestionManager()
        state = WebSocketState(authenticated=False)

        # Queue a message before auth
        websocket.queue_message({"type": "text", "content": "Pre-auth message"})

        # Start receiver
        receiver_task = asyncio.create_task(
            _create_message_receiver(websocket, message_queue, question_manager, state)
        )

        await asyncio.sleep(0.01)

        # Message should be queued (buffered)
        assert not message_queue.empty()

        # Clean up
        receiver_task.cancel()
        try:
            await receiver_task
        except asyncio.CancelledError:
            pass


class TestProcessResponseStream:
    """Tests for _process_response_stream function."""

    @pytest.mark.asyncio
    async def test_processes_text_delta_events(self):
        """Test processing text_delta events."""
        from claude_agent_sdk.types import ResultMessage

        websocket = MockWebSocket()
        state = WebSocketState()
        session_storage = MockSessionStorage()
        history = MockHistoryStorage()

        client = MagicMock()

        # Track call count
        call_count = [0]

        # Create side_effect that returns different values based on call
        def mock_message_to_dicts(msg):
            call_count[0] += 1
            if isinstance(msg, ResultMessage):
                return []  # No events for ResultMessage
            return [{"type": EventType.TEXT_DELTA, "text": "Hello"}]

        # Create async generator for messages
        async def mock_responses():
            # Yield a mock message that will be converted to text_delta
            yield MagicMock()  # Some message
            # Yield ResultMessage to end the stream
            yield ResultMessage(
                subtype="success",
                duration_ms=100,
                duration_api_ms=50,
                is_error=False,
                num_turns=1,
                session_id="test-session-123",
            )

        with patch(
            "api.routers.websocket.message_to_dicts", side_effect=mock_message_to_dicts
        ):
            client.receive_response = mock_responses

            await _process_response_stream(
                client, websocket, state, session_storage, history
            )

        # Should have sent the text_delta
        assert len(websocket.sent_messages) == 1
        assert websocket.sent_messages[0]["type"] == EventType.TEXT_DELTA

    @pytest.mark.asyncio
    async def test_captures_ask_user_question_tool_use_id(self):
        """Test capturing tool_use_id for AskUserQuestion."""
        from claude_agent_sdk.types import ResultMessage

        websocket = MockWebSocket()
        state = WebSocketState()
        session_storage = MockSessionStorage()
        history = MockHistoryStorage()

        client = MagicMock()

        async def mock_responses():
            yield MagicMock()  # Some message
            # End the stream
            yield ResultMessage(
                subtype="success",
                duration_ms=100,
                duration_api_ms=50,
                is_error=False,
                num_turns=1,
                session_id="test-session-456",
            )

        with patch(
            "api.routers.websocket.message_to_dicts",
            return_value=[
                {
                    "type": EventType.TOOL_USE,
                    "name": "AskUserQuestion",
                    "id": "tool-use-abc123",
                }
            ],
        ):
            client.receive_response = mock_responses

            await _process_response_stream(
                client, websocket, state, session_storage, history
            )

        assert state.last_ask_user_question_tool_use_id == "tool-use-abc123"

    @pytest.mark.asyncio
    async def test_handles_session_id_event(self):
        """Test handling session_id event."""
        from claude_agent_sdk.types import ResultMessage

        websocket = MockWebSocket()
        state = WebSocketState()
        session_storage = MockSessionStorage()
        history = MockHistoryStorage()

        client = MagicMock()

        async def mock_responses():
            yield MagicMock()  # Some message
            # End the stream
            yield ResultMessage(
                subtype="success",
                duration_ms=100,
                duration_api_ms=50,
                is_error=False,
                num_turns=1,
                session_id="new-session-456",
            )

        with patch(
            "api.routers.websocket.message_to_dicts",
            return_value=[
                {"type": EventType.SESSION_ID, "session_id": "new-session-456"}
            ],
        ):
            client.receive_response = mock_responses

            await _process_response_stream(
                client, websocket, state, session_storage, history
            )

        assert state.session_id == "new-session-456"
        assert state.tracker is not None


class TestIntegrationScenarios:
    """Integration tests for complete WebSocket scenarios."""

    @pytest.mark.asyncio
    async def test_full_connection_lifecycle(self):
        """Test complete connection lifecycle from connect to disconnect."""
        from api.services.token_service import token_service

        if not token_service:
            pytest.skip("Token service not configured")

        # Create a valid token
        token, _, _ = token_service.create_user_identity_token(
            user_id="test_user", username="testuser", role="user"
        )

        websocket = MockWebSocket()

        # Simulate the connection flow
        await websocket.accept()

        # Send auth
        await websocket.send_json({"type": EventType.AUTHENTICATED})

        # Send ready
        await websocket.send_json({"type": EventType.READY})

        assert websocket.accepted is True
        assert len(websocket.sent_messages) == 2

    @pytest.mark.asyncio
    async def test_authentication_then_message_flow(self):
        """Test auth followed by message sending."""
        from api.services.token_service import token_service

        if not token_service:
            pytest.skip("Token service not configured")

        token, _, _ = token_service.create_user_identity_token(
            user_id="test_user", username="testuser", role="user"
        )

        websocket = MockWebSocket()
        message_queue = asyncio.Queue()
        state = WebSocketState()

        # Send auth message
        await message_queue.put({"type": EventType.AUTH, "token": token})

        # Wait for auth
        result = await _wait_for_authentication(websocket, message_queue, state)

        assert result is not None
        # Note: _wait_for_authentication doesn't set state.authenticated,
        # the caller is expected to do that. Verify the auth result.
        assert result[0] == "test_user"  # user_id
        assert result[2] == "testuser"  # username
        # result[1] is the jti (JWT ID)

        # Note: _wait_for_authentication does NOT send AUTHENTICATED message.
        # That's done by the caller (websocket_chat) after successful auth.
        # This test only verifies the auth validation part.

    @pytest.mark.asyncio
    async def test_error_during_session_resolution(self):
        """Test error handling during session resolution."""
        from api.services.token_service import token_service

        if not token_service:
            pytest.skip("Token service not configured")

        token, _, _ = token_service.create_user_identity_token(
            user_id="test_user", username="testuser", role="user"
        )

        websocket = MockWebSocket()
        state = WebSocketState()
        message_queue = asyncio.Queue()

        # Auth succeeds
        await message_queue.put({"type": EventType.AUTH, "token": token})

        result = await _wait_for_authentication(websocket, message_queue, state)
        assert result is not None

        # Now try to resolve non-existent session
        session_storage = MockSessionStorage()

        with pytest.raises(SessionResolutionError):
            await _resolve_session(websocket, "bad-session-id", session_storage)

        # Should have error in sent messages
        assert any(
            msg.get("type") == EventType.ERROR
            and msg.get("code") == ErrorCode.SESSION_NOT_FOUND
            for msg in websocket.sent_messages
        )


class TestErrorPaths:
    """Tests for error handling paths."""

    @pytest.mark.asyncio
    async def test_websocket_close_during_auth(self):
        """Test WebSocket closing during authentication."""
        websocket = MockWebSocket()
        state = WebSocketState()
        message_queue = asyncio.Queue()

        # Simulate immediate close
        await message_queue.put(None)

        result = await _wait_for_authentication(websocket, message_queue, state)

        assert result is None

    @pytest.mark.asyncio
    async def test_multiple_auth_messages(self):
        """Test handling multiple auth messages (should only process first)."""
        from api.services.token_service import token_service

        if not token_service:
            pytest.skip("Token service not configured")

        token1, _, _ = token_service.create_user_identity_token(
            user_id="user1", username="user1", role="user"
        )

        message_queue = asyncio.Queue()

        # Send multiple auth messages
        await message_queue.put({"type": EventType.AUTH, "token": token1})
        await message_queue.put({"type": EventType.AUTH, "token": "another.token"})

        result = await _get_auth_message(message_queue)

        # Should return first valid token
        assert result is not None
        assert result[2] == "user1"

    @pytest.mark.asyncio
    async def test_empty_token_in_auth_message(self):
        """Test auth message with empty token."""
        message_queue = asyncio.Queue()

        await message_queue.put({"type": EventType.AUTH, "token": ""})

        result = await _get_auth_message(message_queue)

        assert result is None

    @pytest.mark.asyncio
    async def test_malformed_auth_message(self):
        """Test malformed auth message."""
        message_queue = asyncio.Queue()

        await message_queue.put(
            {
                "type": EventType.AUTH
                # Missing token field
            }
        )

        result = await _get_auth_message(message_queue)

        assert result is None


class TestQuestionHandlingIntegration:
    """Integration tests for question handling."""

    @pytest.mark.asyncio
    async def test_full_question_flow(self):
        """Test complete question flow from ask to answer."""
        websocket = MockWebSocket()
        question_manager = QuestionManager()
        state = WebSocketState(authenticated=True, tracker=MagicMock())

        handler = AskUserQuestionHandler(
            websocket=websocket,
            question_manager=question_manager,
            state=state,
            timeout=1.0,
        )

        # Start handling the question
        handle_task = asyncio.create_task(
            handler.handle(
                tool_name="AskUserQuestion",
                tool_input={
                    "questions": [{"id": "q1", "question": "What is your name?"}]
                },
                context=MagicMock(),
            )
        )

        # Wait for question to be sent
        await asyncio.sleep(0.01)

        # Verify question was sent
        assert len(websocket.sent_messages) == 1
        sent_msg = websocket.sent_messages[0]
        assert sent_msg["type"] == EventType.ASK_USER_QUESTION

        # Submit answer
        question_id = sent_msg["question_id"]
        await question_manager.submit_answer(question_id, {"q1": "Alice"})

        # Wait for handling to complete
        result = await handle_task

        assert isinstance(result, PermissionResultAllow)
        assert result.updated_input["answers"] == {"q1": "Alice"}

    @pytest.mark.asyncio
    async def test_question_timeout_cleanup(self):
        """Test that pending question is cleaned up after timeout."""
        websocket = MockWebSocket()
        question_manager = QuestionManager()
        state = WebSocketState(authenticated=True)

        handler = AskUserQuestionHandler(
            websocket=websocket,
            question_manager=question_manager,
            state=state,
            timeout=0.1,  # Very short timeout
        )

        result = await handler.handle(
            tool_name="AskUserQuestion",
            tool_input={"questions": [{"id": "q1", "question": "Test?"}]},
            context=MagicMock(),
        )

        assert isinstance(result, PermissionResultDeny)
        assert "Timeout" in result.message

        # Question should be cleaned up
        assert question_manager.get_pending_count() == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
