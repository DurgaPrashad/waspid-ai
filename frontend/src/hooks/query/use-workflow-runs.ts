import { useQuery } from "@tanstack/react-query";
import WorkforceService from "#/api/workforce-service/workforce-service.api";
import { useIsAuthed } from "./use-is-authed";

export const WORKFLOW_RUNS_QUERY_KEY = ["workforce", "runs"];

const hasActiveRun = (statuses: string[]) =>
  statuses.some((s) => s === "RUNNING" || s === "PAUSED");

/** List workflow runs; polls while any run is still active. */
export const useWorkflowRuns = () => {
  const { data: userIsAuthenticated } = useIsAuthed();

  return useQuery({
    queryKey: WORKFLOW_RUNS_QUERY_KEY,
    queryFn: WorkforceService.getRuns,
    enabled: !!userIsAuthenticated,
    refetchInterval: (query) => {
      const items = query.state.data?.items ?? [];
      return hasActiveRun(items.map((r) => r.status)) ? 4000 : false;
    },
  });
};

/** A single run with tasks + event log; polls while the run is active. */
export const useWorkflowRunDetail = (runId: string | null) => {
  const { data: userIsAuthenticated } = useIsAuthed();

  return useQuery({
    queryKey: [...WORKFLOW_RUNS_QUERY_KEY, runId],
    queryFn: () => WorkforceService.getRunDetail(runId!),
    enabled: !!userIsAuthenticated && !!runId,
    refetchInterval: (query) => {
      const status = query.state.data?.run.status;
      return status === "RUNNING" || status === "PAUSED" ? 3000 : false;
    },
  });
};
