import { openHands } from "../open-hands-axios";
import {
  HubConnection,
  ProviderStatus,
  ToolCallLogPage,
} from "./integrations-hub.types";

/** Client for the Integration Hub endpoints. */
class IntegrationsHubService {
  static async getProviders(): Promise<ProviderStatus[]> {
    const { data } = await openHands.get<ProviderStatus[]>(
      "/api/v1/integrations-hub/providers",
    );
    return data;
  }

  static async createConnection(args: {
    provider: string;
    credential: string;
    name?: string;
    base_url?: string;
  }): Promise<HubConnection> {
    const { data } = await openHands.post<HubConnection>(
      "/api/v1/integrations-hub/connections",
      args,
    );
    return data;
  }

  static async deleteConnection(connectionId: string): Promise<void> {
    await openHands.delete(
      `/api/v1/integrations-hub/connections/${connectionId}`,
    );
  }

  static async checkConnection(connectionId: string): Promise<HubConnection> {
    const { data } = await openHands.post<HubConnection>(
      `/api/v1/integrations-hub/connections/${connectionId}/check`,
    );
    return data;
  }

  static async getToolCalls(): Promise<ToolCallLogPage> {
    const { data } = await openHands.get<ToolCallLogPage>(
      "/api/v1/integrations-hub/tool-calls",
    );
    return data;
  }
}

export default IntegrationsHubService;
