"use client"

import type * as React from "react"
import { cn } from "@/lib/utils"

interface LoaderProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "dots" | "pulse" | "spinner"
  size?: "sm" | "md" | "lg"
}

function Loader({ variant = "dots", size = "md", className, ...props }: LoaderProps) {
  const sizeClasses = {
    sm: "h-4",
    md: "h-6",
    lg: "h-8",
  }[size]

  const dotSizes = {
    sm: "w-1 h-1",
    md: "w-1.5 h-1.5",
    lg: "w-2 h-2",
  }[size]

  if (variant === "dots") {
    return (
      <div className={cn("flex items-center gap-1", sizeClasses, className)} {...props}>
        {[0, 1, 2].map(i => (
          <span
            key={i}
            className={cn("rounded-full bg-primary animate-bounce", dotSizes)}
            style={{
              animationDelay: `${i * 150}ms`,
              animationDuration: "1s",
            }}
          />
        ))}
      </div>
    )
  }

  if (variant === "pulse") {
    return (
      <div className={cn("flex items-center gap-2", sizeClasses, className)} {...props}>
        <span className="text-sm text-muted-foreground animate-pulse">Thinking...</span>
      </div>
    )
  }

  // spinner variant
  return (
    <div className={cn("flex items-center justify-center", sizeClasses, className)} {...props}>
      <div
        className={cn(
          "rounded-full border-2 border-primary border-t-transparent animate-spin",
          size === "sm" && "w-4 h-4",
          size === "md" && "w-6 h-6",
          size === "lg" && "w-8 h-8",
        )}
      />
    </div>
  )
}

export { Loader }
