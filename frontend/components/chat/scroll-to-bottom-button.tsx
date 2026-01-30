"use client"

import { ArrowDown } from "lucide-react"
import { memo } from "react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface ScrollToBottomButtonProps {
  onClick: () => void
  isVisible: boolean
  className?: string
}

export const ScrollToBottomButton = memo(function ScrollToBottomButton({
  onClick,
  isVisible,
  className,
}: ScrollToBottomButtonProps) {
  if (!isVisible) return null

  return (
    <div
      className={cn(
        "absolute bottom-24 left-1/2 z-10 -translate-x-1/2 transition-all duration-200",
        "animate-in fade-in slide-in-from-bottom-2",
        className,
      )}
    >
      <Button
        onClick={onClick}
        size="sm"
        variant="default"
        className="shadow-lg"
        title="Scroll to bottom"
      >
        <ArrowDown className="h-4 w-4" />
      </Button>
    </div>
  )
})
