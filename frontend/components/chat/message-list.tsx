'use client';

import { useEffect, useRef, useState, useMemo, useCallback, memo } from 'react';
import { useChatStore } from '@/lib/store/chat-store';
import { UserMessage } from './user-message';
import { AssistantMessage } from './assistant-message';
import { ToolUseMessage } from './tool-use-message';
import { TypingIndicator } from './typing-indicator';
import { Skeleton } from '@/components/ui/skeleton';
import { WelcomeScreen } from './welcome-screen';
import { ScrollToBottomButton } from './scroll-to-bottom-button';
import type { ChatMessage } from '@/types';
import { Virtuoso, VirtuosoHandle } from 'react-virtuoso';

// Memoized message components to prevent unnecessary re-renders
const MemoizedUserMessage = memo(UserMessage);
const MemoizedAssistantMessage = memo(AssistantMessage);
const MemoizedToolUseMessage = memo(ToolUseMessage);

/**
 * Skeleton loading state for messages
 */
function MessageSkeleton() {
  return (
    <div className="px-2 sm:px-4 pb-4 pt-4 space-y-4 animate-in fade-in duration-300">
      {/* User message skeleton */}
      <div className="flex justify-end">
        <div className="max-w-[80%] space-y-2">
          <Skeleton className="h-4 w-48 ml-auto" />
          <Skeleton className="h-12 w-64 rounded-2xl" />
        </div>
      </div>

      {/* Assistant message skeleton */}
      <div className="flex gap-3">
        <Skeleton className="h-8 w-8 rounded-full shrink-0" />
        <div className="space-y-2 flex-1 max-w-[80%]">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-20 w-full rounded-xl" />
          <Skeleton className="h-4 w-3/4" />
        </div>
      </div>

      {/* Tool use skeleton */}
      <div className="flex gap-3">
        <Skeleton className="h-7 w-7 rounded-md shrink-0" />
        <div className="space-y-2 flex-1 max-w-2xl">
          <Skeleton className="h-9 w-full rounded-lg" />
        </div>
      </div>

      {/* Another assistant message skeleton */}
      <div className="flex gap-3">
        <Skeleton className="h-8 w-8 rounded-full shrink-0" />
        <div className="space-y-2 flex-1 max-w-[80%]">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-16 w-full rounded-xl" />
        </div>
      </div>
    </div>
  );
}

