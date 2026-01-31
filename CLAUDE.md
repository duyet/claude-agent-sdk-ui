# CLAUDE.md

Development guide for Claude Code.

## URLs

**Always use production backend URL** - never localhost for backend connections.

| Service | URL |
|---------|-----|
| Backend API | `https://claude-agent-sdk-fastapi-sg4.tt-ai.org` |
| WebSocket | `wss://claude-agent-sdk-fastapi-sg4.tt-ai.org/api/v1/ws/chat` |
| Frontend | `https://claude-agent-sdk-chat.tt-ai.org` |

## Project Overview

**Claude Agent SDK Chat** - Multi-agent chat application with WebSocket streaming, user auth, and session management.

## Structure

```
backend/                    # FastAPI + Python (port 7001)
├── agents.yaml            # Agent definitions
├── api/routers/           # WebSocket, sessions, auth
├── api/services/          # Session, history, token services
└── data/{username}/       # Per-user sessions + history

frontend/                   # Next.js 15 + Bun (port 7002)
├── app/                   # Pages and API routes
├── components/            # UI components (chat, sidebar, layout)
├── hooks/                 # React hooks (use-chat, use-websocket)
└── lib/store/             # Zustand stores
```

See `backend/CLAUDE.md` and `frontend/CLAUDE.md` for detailed guides.

## Quick Start

```bash
# Backend
cd backend && uv sync && uv run main.py serve --port 7001

# Frontend
cd frontend && bun install && bun dev
```

## Key Workflows

### Adding a New Agent
1. Edit `backend/agents.yaml`
2. Restart backend server
3. Agent appears in frontend automatically

### Debugging WebSocket
1. Check status indicator in chat header
2. Browser console for WebSocket errors
3. Backend logs for auth/connection issues

### Using OpenRouter

[OpenRouter](https://openrouter.ai) provides access to 100+ models (GPT-4, Claude, Llama, Mistral, etc.).

1. Get API key at https://openrouter.ai/keys
2. Add to `backend/.env`:
   ```bash
   OPENROUTER_API_KEY=sk-or-v1-your-key
   OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
   ```
3. Set provider in `backend/config.yaml`:
   ```yaml
   provider: openrouter
   ```
4. Use OpenRouter model names in agents:
   ```yaml
   model: anthropic/claude-3.5-sonnet  # or openai/gpt-4-turbo
   ```

See `backend/CLAUDE.md` for full provider configuration details.

## Testing

```bash
# Backend
cd backend && pytest tests/ -v

# Frontend (manual)
bun dev  # then test in browser
```
