"use client"

import {
  AlertCircle,
  Check,
  CheckCircle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Circle,
  CircleDot,
  ClipboardList,
  Clock,
  Loader2,
  MessageSquare,
} from "lucide-react"
import { useEffect, useState } from "react"
import { NonCollapsibleToolCard, RunningIndicator } from "@/components/chat/tools"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { getToolColorStyles, getToolIcon } from "@/lib/tool-config"
import { cn, formatTime } from "@/lib/utils"
import type { ChatMessage } from "@/types"

/**
 * Special display for TodoWrite - always visible task list (no accordion)
 */
export function TodoWriteDisplay({
  message,
  isRunning,
}: {
  message: ChatMessage
  isRunning: boolean
}) {
  const ToolIcon = getToolIcon("TodoWrite")
  const colorStyles = getToolColorStyles("TodoWrite")

  const todos = message.toolInput?.todos as
    | Array<{
        content?: string
        subject?: string
        status?: string
        activeForm?: string
      }>
    | undefined

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="h-3.5 w-3.5 text-status-success" />
      case "in_progress":
        return <CircleDot className="h-3.5 w-3.5 text-status-info animate-pulse" />
      default:
        return <Circle className="h-3.5 w-3.5 text-status-warning animate-pulse" />
    }
  }

  const getStatusBadge = (status?: string) => {
    const statusText = status || "pending"
    const badgeClass = cn(
      "text-[10px] px-1.5 py-0.5 rounded shrink-0",
      status === "completed" &&
        "bg-status-success-bg text-status-success border border-status-success/20",
      status === "in_progress" &&
        "bg-status-info-bg text-status-info border border-status-info/20 animate-pulse",
      (!status || status === "pending") &&
        "bg-status-warning-bg text-status-warning-fg border border-status-warning/20 animate-pulse",
    )
    return <span className={badgeClass}>{statusText}</span>
  }

  const completedCount = todos?.filter(t => t.status === "completed").length || 0
  const totalCount = todos?.length || 0

  return (
    <NonCollapsibleToolCard
      toolName="TodoWrite"
      ToolIcon={ToolIcon}
      color={colorStyles.iconText?.color}
      isRunning={isRunning}
      timestamp={message.timestamp}
      ariaLabel={`Todo list with ${totalCount} tasks, ${completedCount} completed${isRunning ? ", currently updating" : ""}`}
      headerContent={
        <>
          {todos && todos.length > 0 && (
            <span className="text-[10px] text-muted-foreground" aria-hidden="true">
              {todos.length} {todos.length === 1 ? "task" : "tasks"}
            </span>
          )}
          {isRunning && (
            <span className="ml-auto">
              <RunningIndicator label="Running" />
            </span>
          )}
        </>
      }
    >
      <ul className="p-2 space-y-1 list-none" aria-label="Task list">
        {!todos || todos.length === 0 ? (
          <li className="text-[11px] text-muted-foreground italic px-2 py-1">No todos defined</li>
        ) : (
          todos.map((todo, idx) => {
            const isCompleted = todo.status === "completed"
            const isInProgress = todo.status === "in_progress"
            const taskName = todo.subject || todo.content || todo.activeForm || "Unnamed task"
            const statusText = isCompleted ? "completed" : isInProgress ? "in progress" : "pending"
            return (
              <li
                key={idx}
                className="flex items-center gap-2 text-[11px] px-2 py-1.5 rounded hover:bg-muted/30 transition-colors"
                aria-label={`Task ${idx + 1}: ${taskName}, status: ${statusText}`}
              >
                <div className="shrink-0" aria-hidden="true">
                  {getStatusIcon(todo.status)}
                </div>
                <div
                  className={cn(
                    "flex-1 min-w-0 truncate font-medium",
                    isCompleted && "line-through text-muted-foreground",
                  )}
                >
                  {taskName}
                </div>
                <span aria-hidden="true">{getStatusBadge(todo.status)}</span>
              </li>
            )
          })
        )}
      </ul>
    </NonCollapsibleToolCard>
  )
}

/**
 * Display for EnterPlanMode - shows that Claude is entering planning mode
 */
