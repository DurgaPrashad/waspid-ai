import { useMemo } from "react";
import { useConfig } from "#/hooks/query/use-config";
import { useUserProviders } from "#/hooks/use-user-providers";
import { PageShell, PageHeader, Section } from "#/components/shared/layout";
import { INTEGRATIONS_CATALOG, CATEGORY_LABELS } from "./integrations-catalog";
import { IntegrationCard } from "./integration-card";
import { HubSection } from "./hub-section";
import type { IntegrationCatalogEntry, IntegrationStatus } from "./types";

/**
 * Waspid Integrations surface.
 *
 * Top-level promotion of the integrations IA. The page resolves the
 * status of each catalog entry from REAL hooks:
 *
 *   - useUserProviders().providers      → which source-control
 *                                         providers the current user
 *                                         has tokens for.
 *   - useConfig().providers_configured  → which OAuth clients the
 *                                         deployment has registered.
 *   - useConfig().feature_flags         → which enterprise connectors
 *                                         (Slack/Jira/Jira DC/Linear)
 *                                         are wired on this server.
 *
 * No fake "12 events/min" counts. No simulated connection toggles.
 * Clicking a card deep-links to the existing settings surface that
 * actually manages the connection.
 */
export function IntegrationsScreen() {
  const { data: config } = useConfig();
  const { providers } = useUserProviders();

  const resolveStatus = useMemo(() => {
    const connected = new Set<string>(providers ?? []);
    const oauthConfigured = new Set<string>(config?.providers_configured ?? []);
    const flags = config?.feature_flags;
    const isSaas = config?.app_mode === "saas";

    return (entry: IntegrationCatalogEntry): IntegrationStatus => {
      // Source control: status comes from token presence + OAuth wiring.
      if (entry.category === "source_control") {
        if (connected.has(entry.id)) return "connected";
        if (oauthConfigured.has(entry.id)) return "available";
        return "unavailable";
      }

      // Enterprise messaging / productivity connectors are flag-gated.
      if (entry.enterpriseOnly && !isSaas) return "unavailable";

      switch (entry.id) {
        case "slack":
          // Slack is enterprise; presence is governed by enterprise config,
          // not a single flag. Best-effort: surface as "available" in SaaS.
          return isSaas ? "available" : "unavailable";
        case "jira":
          return flags?.enable_jira ? "available" : "unavailable";
        case "jira_dc":
          return flags?.enable_jira_dc ? "available" : "unavailable";
        case "linear":
          return flags?.enable_linear ? "available" : "unavailable";
        default:
          return "unavailable";
      }
    };
  }, [providers, config]);

  const visibleCatalog = useMemo(() => {
    const isSaas = config?.app_mode === "saas";
    return INTEGRATIONS_CATALOG.filter(
      (entry) => isSaas || !entry.enterpriseOnly,
    );
  }, [config?.app_mode]);

  const grouped = useMemo(() => {
    const map = new Map<
      IntegrationCatalogEntry["category"],
      IntegrationCatalogEntry[]
    >();
    for (const entry of visibleCatalog) {
      const bucket = map.get(entry.category) ?? [];
      bucket.push(entry);
      map.set(entry.category, bucket);
    }
    return Array.from(map.entries());
  }, [visibleCatalog]);

  return (
    <div data-testid="integrations-screen" className="h-full">
      <PageShell
        width="wide"
        header={
          <PageHeader
            eyebrow="Platform"
            title="Integrations"
            subtitle="Connect Waspid to your source control, productivity, and messaging systems."
          />
        }
      >
        {grouped.map(([category, entries]) => (
          <Section
            key={category}
            title={CATEGORY_LABELS[category]}
            description="Status reflects real connection state for this workspace."
          >
            <div
              data-testid={`integrations-category-${category}`}
              className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3"
            >
              {entries.map((entry) => (
                <IntegrationCard
                  key={entry.id}
                  entry={entry}
                  status={resolveStatus(entry)}
                />
              ))}
            </div>
          </Section>
        ))}

        <Section
          title="Integration Hub"
          description="Connected accounts, the tool registry, and tool-call activity. Workflow actions and agents use these connections to act on external systems."
        >
          <HubSection />
        </Section>
      </PageShell>
    </div>
  );
}
