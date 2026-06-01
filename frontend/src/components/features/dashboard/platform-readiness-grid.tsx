import { Cpu, GitBranch, Mail, Wrench } from "lucide-react";
import { useConfig } from "#/hooks/query/use-config";
import { useSettings } from "#/hooks/query/use-settings";
import { useUserProviders } from "#/hooks/use-user-providers";
import { ReadinessCard, type ReadinessStatus } from "./readiness-card";

type Card = {
  key: string;
  icon: typeof Cpu;
  title: string;
  detail: string;
  status: ReadinessStatus;
  statusLabel: string;
  cta?: { label: string; to: string };
};

/**
 * Platform Readiness grid.
 *
 * Every card here is derived from REAL application state via the
 * existing React Query hooks:
 *   - useSettings()       → llm_api_key_set, llm_model, email,
 *                           email_verified, mcp_config
 *   - useConfig()         → app_mode, feature_flags
 *   - useUserProviders()  → list of connected git providers
 *
 * No fabricated counts, no mock data, no fake services. Cards are
 * conditionally rendered based on mode (SaaS-only signals don't
 * appear in OSS) so the grid stays honest in every deployment.
 */
export function PlatformReadinessGrid() {
  const { data: config } = useConfig();
  const { data: settings, isFetching: isFetchingSettings } = useSettings();
  const { providers, isLoadingSettings: isLoadingProviders } = useUserProviders();

  const isSaas = config?.app_mode === "saas";
  const isLoading = isFetchingSettings || isLoadingProviders;

  const cards: Card[] = [];

  // ---- Model card (always shown) -------------------------------------
  const hasModel = Boolean(settings?.llm_api_key_set);
  cards.push({
    key: "model",
    icon: Cpu,
    title: "Language model",
    detail: hasModel
      ? settings?.llm_model || "Configured"
      : "No model configured",
    status: hasModel ? "ok" : "needs-setup",
    statusLabel: hasModel ? "Ready" : "Needs setup",
    cta: hasModel
      ? { label: "Manage model", to: "/settings" }
      : { label: "Configure", to: "/settings" },
  });

  // ---- Git provider card (always shown — drives repo + task surfaces) -
  const providerCount = providers.length;
  cards.push({
    key: "providers",
    icon: GitBranch,
    title: "Source control",
    detail:
      providerCount > 0
        ? `${providerCount} provider${providerCount === 1 ? "" : "s"} connected · ${providers.join(", ")}`
        : "No source-control provider connected",
    status: providerCount > 0 ? "ok" : "needs-setup",
    statusLabel: providerCount > 0 ? "Ready" : "Needs setup",
    cta: { label: "Manage integrations", to: "/settings/integrations" },
  });

  // ---- MCP tool connections (always shown) ---------------------------
  // mcp_config holds the structured MCP server config (sse/stdio/shttp
  // transports). Count concrete entries across the three arrays.
  const mcpServerCount =
    (settings?.mcp_config?.sse_servers?.length ?? 0) +
    (settings?.mcp_config?.stdio_servers?.length ?? 0) +
    (settings?.mcp_config?.shttp_servers?.length ?? 0);
  cards.push({
    key: "mcp",
    icon: Wrench,
    title: "Tool connections",
    detail:
      mcpServerCount > 0
        ? `${mcpServerCount} MCP server${mcpServerCount === 1 ? "" : "s"} configured`
        : "No MCP servers configured",
    status: mcpServerCount > 0 ? "ok" : "warning",
    statusLabel: mcpServerCount > 0 ? "Ready" : "Optional",
    cta: { label: "Configure tools", to: "/settings/mcp" },
  });

  // ---- Email verified (SaaS only — OSS has no email concept) ---------
  if (isSaas) {
    const verified = settings?.email_verified === true;
    cards.push({
      key: "email",
      icon: Mail,
      title: "Account email",
      detail:
        settings?.email && settings.email.length > 0
          ? settings.email
          : "Email not yet set",
      status: verified ? "ok" : "warning",
      statusLabel: verified ? "Verified" : "Unverified",
      cta: { label: "Account settings", to: "/settings/user" },
    });
  }

  // Loading skeleton — render placeholder cards with neutral copy until
  // real settings/providers resolve. Avoids showing "Needs setup" on a
  // freshly-mounted dashboard before the data has come back.
  if (isLoading && !settings) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div
            key={i}
            className="h-[112px] rounded-xl border border-tertiary/30 bg-base-secondary/30 animate-pulse"
          />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {cards.map((card) => (
        <ReadinessCard
          key={card.key}
          icon={card.icon}
          title={card.title}
          detail={card.detail}
          status={card.status}
          statusLabel={card.statusLabel}
          cta={card.cta}
        />
      ))}
    </div>
  );
}
