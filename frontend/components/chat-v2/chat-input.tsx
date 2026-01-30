"use client"

import { useEffect, useRef, useState } from "react"
import {
  PromptInput,
  PromptInputSubmit,
  PromptInputTextarea,
} from "@/components/ai-elements/prompt-input"
import { QueuedMessagesIndicator } from "@/components/chat/queued-messages-indicator"
import { useMessageQueueStore } from "@/lib/store/message-queue-store"

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
  isStreaming?: boolean
  onStop?: () => void
}

/**
 * Chat input using AI Elements PromptInput components.
 * Features:
 * - Auto-resize textarea
 * - Shift+Enter for newlines
 * - Queue indicator for offline messages
 * - Stop button during streaming
 */
export function ChatInput({ onSend, disabled, isStreaming, onStop }: ChatInputProps) {
  const [message, setMessage] = useState("")
  const [queueLength, setQueueLength] = useState(0)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const getQueueLength = useMessageQueueStore(s => s.getQueueLength)

  // Update queue length periodically
  useEffect(() => {
    const updateQueueLength = () => {
      setQueueLength(getQueueLength())
    }

    updateQueueLength()
    const interval = setInterval(updateQueueLength, 1000)

    return () => clearInterval(interval)
  }, [getQueueLength])

  const handleSubmit = () => {
    if (message.trim() && !disabled) {
      onSend(message.trim())
      setMessage("")
    }
  }

  // Auto-focus on mount
  useEffect(() => {
    textareaRef.current?.focus()
  }, [])

  return (
    <div className="shrink-0">
      {/* Queue indicator */}
      {queueLength > 0 && (
        <div className="px-4 pb-2">
          <QueuedMessagesIndicator />
        </div>
      )}

      <PromptInput>
        <PromptInputTextarea
          ref={textareaRef}
          value={message}
          onChange={e => setMessage(e.target.value)}
          onSubmit={handleSubmit}
          placeholder={
            queueLength > 0 ? "Message will be queued until connected..." : "Message Claude..."
          }
          disabled={disabled}
        />
        <PromptInputSubmit
          onClick={handleSubmit}
          disabled={!message.trim() || disabled}
          isLoading={isStreaming}
          onStop={onStop}
        />
      </PromptInput>
    </div>
  )
}
