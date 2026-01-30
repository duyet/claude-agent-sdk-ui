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

## Testing

```bash
# Backend
cd backend && pytest tests/ -v

# Frontend (manual)
bun dev  # then test in browser
```
