"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

interface ConversationProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

const Conversation = React.forwardRef<HTMLDivElement, ConversationProps>(
  ({ className, children, ...props }, ref) => (
    <div ref={ref} className={cn("flex flex-col h-full", className)} {...props}>
      {children}
    </div>
  ),
)
Conversation.displayName = "Conversation"

interface ConversationContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

const ConversationContent = React.forwardRef<HTMLDivElement, ConversationContentProps>(
  ({ className, children, ...props }, ref) => (
    <div ref={ref} className={cn("flex-1 overflow-hidden", className)} {...props}>
      {children}
    </div>
  ),
)
ConversationContent.displayName = "ConversationContent"

interface ConversationEmptyStateProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string
  description?: string
  children?: React.ReactNode
}

const ConversationEmptyState = React.forwardRef<HTMLDivElement, ConversationEmptyStateProps>(
  ({ className, title = "Start a conversation", description, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("flex flex-col items-center justify-center h-full p-8 text-center", className)}
      {...props}
    >
      <h2 className="text-xl font-semibold mb-2">{title}</h2>
      {description && <p className="text-muted-foreground text-sm mb-6">{description}</p>}
      {children}
    </div>
  ),
)
ConversationEmptyState.displayName = "ConversationEmptyState"

export { Conversation, ConversationContent, ConversationEmptyState }
