import { WaspidParsedEvent } from ".";
import {
  UserMessageAction,
  AssistantMessageAction,
  WaspidAction,
  SystemMessageAction,
  CommandAction,
  FinishAction,
  TaskTrackingAction,
} from "./actions";
import {
  AgentStateChangeObservation,
  CommandObservation,
  ErrorObservation,
  MCPObservation,
  WaspidObservation,
  TaskTrackingObservation,
} from "./observations";
import { StatusUpdate } from "./variances";

export const isWaspidEvent = (
  event: unknown,
): event is WaspidParsedEvent =>
  typeof event === "object" &&
  event !== null &&
  "id" in event &&
  "source" in event &&
  "message" in event &&
  "timestamp" in event;

export const isWaspidAction = (
  event: WaspidParsedEvent,
): event is WaspidAction => "action" in event;

export const isWaspidObservation = (
  event: WaspidParsedEvent,
): event is WaspidObservation => "observation" in event;

export const isUserMessage = (
  event: WaspidParsedEvent,
): event is UserMessageAction =>
  isWaspidAction(event) &&
  event.source === "user" &&
  event.action === "message";

export const isAssistantMessage = (
  event: WaspidParsedEvent,
): event is AssistantMessageAction =>
  isWaspidAction(event) &&
  event.source === "agent" &&
  (event.action === "message" || event.action === "finish");

export const isErrorObservation = (
  event: WaspidParsedEvent,
): event is ErrorObservation =>
  isWaspidObservation(event) && event.observation === "error";

export const isCommandAction = (
  event: WaspidParsedEvent,
): event is CommandAction => isWaspidAction(event) && event.action === "run";

export const isAgentStateChangeObservation = (
  event: WaspidParsedEvent,
): event is AgentStateChangeObservation =>
  isWaspidObservation(event) && event.observation === "agent_state_changed";

export const isCommandObservation = (
  event: WaspidParsedEvent,
): event is CommandObservation =>
  isWaspidObservation(event) && event.observation === "run";

export const isFinishAction = (
  event: WaspidParsedEvent,
): event is FinishAction =>
  isWaspidAction(event) && event.action === "finish";

export const isSystemMessage = (
  event: WaspidParsedEvent,
): event is SystemMessageAction =>
  isWaspidAction(event) && event.action === "system";

export const isRejectObservation = (
  event: WaspidParsedEvent,
): event is WaspidObservation =>
  isWaspidObservation(event) && event.observation === "user_rejected";

export const isMcpObservation = (
  event: WaspidParsedEvent,
): event is MCPObservation =>
  isWaspidObservation(event) && event.observation === "mcp";

export const isTaskTrackingAction = (
  event: WaspidParsedEvent,
): event is TaskTrackingAction =>
  isWaspidAction(event) && event.action === "task_tracking";

export const isTaskTrackingObservation = (
  event: WaspidParsedEvent,
): event is TaskTrackingObservation =>
  isWaspidObservation(event) && event.observation === "task_tracking";

export const isStatusUpdate = (event: unknown): event is StatusUpdate =>
  typeof event === "object" &&
  event !== null &&
  "status_update" in event &&
  "type" in event &&
  "id" in event;

export const isActionOrObservation = (
  event: WaspidParsedEvent,
): event is WaspidAction | WaspidObservation =>
  isWaspidAction(event) || isWaspidObservation(event);
