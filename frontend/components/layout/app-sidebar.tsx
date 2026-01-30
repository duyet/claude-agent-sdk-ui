"use client"

import { useState } from "react"
import {
  SidebarAgentSwitcher,
  SidebarHelp,
  SidebarNewSession,
  SidebarSearch,
  SidebarSessions,
  SidebarSettings,
  SidebarUserNav,
} from "@/components/sidebar"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
  SidebarSeparator,
} from "@/components/ui/sidebar"

export function AppSidebar() {
  const [searchQuery, setSearchQuery] = useState("")
  const [searchExpanded, setSearchExpanded] = useState(false)
  const [selectMode, setSelectMode] = useState(false)

  return (
    <Sidebar collapsible="icon" variant="sidebar">
      <SidebarHeader>
        <SidebarAgentSwitcher />
        <SidebarNewSession />
      </SidebarHeader>

      <SidebarContent>
        <ScrollArea className="flex-1">
          <SidebarSearch
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            expanded={searchExpanded}
            setExpanded={setSearchExpanded}
          />
          <SidebarSessions
            searchQuery={searchQuery}
            searchExpanded={searchExpanded}
            setSearchExpanded={setSearchExpanded}
            selectMode={selectMode}
            setSelectMode={setSelectMode}
          />
        </ScrollArea>
      </SidebarContent>

      <SidebarFooter>
        <SidebarSeparator className="my-1" />
        <SidebarSettings />
        <SidebarHelp />
        <SidebarSeparator className="my-1" />
        <SidebarUserNav />
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  )
}
