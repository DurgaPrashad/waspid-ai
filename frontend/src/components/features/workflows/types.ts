/**
 * Waspid workflows domain types.
 *
 * A Waspid workflow is a long-running, multi-step orchestration that
 * chains agent operations, tool calls, and human-in-the-loop steps.
 *
 * NOTE: there is no workflows backend yet. These types define the
 * shape the surface will consume once the backend exists. They are
 * referenced by the /workflows shell so the type contract is in
 * place when the API ships. No mock data is materialized against
 * them in this commit.
 */
import type { StatusPillTone } from "#/components/shared/layout/status-pill";

export type WorkflowRunStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "cancelled"
  | "awaiting_approval";

export interface WorkflowRunSummary {
  id: string;
  workflow_id: string;
  workflow_name: string;
  status: WorkflowRunStatus;
  started_at: string;
  finished_at: string | null;
  duration_ms: number | null;
  triggered_by: "schedule" | "webhook" | "manual" | "agent";
}

export interface WorkflowDefinition {
  id: string;
  name: string;
  description: string | null;
  enabled: boolean;
  last_run: WorkflowRunSummary | null;
  trigger_type: "schedule" | "webhook" | "manual";
  created_at: string;
  updated_at: string;
}

const TONE_BY_STATUS: Record<WorkflowRunStatus, StatusPillTone> = {
  queued: "info",
  running: "info",
  succeeded: "success",
  failed: "danger",
  cancelled: "neutral",
  awaiting_approval: "warning",
};

export function toneForWorkflowStatus(
  status: WorkflowRunStatus,
): StatusPillTone {
  return TONE_BY_STATUS[status];
}

export const WORKFLOW_STATUS_LABELS: Record<WorkflowRunStatus, string> = {
  queued: "Queued",
  running: "Running",
  succeeded: "Succeeded",
  failed: "Failed",
  cancelled: "Cancelled",
  awaiting_approval: "Awaiting approval",
};
