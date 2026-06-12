import {
  GitBranch,
  GitMerge,
  Github,
  Gitlab,
  Hash,
  ListChecks,
  Server,
  Slack,
} from "lucide-react";
import type { IntegrationCatalogEntry } from "./types";

/**
 * Static catalog of Waspid integrations.
 *
 * The catalog is structural: it lists which connectors the Waspid
 * platform knows how to render. Real connection status for each
 * entry is resolved at runtime against:
 *   - useUserProviders()             → source-control connections
 *   - useConfig().feature_flags      → enterprise connector availability
 *   - useConfig().providers_configured → which OAuth clients are wired
 *
 * Adding a new connector here does NOT mean it is live — the status
 * resolver in `integrations-screen.tsx` decides that from real data.
 */
export const INTEGRATIONS_CATALOG: IntegrationCatalogEntry[] = [
  // ---- Source control -------------------------------------------------
  {
    id: "github",
    name: "GitHub",
    description: "Open and manage repositories, PRs, and issues from agents.",
    category: "source_control",
    icon: Github,
    managePath: "/settings/integrations",
  },
  {
    id: "gitlab",
    name: "GitLab",
    description: "Drive merge requests and project work on GitLab.",
    category: "source_control",
    icon: Gitlab,
    managePath: "/settings/integrations",
  },
  {
    id: "bitbucket",
    name: "Bitbucket",
    description: "Operate on Bitbucket repositories and pull requests.",
    category: "source_control",
    icon: GitBranch,
    managePath: "/settings/integrations",
  },
  {
    id: "bitbucket_data_center",
    name: "Bitbucket Data Center",
    description:
      "Self-hosted Bitbucket integration for enterprise deployments.",
    category: "source_control",
    icon: Server,
    managePath: "/settings/integrations",
    enterpriseOnly: true,
  },
  {
    id: "azure_devops",
    name: "Azure DevOps",
    description: "Manage Azure DevOps repositories and pipelines.",
    category: "source_control",
    icon: GitMerge,
    managePath: "/settings/integrations",
  },

  // ---- Productivity & messaging --------------------------------------
  {
    id: "slack",
    name: "Slack",
    description: "Trigger agents from Slack and receive run notifications.",
    category: "messaging",
    icon: Slack,
    managePath: "/settings/integrations",
    enterpriseOnly: true,
  },
  {
    id: "jira",
    name: "Jira",
    description: "Resolve and update Jira issues from agent runs.",
    category: "productivity",
    icon: ListChecks,
    managePath: "/settings/integrations",
    enterpriseOnly: true,
  },
  {
    id: "jira_dc",
    name: "Jira Data Center",
    description: "Self-hosted Jira integration for enterprise deployments.",
    category: "productivity",
    icon: ListChecks,
    managePath: "/settings/integrations",
    enterpriseOnly: true,
  },
  {
    id: "linear",
    name: "Linear",
    description: "Sync agent runs with Linear issues and cycles.",
    category: "productivity",
    icon: Hash,
    managePath: "/settings/integrations",
    enterpriseOnly: true,
  },
];

export const CATEGORY_LABELS: Record<
  IntegrationCatalogEntry["category"],
  string
> = {
  source_control: "Source control",
  productivity: "Productivity",
  messaging: "Messaging",
  tooling: "Tooling",
};
