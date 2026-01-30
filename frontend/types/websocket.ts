// types/websocket.ts
export type EventType =
  | "session_id"
  | "text_delta"
  | "tool_use"
  | "tool_result"
  | "done"
  | "error"
  | "ready"
  | "ask_user_question"
  | "plan_approval"
  | "authenticated"

export interface WebSocketBaseEvent {
  type: EventType
}

export interface QuestionOption {
  label: string
  description: string
}

export interface Question {
  header: string
  question: string
  options: QuestionOption[]
  multiSelect: boolean
}

export interface AskUserQuestionEvent extends WebSocketBaseEvent {
  type: "ask_user_question"
  question_id: string
  questions: Question[]
  timeout: number
}

export interface PlanStep {
  description: string
  status?: "pending" | "in_progress" | "completed"
}

export interface PlanApprovalEvent extends WebSocketBaseEvent {
  type: "plan_approval"
  plan_id: string
  title: string
  summary: string
  steps: PlanStep[]
  timeout: number
}

export interface UserAnswerMessage {
  type: "user_answer"
  question_id: string
  answers: Record<string, string | string[]> // question text -> selected label(s)
}

export interface PlanApprovalMessage {
  type: "plan_approval_response"
  plan_id: string
  approved: boolean
  feedback?: string
}

export interface SessionIdEvent extends WebSocketBaseEvent {
  type: "session_id"
  session_id: string
}

export interface TextDeltaEvent extends WebSocketBaseEvent {
  type: "text_delta"
  text: string
}

export interface ToolUseEvent extends WebSocketBaseEvent {
  type: "tool_use"
  id: string
  name: string
  input: Record<string, unknown>
}

export interface ToolResultEvent extends WebSocketBaseEvent {
  type: "tool_result"
  tool_use_id: string
  content: string
  is_error?: boolean
}

export interface DoneEvent extends WebSocketBaseEvent {
  type: "done"
  turn_count: number
  total_cost_usd?: number
}

export enum WebSocketErrorCode {
  TOKEN_EXPIRED = "TOKEN_EXPIRED",
  TOKEN_INVALID = "TOKEN_INVALID",
  SESSION_NOT_FOUND = "SESSION_NOT_FOUND",
  RATE_LIMITED = "RATE_LIMITED",
  AGENT_NOT_FOUND = "AGENT_NOT_FOUND",
  UNKNOWN = "UNKNOWN",
}

export interface ErrorEvent extends WebSocketBaseEvent {
  type: "error"
  error: string
  code?: WebSocketErrorCode
}

export interface ReadyEvent extends WebSocketBaseEvent {
  type: "ready"
  session_id?: string
  resumed?: boolean
  turn_count?: number
}

export interface ClientMessage {
  content: string
}

export interface AuthMessage {
  type: "auth"
  token: string
}

export interface AuthenticatedEvent extends WebSocketBaseEvent {
  type: "authenticated"
}

export type WebSocketEvent =
  | SessionIdEvent
  | TextDeltaEvent
  | ToolUseEvent
  | ToolResultEvent
  | DoneEvent
  | ErrorEvent
  | ReadyEvent
  | AskUserQuestionEvent
  | PlanApprovalEvent
  | AuthenticatedEvent
