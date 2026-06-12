import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createRoutesStub } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "../../../../test-utils";
import { WorkflowsScreen } from "#/components/features/workflows/workflows-screen";
import WorkforceService from "#/api/workforce-service/workforce-service.api";
import {
  WorkflowRun,
  WorkflowRunDetail,
} from "#/api/workforce-service/workforce.types";

vi.mock("#/hooks/query/use-is-authed", () => ({
  useIsAuthed: () => ({ data: true }),
}));

const RUN: WorkflowRun = {
  id: "run-1",
  user_id: null,
  blueprint_id: null,
  name: "Lead gen workforce",
  status: "RUNNING",
  definition: {
    objective: "Run lead gen",
    summary: "",
    agents: [
      {
        name: "Research",
        role: "Finds leads",
        responsibilities: [],
        system_prompt: "p",
        tools: [],
        integrations: [],
        reports_to: null,
      },
      {
        name: "CRM",
        role: "Updates CRM",
        responsibilities: [],
        system_prompt: "p",
        tools: [],
        integrations: [],
        reports_to: null,
      },
    ],
    workflows: [{ from_agent: "Research", to_agent: "CRM", trigger: "done" }],
  },
  context: {},
  final_output: null,
  error: null,
  created_at: null,
  updated_at: null,
};

const DETAIL: WorkflowRunDetail = {
  run: { ...RUN, status: "COMPLETED", final_output: "FINAL REPORT" },
  tasks: [
    {
      id: "t1",
      run_id: "run-1",
      agent_name: "Research",
      status: "COMPLETED",
      conversation_id: "c1",
      attempts: 1,
      max_attempts: 2,
      requires_approval: false,
      approved: false,
      is_aggregation: false,
      output: "found leads",
      error: null,
      started_at: null,
      finished_at: null,
      created_at: null,
    },
    {
      id: "t2",
      run_id: "run-1",
      agent_name: "CRM",
      status: "WAITING_APPROVAL",
      conversation_id: null,
      attempts: 0,
      max_attempts: 2,
      requires_approval: true,
      approved: false,
      is_aggregation: false,
      output: null,
      error: null,
      started_at: null,
      finished_at: null,
      created_at: null,
    },
  ],
  events: [
    {
      id: "e1",
      run_id: "run-1",
      kind: "workflow_started",
      agent_name: null,
      detail: null,
      created_at: null,
    },
  ],
};

function renderScreen() {
  const RouterStub = createRoutesStub([
    { path: "/", Component: WorkflowsScreen },
  ]);
  return renderWithProviders(<RouterStub initialEntries={["/"]} />);
}

describe("WorkflowsScreen", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("shows an empty state when there are no runs", async () => {
    vi.spyOn(WorkforceService, "getRuns").mockResolvedValue({ items: [] });
    renderScreen();
    expect(await screen.findByTestId("workflows-empty")).toBeInTheDocument();
  });

  it("lists runs with status and agent count", async () => {
    vi.spyOn(WorkforceService, "getRuns").mockResolvedValue({ items: [RUN] });
    renderScreen();
    const row = await screen.findByTestId("workflow-run-row");
    expect(row).toHaveTextContent("Lead gen workforce");
    expect(row).toHaveTextContent("Running");
    expect(row).toHaveTextContent("2 agents");
  });

  it("expands a run into task list, approval button, and final output", async () => {
    vi.spyOn(WorkforceService, "getRuns").mockResolvedValue({ items: [RUN] });
    vi.spyOn(WorkforceService, "getRunDetail").mockResolvedValue(DETAIL);
    renderScreen();

    await userEvent.click(await screen.findByText("Lead gen workforce"));

    await waitFor(() =>
      expect(screen.getByTestId("workflow-run-detail")).toBeInTheDocument(),
    );
    expect(screen.getAllByTestId("workflow-task-row")).toHaveLength(2);
    expect(screen.getByTestId("approve-task-button")).toBeInTheDocument();
    expect(screen.getByTestId("workflow-final-output")).toHaveTextContent(
      "FINAL REPORT",
    );
    expect(screen.getByTestId("workflow-event-log")).toHaveTextContent(
      "workflow_started",
    );
  });

  it("approving a task calls the API", async () => {
    vi.spyOn(WorkforceService, "getRuns").mockResolvedValue({ items: [RUN] });
    vi.spyOn(WorkforceService, "getRunDetail").mockResolvedValue(DETAIL);
    const approveSpy = vi
      .spyOn(WorkforceService, "approveTask")
      .mockResolvedValue(DETAIL.tasks[1]);
    renderScreen();

    await userEvent.click(await screen.findByText("Lead gen workforce"));
    await userEvent.click(await screen.findByTestId("approve-task-button"));

    await waitFor(() =>
      expect(approveSpy).toHaveBeenCalledWith("run-1", "t2"),
    );
  });

  it("pause action calls the API for a running workflow", async () => {
    vi.spyOn(WorkforceService, "getRuns").mockResolvedValue({ items: [RUN] });
    const actionSpy = vi
      .spyOn(WorkforceService, "runAction")
      .mockResolvedValue({ ...RUN, status: "PAUSED" });
    renderScreen();

    await userEvent.click(await screen.findByTitle("Pause"));
    await waitFor(() =>
      expect(actionSpy).toHaveBeenCalledWith("run-1", "pause"),
    );
  });
});