export function EnterPlanModeDisplay({
  message,
  isRunning,
}: {
  message: ChatMessage
  isRunning: boolean
}) {
  return (
    <NonCollapsibleToolCard
      toolName="Entering Plan Mode"
      ToolIcon={ClipboardList}
      color="hsl(var(--tool-plan))"
      isRunning={isRunning}
      timestamp={message.timestamp}
      ariaLabel={`Entering plan mode${isRunning ? ", analyzing task" : ""}`}
      headerContent={
        <>
          <span
            className="text-[10px] px-1.5 py-0.5 rounded border"
            style={{
              backgroundColor: "hsl(var(--tool-plan) / 0.1)",
              color: "hsl(var(--tool-plan))",
              borderColor: "hsl(var(--tool-plan) / 0.2)",
            }}
            aria-hidden="true"
          >
            Planning
          </span>
          {isRunning && (
            <span className="ml-auto">
              <RunningIndicator label="Analyzing" color="hsl(var(--tool-plan))" />
            </span>
          )}
        </>
      }
    >
      <div className="px-3 py-2">
        <p className="text-[11px] text-muted-foreground leading-relaxed">
          Claude is analyzing the task and will propose an implementation plan for your approval.
        </p>
      </div>
    </NonCollapsibleToolCard>
  )
}

/**
 * Display for ExitPlanMode - shows the plan ready for approval
 */
