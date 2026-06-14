// Waspid AI OS
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createRoutesStub } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "../../../../test-utils";
import { WorkforceBuilderScreen } from "#/components/features/workforce/workforce-builder-screen";
import WorkforceService from "#/api/workforce-service/workforce-service.api";
import { WorkforceDefinition } from "#/api/workforce-service/workforce.types";

vi.mock("#/hooks/query/use-is-authed", () => ({
  useIsAuthed: () => ({ data: true }),
}));

const DEFINITION: WorkforceDefinition = {
  objective: "Build me a real estate lead generation business",
  summary: "A compact lead-gen workforce.",
  agents: [
    {
      name: "Sales Manager Agent",
      role: "Coordinates the team",
      responsibilities: ["review results"],
      system_prompt: "You are the sales manager.",
      tools: ["browser"],
      integrations: [],
      reports_to: null,
    },
    {
      name: "Lead Research Agent",
      role: "Finds leads",
      responsibilities: ["research prospects"],
      system_prompt: "You research leads.",
      tools: ["web_search"],
      integrations: [],
      reports_to: "Sales Manager Agent",
    },
  ],
  workflows: [
    {
      from_agent: "Lead Research Agent",
      to_agent: "Sales Manager Agent",
      trigger: "leads collected",
    },
  ],
};

function renderScreen() {
  const RouterStub = createRoutesStub([
    { path: "/", Component: WorkforceBuilderScreen },
  ]);
  return renderWithProviders(<RouterStub initialEntries={["/"]} />);
}

describe("WorkforceBuilderScreen", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(WorkforceService, "getBlueprints").mockResolvedValue({
      items: [],
    });
  });

  it("renders the objective input and an empty blueprint library", async () => {
    renderScreen();
    expect(
      screen.getByTestId("workforce-objective-input"),
    ).toBeInTheDocument();
    expect(
      await screen.findByTestId("blueprint-library-empty"),
    ).toBeInTheDocument();
  });

  it("disables generate until an objective is typed", async () => {
    renderScreen();
    const button = screen.getByTestId("workforce-generate-button");
    expect(button).toBeDisabled();
    await userEvent.type(
      screen.getByTestId("workforce-objective-input"),
      "Build me a software development agency",
    );
    expect(button).toBeEnabled();
  });

  it("generates and displays a workforce", async () => {
    const generateSpy = vi
      .spyOn(WorkforceService, "generateWorkforce")
      .mockResolvedValue(DEFINITION);

    renderScreen();
    await userEvent.type(
      screen.getByTestId("workforce-objective-input"),
      DEFINITION.objective,
    );
    await userEvent.click(screen.getByTestId("workforce-generate-button"));

    await waitFor(() =>
      expect(screen.getByTestId("workforce-graph")).toBeInTheDocument(),
    );
    expect(generateSpy).toHaveBeenCalledWith({
      objective: DEFINITION.objective,
    });
    expect(screen.getAllByTestId("agent-spec-card")).toHaveLength(2);
    // Appears in both the org graph (SVG) and the agent card.
    expect(
      screen.getAllByText("Lead Research Agent").length,
    ).toBeGreaterThanOrEqual(2);
  });

  it("shows an error when generation fails", async () => {
    vi.spyOn(WorkforceService, "generateWorkforce").mockRejectedValue(
      new Error("Workforce generation failed"),
    );
    renderScreen();
    await userEvent.type(
      screen.getByTestId("workforce-objective-input"),
      "anything",
    );
    await userEvent.click(screen.getByTestId("workforce-generate-button"));
    expect(
      await screen.findByTestId("workforce-generate-error"),
    ).toBeInTheDocument();
  });

  it("saves the generated workforce as a blueprint", async () => {
    vi.spyOn(WorkforceService, "generateWorkforce").mockResolvedValue(
      DEFINITION,
    );
    const createSpy = vi
      .spyOn(WorkforceService, "createBlueprint")
      .mockResolvedValue({
        id: "bp-1",
        user_id: null,
        name: "Lead Gen",
        definition: DEFINITION,
        created_at: null,
        updated_at: null,
      });

    renderScreen();
    await userEvent.type(
      screen.getByTestId("workforce-objective-input"),
      DEFINITION.objective,
    );
    await userEvent.click(screen.getByTestId("workforce-generate-button"));
    await screen.findByTestId("blueprint-save-button");

    const nameInput = screen.getByTestId("blueprint-name-input");
    await userEvent.clear(nameInput);
    await userEvent.type(nameInput, "Lead Gen");
    await userEvent.click(screen.getByTestId("blueprint-save-button"));

    await waitFor(() =>
      expect(createSpy).toHaveBeenCalledWith("Lead Gen", DEFINITION),
    );
  });

  it("lists saved blueprints from the library", async () => {
    vi.spyOn(WorkforceService, "getBlueprints").mockResolvedValue({
      items: [
        {
          id: "bp-1",
          user_id: null,
          name: "Real Estate Pack",
          definition: DEFINITION,
          created_at: null,
          updated_at: null,
        },
      ],
    });
    renderScreen();
    expect(
      await screen.findByTestId("blueprint-library"),
    ).toBeInTheDocument();
    expect(screen.getByText("Real Estate Pack")).toBeInTheDocument();
    expect(screen.getByText(/2 agents · 1 handoffs/)).toBeInTheDocument();
  });
});
