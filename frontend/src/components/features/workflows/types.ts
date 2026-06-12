/**
 * Waspid workflows domain helpers.
 *
 * Workflow runs are executed by the backend workflow runtime
 * (/api/v1/workforce/runs); API types live in
 * `#/api/workforce-service/workforce.types`. This module maps runtime
 * statuses onto the shared StatusPill tones.
 */
import type { StatusPillTone } from "#/components/shared/layout/status-pill";
import type {
  WorkflowRunStatus,
  WorkflowTaskStatus,
} from "#/api/workforce-service/workforce.types";

const RUN_TONE: Record<WorkflowRunStatus, StatusPillTone> = {
  RUNNING: "info",
  PAUSED: "warning",
  COMPLETED: "success",
  FAILED: "danger",
  CANCELLED: "neutral",
};

const TASK_TONE: Record<WorkflowTaskStatus, StatusPillTone> = {
  QUEUED: "neutral",
  WAITING_APPROVAL: "warning",
  RUNNING: "info",
  COMPLETED: "success",
  FAILED: "danger",
  CANCELLED: "neutral",
};

export const toneForRunStatus = (status: WorkflowRunStatus): StatusPillTone =>
  RUN_TONE[status] ?? "neutral";

export const toneForTaskStatus = (status: WorkflowTaskStatus): StatusPillTone =>
  TASK_TONE[status] ?? "neutral";

export const RUN_STATUS_LABELS: Record<WorkflowRunStatus, string> = {
  RUNNING: "Running",
  PAUSED: "Paused",
  COMPLETED: "Completed",
  FAILED: "Failed",
  CANCELLED: "Cancelled",
};

export const TASK_STATUS_LABELS: Record<WorkflowTaskStatus, string> = {
  QUEUED: "Queued",
  WAITING_APPROVAL: "Awaiting approval",
  RUNNING: "Running",
  COMPLETED: "Completed",
  FAILED: "Failed",
  CANCELLED: "Cancelled",
};
