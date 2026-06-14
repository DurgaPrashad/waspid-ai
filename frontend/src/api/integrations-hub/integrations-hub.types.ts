// Waspid AI OS
/**
 * Types for the Integration Hub API (/api/v1/integrations-hub).
 * Mirrors waspid/app_server/integrations_hub/hub_models.py.
 */

export type ToolExecution = "server" | "sandbox" | "mcp";

export interface ToolSpec {
  name: string;
  description: string;
  execution: ToolExecution;
  params: Record<string, string>;
  required_params: string[];
}

export interface IntegrationProviderSpec {
  id: string;
  name: string;
  category: string;
  credential_kind: "api_key" | "webhook_url" | "oauth_token";
  sandbox_env_var: string | null;
  base_url_required: boolean;
  tools: ToolSpec[];
  notes: string;
}

export interface HubConnection {
  id: string;
  user_id: string | null;
  provider: string;
  name: string;
  base_url: string | null;
  created_at: string | null;
  last_check_at: string | null;
  last_check_ok: boolean | null;
}

export interface ProviderStatus {
  spec: IntegrationProviderSpec;
  connection: HubConnection | null;
}

export interface ToolCallLogEntry {
  id: string;
  provider: string;
  tool: string;
  ok: boolean;
  status_code: number | null;
  error: string | null;
  latency_ms: number | null;
  run_id: string | null;
  agent_name: string | null;
  created_at: string | null;
}

export interface ToolCallStats {
  total: number;
  failures: number;
  avg_latency_ms: number | null;
}

export interface ToolCallLogPage {
  items: ToolCallLogEntry[];
  stats: ToolCallStats;
}
