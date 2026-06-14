// Waspid AI OS
import type { LucideIcon } from "lucide-react";
import type { StatusPillTone } from "#/components/shared/layout/status-pill";

/**
 * Waspid integrations domain types.
 *
 * A Waspid integration is an external system Waspid can connect to —
 * source control, productivity, messaging, observability, etc.
 *
 * `IntegrationStatus` is a small enum that captures the three real
 * states each catalog entry can resolve to:
 *
 *   - "connected"   → the user/org has linked credentials.
 *   - "available"   → the connector is configured server-side
 *                     (auth_url / OAuth flow ready) but not yet linked
 *                     by the current user.
 *   - "unavailable" → the connector is not configured for this
 *                     deployment (feature flag off, no OAuth client,
 *                     etc.). We render it so admins can see what's
 *                     possible, but we don't pretend it's live.
 */
export type IntegrationStatus = "connected" | "available" | "unavailable";

export type IntegrationCategory =
  | "source_control"
  | "productivity"
  | "messaging"
  | "tooling";

export interface IntegrationCatalogEntry {
  id: string;
  name: string;
  description: string;
  category: IntegrationCategory;
  icon: LucideIcon;
  /** Deep-link to the existing settings surface that manages this connector. */
  managePath: string;
  /**
   * True if the connector is enterprise-only (requires SaaS / enterprise
   * deployment + the relevant feature flag). Used to filter the catalog
   * in OSS deployments.
   */
  enterpriseOnly?: boolean;
}

export const STATUS_TONE: Record<IntegrationStatus, StatusPillTone> = {
  connected: "success",
  available: "info",
  unavailable: "neutral",
};

export const STATUS_LABEL: Record<IntegrationStatus, string> = {
  connected: "Connected",
  available: "Available",
  unavailable: "Not configured",
};
