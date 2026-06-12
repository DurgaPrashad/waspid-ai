import { useMutation } from "@tanstack/react-query";
import WorkforceService from "#/api/workforce-service/workforce-service.api";
import { GenerateWorkforceRequest } from "#/api/workforce-service/workforce.types";

export const useGenerateWorkforce = () =>
  useMutation({
    mutationKey: ["workforce", "generate"],
    mutationFn: (request: GenerateWorkforceRequest) =>
      WorkforceService.generateWorkforce(request),
  });