export function MessageList() {
  const messages = useChatStore((s) => s.messages);
  const isStreaming = useChatStore((s) => s.isStreaming);
  const connectionStatus = useChatStore((s) => s.connectionStatus);
  const virtuosoRef = useRef<VirtuosoHandle>(null);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const [userScrolled, setUserScrolled] = useState(false);

  // Filter out invalid messages and tool_result (rendered inline with tool_use)
  const renderableMessages = useMemo(() => {
    return messages.filter(m => m && m.role && m.role !== 'tool_result');
  }, [messages]);

  // Track initial load state - show skeleton briefly while hydrating
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsInitialLoad(false);
    }, 100);
    return () => clearTimeout(timer);
  }, []);

  // Auto-scroll to bottom when new messages arrive, but only if user hasn't scrolled up
  useEffect(() => {
    if (!userScrolled && virtuosoRef.current) {
      virtuosoRef.current.scrollToIndex({
        index: 'LAST',
        behavior: 'smooth' as const,
      });
    }
  }, [renderableMessages.length, userScrolled]);

  // Helper to find the tool_result for a tool_use message
  // NOTE: Must search original messages array since tool_results are filtered from renderableMessages
  const findToolResult = useCallback((toolUseId: string, messageIndex: number): ChatMessage | undefined => {
    // First try direct ID match using the actual toolUseId from the tool_use message
    const toolUseMessage = renderableMessages[messageIndex];
    const actualToolUseId = toolUseMessage?.toolUseId || toolUseId;

    const directMatch = messages.find(m => m.role === 'tool_result' && m.toolUseId === actualToolUseId);
    if (directMatch) {
      return directMatch;
    }

    // Fallback: find the next tool_result after this message in the original array
    for (let i = 0; i < messages.length; i++) {
      const message = messages[i];
      if (message.id === toolUseId) {
        // Found the tool_use, now look for its result after it
        for (let j = i + 1; j < messages.length; j++) {
          if (messages[j].role === 'tool_result') {
            return messages[j];
          }
          if (messages[j].role === 'tool_use') {
            break; // Hit another tool_use, stop looking
          }
        }
        break;
      }
    }
    return undefined;
  }, [messages, renderableMessages]);

  // Find the last tool_use message index
  // NOTE: Must be defined before any early returns to follow Rules of Hooks
  const lastToolUseIndex = useMemo(() => {
    for (let i = renderableMessages.length - 1; i >= 0; i--) {
      if (renderableMessages[i].role === 'tool_use') {
        return i;
      }
    }
    return -1;
  }, [renderableMessages]);

  // Handle scroll state changes
  const handleAtBottomStateChange = useCallback((atBottom: boolean) => {
    setShowScrollButton(!atBottom);
    if (atBottom) {
      setUserScrolled(false);
    }
  }, []);

  // Handle user scroll - Virtuoso passes a boolean indicating if scrolling is active
  const handleScroll = useCallback((isScrolling: boolean) => {
    // If user is scrolling (not auto-scrolling), mark as user scrolled
    if (isScrolling) {
      setUserScrolled(true);
    }
  }, []);

  // Scroll to bottom handler
  const scrollToBottom = useCallback(() => {
    if (virtuosoRef.current) {
      virtuosoRef.current.scrollToIndex({
        index: 'LAST',
        behavior: 'smooth' as const,
      });
      setUserScrolled(false);
    }
  }, []);

  // Item content renderer for Virtuoso
  const itemContent = useCallback((index: number, message: ChatMessage) => {
    switch (message.role) {
      case 'user':
        return <MemoizedUserMessage key={message.id} message={message} />;
      case 'assistant':
        return <MemoizedAssistantMessage key={message.id} message={message} />;
      case 'tool_use': {
        // Find the corresponding tool_result for this tool_use
        const toolResult = findToolResult(message.id, index);
        // Determine if this tool is currently running:
        // - It's the last tool_use message
        // - The stream is still active
        // - No result has arrived yet
        const isToolRunning = isStreaming && index === lastToolUseIndex && !toolResult;
        // Include result id in key to force re-render when result arrives
        const componentKey = toolResult ? `${message.id}-${toolResult.id}` : message.id;
        return (
          <MemoizedToolUseMessage
            key={componentKey}
            message={message}
            result={toolResult}
            isRunning={isToolRunning}
          />
        );
      }
      default:
        return null;
    }
  }, [findToolResult, isStreaming, lastToolUseIndex]);

  // Show skeleton during initial load when reconnecting to existing session
  if (isInitialLoad && connectionStatus === 'connecting') {
    return (
      <div className="h-full overflow-y-auto">
        <MessageSkeleton />
      </div>
    );
  }

  if (renderableMessages.length === 0) {
    return <WelcomeScreen />;
  }

  return (
    <div className="relative h-full">
      <Virtuoso
        ref={virtuosoRef}
        style={{ height: '100%' }}
        data={renderableMessages}
        initialItemCount={50}
        overscan={200}
        atBottomStateChange={handleAtBottomStateChange}
        isScrolling={handleScroll}
        itemContent={itemContent}
        components={{
          // Empty header to maintain consistent padding
          Header: () => <div className="h-4" />,
          // Footer with typing indicator
          Footer: () => (
            <div className="px-2 sm:px-4 pb-4">
              {isStreaming && <TypingIndicator />}
            </div>
          ),
        }}
        // Custom scroll behavior
        followOutput={
          userScrolled
            ? false
            : ('smooth' as const)
        }
      />
      <ScrollToBottomButton
        isVisible={showScrollButton}
        onClick={scrollToBottom}
      />
    </div>
  );
}
