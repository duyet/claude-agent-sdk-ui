"use client"

import { ChevronDown, ExternalLink, FileText } from "lucide-react"
import * as React from "react"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { cn } from "@/lib/utils"

interface SourcesProps {
  children: React.ReactNode
  count?: number
  defaultOpen?: boolean
  className?: string
}

function Sources({ children, count, defaultOpen = false, className }: SourcesProps) {
  const [isOpen, setIsOpen] = React.useState(defaultOpen)

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen} className={className}>
      <CollapsibleTrigger className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors py-1">
        <FileText className="h-3.5 w-3.5" />
        <span className="font-medium">Sources</span>
        {count !== undefined && (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted">{count}</span>
        )}
        <ChevronDown className={cn("h-3.5 w-3.5 transition-transform", isOpen && "rotate-180")} />
      </CollapsibleTrigger>
      <CollapsibleContent className="pt-2">
        <div className="space-y-1">{children}</div>
      </CollapsibleContent>
    </Collapsible>
  )
}

interface SourceProps {
  title: string
  url?: string
  description?: string
  className?: string
}

function Source({ title, url, description, className }: SourceProps) {
  const content = (
    <div
      className={cn(
        "flex items-start gap-2 p-2 rounded-md text-sm hover:bg-muted/50 transition-colors",
        url && "cursor-pointer",
        className,
      )}
    >
      <FileText className="h-4 w-4 shrink-0 mt-0.5 text-muted-foreground" />
      <div className="min-w-0 flex-1">
        <div className="font-medium truncate">{title}</div>
        {description && (
          <div className="text-xs text-muted-foreground line-clamp-2">{description}</div>
        )}
      </div>
      {url && <ExternalLink className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />}
    </div>
  )

  if (url) {
    return (
      <a href={url} target="_blank" rel="noopener noreferrer">
        {content}
      </a>
    )
  }

  return content
}

export { Sources, Source }
