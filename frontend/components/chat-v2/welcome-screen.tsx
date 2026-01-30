"use client"

import { Bot } from "lucide-react"
import { useAgents } from "@/hooks/use-agents"
import { useChatStore } from "@/lib/store/chat-store"

/**
 * Minimal welcome screen when agent is selected but no messages yet.
 * Shows just the agent name to indicate readiness.
 */
export function WelcomeScreen() {
  const agentId = useChatStore(s => s.agentId)
  const { data: agents } = useAgents()
  const currentAgent = agents?.find(a => a.agent_id === agentId)

  return (
    <div className="flex h-full flex-col items-center justify-center px-4">
      <div className="animate-in fade-in slide-in-from-bottom-2 duration-300 text-center space-y-3">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
          <Bot className="h-6 w-6 text-primary" />
        </div>
        {currentAgent && (
          <>
            <h2 className="text-lg font-medium text-foreground">{currentAgent.name}</h2>
            {currentAgent.description && (
              <p className="text-sm text-muted-foreground max-w-md">{currentAgent.description}</p>
            )}
          </>
        )}
        <p className="text-xs text-muted-foreground pt-2">Type a message to start</p>
      </div>
    </div>
  )
}
