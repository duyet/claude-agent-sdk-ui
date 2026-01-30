"use client"

import { useCallback, useMemo } from "react"
import type { ChatMessage } from "@/types"

/**
 * Adapter hook to transform ChatMessage[] from store to AI Elements format.
 * Handles message grouping and tool result matching.
 */
export function useChatMessages(messages: ChatMessage[]) {
  // Filter out tool_result messages (they're rendered inline with tool_use)
  const renderableMessages = useMemo(() => {
    return messages.filter(m => m?.role && m.role !== "tool_result")
  }, [messages])

  // Helper to find the tool_result for a tool_use message
  const findToolResult = useCallback(
    (toolUseId: string, messageIndex: number): ChatMessage | undefined => {
      // First try direct ID match using the actual toolUseId from the tool_use message
      const toolUseMessage = renderableMessages[messageIndex]
      const actualToolUseId = toolUseMessage?.toolUseId || toolUseId

      const directMatch = messages.find(
        m => m.role === "tool_result" && m.toolUseId === actualToolUseId,
      )
      if (directMatch) {
        return directMatch
      }

      // Fallback: find the next tool_result after this message in the original array
      for (let i = 0; i < messages.length; i++) {
        const message = messages[i]
        if (message.id === toolUseId) {
          // Found the tool_use, now look for its result after it
          for (let j = i + 1; j < messages.length; j++) {
            if (messages[j].role === "tool_result") {
              return messages[j]
            }
            if (messages[j].role === "tool_use") {
              break // Hit another tool_use, stop looking
            }
          }
          break
        }
      }
      return undefined
    },
    [messages, renderableMessages],
  )

  // Find the last tool_use message index
  const lastToolUseIndex = useMemo(() => {
    for (let i = renderableMessages.length - 1; i >= 0; i--) {
      if (renderableMessages[i].role === "tool_use") {
        return i
      }
    }
    return -1
  }, [renderableMessages])

  return {
    renderableMessages,
    findToolResult,
    lastToolUseIndex,
  }
}
