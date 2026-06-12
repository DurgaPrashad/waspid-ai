// Import all event types
import {
  ACPToolCallEvent,
  ActionEvent,
  MessageEvent,
  ObservationEvent,
  UserRejectObservation,
  AgentErrorEvent,
  SystemPromptEvent,
  CondensationEvent,
  CondensationRequestEvent,
  CondensationSummaryEvent,
  ConversationStateUpdateEvent,
  ConversationErrorEvent,
  HookExecutionEvent,
  PauseEvent,
  ServerErrorEvent,
} from "./events/index";

/**
 * Union type representing all possible Waspid events.
 * This includes all main event types that can occur in the system.
 */
export type WaspidEvent =
  // Core action and observation events
  | ActionEvent
  | MessageEvent
  | ObservationEvent
  | UserRejectObservation
  | AgentErrorEvent
  | SystemPromptEvent
  // ACP sub-agent tool call events
  | ACPToolCallEvent
  // Hook events
  | HookExecutionEvent
  // Conversation management events
  | CondensationEvent
  | CondensationRequestEvent
  | CondensationSummaryEvent
  | ConversationStateUpdateEvent
  | ConversationErrorEvent
  // Control events
  | PauseEvent
  | ServerErrorEvent;
