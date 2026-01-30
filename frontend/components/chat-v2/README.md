# Chat V2 Components

AI Elements-based chat interface for the Claude Agent SDK. This is a complete rewrite of the chat UI using AI Elements primitives while maintaining all existing functionality.

## Overview

Chat V2 provides a production-ready chat interface with:

- **AI Elements Integration**: Built with `@/components/ai-elements` for consistent UX
- **WebSocket Communication**: Real-time streaming with auto-reconnect
- **Message Virtualization**: Performant rendering via `react-virtuoso`
- **Special Tool Support**: Custom renderers for TodoWrite, PlanMode, AskUserQuestion
- **Error Handling**: Error boundaries and graceful degradation
- **Offline Support**: Message queuing when disconnected
- **Cross-Tab Sync**: Shared state across browser tabs

## Components

### ChatContainer

Main container component that orchestrates the entire chat experience.

```tsx
import { ChatContainer } from '@/components/chat-v2';

export default function ChatPage() {
  return <ChatContainer />;
}
```

**Features:**
- Error boundary for graceful error handling
- Connection status banner for reconnection states
- History loading with retry logic
- Modal integration (QuestionModal, PlanApprovalModal)
- WebSocket lifecycle management

### ChatHeader

Header bar with sidebar toggle, agent selector, and status indicators.

**Features:**
- Sidebar toggle button
- Agent switcher dropdown
- Connection status indicator
- Tab leader/follower indicator
- Theme toggle
- New chat button

**Uses:**
- `SidebarTrigger` pattern with PanelLeft/PanelRight icons
- `Separator` components for visual division
- `StatusIndicator` for connection state

### MessageList

Virtualized message list using AI Elements Message components.

**Features:**
- Virtuoso for performance with large message lists
- Automatic scroll-to-bottom behavior
- User scroll detection
- Skeleton loading states
- Special tool displays

**Uses:**
- `Message`, `MessageContent`, `MessageAvatar` from AI Elements
- `Tool`, `ToolInput`, `ToolResult` from AI Elements
- `Loader` for streaming indicator
- `ScrollToBottomButton` for UX

### ChatInput

Input component using AI Elements PromptInput primitives.

**Features:**
- Auto-resize textarea
- Shift+Enter for newlines
- Queue indicator for offline messages
- Stop button during streaming
- Auto-focus on mount

**Uses:**
- `PromptInput`, `PromptInputTextarea`, `PromptInputSubmit` from AI Elements
- `QueuedMessagesIndicator` for offline support

### WelcomeScreen

Empty state display when no messages exist.

**Features:**
- Gradient background
- Fade-in animation
- Sparkles icon

**Uses:**
- `ConversationEmptyState` from AI Elements

### Special Tool Displays

Custom renderers for special tool types that don't follow standard tool patterns.

#### TodoWriteDisplay
- Always visible (non-collapsible)
- Task list with status icons
- Progress indicator
- Running state animation

#### EnterPlanModeDisplay
- Planning mode indicator
- Non-collapsible
- Analysis state

#### ExitPlanModeDisplay
- Plan completion summary
- Swarm configuration display
- Permission requests
- Remote session info

#### AskUserQuestionDisplay
- Collapsible question card
- Tabbed multi-question interface
- Answer highlighting
- Option selection display

## Hooks

### useChatMessages

Adapter hook that transforms ChatMessage[] to AI Elements format.

```tsx
const { renderableMessages, findToolResult, lastToolUseIndex } = useChatMessages(messages);
```

**Returns:**
- `renderableMessages`: Filtered messages (excludes tool_result)
- `findToolResult`: Helper to find tool result for a tool_use message
- `lastToolUseIndex`: Index of last tool_use (for running state detection)

## Message Flow

1. **User Input**: ChatInput captures user message
2. **WebSocket**: useChat hook sends message via WebSocket
3. **Streaming**: Text deltas arrive and update last assistant message
4. **Tool Calls**: tool_use events create tool messages
5. **Tool Results**: tool_result events are matched to tool_use messages
6. **Rendering**: MessageList virtualizes and renders all messages

## Tool Rendering Logic

### Standard Tools
- Use AI Elements `Tool` component
- Collapsible with summary
- Display input and result
- Status indicator (pending/running/completed/error)

### Special Tools
- TodoWrite: Task list, always visible
- EnterPlanMode: Planning indicator
- ExitPlanMode: Plan summary
- AskUserQuestion: Multi-question interface with tabs

## Error Handling

### Error Boundary
Wraps ChatContainerInner to catch rendering errors:
- Displays user-friendly error message
- Retry button
- Development-only stack trace
- Reload page option

### Connection Errors
- Banner for reconnecting states
- Manual reconnect button
- Retry counter display
- Auto-recovery from session_not_found

### History Load Errors
- Inline error notification
- Retry with exponential backoff
- Max retry limit (3 attempts)
- User-friendly error messages

## State Management

### Chat Store (Zustand)
- `messages`: ChatMessage[]
- `sessionId`: Current session ID
- `agentId`: Selected agent ID
- `isStreaming`: Streaming state
- `connectionStatus`: WebSocket status
- `pendingMessage`: Message to send on connect

### UI Store
- `sidebarOpen`: Sidebar visibility

### Message Queue Store
- Queue messages when offline
- Auto-send when reconnected

## Performance Optimizations

1. **Virtualization**: Only render visible messages
2. **Memoization**: Memo user/assistant/tool components
3. **Selective Re-renders**: Use getState() to avoid closures
4. **Debounced Scroll**: Smooth scroll with user override
5. **Lazy Loading**: Dynamic imports for broadcast channel

## Accessibility

- ARIA labels on all interactive elements
- Role attributes for semantic structure
- Keyboard navigation support
- Screen reader announcements for status changes
- Focus management (auto-focus input)

## Styling

- Uses Tailwind CSS with design system tokens
- Responsive breakpoints (sm, md)
- Dark mode support
- Terracotta theme colors
- Consistent spacing and typography

## Migration from Chat V1

To migrate from the original chat components:

```tsx
// Before
import { ChatContainer } from '@/components/chat';

// After
import { ChatContainer } from '@/components/chat-v2';
```

All functionality is preserved:
- WebSocket integration
- Special tool rendering
- Error handling
- Offline support
- Session management

The only difference is the use of AI Elements primitives for improved consistency and UX.

## Development

### Adding a New Special Tool

1. Create display function in `special-tool-displays.tsx`:
```tsx
export function MyToolDisplay({ message, isRunning }: { message: ChatMessage; isRunning: boolean }) {
  return (
    <NonCollapsibleToolCard
      toolName="MyTool"
      ToolIcon={MyIcon}
      color="hsl(var(--tool-mytool))"
      isRunning={isRunning}
      timestamp={message.timestamp}
    >
      {/* Custom content */}
    </NonCollapsibleToolCard>
  );
}
```

2. Add case in `message-list.tsx` ToolUseMessageComponent:
```tsx
if (toolName === 'MyTool') {
  return <MyToolDisplay message={message} isRunning={isRunning} />;
}
```

3. Export from `special-tool-displays.tsx` and `index.ts`

### Testing

```bash
# Type checking
npx tsc --noEmit

# Linting
npm run lint

# Build
npm run build
```

## Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions
- Mobile: iOS Safari 14+, Chrome Android

## Dependencies

- React 19
- Next.js 16
- Zustand (state management)
- react-virtuoso (virtualization)
- Tailwind CSS (styling)
- Lucide React (icons)
- AI Elements (UI primitives)

## License

Part of Claude Agent SDK - see project root for license details.
