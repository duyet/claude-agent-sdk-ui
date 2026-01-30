"use client"

import { SendHorizontal, Square } from "lucide-react"
import * as React from "react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface PromptInputProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

const PromptInput = React.forwardRef<HTMLDivElement, PromptInputProps>(
  ({ className, children, ...props }, ref) => (
    <div ref={ref} className={cn("border-t bg-background p-4", className)} {...props}>
      <div className="relative flex items-end gap-2 rounded-xl border bg-card p-2 shadow-sm">
        {children}
      </div>
    </div>
  ),
)
PromptInput.displayName = "PromptInput"

interface PromptInputTextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  onSubmit?: () => void
}

const PromptInputTextarea = React.forwardRef<HTMLTextAreaElement, PromptInputTextareaProps>(
  ({ className, onSubmit, onKeyDown, ...props }, ref) => {
    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault()
        onSubmit?.()
      }
      onKeyDown?.(e)
    }

    return (
      <textarea
        ref={ref}
        className={cn(
          "flex-1 resize-none bg-transparent text-sm placeholder:text-muted-foreground focus:outline-none min-h-[40px] max-h-[200px] py-2 px-2",
          className,
        )}
        onKeyDown={handleKeyDown}
        {...props}
      />
    )
  },
)
PromptInputTextarea.displayName = "PromptInputTextarea"

interface PromptInputSubmitProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  isLoading?: boolean
  onStop?: () => void
}

const PromptInputSubmit = React.forwardRef<HTMLButtonElement, PromptInputSubmitProps>(
  ({ className, isLoading, onStop, onClick, disabled, ...props }, ref) => (
    <Button
      ref={ref}
      type="button"
      size="icon"
      variant={isLoading ? "destructive" : "default"}
      className={cn("h-8 w-8 shrink-0", className)}
      disabled={disabled && !isLoading}
      onClick={isLoading ? onStop : onClick}
      {...props}
    >
      {isLoading ? <Square className="h-4 w-4" /> : <SendHorizontal className="h-4 w-4" />}
      <span className="sr-only">{isLoading ? "Stop" : "Send"}</span>
    </Button>
  ),
)
PromptInputSubmit.displayName = "PromptInputSubmit"

export { PromptInput, PromptInputTextarea, PromptInputSubmit }
