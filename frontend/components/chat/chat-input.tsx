"use client"
import { Send } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { useMessageQueueStore } from "@/lib/store/message-queue-store"
import { QueuedMessagesIndicator } from "./queued-messages-indicator"

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
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

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  useEffect(() => {
    textareaRef.current?.focus()
  }, [])

  return (
    <div className="bg-background px-2 sm:px-4 py-3">
      <div className="mx-auto max-w-3xl">
        {/* Show queued messages indicator if there are queued messages */}
        {queueLength > 0 && (
          <div className="mb-2">
            <QueuedMessagesIndicator />
          </div>
        )}
        <div className="flex items-end gap-2 rounded-2xl border border-border bg-background p-2 shadow-sm">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={e => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              queueLength > 0 ? "Message will be queued until connected..." : "Message Claude..."
            }
            className="chat-textarea flex-1 min-h-[60px] max-h-[200px] resize-none bg-transparent px-3 py-2 text-base md:text-sm placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50"
            disabled={disabled}
          />
          <Button
            onClick={handleSubmit}
            disabled={!message.trim() || disabled}
            size="icon"
            className="h-10 w-10 shrink-0 rounded-xl bg-primary text-white hover:bg-primary-hover disabled:opacity-50"
          >
            <Send className="h-5 w-5" />
          </Button>
        </div>
      </div>
    </div>
  )
}
