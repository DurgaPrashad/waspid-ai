export type WaspidEventType =
  | "message"
  | "system"
  | "agent_state_changed"
  | "change_agent_state"
  | "run"
  | "read"
  | "write"
  | "edit"
  | "run_ipython"
  | "delegate"
  | "browse"
  | "browse_interactive"
  | "reject"
  | "think"
  | "finish"
  | "error"
  | "recall"
  | "mcp"
  | "call_tool_mcp"
  | "task_tracking"
  | "user_rejected";

export type WaspidSourceType = "agent" | "user" | "environment" | "hook";

interface WaspidBaseEvent {
  id: number;
  source: WaspidSourceType;
  message: string;
  timestamp: string; // ISO 8601
}

export interface WaspidActionEvent<
  T extends WaspidEventType,
> extends WaspidBaseEvent {
  action: T;
  args: Record<string, unknown>;
}

export interface WaspidObservationEvent<
  T extends WaspidEventType,
> extends WaspidBaseEvent {
  cause: number;
  observation: T;
  content: string;
  extras: Record<string, unknown>;
}
