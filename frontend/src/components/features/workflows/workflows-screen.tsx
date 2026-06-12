import { useState } from "react";
import { Link } from "react-router";
import {
  ChevronDown,
  ChevronRight,
  Pause,
  Play,
  Workflow as WorkflowIcon,
  XCircle,
} from "lucide-react";
import { PageShell, PageHeader, Section } from "#/components/shared/layout";
import { StatusPill } from "#/components/shared/layout/status-pill";
import { WorkflowRun } from "#/api/workforce-service/workforce.types";
import {
  useWorkflowRunDetail,
  useWorkflowRuns,
} from "#/hooks/query/use-workflow-runs";
import { useWorkflowRunAction } from "#/hooks/mutation/use-workflow-run-mutations";
import { RUN_STATUS_LABELS, toneForRunStatus } from "./types";
import { WorkflowRunDetailView } from "./workflow-run-detail";

function RunRow({ run, expanded, onToggle, onAction, detail }: RunRowProps) {
  const isActive = run.status === "RUNNING" || run.status === "PAUSED";
  return (
    <li
      data-testid="workflow-run-row"
      className="rounded-xl border border-tertiary/40 bg-base-secondary/20"
    >
      <div className="flex items-center justify-between gap-3 px-4 py-3">
        <button
          type="button"
          onClick={onToggle}
          className="flex min-w-0 flex-1 items-center gap-2 text-left"
        >
          {expanded ? (
            <ChevronDown className="h-4 w-4 shrink-0 text-basic" aria-hidden />
          ) : (
            <ChevronRight className="h-4 w-4 shrink-0 text-basic" aria-hidden />
          )}
          <span className="truncate text-sm font-medium text-content">
            {run.name}
          </span>
          <StatusPill tone={toneForRunStatus(run.status)}>
            {RUN_STATUS_LABELS[run.status]}
          </StatusPill>
          <span className="text-[11px] text-basic">
            {run.definition.agents.length} agents
          </span>
        </button>
        {isActive && (
          <div className="flex items-center gap-1.5 shrink-0">
            {run.status === "RUNNING" ? (
              <button
                type="button"
                title="Pause"
                onClick={() => onAction("pause")}
                className="rounded p-1.5 text-basic hover:bg-tertiary/30 hover:text-content"
              >
                <Pause className="h-4 w-4" aria-hidden />
              </button>
            ) : (
              <button
                type="button"
                title="Resume"
                onClick={() => onAction("resume")}
                className="rounded p-1.5 text-basic hover:bg-tertiary/30 hover:text-content"
              >
                <Play className="h-4 w-4" aria-hidden />
              </button>
            )}
            <button
              type="button"
              title="Cancel"
              onClick={() => onAction("cancel")}
              className="rounded p-1.5 text-basic hover:bg-red-500/20 hover:text-red-400"
            >
              <XCircle className="h-4 w-4" aria-hidden />
            </button>
          </div>
        )}
      </div>
      {expanded && detail && (
        <div className="border-t border-tertiary/30 px-4 py-3">{detail}</div>
      )}
    </li>
  );
}

/**
 * Waspid Workflows surface — the execution dashboard for the workflow
 * runtime. Lists every workforce run with live status (polled while
 * active), and expands into per-agent task state, approvals, the run
 * timeline, and the final deliverable.
 */
export function WorkflowsScreen() {
  const { data, isLoading, error } = useWorkflowRuns();
  const [expandedRunId, setExpandedRunId] = useState<string | null>(null);
  const detail = useWorkflowRunDetail(expandedRunId);
  const runAction = useWorkflowRunAction();

  const runs = data?.items ?? [];

  return (
    <div data-testid="workflows-screen" className="h-full">
      <PageShell
        width="wide"
        header={
          <PageHeader
            eyebrow="Operations"
            title="Workflows"
            subtitle="Autonomous workforce runs: agents executing, handing off, and aggregating results."
          />
        }
      >
        <Section
          title="Workflow runs"
          description="Active and historical orchestration runs across this workspace."
        >
          {isLoading && <p className="text-xs text-basic">Loading runs…</p>}
          {error != null && (
            <p className="text-xs text-red-400">
              Could not load workflow runs. Try again later.
            </p>
          )}
          {!isLoading && !error && runs.length === 0 && (
            <div
              data-testid="workflows-empty"
              className="rounded-xl border border-dashed border-tertiary/40 bg-base-secondary/20 px-6 py-12 text-center"
            >
              <WorkflowIcon
                className="mx-auto mb-3 h-8 w-8 text-basic"
                aria-hidden
              />
              <p className="text-sm font-medium text-content">
                No workforce runs yet.
              </p>
              <p className="mt-1 mx-auto max-w-md text-xs text-basic">
                Generate a workforce in the Workforce Builder and click
                &ldquo;Deploy &amp; run&rdquo; — agents will execute and hand
                off to each other automatically.
              </p>
              <Link
                to="/workforce"
                className="mt-5 inline-flex items-center gap-1.5 rounded-md border border-tertiary/50 px-3 py-1.5 text-xs font-medium text-content/90 hover:border-tertiary/70 hover:text-content"
              >
                Open Workforce Builder
              </Link>
            </div>
          )}

          <ul className="flex flex-col gap-2">
            {runs.map((run) => (
              <RunRow
                key={run.id}
                run={run}
                expanded={expandedRunId === run.id}
                onToggle={() =>
                  setExpandedRunId(expandedRunId === run.id ? null : run.id)
                }
                onAction={(action) =>
                  runAction.mutate({ runId: run.id, action })
                }
                detail={
                  expandedRunId === run.id && detail.data ? (
                    <WorkflowRunDetailView detail={detail.data} />
                  ) : null
                }
              />
            ))}
          </ul>
        </Section>
      </PageShell>
    </div>
  );
}

interface RunRowProps {
  run: WorkflowRun;
  expanded: boolean;
  onToggle: () => void;
  onAction: (action: "pause" | "resume" | "cancel") => void;
  detail: React.ReactNode;
}
