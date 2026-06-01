import {
  Activity,
  Bot,
  Building2,
  LayoutDashboard,
  Plug,
  Rocket,
  Settings as SettingsIcon,
  Workflow,
  type LucideIcon,
} from "lucide-react";

/**
 * Waspid primary navigation — the enterprise IA exposed in the app shell.
 *
 * The list is the SINGLE SOURCE OF TRUTH for top-level navigation: the
 * sidebar renders directly from this config. Adding a new top-level
 * surface is a one-line change here once the route + page exist.
 *
 * `status` is intentional:
 *   - "active"  → the destination route exists today.
 *   - "planned" → the surface is part of the IA but no route is wired
 *                 yet. The sidebar shows it disabled with a "Soon" badge.
 *                 NO placeholder route is added — clicking does nothing.
 *
 * Only flip "planned" → "active" once a real destination page is built.
 * Do NOT add a fake page just to satisfy a nav item.
 */
export type NavStatus = "active" | "planned";

export interface NavItem {
  id: string;
  label: string;
  description: string;
  icon: LucideIcon;
  status: NavStatus;
  /** Destination route. Required when status === "active". */
  to: string | null;
}

export interface NavGroup {
  id: string;
  label: string;
  items: NavItem[];
}

export const PRIMARY_NAV: NavGroup[] = [
  {
    id: "workforce",
    label: "Workforce",
    items: [
      {
        id: "dashboard",
        label: "Operations Center",
        description: "Workforce overview, readiness, and recent operations",
        icon: LayoutDashboard,
        status: "active",
        to: "/",
      },
      {
        id: "agents",
        label: "Agents",
        description: "Build, configure, and deploy AI agents",
        icon: Bot,
        status: "active",
        to: "/agents",
      },
      {
        id: "workflows",
        label: "Workflows",
        description: "Orchestrate multi-agent automations and long-running operations",
        icon: Workflow,
        status: "active",
        to: "/workflows",
      },
    ],
  },
  {
    id: "operations",
    label: "Operations",
    items: [
      {
        id: "monitoring",
        label: "Monitoring",
        description: "Realtime execution, audit trails, and platform health",
        icon: Activity,
        status: "active",
        to: "/monitoring",
      },
      {
        id: "deployments",
        label: "Deployments",
        description: "Environments, rollouts, and infra",
        icon: Rocket,
        status: "planned",
        to: null,
      },
    ],
  },
  {
    id: "platform",
    label: "Platform",
    items: [
      {
        id: "integrations",
        label: "Integrations",
        description: "Connectors, APIs, and webhooks",
        icon: Plug,
        status: "active",
        to: "/integrations",
      },
      {
        id: "organization",
        label: "Organization",
        description: "Members, roles, and org settings",
        icon: Building2,
        status: "active",
        to: "/settings/org",
      },
      {
        id: "settings",
        label: "Settings",
        description: "Personal and workspace preferences",
        icon: SettingsIcon,
        status: "active",
        to: "/settings",
      },
    ],
  },
];

/**
 * Resolve which nav item is active for a given pathname.
 *
 * Uses "segment-boundary prefix matching" — a nav item is considered
 * active when the pathname equals its `to` or starts with `to + "/"`.
 * This prevents accidental matches like `/settings/org-defaults`
 * highlighting the Organization item (whose `to` is `/settings/org`).
 *
 * When multiple nav items match, the one with the longest `to` wins,
 * so deeper surfaces (Integrations, Organization) take precedence over
 * the general Settings entry.
 */
export function resolveActiveNavId(
  pathname: string,
  groups: NavGroup[] = PRIMARY_NAV,
): string | null {
  let bestId: string | null = null;
  let bestLength = -1;

  for (const group of groups) {
    for (const item of group.items) {
      if (item.status !== "active" || item.to == null) continue;
      const isMatch =
        item.to === "/"
          ? pathname === "/"
          : pathname === item.to || pathname.startsWith(`${item.to}/`);
      if (isMatch && item.to.length > bestLength) {
        bestId = item.id;
        bestLength = item.to.length;
      }
    }
  }

  return bestId;
}
