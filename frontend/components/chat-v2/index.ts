/**
 * Chat v2 components using AI Elements
 *
 * This module provides a complete chat interface built with AI Elements components.
 * It maintains all the functionality of the original chat components while using
 * the new AI Elements primitives for consistency and improved UX.
 *
 * Key features:
 * - WebSocket integration with auto-reconnect
 * - Message virtualization for performance
 * - Special tool rendering (TodoWrite, PlanMode, AskUserQuestion)
 * - Error boundaries and graceful error handling
 * - Message queuing for offline support
 * - Cross-tab synchronization
 */

export { ChatContainer } from "./chat-container"
export { ChatHeader } from "./chat-header"
export { ChatInput } from "./chat-input"
export { MessageList } from "./message-list"
export {
  AskUserQuestionDisplay,
  EnterPlanModeDisplay,
  ExitPlanModeDisplay,
  TodoWriteDisplay,
} from "./special-tool-displays"
export { useChatMessages } from "./use-chat-messages"
export { WelcomeScreen } from "./welcome-screen"
