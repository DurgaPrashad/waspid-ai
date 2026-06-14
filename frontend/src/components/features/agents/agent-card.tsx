// Waspid AI OS
import { Link } from "react-router";
import { ArrowUpRight } from "lucide-react";
import type { V1AppConversation } from "#/api/conversation-service/v1-conversation-service.types";
import { useConfig } from "#/hooks/query/use-config";
import { agentDisplayLabel } from "#/utils/agent-display-label";
import { formatTimeDelta } from "#/utils/format-time-delta";
import { StatusPill } from "#/components/shared/layout/status-pill";
import { cn } from "#/utils/utils";
import {
  LIFECYCLE_LABELS,
  lifecycleFromSandboxStatus,
  toneForLifecycle,
} from "./types";

interface AgentCardProps {
  conversation: V1AppConversation;
}

/**
 * Card surface for ONE Waspid agent (i.e. one V1AppConversation).
 *
 * The card pulls REAL fields from the runtime: title, agent kind,
 * model, repository context, sandbox lifecycle, last-update time.
 * No synthetic metrics. Clicking the card deep-links to the existing
 * conversation route so the user can drive the agent.
 */
export function AgentCard({ conversation }: AgentCardProps) {
  const { data: config } = useConfig();

  const lifecycle = lifecycleFromSandboxStatus(conversation.sandbox_status);
  const tone = toneForLifecycle(lifecycle);
  const lifecycleLabel = LIFECYCLE_LABELS[lifecycle];

  const agentLabel = agentDisplayLabel(
    conversation.agent_kind,
    conversation.llm_model,
    conversation.tags,
    config?.acp_providers,
  );

  const timestamp = conversation.updated_at || conversation.created_at;

  return (
    <Link
      to={`/conversations/${conversation.id}`}
      className={cn(
        "group flex flex-col gap-3 rounded-xl border border-tertiary/40 bg-base-secondary/40 p-5",
        "transition-colors hover:border-tertiary/60",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex flex-col gap-1 min-w-0">
          <span className="truncate text-sm font-semibold text-content">
            {conversation.title || "Untitled agent"}
          </span>
          {agentLabel && (
            <span className="truncate text-xs text-basic">{agentLabel}</span>
          )}
        </div>
        <StatusPill tone={tone}>{lifecycleLabel}</StatusPill>
      </div>

      <dl className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs text-basic">
        {conversation.selected_repository && (
          <>
            <dt className="text-basic/60">Repository</dt>
            <dd className="truncate text-content/80">
              {conversation.selected_repository}
            </dd>
          </>
        )}
        {conversation.selected_branch && (
          <>
            <dt className="text-basic/60">Branch</dt>
            <dd className="truncate text-content/80">
              {conversation.selected_branch}
            </dd>
          </>
        )}
        {conversation.llm_model && (
          <>
            <dt className="text-basic/60">Model</dt>
            <dd className="truncate text-content/80">
              {conversation.llm_model}
            </dd>
          </>
        )}
        {timestamp && (
          <>
            <dt className="text-basic/60">Last activity</dt>
            <dd className="truncate text-content/80">
              {formatTimeDelta(timestamp)} ago
            </dd>
          </>
        )}
      </dl>

      <span className="inline-flex items-center gap-1 self-end text-xs font-medium text-content/80 group-hover:text-content">
        Open
        <ArrowUpRight className="h-3.5 w-3.5" aria-hidden />
      </span>
    </Link>
  );
}
