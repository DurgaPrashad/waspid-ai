/**
 * Types for the workforce agent factory API (/api/v1/workforce).
 * Mirrors waspid/app_server/workforce/workforce_models.py.
 */

export interface AgentSpec {
  name: string;
  role: string;
  responsibilities: string[];
  system_prompt: string;
  tools: string[];
  integrations: string[];
  reports_to: string | null;
}

export interface WorkflowEdge {
  from_agent: string;
  to_agent: string;
  trigger: string;
}

export interface WorkforceDefinition {
  objective: string;
  summary: string;
  agents: AgentSpec[];
  workflows: WorkflowEdge[];
}

export interface WorkforceBlueprint {
  id: string;
  user_id: string | null;
  name: string;
  definition: WorkforceDefinition;
  created_at: string | null;
  updated_at: string | null;
}

export interface BlueprintExport {
  version: number;
  name: string;
  definition: WorkforceDefinition;
}

export interface GenerateWorkforceRequest {
  objective: string;
  max_agents?: number;
}

export interface WorkforceBlueprintPage {
  items: WorkforceBlueprint[];
}

// --- Workflow runtime -------------------------------------------------

export type WorkflowRunStatus =
  | "RUNNING"
  | "PAUSED"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED";

export type WorkflowTaskStatus =
  | "QUEUED"
  | "WAITING_APPROVAL"
  | "RUNNING"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED";

export interface WorkflowRun {
  id: string;
  user_id: string | null;
  blueprint_id: string | null;
  name: string;
  status: WorkflowRunStatus;
  definition: WorkforceDefinition;
  context: Record<string, string>;
  final_output: string | null;
  error: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface WorkflowTask {
  id: string;
  run_id: string;
  agent_name: string;
  status: WorkflowTaskStatus;
  conversation_id: string | null;
  attempts: number;
  max_attempts: number;
  requires_approval: boolean;
  approved: boolean;
  is_aggregation: boolean;
  output: string | null;
  error: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string | null;
}

export interface WorkflowRunEvent {
  id: string;
  run_id: string;
  kind: string;
  agent_name: string | null;
  detail: string | null;
  created_at: string | null;
}

export interface WorkflowRunDetail {
  run: WorkflowRun;
  tasks: WorkflowTask[];
  events: WorkflowRunEvent[];
}

export interface StartWorkflowRunRequest {
  blueprint_id?: string;
  definition?: WorkforceDefinition;
  name?: string;
}

export interface WorkflowRunPage {
  items: WorkflowRun[];
}
