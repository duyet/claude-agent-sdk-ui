"use client"

import { Brain, ChevronDown } from "lucide-react"
import * as React from "react"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { cn } from "@/lib/utils"

interface ReasoningProps {
  children: React.ReactNode
  isStreaming?: boolean
  defaultOpen?: boolean
  className?: string
}

function Reasoning({ children, isStreaming = false, defaultOpen, className }: ReasoningProps) {
  const [isOpen, setIsOpen] = React.useState(defaultOpen ?? isStreaming)

  // Auto-open when streaming starts, auto-close when streaming ends
  React.useEffect(() => {
    if (isStreaming) {
      setIsOpen(true)
    }
  }, [isStreaming])

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen} className={className}>
      <CollapsibleTrigger className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors w-full py-1">
        <Brain className="h-3.5 w-3.5" />
        <span className="font-medium">Thinking</span>
        {isStreaming && (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-primary/10 text-primary animate-pulse">
            Active
          </span>
        )}
        <ChevronDown
          className={cn("h-3.5 w-3.5 ml-auto transition-transform", isOpen && "rotate-180")}
        />
      </CollapsibleTrigger>
      <CollapsibleContent className="pt-2">
        <div className="pl-5 border-l-2 border-muted text-sm text-muted-foreground">{children}</div>
      </CollapsibleContent>
    </Collapsible>
  )
}

export { Reasoning }
