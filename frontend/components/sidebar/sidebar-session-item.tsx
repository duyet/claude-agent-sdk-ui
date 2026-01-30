"use client"

import { formatDistanceToNow } from "date-fns"
import { Check, MessageSquare, Trash2, X } from "lucide-react"
import { useRouter } from "next/navigation"
import { useEffect, useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { SidebarMenuAction, SidebarMenuButton, SidebarMenuItem } from "@/components/ui/sidebar"
import { useDeleteSession, useResumeSession, useUpdateSession } from "@/hooks/use-sessions"
import { apiClient } from "@/lib/api-client"
import { convertHistoryToChatMessages } from "@/lib/history-utils"
import { useChatStore } from "@/lib/store/chat-store"
import { useUIStore } from "@/lib/store/ui-store"
import { cn } from "@/lib/utils"
import type { SessionInfo } from "@/types"

interface SidebarSessionItemProps {
  session: SessionInfo
  isActive?: boolean
  selectMode?: boolean
  isSelected?: boolean
  onToggleSelect?: () => void
}

export function SidebarSessionItem({
  session,
  isActive,
  selectMode = false,
  isSelected = false,
  onToggleSelect,
}: SidebarSessionItemProps) {
  const router = useRouter()
  const currentSessionId = useChatStore(s => s.sessionId)
  const setSessionId = useChatStore(s => s.setSessionId)
  const setAgentId = useChatStore(s => s.setAgentId)
  const clearMessages = useChatStore(s => s.clearMessages)
  const setMessages = useChatStore(s => s.setMessages)
  const deleteSession = useDeleteSession()
  const resumeSession = useResumeSession()
  const updateSession = useUpdateSession()
  const _isMobile = useUIStore(s => s.isMobile)

  const [isDeleting, setIsDeleting] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [editName, setEditName] = useState("")
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [isEditing])

  const displayName = session.name || session.first_message || "New conversation"
  const relativeTime = formatDistanceToNow(new Date(session.created_at), { addSuffix: true })

  const handleClick = async () => {
    if (isLoading || isDeleting || selectMode || isEditing) return

    setIsLoading(true)

    try {
      router.push(`/s/${session.session_id}`)

      const historyData = await apiClient.getSessionHistory(session.session_id)
      const chatMessages = convertHistoryToChatMessages(historyData.messages)
      clearMessages()
      setMessages(chatMessages)
      setSessionId(session.session_id)

      if (session.agent_id) {
        setAgentId(session.agent_id)
      }

      try {
        await resumeSession.mutateAsync({ id: session.session_id })
      } catch (resumeError) {
        console.warn("Resume session API failed (non-blocking):", resumeError)
      }
    } catch (error) {
      console.error("Failed to load session:", error)
      setSessionId(session.session_id)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (isDeleting || isLoading) return

    if (confirm("Are you sure you want to delete this conversation?")) {
      setIsDeleting(true)
      try {
        await deleteSession.mutateAsync(session.session_id)

        if (currentSessionId === session.session_id) {
          setSessionId(null)
          setAgentId(null)
          clearMessages()
        }
      } catch (error) {
        console.error("Failed to delete session:", error)
        alert(
          `Failed to delete session: ${error instanceof Error ? error.message : "Unknown error"}`,
        )
      } finally {
        setIsDeleting(false)
      }
    }
  }

  const handleStartEdit = (e: React.MouseEvent) => {
    e.stopPropagation()
    setEditName(session.name || "")
    setIsEditing(true)
  }

  const handleCancelEditClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    setIsEditing(false)
    setEditName("")
  }

  const handleCancelEditKey = () => {
    setIsEditing(false)
    setEditName("")
  }

  const handleSaveEditClick = async (e: React.MouseEvent) => {
    e.stopPropagation()
    const newName = editName.trim() || null

    try {
      await updateSession.mutateAsync({ id: session.session_id, name: newName })
      setIsEditing(false)
    } catch (error) {
      console.error("Failed to update session name:", error)
    }
  }

  const handleSaveEditKey = async () => {
    const newName = editName.trim() || null

    try {
      await updateSession.mutateAsync({ id: session.session_id, name: newName })
      setIsEditing(false)
    } catch (error) {
      console.error("Failed to update session name:", error)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (isEditing) {
      e.stopPropagation()
      if (e.key === "Enter") {
        handleSaveEditKey()
      } else if (e.key === "Escape") {
        handleCancelEditKey()
      }
    }
  }

  if (isEditing) {
    return (
      <SidebarMenuItem>
        <div className="flex items-center gap-1 px-2" onClick={e => e.stopPropagation()}>
          <Input
            ref={inputRef}
            value={editName}
            onChange={e => setEditName(e.target.value)}
            placeholder="Session name"
            className="h-6 text-xs"
            onKeyDown={handleKeyDown}
          />
          <Button
            variant="ghost"
            size="icon"
            className="size-6 shrink-0"
            onClick={handleSaveEditClick}
            disabled={updateSession.isPending}
          >
            <Check className="size-3 text-green-600" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="size-6 shrink-0"
            onClick={handleCancelEditClick}
          >
            <X className="size-3 text-red-600" />
          </Button>
        </div>
      </SidebarMenuItem>
    )
  }

  return (
    <SidebarMenuItem>
      <SidebarMenuButton
        onClick={selectMode ? onToggleSelect : handleClick}
        onDoubleClick={!selectMode ? handleStartEdit : undefined}
        isActive={isActive && !selectMode}
        tooltip={displayName}
        className={cn(
          isSelected && selectMode && "bg-primary/10",
          (isDeleting || isLoading) && "opacity-50",
        )}
      >
        {selectMode ? (
          <Checkbox
            checked={isSelected}
            className="size-3.5 shrink-0"
            onClick={e => e.stopPropagation()}
          />
        ) : (
          <MessageSquare className="size-4 shrink-0" />
        )}
        <div className="flex min-w-0 flex-1 items-center gap-2">
          <span className="truncate text-sm">{displayName}</span>
          <span className="text-[10px] text-muted-foreground shrink-0 whitespace-nowrap">
            {relativeTime}
          </span>
        </div>
      </SidebarMenuButton>

      {!selectMode && (
        <SidebarMenuAction showOnHover onClick={handleDelete} title="Delete conversation">
          <Trash2 className="size-4" />
        </SidebarMenuAction>
      )}
    </SidebarMenuItem>
  )
}
