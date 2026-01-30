"""Centralized constants for API communication."""

from enum import IntEnum, StrEnum


class EventType(StrEnum):
    """Event types for SSE and WebSocket communication."""
    SESSION_ID = "session_id"
    TEXT_DELTA = "text_delta"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"
    DONE = "done"
    ERROR = "error"
    READY = "ready"
    ASK_USER_QUESTION = "ask_user_question"
    USER_ANSWER = "user_answer"
    PLAN_APPROVAL = "plan_approval"
    PLAN_APPROVAL_RESPONSE = "plan_approval_response"
    AUTH = "auth"
    AUTHENTICATED = "authenticated"


class MessageRole(StrEnum):
    """Message roles for conversation history."""
    USER = "user"
    ASSISTANT = "assistant"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"


class ErrorCode(StrEnum):
    """Structured error codes for WebSocket error events."""
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    RATE_LIMITED = "RATE_LIMITED"
    AGENT_NOT_FOUND = "AGENT_NOT_FOUND"
    UNKNOWN = "UNKNOWN"


class WSCloseCode(IntEnum):
    """WebSocket close codes for application-specific errors.

    Range 4000-4999 is reserved for application use per RFC 6455.
    """
    AUTH_FAILED = 4001
    SDK_CONNECTION_FAILED = 4002
    TOKEN_EXPIRED = 4005
    TOKEN_INVALID = 4006
    RATE_LIMITED = 4007
    AGENT_NOT_FOUND = 4008
    SESSION_NOT_FOUND = 4004


# Configuration defaults
ASK_USER_QUESTION_TIMEOUT = 60  # seconds
FIRST_MESSAGE_TRUNCATE_LENGTH = 100
