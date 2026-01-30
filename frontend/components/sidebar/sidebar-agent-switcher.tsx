'use client';

import * as React from 'react';
import { ChevronsUpDown, Bot, Check } from 'lucide-react';
import { useAgents } from '@/hooks/use-agents';
import { useChatStore } from '@/lib/store/chat-store';
import type { AgentInfo } from '@/types';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSkeleton,
  useSidebar,
} from '@/components/ui/sidebar';

export function SidebarAgentSwitcher() {
  const { isMobile } = useSidebar();
  const { data: agents, isLoading } = useAgents();
  const agentId = useChatStore((s) => s.agentId);
  const setAgentId = useChatStore((s) => s.setAgentId);

  const activeAgent = React.useMemo(() => {
    if (!agents?.length) return null;
    return (
      agents.find((a: AgentInfo) => a.agent_id === agentId) ||
      agents.find((a: AgentInfo) => a.is_default) ||
      agents[0]
    );
  }, [agents, agentId]);

  if (isLoading) {
    return (
      <SidebarMenu>
        <SidebarMenuItem>
          <SidebarMenuSkeleton showIcon />
        </SidebarMenuItem>
      </SidebarMenu>
    );
  }

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton
              size="lg"
              className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
            >
              <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                <Bot className="size-4" />
              </div>
              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-medium">
                  {activeAgent?.name || 'Select Agent'}
                </span>
                <span className="truncate text-xs text-muted-foreground">
                  {activeAgent?.model}
                </span>
              </div>
              <ChevronsUpDown className="ml-auto" />
            </SidebarMenuButton>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className="w-[--radix-dropdown-menu-trigger-width] min-w-56 rounded-lg"
            align="start"
            side={isMobile ? 'bottom' : 'right'}
            sideOffset={4}
          >
            <DropdownMenuLabel className="text-xs text-muted-foreground">
              Agents
            </DropdownMenuLabel>
            {agents?.map((agent: AgentInfo) => (
              <DropdownMenuItem
                key={agent.agent_id}
                onClick={() => setAgentId(agent.agent_id)}
                className="gap-2 p-2"
              >
                <div className="flex size-6 items-center justify-center rounded-md border bg-background">
                  <Bot className="size-3.5 shrink-0" />
                </div>
                <div className="flex flex-1 flex-col gap-0.5 overflow-hidden">
                  <span className="truncate text-sm">{agent.name}</span>
                  <span className="truncate text-xs text-muted-foreground">
                    {agent.model}
                  </span>
                </div>
                {agent.agent_id === agentId && (
                  <Check className="size-4 text-primary" />
                )}
                {agent.is_default && (
                  <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">
                    default
                  </span>
                )}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  );
}
