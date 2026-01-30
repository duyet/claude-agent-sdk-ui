'use client';

import { Search, X } from 'lucide-react';
import { SidebarInput } from '@/components/ui/sidebar';
import { Button } from '@/components/ui/button';

interface SidebarSearchProps {
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  expanded: boolean;
  setExpanded: (expanded: boolean) => void;
}

export function SidebarSearch({
  searchQuery,
  setSearchQuery,
  expanded,
  setExpanded,
}: SidebarSearchProps) {
  if (!expanded) {
    return null;
  }

  return (
    <div className="px-2 py-2">
      <div className="relative flex items-center gap-2">
        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <SidebarInput
          type="text"
          placeholder="Search conversations..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-9 pr-9"
          autoFocus
        />
        {searchQuery && (
          <Button
            variant="ghost"
            size="icon"
            className="absolute right-2 top-1/2 size-6 -translate-y-1/2"
            onClick={() => setSearchQuery('')}
          >
            <X className="size-3" />
          </Button>
        )}
      </div>
    </div>
  );
}
