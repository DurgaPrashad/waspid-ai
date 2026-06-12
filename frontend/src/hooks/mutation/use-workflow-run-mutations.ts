import { useMutation, useQueryClient } from "@tanstack/react-query";
import WorkforceService from "#/api/workforce-service/workforce-service.api";
import { StartWorkflowRunRequest } from "#/api/workforce-service/workforce.types";
import { WORKFLOW_RUNS_QUERY_KEY } from "#/hooks/query/use-workflow-runs";

const useInvalidateRuns = () => {
  const queryClient = useQueryClient();
  return () =>
    queryClient.invalidateQueries({ queryKey: WORKFLOW_RUNS_QUERY_KEY });
};

export const useStartWorkflowRun = () => {
  const invalidate = useInvalidateRuns();
  return useMutation({
    mutationFn: (request: StartWorkflowRunRequest) =>
      WorkforceService.startRun(request),
    onSuccess: invalidate,
  });
};

export const useWorkflowRunAction = () => {
  const invalidate = useInvalidateRuns();
  return useMutation({
    mutationFn: ({
      runId,
      action,
    }: {
      runId: string;
      action: "pause" | "resume" | "cancel";
    }) => WorkforceService.runAction(runId, action),
    onSuccess: invalidate,
  });
};

export const useApproveWorkflowTask = () => {
  const invalidate = useInvalidateRuns();
  return useMutation({
    mutationFn: ({ runId, taskId }: { runId: string; taskId: string }) =>
      WorkforceService.approveTask(runId, taskId),
    onSuccess: invalidate,
  });
};

export const useRetryWorkflowTask = () => {
  const invalidate = useInvalidateRuns();
  return useMutation({
    mutationFn: ({ runId, taskId }: { runId: string; taskId: string }) =>
      WorkforceService.retryTask(runId, taskId),
    onSuccess: invalidate,
  });
};
