"use client"

import { Bot } from "lucide-react"
import { memo, useCallback, useRef, useState } from "react"
import ReactMarkdown from "react-markdown"
import { Virtuoso, type VirtuosoHandle } from "react-virtuoso"
import { Loader } from "@/components/ai-elements/loader"
import { Message, MessageAvatar, MessageContent } from "@/components/ai-elements/message"
import { Tool, ToolInput, ToolResult } from "@/components/ai-elements/tool"
import { ScrollToBottomButton } from "@/components/chat/scroll-to-bottom-button"
import { ToolInputDisplay, ToolResultDisplay } from "@/components/chat/tools"
import { Skeleton } from "@/components/ui/skeleton"
import { useChatStore } from "@/lib/store/chat-store"
import { getToolColorStyles, getToolIcon, getToolSummary } from "@/lib/tool-config"
import { formatTime } from "@/lib/utils"
import type { ChatMessage } from "@/types"
import {
  AskUserQuestionDisplay,
  EnterPlanModeDisplay,
  ExitPlanModeDisplay,
  TodoWriteDisplay,
} from "./special-tool-displays"
import { useChatMessages } from "./use-chat-messages"

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
    </div>
  )
}

/**
 * User message component
 */
const UserMessageComponent = memo(({ message }: { message: ChatMessage }) => (
  <Message>
    <div className="flex flex-col gap-1 max-w-[80%] ml-auto">
      <div className="rounded-2xl bg-primary px-4 py-2.5 text-primary-foreground shadow-sm">
        <p className="text-sm whitespace-pre-wrap break-words">{message.content}</p>
      </div>
      <span className="text-xs text-muted-foreground text-right px-1">
        {formatTime(message.timestamp)}
      </span>
    </div>
  </Message>
))
UserMessageComponent.displayName = "UserMessage"

/**
 * Assistant message component
 */
const AssistantMessageComponent = memo(({ message }: { message: ChatMessage }) => (
  <Message>
    <MessageAvatar className="bg-primary/10 text-primary">
      <Bot className="h-4 w-4" />
    </MessageAvatar>
    <MessageContent>
      <div className="prose prose-sm max-w-none dark:prose-invert prose-p:leading-relaxed prose-pre:bg-muted prose-code:text-sm">
        <ReactMarkdown>{message.content}</ReactMarkdown>
      </div>
      <span className="text-xs text-muted-foreground">{formatTime(message.timestamp)}</span>
    </MessageContent>
  </Message>
))
AssistantMessageComponent.displayName = "AssistantMessage"

/**
 * Tool use message component
 */
interface ToolUseMessageProps {
  message: ChatMessage
  result?: ChatMessage
  isRunning: boolean
}

const ToolUseMessageComponent = memo(({ message, result, isRunning }: ToolUseMessageProps) => {
  const toolName = message.toolName || ""
  const ToolIcon = getToolIcon(toolName)
  const colorStyles = getToolColorStyles(toolName)
  const summary = getToolSummary(toolName, message.toolInput)
  const hasResult = !!result
  const isError = result?.isError

  // Determine status
  const status = isRunning ? "running" : hasResult ? (isError ? "error" : "completed") : "pending"

  // Special rendering for specific tools
  if (toolName === "TodoWrite") {
    return <TodoWriteDisplay message={message} isRunning={isRunning} />
  }

  if (toolName === "EnterPlanMode") {
    return <EnterPlanModeDisplay message={message} isRunning={isRunning} />
  }

  if (toolName === "ExitPlanMode") {
    return <ExitPlanModeDisplay message={message} isRunning={isRunning} />
  }

  if (toolName === "AskUserQuestion") {
    return (
      <AskUserQuestionDisplay message={message} isRunning={isRunning} answer={result?.content} />
    )
  }

  // Standard tool rendering
  if (!message.toolInput) return null

  return (
    <Tool
      name={toolName}
      icon={ToolIcon}
      iconColor={colorStyles.iconText?.color}
      status={status}
      summary={summary}
    >
      {/* Tool Input */}
      <ToolInput>
        <ToolInputDisplay toolName={toolName} input={message.toolInput} />
      </ToolInput>

      {/* Tool Result */}
      {hasResult && (
        <ToolResult isError={isError}>
          <ToolResultDisplay content={result.content} isError={isError} />
        </ToolResult>
      )}

      {/* Loading state */}
      {isRunning && !hasResult && (
        <div className="p-3 flex items-center gap-2">
          <Loader variant="dots" size="sm" />
          <span className="text-xs text-muted-foreground">Waiting for result...</span>
        </div>
      )}
    </Tool>
  )
})
ToolUseMessageComponent.displayName = "ToolUseMessage"

