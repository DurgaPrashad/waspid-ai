// Waspid AI OS
import { Link } from "react-router";
import { StatusPill } from "#/components/shared/layout/status-pill";
import { formatTimeDelta } from "#/utils/format-time-delta";
import type { MonitoringRun } from "./types";

interface RunRowProps {
  run: MonitoringRun;
}

/**
 * Compact row representation of one Waspid run.
 *
 * Renders only verifiable runtime fields. Cost and tokens come from
 * the real `metrics.accumulated_*` snapshot on the conversation. When
 * a field is null we render "—" — we never substitute a fake zero.
 */
export function RunRow({ run }: RunRowProps) {
  return (
    <Link
      to={`/conversations/${run.id}`}
      className="grid grid-cols-12 gap-3 px-4 py-3 border-b border-tertiary/30 hover:bg-base-secondary/30 transition-colors"
      data-testid="monitoring-run-row"
    >
      <div className="col-span-12 sm:col-span-4 min-w-0">
        <div className="truncate text-sm font-medium text-content">
          {run.title}
        </div>
        {run.repository && (
          <div className="truncate text-xs text-basic">
            {run.repository}
            {run.branch ? ` · ${run.branch}` : null}
          </div>
        )}
      </div>

      <div className="col-span-6 sm:col-span-2 flex items-center">
        <StatusPill tone={run.lifecycleTone}>{run.lifecycleLabel}</StatusPill>
      </div>

      <div
        className="col-span-6 sm:col-span-2 truncate text-xs text-basic flex items-center"
        title={run.llm_model ?? ""}
      >
        {run.llm_model || "—"}
      </div>

      <div className="col-span-6 sm:col-span-2 text-xs text-basic flex items-center">
        {formatCost(run.accumulated_cost)}
      </div>

      <div className="col-span-6 sm:col-span-2 text-xs text-basic flex items-center">
        {formatTimeDelta(run.updated_at || run.created_at)} ago
      </div>
    </Link>
  );
}

function formatCost(cost: number | null): string {
  if (cost == null) return "—";
  if (cost === 0) return "$0.00";
  if (cost < 0.01) return "<$0.01";
  return `$${cost.toFixed(2)}`;
}
