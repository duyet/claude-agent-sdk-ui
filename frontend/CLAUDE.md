# Frontend CLAUDE.md

Next.js 15 frontend for Claude Agent SDK Chat.

## Commands

```bash
cd frontend
bun install                          # Install dependencies
bun dev                              # Dev server (port 7002)
bun run build                        # Production build
bun run tsc --noEmit                 # Type check
bunx biome check .                   # Lint + format
bunx shadcn@latest add <component>   # Add shadcn component
```

## Structure

```
frontend/
├── app/
│   ├── page.tsx                # Main chat page
│   ├── layout.tsx              # Root layout with providers
│   ├── (auth)/login/           # Login page
│   ├── s/[sessionId]/          # Session URL route
│   └── api/
│       ├── auth/               # Auth routes (login, logout, token, refresh)
│       └── proxy/[...path]/    # Backend API proxy
├── components/
│   ├── chat/                   # Chat components
│   │   ├── chat-container.tsx  # Main chat wrapper
│   │   ├── chat-header.tsx     # Header with title, stats, status
│   │   ├── chat-input.tsx      # Message input
│   │   ├── message-list.tsx    # Message display
│   │   ├── session-title.tsx   # Editable title
│   │   └── status-indicator.tsx # Connection status
│   ├── sidebar/                # Sidebar navigation
│   │   ├── sidebar-sessions.tsx    # Session list
│   │   ├── sidebar-agent-switcher.tsx
│   │   └── sidebar-settings.tsx    # Theme toggle
│   ├── layout/                 # Layout components
│   │   ├── app-sidebar.tsx     # Main sidebar
│   │   └── dashboard-layout.tsx
│   ├── ui/                     # shadcn/ui primitives
│   └── providers/              # Context providers
├── hooks/
│   ├── use-chat.ts             # Chat logic + WebSocket events
│   ├── use-websocket.ts        # WebSocket connection
│   ├── use-sessions.ts         # Session queries/mutations
│   └── use-agents.ts           # Agent queries
├── lib/
│   ├── store/
│   │   ├── chat-store.ts       # Messages, session, stats
│   │   ├── ui-store.ts         # Sidebar, theme
│   │   ├── question-store.ts   # User question modal
│   │   └── plan-store.ts       # Plan approval modal
│   ├── websocket-manager.ts    # WebSocket with token refresh
│   ├── broadcast-channel.ts    # Multi-tab sync
│   └── api-client.ts           # REST API client
└── types/
    ├── index.ts                # Core types
    └── websocket.ts            # WebSocket event types
```

## Key Patterns

### Zustand Stores

```typescript
// Access state reactively
const sessionId = useChatStore((s) => s.sessionId)

// Access state imperatively (avoid closure staleness)
const currentMessages = useChatStore.getState().messages
```

**Stores:**
- `chat-store` - messages, sessionId, agentId, connectionStatus, sessionStats
- `ui-store` - sidebarOpen, theme, isMobile
- `question-store` - question modal state
- `plan-store` - plan approval modal state

### WebSocket Events in use-chat.ts

```typescript
case 'ready':
  setConnectionStatus('connected')
  setSessionId(event.session_id)
  break

case 'text_delta':
  // Create or update assistant message
  break

case 'done':
  setStreaming(false)
  // Update sessionStats with cost/turn_count
  break
```

### Message Types

```typescript
interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'tool_use' | 'tool_result'
  content: string
  timestamp: Date
  toolName?: string      // for tool_use
  toolInput?: object     // for tool_use
  toolUseId?: string     // for tool_result
  isError?: boolean      // for tool_result
}
```

### Session Stats

```typescript
interface SessionStats {
  totalCost: number      // Cumulative USD cost
  turnCount: number      // Total turns
  startTime: Date | null // Session start
}
```

Stats displayed in header: `5 turns · $0.02 · 12m`

## Component Guidelines

- Use `'use client'` for client components
- UI primitives in `components/ui/`
- Feature components in `components/{feature}/`
- Always invalidate queries after mutations:
  ```typescript
  queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.SESSIONS] })
  ```

## API Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/api/auth/login` | POST | Login, set cookie |
| `/api/auth/logout` | POST | Clear cookie |
| `/api/auth/token` | GET | Get current JWT |
| `/api/auth/refresh` | POST | Refresh JWT |
| `/api/proxy/[...path]` | * | Proxy to backend |

## Adding New Features

### New WebSocket Event
1. Add type to `types/websocket.ts`
2. Add handler in `hooks/use-chat.ts` switch
3. Update store if needed

### New UI Component
1. Add to appropriate `components/` folder
2. Export from `index.ts`
3. Use shadcn primitives from `components/ui/`

### New Store
1. Create in `lib/store/`
2. Use Zustand with persist if needed
3. Export from store file
