import { useMutation, useQueryClient } from "@tanstack/react-query";
import WorkforceService from "#/api/workforce-service/workforce-service.api";
import {
  BlueprintExport,
  WorkforceDefinition,
} from "#/api/workforce-service/workforce.types";
import { WORKFORCE_BLUEPRINTS_QUERY_KEY } from "#/hooks/query/use-workforce-blueprints";

const useInvalidateBlueprints = () => {
  const queryClient = useQueryClient();
  return () =>
    queryClient.invalidateQueries({ queryKey: WORKFORCE_BLUEPRINTS_QUERY_KEY });
};

export const useCreateBlueprint = () => {
  const invalidate = useInvalidateBlueprints();
  return useMutation({
    mutationFn: ({
      name,
      definition,
    }: {
      name: string;
      definition: WorkforceDefinition;
    }) => WorkforceService.createBlueprint(name, definition),
    onSuccess: invalidate,
  });
};

export const useDeleteBlueprint = () => {
  const invalidate = useInvalidateBlueprints();
  return useMutation({
    mutationFn: (blueprintId: string) =>
      WorkforceService.deleteBlueprint(blueprintId),
    onSuccess: invalidate,
  });
};

export const useCloneBlueprint = () => {
  const invalidate = useInvalidateBlueprints();
  return useMutation({
    mutationFn: (blueprintId: string) =>
      WorkforceService.cloneBlueprint(blueprintId),
    onSuccess: invalidate,
  });
};

export const useImportBlueprint = () => {
  const invalidate = useInvalidateBlueprints();
  return useMutation({
    mutationFn: (blueprint: BlueprintExport) =>
      WorkforceService.importBlueprint(blueprint),
    onSuccess: invalidate,
  });
};