/**
 * Main message list component using AI Elements and Virtuoso
 */
export function MessageList() {
  const messages = useChatStore(s => s.messages)
  const isStreaming = useChatStore(s => s.isStreaming)
  const connectionStatus = useChatStore(s => s.connectionStatus)
  const virtuosoRef = useRef<VirtuosoHandle>(null)
  const [showScrollButton, setShowScrollButton] = useState(false)
  const [userScrolled, setUserScrolled] = useState(false)

  const { renderableMessages, findToolResult, lastToolUseIndex } = useChatMessages(messages)

  // Handle scroll state changes
  const handleAtBottomStateChange = useCallback((atBottom: boolean) => {
    setShowScrollButton(!atBottom)
    if (atBottom) {
      setUserScrolled(false)
    }
  }, [])

  // Handle user scroll
  const handleScroll = useCallback((isScrolling: boolean) => {
    if (isScrolling) {
      setUserScrolled(true)
    }
  }, [])

  // Scroll to bottom handler
  const scrollToBottom = useCallback(() => {
    if (virtuosoRef.current) {
      virtuosoRef.current.scrollToIndex({
        index: "LAST",
        behavior: "smooth" as const,
      })
      setUserScrolled(false)
    }
  }, [])

  // Item content renderer for Virtuoso
  const itemContent = useCallback(
    (index: number, message: ChatMessage | undefined) => {
      if (!message) return null

      switch (message.role) {
        case "user":
          return <UserMessageComponent key={message.id} message={message} />
        case "assistant":
          return <AssistantMessageComponent key={message.id} message={message} />
        case "tool_use": {
          const toolResult = findToolResult(message.id, index)
          const isToolRunning = isStreaming && index === lastToolUseIndex && !toolResult
          const componentKey = toolResult ? `${message.id}-${toolResult.id}` : message.id
          return (
            <ToolUseMessageComponent
              key={componentKey}
              message={message}
              result={toolResult}
              isRunning={isToolRunning}
            />
          )
        }
        default:
          return null
      }
    },
    [findToolResult, isStreaming, lastToolUseIndex],
  )

  // Show skeleton during initial load
  if (connectionStatus === "connecting" && renderableMessages.length === 0) {
    return (
      <div className="h-full overflow-y-auto">
        <MessageSkeleton />
      </div>
    )
  }

  return (
    <div className="relative h-full">
      <Virtuoso
        ref={virtuosoRef}
        style={{ height: "100%" }}
        data={renderableMessages}
        initialItemCount={Math.min(renderableMessages.length, 20)}
        overscan={200}
        atBottomStateChange={handleAtBottomStateChange}
        isScrolling={handleScroll}
        itemContent={itemContent}
        components={{
          Header: () => <div className="h-4" />,
          Footer: () => (
            <div className="px-2 sm:px-4 pb-4">
              {isStreaming && <Loader variant="dots" size="md" />}
            </div>
          ),
        }}
        followOutput={userScrolled ? false : ("smooth" as const)}
      />
      <ScrollToBottomButton isVisible={showScrollButton} onClick={scrollToBottom} />
    </div>
  )
}
