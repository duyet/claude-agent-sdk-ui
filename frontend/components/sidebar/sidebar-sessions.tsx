"use client"

import { Check, CheckSquare, ChevronDown, Loader2, Search, Trash2 } from "lucide-react"
import { useCallback, useMemo, useState } from "react"
import { Button } from "@/components/ui/button"
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuSkeleton,
} from "@/components/ui/sidebar"
import { useBatchDeleteSessions, useSessions } from "@/hooks/use-sessions"
import { useChatStore } from "@/lib/store/chat-store"
import { SidebarSessionItem } from "./sidebar-session-item"

const SESSIONS_PAGE_SIZE = 20

interface SidebarSessionsProps {
  searchQuery: string
  searchExpanded: boolean
  setSearchExpanded: (expanded: boolean) => void
  selectMode: boolean
  setSelectMode: (mode: boolean) => void
}

export function SidebarSessions({
  searchQuery,
  searchExpanded,
  setSearchExpanded,
  selectMode,
  setSelectMode,
}: SidebarSessionsProps) {
  const { data: sessions, isLoading } = useSessions()
  const sessionId = useChatStore(s => s.sessionId)
  const setSessionId = useChatStore(s => s.setSessionId)
  const setAgentId = useChatStore(s => s.setAgentId)
  const clearMessages = useChatStore(s => s.clearMessages)

  const [displayCount, setDisplayCount] = useState(SESSIONS_PAGE_SIZE)
  const [isLoadingMore, setIsLoadingMore] = useState(false)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const batchDelete = useBatchDeleteSessions()

  const { filteredSessions, totalCount, hasMore } = useMemo(() => {
    if (!sessions) return { filteredSessions: [], totalCount: 0, hasMore: false }

    let filtered = sessions

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(session => {
        const name = session.name || ""
        const firstMessage = session.first_message || ""
        return name.toLowerCase().includes(query) || firstMessage.toLowerCase().includes(query)
      })
    }

    const displayed = filtered.slice(0, displayCount)

    return {
      filteredSessions: displayed,
      totalCount: filtered.length,
      hasMore: filtered.length > displayCount,
    }
  }, [sessions, searchQuery, displayCount])

  const handleLoadMore = useCallback(() => {
    setIsLoadingMore(true)
    setTimeout(() => {
      setDisplayCount(prev => prev + SESSIONS_PAGE_SIZE)
      setIsLoadingMore(false)
    }, 150)
  }, [])

  const toggleSelect = (id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const handleSelectAll = useCallback(() => {
    if (filteredSessions.length === 0) return

    const allSelected = filteredSessions.every(session => selectedIds.has(session.session_id))

    if (allSelected) {
      setSelectedIds(prev => {
        const next = new Set(prev)
        filteredSessions.forEach(session => next.delete(session.session_id))
        return next
      })
    } else {
      setSelectedIds(prev => {
        const next = new Set(prev)
        filteredSessions.forEach(session => next.add(session.session_id))
        return next
      })
    }
  }, [filteredSessions, selectedIds])

  const handleBatchDelete = async () => {
    if (selectedIds.size === 0) return

    if (confirm(`Delete ${selectedIds.size} conversation${selectedIds.size > 1 ? "s" : ""}?`)) {
      try {
        await batchDelete.mutateAsync(Array.from(selectedIds))

        if (sessionId && selectedIds.has(sessionId)) {
          setSessionId(null)
          setAgentId(null)
          clearMessages()
        }

        setSelectMode(false)
      } catch (error) {
        console.error("Batch delete failed:", error)
      }
    }
  }

  return (
    <SidebarGroup className="group-data-[collapsible=icon]:hidden">
      <div className="flex items-center justify-between px-2">
        <SidebarGroupLabel>History</SidebarGroupLabel>
        {sessions && sessions.length > 0 && (
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              className="size-6"
              onClick={() => setSearchExpanded(!searchExpanded)}
              title="Search conversations"
            >
              <Search className={`size-3.5 ${searchExpanded ? "text-primary" : ""}`} />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="size-6"
              onClick={() => setSelectMode(!selectMode)}
              title={selectMode ? "Cancel selection" : "Select sessions"}
            >
              <CheckSquare className={`size-3.5 ${selectMode ? "text-primary" : ""}`} />
            </Button>
          </div>
        )}
      </div>

      {selectMode && filteredSessions.length > 0 && (
        <div className="flex items-center justify-between px-2 py-1.5">
          <div className="flex items-center gap-2">
            {selectedIds.size > 0 && (
              <Button
                variant="destructive"
                size="sm"
                className="h-6 px-2 text-xs"
                onClick={handleBatchDelete}
                disabled={batchDelete.isPending}
              >
                <Trash2 className="mr-1 size-3" />
                Delete
              </Button>
            )}
            <span className="text-xs text-muted-foreground">
              {selectedIds.size > 0
                ? `${selectedIds.size} of ${filteredSessions.length} selected`
                : `${filteredSessions.length} conversations`}
            </span>
          </div>
          <Button variant="ghost" size="sm" className="h-6 px-2 text-xs" onClick={handleSelectAll}>
            {filteredSessions.every(s => selectedIds.has(s.session_id)) ? (
              <>
                <Check className="mr-1 size-3" />
                Deselect
              </>
            ) : (
              <>
                <CheckSquare className="mr-1 size-3" />
                Select All
              </>
            )}
          </Button>
        </div>
      )}

      <SidebarGroupContent>
        <SidebarMenu>
          {isLoading ? (
            Array.from({ length: 8 }).map((_, i) => <SidebarMenuSkeleton key={i} showIcon />)
          ) : filteredSessions.length > 0 ? (
            <>
              {totalCount > SESSIONS_PAGE_SIZE && (
                <div className="px-2 pb-1 text-[10px] text-muted-foreground">
                  {filteredSessions.length}/{totalCount}
                </div>
              )}

              {filteredSessions.map(session => (
                <SidebarSessionItem
                  key={session.session_id}
                  session={session}
                  isActive={session.session_id === sessionId}
                  selectMode={selectMode}
                  isSelected={selectedIds.has(session.session_id)}
                  onToggleSelect={() => toggleSelect(session.session_id)}
                />
              ))}

              {hasMore && (
                <div className="pt-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-full text-[10px] text-muted-foreground hover:text-foreground"
                    onClick={handleLoadMore}
                    disabled={isLoadingMore}
                  >
                    {isLoadingMore ? (
                      <>
                        <Loader2 className="mr-1.5 size-3 animate-spin" />
                        Loading...
                      </>
                    ) : (
                      <>
                        <ChevronDown className="mr-1.5 size-3" />+
                        {totalCount - filteredSessions.length} more
                      </>
                    )}
                  </Button>
                </div>
              )}
            </>
          ) : (
            <div className="px-2 text-xs text-muted-foreground">
              {searchQuery ? "No matching conversations" : "No conversations yet"}
            </div>
          )}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  )
}
