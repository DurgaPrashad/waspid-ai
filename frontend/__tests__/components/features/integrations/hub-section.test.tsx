// Waspid AI OS
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "../../../../test-utils";
import { HubSection } from "#/components/features/integrations/hub-section";
import IntegrationsHubService from "#/api/integrations-hub/integrations-hub.api";
import { ProviderStatus } from "#/api/integrations-hub/integrations-hub.types";

vi.mock("#/hooks/query/use-is-authed", () => ({
  useIsAuthed: () => ({ data: true }),
}));

const SLACK: ProviderStatus = {
  spec: {
    id: "slack",
    name: "Slack",
    category: "communication",
    credential_kind: "api_key",
    sandbox_env_var: "SLACK_BOT_TOKEN",
    base_url_required: false,
    notes: "Use a bot token.",
    tools: [
      {
        name: "send_message",
        description: "Post a message to a channel",
        execution: "server",
        params: { channel: "Channel", text: "Text" },
        required_params: ["channel", "text"],
      },
    ],
  },
  connection: null,
};

const CONNECTED_GITHUB: ProviderStatus = {
  spec: {
    id: "github",
    name: "GitHub",
    category: "development",
    credential_kind: "api_key",
    sandbox_env_var: "GITHUB_TOKEN",
    base_url_required: false,
    notes: "",
    tools: [],
  },
  connection: {
    id: "conn-1",
    user_id: null,
    provider: "github",
    name: "",
    base_url: null,
    created_at: null,
    last_check_at: "2026-06-12T00:00:00Z",
    last_check_ok: true,
  },
};

describe("HubSection", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(IntegrationsHubService, "getToolCalls").mockResolvedValue({
      items: [
        {
          id: "call-1",
          provider: "slack",
          tool: "send_message",
          ok: true,
          status_code: 200,
          error: null,
          latency_ms: 120,
          run_id: null,
          agent_name: "CRM Agent",
          created_at: null,
        },
      ],
      stats: { total: 5, failures: 1, avg_latency_ms: 150 },
    });
  });

  it("renders provider cards with connection state and stats", async () => {
    vi.spyOn(IntegrationsHubService, "getProviders").mockResolvedValue([
      SLACK,
      CONNECTED_GITHUB,
    ]);
    renderWithProviders(<HubSection />);

    const cards = await screen.findAllByTestId("hub-provider-card");
    expect(cards).toHaveLength(2);
    expect(screen.getByTestId("hub-connect-button")).toBeInTheDocument();
    expect(screen.getByText("healthy")).toBeInTheDocument();
    expect(screen.getByTestId("hub-stats")).toHaveTextContent("5 tool calls");
    expect(screen.getByTestId("hub-tool-call-log")).toHaveTextContent(
      "slack.send_message",
    );
  });

  it("connects a provider with an API key", async () => {
    vi.spyOn(IntegrationsHubService, "getProviders").mockResolvedValue([
      SLACK,
    ]);
    const createSpy = vi
      .spyOn(IntegrationsHubService, "createConnection")
      .mockResolvedValue({
        ...CONNECTED_GITHUB.connection!,
        provider: "slack",
      });
    renderWithProviders(<HubSection />);

    await userEvent.click(await screen.findByTestId("hub-connect-button"));
    await userEvent.type(
      screen.getByTestId("hub-credential-input"),
      "xoxb-secret",
    );
    await userEvent.click(screen.getByTestId("hub-save-connection-button"));

    await waitFor(() => expect(createSpy).toHaveBeenCalled());
    expect(createSpy.mock.calls[0][0]).toEqual({
      provider: "slack",
      credential: "xoxb-secret",
      base_url: undefined,
    });
  });

  it("disconnects and health-checks an existing connection", async () => {
    vi.spyOn(IntegrationsHubService, "getProviders").mockResolvedValue([
      CONNECTED_GITHUB,
    ]);
    const checkSpy = vi
      .spyOn(IntegrationsHubService, "checkConnection")
      .mockResolvedValue(CONNECTED_GITHUB.connection!);
    const deleteSpy = vi
      .spyOn(IntegrationsHubService, "deleteConnection")
      .mockResolvedValue();
    renderWithProviders(<HubSection />);

    await userEvent.click(await screen.findByTestId("hub-check-button"));
    await waitFor(() => expect(checkSpy).toHaveBeenCalled());
    expect(checkSpy.mock.calls[0][0]).toBe("conn-1");

    await userEvent.click(screen.getByTestId("hub-disconnect-button"));
    await waitFor(() => expect(deleteSpy).toHaveBeenCalled());
    expect(deleteSpy.mock.calls[0][0]).toBe("conn-1");
  });
});
