// Waspid AI OS
import { Link } from "react-router";
import { CheckCircle2, ExternalLink, RotateCcw } from "lucide-react";
import { WorkflowRunDetail } from "#/api/workforce-service/workforce.types";
import {
  useApproveWorkflowTask,
  useRetryWorkflowTask,
} from "#/hooks/mutation/use-workflow-run-mutations";
import { StatusPill } from "#/components/shared/layout/status-pill";
import { TASK_STATUS_LABELS, toneForTaskStatus } from "./types";

interface WorkflowRunDetailViewProps {
  detail: WorkflowRunDetail;
}

export function WorkflowRunDetailView({ detail }: WorkflowRunDetailViewProps) {
  const approve = useApproveWorkflowTask();
  const retry = useRetryWorkflowTask();
  const { run, tasks, events } = detail;

  return (
    <div data-testid="workflow-run-detail" className="flex flex-col gap-4">
      <div>
        <p className="mb-2 text-xs font-medium text-content">Agents</p>
        <ul className="flex flex-col gap-1.5">
          {tasks.map((task) => (
            <li
              key={task.id}
              data-testid="workflow-task-row"
              className="flex items-center justify-between gap-3 rounded-lg border border-tertiary/30 bg-base-secondary/10 px-3 py-2"
            >
              <div className="flex items-center gap-2 min-w-0">
                <StatusPill tone={toneForTaskStatus(task.status)}>
                  {TASK_STATUS_LABELS[task.status]}
                </StatusPill>
                <span className="truncate text-sm text-content">
                  {task.agent_name}
                  {task.is_aggregation && (
                    <span className="ml-1 text-[10px] text-basic">
                      (final report)
                    </span>
                  )}
                </span>
                {task.attempts > 1 && (
                  <span className="text-[10px] text-basic">
                    attempt {task.attempts}/{task.max_attempts}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-1.5 shrink-0">
                {task.status === "WAITING_APPROVAL" && (
                  <button
                    type="button"
                    data-testid="approve-task-button"
                    onClick={() =>
                      approve.mutate({ runId: run.id, taskId: task.id })
                    }
                    disabled={approve.isPending}
                    className="inline-flex items-center gap-1 rounded-md border border-tertiary/50 px-2 py-1 text-[11px] font-medium text-content/90 hover:border-tertiary/70 disabled:opacity-50"
                  >
                    <CheckCircle2 className="h-3 w-3" aria-hidden />
                    Approve
                  </button>
                )}
                {task.status === "FAILED" && (
                  <button
                    type="button"
                    data-testid="retry-task-button"
                    onClick={() =>
                      retry.mutate({ runId: run.id, taskId: task.id })
                    }
                    disabled={retry.isPending}
                    className="inline-flex items-center gap-1 rounded-md border border-tertiary/50 px-2 py-1 text-[11px] font-medium text-content/90 hover:border-tertiary/70 disabled:opacity-50"
                  >
                    <RotateCcw className="h-3 w-3" aria-hidden />
                    Retry
                  </button>
                )}
                {task.conversation_id && (
                  <Link
                    to={`/conversations/${task.conversation_id}`}
                    className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] text-basic hover:text-content"
                  >
                    <ExternalLink className="h-3 w-3" aria-hidden />
                    Open run
                  </Link>
                )}
              </div>
            </li>
          ))}
        </ul>
      </div>

      {run.final_output && (
        <div>
          <p className="mb-2 text-xs font-medium text-content">
            Final deliverable
          </p>
          <pre
            data-testid="workflow-final-output"
            className="whitespace-pre-wrap rounded-lg border border-tertiary/30 bg-base-secondary/10 p-3 text-xs text-content/90"
          >
            {run.final_output}
          </pre>
        </div>
      )}

      {run.error && (
        <p className="text-xs text-red-400">Run error: {run.error}</p>
      )}

      <div>
        <p className="mb-2 text-xs font-medium text-content">Timeline</p>
        <ul
          data-testid="workflow-event-log"
          className="flex max-h-64 flex-col gap-1 overflow-y-auto text-[11px] text-basic"
        >
          {events.map((event) => (
            <li key={event.id} className="flex gap-2">
              <span className="shrink-0 text-content/60">
                {event.created_at
                  ? new Date(event.created_at).toLocaleTimeString()
                  : ""}
              </span>
              <span className="text-content/80">{event.kind}</span>
              {event.agent_name && <span>· {event.agent_name}</span>}
              {event.detail && <span>— {event.detail}</span>}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
