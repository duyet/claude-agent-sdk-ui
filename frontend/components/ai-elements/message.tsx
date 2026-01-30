"use client"

import { cva, type VariantProps } from "class-variance-authority"
import * as React from "react"
import { cn } from "@/lib/utils"

const messageVariants = cva("group flex gap-3 py-2 px-2 sm:px-4", {
  variants: {
    role: {
      user: "justify-end",
      assistant: "justify-start",
      system: "justify-center",
    },
  },
  defaultVariants: {
    role: "assistant",
  },
})

interface MessageProps
  extends Omit<React.HTMLAttributes<HTMLDivElement>, "role">,
    VariantProps<typeof messageVariants> {
  children: React.ReactNode
}

const Message = React.forwardRef<HTMLDivElement, MessageProps>(
  ({ className, role, children, ...props }, ref) => (
    <div ref={ref} className={cn(messageVariants({ role }), className)} data-role={role} {...props}>
      {children}
    </div>
  ),
)
Message.displayName = "Message"

interface MessageContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

const MessageContent = React.forwardRef<HTMLDivElement, MessageContentProps>(
  ({ className, children, ...props }, ref) => (
    <div ref={ref} className={cn("min-w-0 flex-1 space-y-2", className)} {...props}>
      {children}
    </div>
  ),
)
MessageContent.displayName = "MessageContent"

interface MessageAvatarProps extends React.HTMLAttributes<HTMLDivElement> {
  children?: React.ReactNode
  fallback?: string
}

const MessageAvatar = React.forwardRef<HTMLDivElement, MessageAvatarProps>(
  ({ className, children, fallback, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("flex h-8 w-8 shrink-0 items-center justify-center rounded-full", className)}
      {...props}
    >
      {children || (
        <span className="text-xs font-medium">{fallback?.charAt(0).toUpperCase() || "?"}</span>
      )}
    </div>
  ),
)
MessageAvatar.displayName = "MessageAvatar"

interface MessageActionsProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

const MessageActions = React.forwardRef<HTMLDivElement, MessageActionsProps>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  ),
)
MessageActions.displayName = "MessageActions"

export { Message, MessageContent, MessageAvatar, MessageActions, messageVariants }
