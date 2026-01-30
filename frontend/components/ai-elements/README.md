# AI Elements - Compound Components

AI SDK-inspired UI components for WebSocket-based chat applications.

## Components

### Conversation

Container for chat conversations.

```tsx
import { Conversation, ConversationContent, ConversationEmptyState } from '@/components/ai-elements';

<Conversation>
  <ConversationContent>
    {messages.length === 0 ? (
      <ConversationEmptyState
        title="Start a conversation"
        description="Ask me anything!"
      />
    ) : (
      <MessageList messages={messages} />
    )}
  </ConversationContent>
</Conversation>
```

### Message

Display chat messages with role-based styling.

```tsx
import { Message, MessageContent, MessageAvatar, MessageActions } from '@/components/ai-elements';

<Message role="assistant">
  <MessageAvatar fallback="AI" />
  <MessageContent>
    <p>Hello! How can I help you?</p>
  </MessageContent>
  <MessageActions>
    <Button size="icon" variant="ghost"><Copy className="h-4 w-4" /></Button>
  </MessageActions>
</Message>
```

### PromptInput

Input area with textarea and submit button.

```tsx
import { PromptInput, PromptInputTextarea, PromptInputSubmit } from '@/components/ai-elements';

<PromptInput>
  <PromptInputTextarea
    value={input}
    onChange={(e) => setInput(e.target.value)}
    onSubmit={handleSubmit}
    placeholder="Type your message..."
  />
  <PromptInputSubmit
    isLoading={isLoading}
    onStop={handleStop}
    onClick={handleSubmit}
  />
</PromptInput>
```

### Tool

Display tool calls with collapsible details.

```tsx
import { Tool, ToolInput, ToolResult } from '@/components/ai-elements';
import { FileText } from 'lucide-react';

<Tool
  name="Read File"
  icon={FileText}
  status="completed"
  summary="README.md"
>
  <ToolInput>
    <code className="text-xs">{"{ file_path: 'README.md' }"}</code>
  </ToolInput>
  <ToolResult>
    <pre className="text-xs">File contents...</pre>
  </ToolResult>
</Tool>
```

### Reasoning

Collapsible thinking/reasoning section.

```tsx
import { Reasoning } from '@/components/ai-elements';

<Reasoning isStreaming={isStreaming}>
  <p>Let me analyze this step by step...</p>
</Reasoning>
```

### Sources

Display sources/citations.

```tsx
import { Sources, Source } from '@/components/ai-elements';

<Sources count={3}>
  <Source
    title="Documentation"
    url="https://example.com/docs"
    description="Official documentation"
  />
  <Source
    title="API Reference"
    url="https://example.com/api"
  />
</Sources>
```

### Loader

Streaming indicators.

```tsx
import { Loader } from '@/components/ai-elements';

<Loader variant="dots" size="md" />
<Loader variant="pulse" size="md" />
<Loader variant="spinner" size="md" />
```

## Design Principles

- **Compound Components**: Parent + children pattern for flexibility
- **Accessibility**: Proper ARIA attributes and semantic HTML
- **Responsive**: Mobile-first design with responsive classes
- **Themeable**: Uses Tailwind CSS with design tokens
- **Type-Safe**: Full TypeScript support with proper types

## Integration with WebSocket Chat

These components work with WebSocket-based chat (not AI SDK's useChat). Example integration:

```tsx
import { useChat } from '@/hooks/use-chat';
import { Message, MessageContent, MessageAvatar } from '@/components/ai-elements';

function ChatMessages() {
  const { messages } = useChat();

  return (
    <div className="space-y-4">
      {messages.map((message) => (
        <Message key={message.id} role={message.role}>
          <MessageAvatar fallback={message.role === 'user' ? 'U' : 'AI'} />
          <MessageContent>
            <p>{message.content}</p>
          </MessageContent>
        </Message>
      ))}
    </div>
  );
}
```

## Status Types

Tool component supports these status types:
- `pending` - Tool call queued
- `running` - Tool currently executing
- `completed` - Tool finished successfully
- `error` - Tool execution failed