export function ExitPlanModeDisplay({
  message,
  isRunning,
}: {
  message: ChatMessage
  isRunning: boolean
}) {
  const input = message.toolInput || {}
  const launchSwarm = input.launchSwarm as boolean | undefined
  const teammateCount = input.teammateCount as number | undefined
  const allowedPrompts = input.allowedPrompts as Array<{ tool: string; prompt: string }> | undefined
  const pushToRemote = input.pushToRemote as boolean | undefined
  const remoteSessionTitle = input.remoteSessionTitle as string | undefined

  const permissionCount = allowedPrompts?.length || 0
  const hasDetails = launchSwarm || permissionCount > 0 || pushToRemote

  return (
    <NonCollapsibleToolCard
      toolName="ExitPlanMode"
      ToolIcon={CheckCircle}
      color="hsl(var(--tool-plan))"
      isRunning={isRunning}
      timestamp={message.timestamp}
      ariaLabel={`Plan mode completed${launchSwarm ? `, using ${teammateCount || "auto"} agents` : ""}${permissionCount > 0 ? `, ${permissionCount} permissions requested` : ""}`}
      headerContent={
        <>
          <span
            className="text-[10px] px-1.5 py-0.5 rounded border"
            style={{
              backgroundColor: "hsl(var(--progress-high) / 0.1)",
              color: "hsl(var(--progress-high))",
              borderColor: "hsl(var(--progress-high) / 0.2)",
            }}
            aria-hidden="true"
          >
            Plan Complete
          </span>
          {isRunning && (
            <span className="ml-auto">
              <RunningIndicator label="Processing" color="hsl(var(--tool-plan))" />
            </span>
          )}
        </>
      }
    >
      <div className="p-3 space-y-2">
        <p className="text-[11px] text-muted-foreground leading-relaxed">
          Planning phase has concluded.{" "}
          {hasDetails ? "Implementation details:" : "Ready to proceed with implementation."}
        </p>
        {hasDetails && (
          <div className="flex flex-wrap gap-2">
            {launchSwarm && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-status-info-bg text-status-info border border-status-info/20">
                Swarm: {teammateCount || "auto"} agents
              </span>
            )}
            {pushToRemote && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-500 border border-purple-500/20">
                Remote: {remoteSessionTitle || "Claude.ai"}
              </span>
            )}
            {allowedPrompts && allowedPrompts.length > 0 && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-status-warning-bg text-status-warning-fg border border-status-warning/20">
                {allowedPrompts.length} permission{allowedPrompts.length > 1 ? "s" : ""} requested
              </span>
            )}
          </div>
        )}
        {allowedPrompts && allowedPrompts.length > 0 && (
          <div className="space-y-1 pt-1">
            <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
              Requested Permissions
            </span>
            <div className="space-y-1">
              {allowedPrompts.map((perm, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2 text-[11px] text-muted-foreground"
                >
                  <AlertCircle className="h-3 w-3 text-status-warning" />
                  <span className="font-mono text-[10px] bg-muted/50 px-1 rounded">
                    {perm.tool}
                  </span>
                  <span>{perm.prompt}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </NonCollapsibleToolCard>
  )
}

/**
 * Display for AskUserQuestion - collapsible with tabbed questions and answer
 */
export function AskUserQuestionDisplay({
  message,
  isRunning,
  answer,
}: {
  message: ChatMessage
  isRunning: boolean
  answer?: string
}) {
  const [activeTab, setActiveTab] = useState(0)
  const [expanded, setExpanded] = useState(!answer)

  const rawQuestions = message.toolInput?.questions
  const questions = Array.isArray(rawQuestions)
    ? (rawQuestions as Array<{
        question: string
        header?: string
        options?: Array<{ label: string; description?: string }>
        multiSelect?: boolean
      }>)
    : undefined

  const parsedAnswers = answer ? parseAnswerContent(answer) : null
  const questionCount = questions?.length ?? 0
  const hasAnswer = !!parsedAnswers && Object.keys(parsedAnswers).length > 0

  useEffect(() => {
    if (hasAnswer) {
      setExpanded(false)
    }
  }, [hasAnswer])

  const getSummary = () => {
    if (hasAnswer && questions && questions.length > 0) {
      const firstQuestion = questions[0]
      const firstAnswer = parsedAnswers?.[firstQuestion.question]
      if (firstAnswer) {
        const answerText = Array.isArray(firstAnswer) ? firstAnswer.join(", ") : firstAnswer
        return answerText.length > 50 ? `${answerText.slice(0, 50)}...` : answerText
      }
    }
    if (questions && questions.length > 0) {
      const q = questions[0].question
      return q.length > 40 ? `${q.slice(0, 40)}...` : q
    }
    return null
  }

  const statusText = hasAnswer ? "answered" : "waiting for response"
  const detailsId = `question-details-${message.toolUseId || message.timestamp}`

  return (
    <div
      className="group flex gap-2 sm:gap-3 py-1.5 px-2 sm:px-4"
      role="article"
      aria-label={`User question with ${questionCount} ${questionCount === 1 ? "question" : "questions"}, status: ${statusText}`}
    >
      <div
        className={cn(
          "flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-border",
          isRunning && "animate-pulse",
        )}
        style={{ color: "hsl(var(--tool-question))" }}
        aria-hidden="true"
      >
        {isRunning ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
        ) : hasAnswer ? (
          <Check className="h-3.5 w-3.5" />
        ) : (
          <MessageSquare className="h-3.5 w-3.5" />
        )}
      </div>
      <div className="min-w-0 flex-1" aria-live="polite">
        <Card
          className="overflow-hidden rounded-lg shadow-sm w-full md:max-w-2xl bg-muted/30 border-l-2"
          style={{ borderLeftColor: "hsl(var(--tool-question))" }}
        >
          {/* Header - clickable to expand/collapse */}
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start rounded-none px-2 sm:px-3 py-2 text-xs hover:bg-muted/50 h-auto min-h-[40px] sm:min-h-[36px] border-b border-border/50"
            onClick={() => setExpanded(!expanded)}
            aria-expanded={expanded}
            aria-controls={detailsId}
          >
            <div className="flex items-center gap-2 w-full">
              {expanded ? (
                <ChevronDown className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
              ) : (
                <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
              )}
              <span className="font-medium text-foreground">AskUserQuestion</span>
              <span
                className="text-xs sm:text-[10px] px-1.5 py-0.5 rounded border"
                style={{
                  backgroundColor: hasAnswer
                    ? "hsl(var(--progress-high) / 0.1)"
                    : "hsl(var(--tool-question) / 0.1)",
                  color: hasAnswer ? "hsl(var(--progress-high))" : "hsl(var(--tool-question))",
                  borderColor: hasAnswer
                    ? "hsl(var(--progress-high) / 0.2)"
                    : "hsl(var(--tool-question) / 0.2)",
                }}
              >
                {hasAnswer ? "Answered" : "Waiting"}
              </span>
              {!expanded && getSummary() && (
                <>
                  <span className="text-muted-foreground/60">:</span>
                  <span className="text-muted-foreground/80 font-normal text-xs sm:text-[11px] truncate">
                    {getSummary()}
                  </span>
                </>
              )}
              <span className="ml-auto flex items-center gap-1.5 shrink-0" role="status">
                {hasAnswer ? (
                  <CheckCircle2 className="h-4 w-4 text-status-success" aria-label="Answered" />
                ) : (
                  <span className="flex items-center gap-1 text-status-warning">
                    <Clock className="h-4 w-4" aria-hidden="true" />
                    <span className="text-xs sm:text-[10px] font-medium">Waiting</span>
                  </span>
                )}
              </span>
            </div>
          </Button>

          {/* Expanded content */}
          <div
            className={cn(
              "grid transition-all duration-200 ease-out",
              expanded ? "grid-rows-[1fr]" : "grid-rows-[0fr]",
            )}
            id={detailsId}
          >
            <div className="overflow-hidden">
              {questionCount > 0 && (
                <div className="border-b-[3px] border-border bg-muted/20" role="tablist">
                  <div className="px-3 pt-2">
                    <div className="flex items-end gap-3">
                      <span className="text-xs sm:text-[10px] font-medium text-muted-foreground uppercase tracking-wider shrink-0 pb-1.5">
                        Questions
                      </span>
                      {questionCount > 1 ? (
                        <div className="flex gap-1">
                          {questions?.map((q, idx) => {
                            const isActive = activeTab === idx
                            const questionAnswer = parsedAnswers?.[q.question]
                            const isAnswered = !!questionAnswer
                            return (
                              <button
                                key={idx}
                                onClick={() => setActiveTab(idx)}
                                role="tab"
                                aria-selected={isActive}
                                className={cn(
                                  "flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium transition-colors whitespace-nowrap rounded-t-md -mb-[3px]",
                                  isActive
                                    ? "bg-background border-[3px] border-b-0 border-primary text-foreground"
                                    : "text-muted-foreground hover:text-foreground hover:bg-muted/50",
                                )}
                              >
                                {isAnswered ? (
                                  <Check className="h-3.5 w-3.5 text-status-success" />
                                ) : (
                                  <span className="w-5 h-5 rounded-full bg-muted border border-border flex items-center justify-center text-[10px] font-bold">
                                    {idx + 1}
                                  </span>
                                )}
                                <span className="max-w-[100px] truncate">
                                  {q.header || `Q${idx + 1}`}
                                </span>
                              </button>
                            )
                          })}
                        </div>
                      ) : (
                        <span className="text-xs sm:text-[10px] text-muted-foreground pb-1.5">
                          1 of 1
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Question content */}
              <div className="p-3 bg-background/50" role="tabpanel">
                {!questions || questions.length === 0 ? (
                  <div className="text-[11px] text-muted-foreground italic">
                    No questions defined
                  </div>
                ) : (
                  <QuestionContent
                    question={questions[activeTab]}
                    answer={parsedAnswers?.[questions[activeTab]?.question]}
                  />
                )}
              </div>
            </div>
          </div>
        </Card>
        <div className="mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <span className="text-xs sm:text-[11px] text-muted-foreground">
            {formatTime(message.timestamp)}
          </span>
        </div>
      </div>
    </div>
  )
}

function QuestionContent({
  question,
  answer,
}: {
  question: {
    question: string
    header?: string
    options?: Array<{ label: string; description?: string }>
    multiSelect?: boolean
  }
  answer?: string | string[]
}) {
  const answers = Array.isArray(answer) ? answer : answer ? [answer] : []

  return (
    <div className="space-y-2">
      <div>
        {question.header && (
          <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground mr-2">
            {question.header}:
          </span>
        )}
        <span className="text-xs text-foreground">{question.question}</span>
      </div>
      {question.options && question.options.length > 0 && (
        <div className="space-y-0.5 pl-1">
          {question.options.map((opt, oIdx) => {
            const isSelected =
              answers.includes(opt.label) || answers.some(a => a.includes(opt.label))
            return (
              <div
                key={oIdx}
                className={cn(
                  "flex items-center gap-2 text-[11px] px-2 py-1 rounded transition-colors",
                  isSelected
                    ? "bg-status-success-bg text-foreground"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {isSelected ? (
                  <Check className="h-3 w-3 text-status-success shrink-0" />
                ) : (
                  <span className="w-3 h-3 flex items-center justify-center text-[9px] font-medium text-muted-foreground/50 shrink-0">
                    {String.fromCharCode(65 + oIdx)}
                  </span>
                )}
                <span className={cn("truncate", isSelected && "font-medium")}>{opt.label}</span>
                {opt.description && (
                  <span className="text-[10px] text-muted-foreground/70 truncate hidden sm:inline">
                    - {opt.description}
                  </span>
                )}
              </div>
            )
          })}
        </div>
      )}
      {answers.length > 0 && (!question.options || question.options.length === 0) && (
        <div className="pt-2 border-t border-border/50">
          <div className="flex items-center gap-2 mb-2">
            <Check className="h-3 w-3 text-status-success" />
            <span className="text-[10px] font-medium text-status-success-fg uppercase tracking-wider">
              User&apos;s Answer
            </span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {answers.map((ans, idx) => (
              <span
                key={idx}
                className="text-[11px] px-2 py-1 rounded-md bg-status-success-bg text-status-success-fg border border-status-success/30 font-medium"
              >
                {ans}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function parseAnswerContent(content: string): Record<string, string | string[]> | null {
  try {
    const parsed = JSON.parse(content)
    if (typeof parsed === "object" && parsed !== null) {
      return parsed
    }
  } catch {
    const result: Record<string, string | string[]> = {}
    const selectMatch = content.match(/(?:selected|answer|chose|picked):\s*(.+)/i)
    if (selectMatch) {
      result["_answer"] = selectMatch[1].trim()
      return result
    }
    if (content.trim()) {
      result["_answer"] = content.trim()
      return result
    }
  }
  return null
}
