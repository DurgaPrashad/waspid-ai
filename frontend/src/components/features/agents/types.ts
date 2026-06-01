import type { V1SandboxStatus } from "#/api/sandbox-service/sandbox-service.types";

/**
 * Waspid agents domain types.
 *
 * The Waspid "agent" is the unit of AI labor: a running conversation
 * driven by an agent runtime (model + tools + skills + memory). This
 * file defines the lifecycle and tone vocabulary that the /agents
 * surface uses — both for currently-running agents and for stored
 * agent configurations.
 *
 * The lifecycle deliberately matches the real `V1SandboxStatus` /
 * `ConversationStatus` enums published by the runtime so the surface
 * never invents states the backend can't produce.
 */
export type AgentLifecycle =
  | "starting"
  | "running"
  | "awaiting_input"
  | "paused"
  | "stopped"
  | "finished"
  | "error";

/** Visual tone derived from the lifecycle. UI primitives consume this. */
export type AgentTone = "info" | "success" | "warning" | "danger" | "neutral";

const TONE_BY_LIFECYCLE: Record<AgentLifecycle, AgentTone> = {
  starting: "info",
  running: "success",
  awaiting_input: "warning",
  paused: "warning",
  stopped: "neutral",
  finished: "neutral",
  error: "danger",
};

export function toneForLifecycle(lifecycle: AgentLifecycle): AgentTone {
  return TONE_BY_LIFECYCLE[lifecycle];
}

/**
 * Map a real `V1SandboxStatus` to an `AgentLifecycle`.
 *
 * The mapping intentionally preserves the runtime's vocabulary —
 * we don't invent a state if the sandbox doesn't have one.
 */
export function lifecycleFromSandboxStatus(
  status: V1SandboxStatus | null | undefined,
): AgentLifecycle {
  switch (status) {
    case "RUNNING":
      return "running";
    case "PAUSED":
      return "paused";
    case "ERROR":
      return "error";
    case "MISSING":
      return "stopped";
    default:
      return "stopped";
  }
}

export const LIFECYCLE_LABELS: Record<AgentLifecycle, string> = {
  starting: "Starting",
  running: "Running",
  awaiting_input: "Awaiting input",
  paused: "Paused",
  stopped: "Stopped",
  finished: "Finished",
  error: "Error",
};
