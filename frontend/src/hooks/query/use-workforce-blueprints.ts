import { useQuery } from "@tanstack/react-query";
import WorkforceService from "#/api/workforce-service/workforce-service.api";
import { useIsAuthed } from "./use-is-authed";

export const WORKFORCE_BLUEPRINTS_QUERY_KEY = ["workforce", "blueprints"];

export const useWorkforceBlueprints = () => {
  const { data: userIsAuthenticated } = useIsAuthed();

  return useQuery({
    queryKey: WORKFORCE_BLUEPRINTS_QUERY_KEY,
    queryFn: WorkforceService.getBlueprints,
    enabled: !!userIsAuthenticated,
  });
};
