"use client"

import { ArrowRight, Bot, Send } from "lucide-react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useAgents } from "@/hooks/use-agents"
import { useChatStore } from "@/lib/store/chat-store"
import { cn } from "@/lib/utils"

export function AgentGrid() {
  const { data: agents, isLoading, error } = useAgents()
  const setAgentId = useChatStore(s => s.setAgentId)
  const setPendingMessage = useChatStore(s => s.setPendingMessage)
  const [message, setMessage] = useState("")
  const [hoveredAgent, setHoveredAgent] = useState<string | null>(null)

  const handleSendMessage = () => {
    if (!message.trim()) return

    // Find default agent or first available agent
    const defaultAgent = agents?.find(a => a.is_default) || agents?.[0]
    if (defaultAgent) {
      setPendingMessage(message.trim())
      setAgentId(defaultAgent.agent_id)
      setMessage("")
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleAgentClick = (agentId: string) => {
    setAgentId(agentId)
  }

  if (isLoading) {
    return (
      <div className="flex h-full flex-col items-center justify-center p-8">
        <Skeleton className="h-10 w-64 mb-4" />
        <Skeleton className="h-4 w-48 mb-8" />
        <div className="flex flex-wrap justify-center gap-2 max-w-xl">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-9 w-32 rounded-full" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <p className="text-destructive">Failed to load agents. Please try again.</p>
        </div>
      </div>
    )
  }

  const defaultAgent = agents?.find(a => a.is_default)
  const sortedAgents = agents
    ? [...(defaultAgent ? [defaultAgent] : []), ...agents.filter(a => !a.is_default)]
    : []

  return (
    <div className="flex h-full flex-col">
      {/* Centered welcome content */}
      <div className="flex flex-1 flex-col items-center justify-center px-4 pb-24">
        <div className="w-full max-w-2xl space-y-8">
          {/* Greeting */}
          <div className="text-center">
            <h1 className="text-2xl font-semibold text-foreground">What can I help you with?</h1>
          </div>

          {/* Agent pills */}
          <div className="flex flex-wrap justify-center gap-2">
            {sortedAgents.map(agent => (
              <button
                key={agent.agent_id}
                onClick={() => handleAgentClick(agent.agent_id)}
                onMouseEnter={() => setHoveredAgent(agent.agent_id)}
                onMouseLeave={() => setHoveredAgent(null)}
                className={cn(
                  "group flex items-center gap-2 rounded-full border px-4 py-2 text-sm transition-all",
                  "hover:border-primary hover:bg-primary/5",
                  agent.is_default && "border-primary/50 bg-primary/5",
                )}
              >
                <Bot className="size-4 text-muted-foreground group-hover:text-primary" />
                <span className="font-medium">{agent.name}</span>
                {agent.is_default && (
                  <span className="text-[10px] text-muted-foreground">default</span>
                )}
                <ArrowRight
                  className={cn(
                    "size-3.5 text-muted-foreground transition-all",
                    hoveredAgent === agent.agent_id
                      ? "opacity-100 translate-x-0"
                      : "opacity-0 -translate-x-1",
                  )}
                />
              </button>
            ))}
          </div>

          {/* Agent description tooltip */}
          {hoveredAgent && (
            <div className="text-center animate-in fade-in duration-150">
              <p className="text-sm text-muted-foreground">
                {agents?.find(a => a.agent_id === hoveredAgent)?.description}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Chat input */}
      <div className="sticky bottom-0 border-t bg-background px-4 py-3">
        <div className="mx-auto max-w-2xl">
          <div className="flex items-end gap-2 rounded-xl border bg-background p-2 shadow-sm focus-within:ring-1 focus-within:ring-ring">
            <textarea
              value={message}
              onChange={e => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Message Claude..."
              rows={1}
              className="flex-1 resize-none bg-transparent px-2 py-1.5 text-sm placeholder:text-muted-foreground focus:outline-none"
              style={{ minHeight: "36px", maxHeight: "200px" }}
              disabled={isLoading || !agents?.length}
            />
            <Button
              onClick={handleSendMessage}
              disabled={!message.trim() || isLoading || !agents?.length}
              size="icon"
              className="h-8 w-8 shrink-0 rounded-lg"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
          <p className="mt-2 text-center text-xs text-muted-foreground">
            Press Enter to send, Shift+Enter for new line
          </p>
        </div>
      </div>
    </div>
  )
}
