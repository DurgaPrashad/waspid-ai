import type { V1AppConversation } from "#/api/conversation-service/v1-conversation-service.types";
import type { StatusPillTone } from "#/components/shared/layout/status-pill";
import {
  lifecycleFromSandboxStatus,
  toneForLifecycle,
  LIFECYCLE_LABELS,
  type AgentLifecycle,
} from "#/components/features/agents/types";

/**
 * Waspid monitoring domain types.
 *
 * Monitoring treats every running V1AppConversation as a "run".
 * The unit of observation is the same as in /agents — what differs
 * is the framing: agents = fleet identity, monitoring = activity
 * stream.
 *
 * Reuses the agent lifecycle vocabulary so both surfaces show the
 * same state for the same conversation.
 */
export interface MonitoringRun {
  id: string;
  title: string;
  lifecycle: AgentLifecycle;
  lifecycleLabel: string;
  lifecycleTone: StatusPillTone;
  llm_model: string | null;
  repository: string | null;
  branch: string | null;
  created_at: string;
  updated_at: string;
  accumulated_cost: number | null;
  accumulated_prompt_tokens: number | null;
  accumulated_completion_tokens: number | null;
}

/**
 * Project a raw V1AppConversation into a monitoring-shaped run.
 *
 * Returns only fields the runtime actually publishes; never invents
 * derived metrics. Token counts are read from `metrics.accumulated_token_usage`
 * (real) — if the field is null, downstream UI renders "—" rather
 * than fabricating a zero.
 */
export function toMonitoringRun(conv: V1AppConversation): MonitoringRun {
  const lifecycle = lifecycleFromSandboxStatus(conv.sandbox_status);
  const tokens = conv.metrics?.accumulated_token_usage ?? null;

  return {
    id: conv.id,
    title: conv.title || "Untitled run",
    lifecycle,
    lifecycleLabel: LIFECYCLE_LABELS[lifecycle],
    lifecycleTone: toneForLifecycle(lifecycle),
    llm_model: conv.llm_model,
    repository: conv.selected_repository,
    branch: conv.selected_branch,
    created_at: conv.created_at,
    updated_at: conv.updated_at,
    accumulated_cost: conv.metrics?.accumulated_cost ?? null,
    accumulated_prompt_tokens: tokens?.prompt_tokens ?? null,
    accumulated_completion_tokens: tokens?.completion_tokens ?? null,
  };
}
