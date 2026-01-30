"use client"

import { Moon, Plus, Radio, Sun } from "lucide-react"
import { useRouter } from "next/navigation"
import { useTheme } from "next-themes"
import { useEffect, useRef, useState } from "react"
import { AgentSwitcher } from "@/components/agent/agent-switcher"
import { StatusIndicator } from "@/components/chat/status-indicator"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { useChatStore } from "@/lib/store/chat-store"

/**
 * Chat header with SidebarTrigger, agent selector, and status indicator.
 * Uses shadcn SidebarTrigger for proper sidebar control.
 */
export function ChatHeader() {
  const router = useRouter()
  const agentId = useChatStore(s => s.agentId)
  const status = useChatStore(s => s.connectionStatus)
  const { theme, setTheme } = useTheme()
  const [isLeader, setIsLeader] = useState<boolean | null>(null)
  const cleanupRef = useRef<(() => void) | null>(null)

  // Check if this tab is the leader
  useEffect(() => {
    // Dynamic import to avoid SSR issues
    import("@/lib/broadcast-channel").then(({ getTabBroadcastChannel }) => {
      const channel = getTabBroadcastChannel()
      setIsLeader(channel.getIsLeader())

      cleanupRef.current = channel.onLeaderChange(leader => {
        setIsLeader(leader)
      })
    })

    return () => {
      cleanupRef.current?.()
    }
  }, [])

  return (
    <header className="flex h-10 items-center justify-between border-b bg-background px-2 sm:px-4 shrink-0">
      {/* Left: Sidebar toggle, agent selector, status */}
      <div className="flex items-center gap-2">
        <SidebarTrigger className="-ml-1" />

        {agentId && (
          <>
            <Separator orientation="vertical" className="h-4" />
            <AgentSwitcher />
            <Separator orientation="vertical" className="h-4" />
            <StatusIndicator status={status} />
          </>
        )}

        {/* Tab state indicator - only show when connected */}
        {agentId && isLeader !== null && (
          <>
            <Separator orientation="vertical" className="h-4" />
            <div
              className="flex items-center gap-1 text-xs text-muted-foreground"
              title={
                isLeader
                  ? "This tab is the leader (manages WebSocket connection)"
                  : "This tab is a follower (receives from leader)"
              }
            >
              <Radio
                className={`h-3 w-3 ${isLeader ? "text-green-500" : "text-muted-foreground"}`}
              />
              <span className="hidden sm:inline">{isLeader ? "Leader" : "Follower"}</span>
            </div>
          </>
        )}
      </div>

      {/* Right: Theme toggle and new chat */}
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 shrink-0"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
        >
          {theme === "dark" ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5" />}
        </Button>

        {agentId && (
          <Button
            onClick={() => {
              const store = useChatStore.getState()
              store.setAgentId(null)
              store.setSessionId(null)
              store.clearMessages()
              store.setConnectionStatus("disconnected")
              router.push("/")
            }}
            className="gap-2 h-7 px-3 bg-foreground hover:bg-foreground/90 text-background font-medium shadow-sm dark:shadow-none dark:border dark:border-border text-sm"
            aria-label="Start new chat"
          >
            <Plus className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">New Chat</span>
          </Button>
        )}
      </div>
    </header>
  )
}
