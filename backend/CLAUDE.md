# Backend CLAUDE.md

FastAPI backend for Claude Agent SDK Chat.

## Commands

```bash
cd backend
uv sync                              # Install dependencies
uv run main.py serve --port 7001     # Start server
uv run main.py chat                  # CLI chat (prompts for password)
uv run main.py agents                # List agents
uv run main.py sessions              # List sessions
pytest tests/ -v                     # Run tests
```

## Structure

```
backend/
├── main.py                 # CLI entry point (Click)
├── agents.yaml             # Agent definitions
├── subagents.yaml          # Delegation subagents
├── config.yaml             # Provider config
├── api/
│   ├── routers/
│   │   ├── websocket.py    # WebSocket chat handler
│   │   ├── sessions.py     # Session CRUD
│   │   ├── auth.py         # JWT auth routes
│   │   └── user_auth.py    # User login/register
│   ├── services/
│   │   ├── session_manager.py   # Session lifecycle
│   │   ├── history_tracker.py   # Message history
│   │   ├── token_service.py     # JWT tokens
│   │   └── question_manager.py  # User questions
│   ├── dependencies/       # Auth dependencies
│   ├── middleware/         # API key + JWT validation
│   └── models/             # Pydantic models
├── agent/core/             # Agent utilities
├── core/settings.py        # App settings
└── data/{username}/        # Per-user data
    ├── sessions.json       # Session metadata
    └── history/{id}.jsonl  # Message history
```

## Agent Configuration

Edit `agents.yaml`:

```yaml
agent-id-xyz123:
  name: "Display Name"
  description: "What this agent does"
  system_prompt: |
    Instructions (APPENDED to default prompt)
  subagents:
    - reviewer
  tools:
    - Read
    - Write
    - Edit
    - Bash
    - Grep
    - Glob
  model: sonnet  # haiku, sonnet, opus
```

## WebSocket Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `ready` | Server→Client | Connection established, session_id provided |
| `text_delta` | Server→Client | Streaming text chunk |
| `tool_use` | Server→Client | Tool invocation started |
| `tool_result` | Server→Client | Tool execution result |
| `done` | Server→Client | Turn complete, includes cost/turn_count |
| `error` | Server→Client | Error with code |
| `ask_user_question` | Server→Client | Question for user |
| `plan_approval` | Server→Client | Plan needs approval |

## Authentication

All routes require:
1. `X-API-Key` header - API key from `.env`
2. `Authorization: Bearer <token>` - JWT token

```python
from api.dependencies.auth import get_current_user, verify_api_key

@router.get("/api/v1/sessions")
async def list_sessions(
    current_user: User = Depends(get_current_user),
    api_key: str = Depends(verify_api_key)
):
    # current_user.username available
    pass
```

## Per-User Data

All user data isolated in `data/{username}/`:
- Use `agent/core/storage.py` utilities
- Never hardcode paths
- Session IDs are UUIDs

## Environment Variables

```bash
# .env
API_KEY=your-api-key           # For X-API-Key header
JWT_SECRET=your-jwt-secret     # For token signing
ANTHROPIC_API_KEY=sk-...       # Claude API key
# or
ZAI_API_KEY=...                # Alternative provider
```

## Adding WebSocket Events

1. Add event type to `api/routers/websocket.py`
2. Send via `await websocket.send_json({"type": "event_name", ...})`
3. Add frontend handler in `hooks/use-chat.ts`
