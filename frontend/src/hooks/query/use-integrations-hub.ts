import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import IntegrationsHubService from "#/api/integrations-hub/integrations-hub.api";
import { useIsAuthed } from "./use-is-authed";

export const HUB_QUERY_KEY = ["integrations-hub"];

export const useHubProviders = () => {
  const { data: userIsAuthenticated } = useIsAuthed();
  return useQuery({
    queryKey: [...HUB_QUERY_KEY, "providers"],
    queryFn: IntegrationsHubService.getProviders,
    enabled: !!userIsAuthenticated,
  });
};

export const useHubToolCalls = () => {
  const { data: userIsAuthenticated } = useIsAuthed();
  return useQuery({
    queryKey: [...HUB_QUERY_KEY, "tool-calls"],
    queryFn: IntegrationsHubService.getToolCalls,
    enabled: !!userIsAuthenticated,
  });
};

const useInvalidateHub = () => {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: HUB_QUERY_KEY });
};

export const useCreateHubConnection = () => {
  const invalidate = useInvalidateHub();
  return useMutation({
    mutationFn: IntegrationsHubService.createConnection,
    onSuccess: invalidate,
  });
};

export const useDeleteHubConnection = () => {
  const invalidate = useInvalidateHub();
  return useMutation({
    mutationFn: IntegrationsHubService.deleteConnection,
    onSuccess: invalidate,
  });
};

export const useCheckHubConnection = () => {
  const invalidate = useInvalidateHub();
  return useMutation({
    mutationFn: IntegrationsHubService.checkConnection,
    onSuccess: invalidate,
  });
};
