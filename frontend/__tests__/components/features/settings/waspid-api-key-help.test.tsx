import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { WaspidApiKeyHelp } from "#/components/features/settings/waspid-api-key-help";

describe("WaspidApiKeyHelp", () => {
  it("renders the help link with the provided testId", () => {
    render(<WaspidApiKeyHelp testId="waspid-api-key-help" />);

    expect(screen.getByTestId("waspid-api-key-help")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "SETTINGS$NAV_API_KEYS" }),
    ).toHaveAttribute("href", "/settings/api-keys");
  });

  it("renders the billing info paragraph with the pricing-details link", () => {
    render(<WaspidApiKeyHelp testId="waspid-api-key-help" />);

    expect(screen.getByText("SETTINGS$LLM_BILLING_INFO")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "SETTINGS$SEE_PRICING_DETAILS" }),
    ).toHaveAttribute(
      "href",
      "https://github.com/DurgaPrashad/waspid-ai/blob/main/docs/INSTALL.md",
    );
  });
});
