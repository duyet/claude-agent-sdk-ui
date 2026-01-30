"use client"

import { Keyboard } from "lucide-react"
import { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"

export function SidebarHelp() {
  const [keyboardShortcutsOpen, setKeyboardShortcutsOpen] = useState(false)

  const shortcuts = [
    { key: "Cmd/Ctrl + B", description: "Toggle sidebar" },
    { key: "Cmd/Ctrl + K", description: "New conversation" },
    { key: "Cmd/Ctrl + /", description: "Show keyboard shortcuts" },
    { key: "Escape", description: "Cancel current action" },
  ]

  return (
    <>
      <SidebarGroup className="group-data-[collapsible=icon]:hidden">
        <SidebarGroupLabel>Help</SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton
                onClick={() => setKeyboardShortcutsOpen(true)}
                tooltip="View keyboard shortcuts"
              >
                <Keyboard className="size-4" />
                <span>Keyboard Shortcuts</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>

      <Dialog open={keyboardShortcutsOpen} onOpenChange={setKeyboardShortcutsOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Keyboard Shortcuts</DialogTitle>
            <DialogDescription>Use these keyboard shortcuts to navigate faster</DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            {shortcuts.map(shortcut => (
              <div key={shortcut.key} className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">{shortcut.description}</span>
                <kbd className="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground opacity-100">
                  {shortcut.key}
                </kbd>
              </div>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}
