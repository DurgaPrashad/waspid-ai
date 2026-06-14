// Waspid AI OS
import { openHands } from "../open-hands-axios";
import {
  BlueprintExport,
  GenerateWorkforceRequest,
  StartWorkflowRunRequest,
  WorkflowRun,
  WorkflowRunDetail,
  WorkflowRunPage,
  WorkflowTask,
  WorkforceBlueprint,
  WorkforceBlueprintPage,
  WorkforceDefinition,
} from "./workforce.types";

/**
 * Client for the workforce agent factory endpoints.
 */
class WorkforceService {
  static async generateWorkforce(
    request: GenerateWorkforceRequest,
  ): Promise<WorkforceDefinition> {
    const { data } = await openHands.post<WorkforceDefinition>(
      "/api/v1/workforce/generate",
      request,
    );
    return data;
  }

  static async getBlueprints(): Promise<WorkforceBlueprintPage> {
    const { data } = await openHands.get<WorkforceBlueprintPage>(
      "/api/v1/workforce/blueprints",
    );
    return data;
  }

  static async createBlueprint(
    name: string,
    definition: WorkforceDefinition,
  ): Promise<WorkforceBlueprint> {
    const { data } = await openHands.post<WorkforceBlueprint>(
      "/api/v1/workforce/blueprints",
      { name, definition },
    );
    return data;
  }

  static async deleteBlueprint(blueprintId: string): Promise<void> {
    await openHands.delete(`/api/v1/workforce/blueprints/${blueprintId}`);
  }

  static async cloneBlueprint(
    blueprintId: string,
  ): Promise<WorkforceBlueprint> {
    const { data } = await openHands.post<WorkforceBlueprint>(
      `/api/v1/workforce/blueprints/${blueprintId}/clone`,
    );
    return data;
  }

  static async exportBlueprint(blueprintId: string): Promise<BlueprintExport> {
    const { data } = await openHands.get<BlueprintExport>(
      `/api/v1/workforce/blueprints/${blueprintId}/export`,
    );
    return data;
  }

  static async importBlueprint(
    blueprint: BlueprintExport,
  ): Promise<WorkforceBlueprint> {
    const { data } = await openHands.post<WorkforceBlueprint>(
      "/api/v1/workforce/blueprints/import",
      blueprint,
    );
    return data;
  }

  // --- Workflow runtime ------------------------------------------------

  static async startRun(
    request: StartWorkflowRunRequest,
  ): Promise<WorkflowRun> {
    const { data } = await openHands.post<WorkflowRun>(
      "/api/v1/workforce/runs",
      request,
    );
    return data;
  }

  static async getRuns(): Promise<WorkflowRunPage> {
    const { data } = await openHands.get<WorkflowRunPage>(
      "/api/v1/workforce/runs",
    );
    return data;
  }

  static async getRunDetail(runId: string): Promise<WorkflowRunDetail> {
    const { data } = await openHands.get<WorkflowRunDetail>(
      `/api/v1/workforce/runs/${runId}`,
    );
    return data;
  }

  static async runAction(
    runId: string,
    action: "pause" | "resume" | "cancel",
  ): Promise<WorkflowRun> {
    const { data } = await openHands.post<WorkflowRun>(
      `/api/v1/workforce/runs/${runId}/${action}`,
    );
    return data;
  }

  static async approveTask(
    runId: string,
    taskId: string,
  ): Promise<WorkflowTask> {
    const { data } = await openHands.post<WorkflowTask>(
      `/api/v1/workforce/runs/${runId}/tasks/${taskId}/approve`,
    );
    return data;
  }

  static async retryTask(runId: string, taskId: string): Promise<WorkflowTask> {
    const { data } = await openHands.post<WorkflowTask>(
      `/api/v1/workforce/runs/${runId}/tasks/${taskId}/retry`,
    );
    return data;
  }
}

export default WorkforceService;
