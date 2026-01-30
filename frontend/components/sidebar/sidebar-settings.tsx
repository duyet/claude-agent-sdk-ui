'use client';

import { Sun, Moon, Laptop } from 'lucide-react';
import { useTheme } from 'next-themes';
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
} from '@/components/ui/sidebar';

export function SidebarSettings() {
  const { theme, setTheme } = useTheme();

  const themeOptions = [
    { value: 'light', label: 'Light', icon: Sun },
    { value: 'dark', label: 'Dark', icon: Moon },
    { value: 'system', label: 'System', icon: Laptop },
  ];

  return (
    <SidebarGroup className="group-data-[collapsible=icon]:hidden">
      <SidebarGroupLabel>Theme</SidebarGroupLabel>
      <SidebarGroupContent>
        <SidebarMenu>
          {themeOptions.map((option) => {
            const Icon = option.icon;
            return (
              <SidebarMenuItem key={option.value}>
                <SidebarMenuButton
                  onClick={() => setTheme(option.value)}
                  isActive={theme === option.value}
                  tooltip={`Switch to ${option.label} theme`}
                >
                  <Icon className="size-4" />
                  <span>{option.label}</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            );
          })}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  );
}
