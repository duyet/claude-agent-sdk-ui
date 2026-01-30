'use client';

import { Plus } from 'lucide-react';
import { useChatStore } from '@/lib/store/chat-store';
import {
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
} from '@/components/ui/sidebar';

export function SidebarNewSession() {
  const setSessionId = useChatStore((s) => s.setSessionId);
  const setAgentId = useChatStore((s) => s.setAgentId);
  const clearMessages = useChatStore((s) => s.clearMessages);

  const handleNewSession = () => {
    setSessionId(null);
    setAgentId(null);
    clearMessages();
  };

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <SidebarMenuButton onClick={handleNewSession} tooltip="Start a new conversation">
          <Plus className="size-4" />
          <span>New Chat</span>
        </SidebarMenuButton>
      </SidebarMenuItem>
    </SidebarMenu>
  );
}
