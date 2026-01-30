"use client"

import { CheckCircle2, ChevronDown, Clock, Loader2, type LucideIcon, XCircle } from "lucide-react"
import * as React from "react"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { cn } from "@/lib/utils"

type ToolStatus = "pending" | "running" | "completed" | "error"

interface ToolProps {
  name: string
  icon?: LucideIcon
  iconColor?: string
  status?: ToolStatus
  summary?: string
  children?: React.ReactNode
  defaultOpen?: boolean
  className?: string
}

function Tool({
  name,
  icon: Icon,
  iconColor,
  status = "pending",
  summary,
  children,
  defaultOpen = false,
  className,
}: ToolProps) {
  const [isOpen, setIsOpen] = React.useState(defaultOpen)

  const StatusIcon = {
    pending: Clock,
    running: Loader2,
    completed: CheckCircle2,
    error: XCircle,
  }[status]

  const statusStyles = {
    pending: "text-muted-foreground",
    running: "text-primary animate-spin",
    completed: "text-status-success",
    error: "text-destructive",
  }[status]

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen} className={className}>
      <div className={cn("group flex gap-2 sm:gap-3 py-1.5 px-2 sm:px-4")}>
        <div
          className={cn(
            "flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-border",
            status === "running" && "animate-pulse",
          )}
          style={iconColor ? { color: iconColor } : undefined}
        >
          {Icon && <Icon className="h-3.5 w-3.5" />}
        </div>
        <div className="min-w-0 flex-1">
          <CollapsibleTrigger className="flex items-center gap-2 w-full text-left">
            <span className="font-medium text-sm">{name}</span>
            <StatusIcon className={cn("h-3.5 w-3.5", statusStyles)} />
            {summary && (
              <span className="text-xs text-muted-foreground truncate flex-1">{summary}</span>
            )}
            {children && (
              <ChevronDown
                className={cn(
                  "h-3.5 w-3.5 shrink-0 text-muted-foreground transition-transform",
                  isOpen && "rotate-180",
                )}
              />
            )}
          </CollapsibleTrigger>
          {children && (
            <CollapsibleContent className="pt-2">
              <div className="rounded-lg border bg-muted/30 overflow-hidden">{children}</div>
            </CollapsibleContent>
          )}
        </div>
      </div>
    </Collapsible>
  )
}

interface ToolHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

const ToolHeader = React.forwardRef<HTMLDivElement, ToolHeaderProps>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("px-3 py-2 border-b border-border/50 bg-muted/50", className)}
      {...props}
    >
      {children}
    </div>
  ),
)
ToolHeader.displayName = "ToolHeader"

interface ToolInputProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

const ToolInput = React.forwardRef<HTMLDivElement, ToolInputProps>(
  ({ className, children, ...props }, ref) => (
    <div ref={ref} className={cn("p-3 border-b border-border/30", className)} {...props}>
      <div className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider mb-1.5">
        Input
      </div>
      {children}
    </div>
  ),
)
ToolInput.displayName = "ToolInput"

interface ToolResultProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
  isError?: boolean
}

const ToolResult = React.forwardRef<HTMLDivElement, ToolResultProps>(
  ({ className, children, isError, ...props }, ref) => (
    <div ref={ref} className={cn("p-3", className)} {...props}>
      <div className="flex items-center gap-2 mb-1.5">
        <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
          Output
        </span>
        {isError && (
          <span className="text-[9px] px-1.5 py-0.5 rounded bg-destructive/10 text-destructive border border-destructive/20">
            Error
          </span>
        )}
      </div>
      {children}
    </div>
  ),
)
ToolResult.displayName = "ToolResult"

export { Tool, ToolHeader, ToolInput, ToolResult, type ToolStatus }
