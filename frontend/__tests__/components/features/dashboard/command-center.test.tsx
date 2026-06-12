import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createRoutesStub } from "react-router";
import { describe, expect, it } from "vitest";
import { renderWithProviders } from "../../../../test-utils";
import { CommandCenter } from "#/components/features/dashboard/command-center";

function renderCommandCenter() {
  const RouterStub = createRoutesStub([
    { path: "/", Component: CommandCenter },
    {
      path: "/workforce",
      Component: () => <div data-testid="builder-route" />,
    },
    { path: "/agents", Component: () => <div data-testid="agents-route" /> },
  ]);
  return renderWithProviders(<RouterStub initialEntries={["/"]} />);
}

describe("CommandCenter", () => {
  it("renders the workforce prompt and command cards", () => {
    renderCommandCenter();
    expect(screen.getByText("What would you like to build?")).toBeInTheDocument();
    expect(screen.getAllByTestId("command-card")).toHaveLength(6);
  });

  it("submits the objective to the workforce builder", async () => {
    renderCommandCenter();
    await userEvent.type(
      screen.getByTestId("command-center-objective"),
      "Build me a recruitment agency",
    );
    await userEvent.click(screen.getByTestId("command-center-build"));
    expect(await screen.findByTestId("builder-route")).toBeInTheDocument();
  });

  it("example chips navigate to the builder", async () => {
    renderCommandCenter();
    await userEvent.click(
      screen.getByText("Build me a recruitment agency"),
    );
    expect(await screen.findByTestId("builder-route")).toBeInTheDocument();
  });

  it("command cards navigate to their surfaces", async () => {
    renderCommandCenter();
    await userEvent.click(screen.getByText("Active Workforces"));
    expect(await screen.findByTestId("agents-route")).toBeInTheDocument();
  });
});
