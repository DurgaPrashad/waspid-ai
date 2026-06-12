import { Link } from "react-router";
import { ArrowUpRight } from "lucide-react";
import { StatusPill } from "#/components/shared/layout/status-pill";
import { cn } from "#/utils/utils";
import {
  STATUS_LABEL,
  STATUS_TONE,
  type IntegrationCatalogEntry,
  type IntegrationStatus,
} from "./types";

interface IntegrationCardProps {
  entry: IntegrationCatalogEntry;
  status: IntegrationStatus;
}

/**
 * Card surface for ONE Waspid integration catalog entry.
 *
 * Renders the connector identity (icon + name + description), its
 * resolved connection status (driven by real hooks at the screen
 * level), and a deep-link to the settings page that manages the
 * connection.
 */
export function IntegrationCard({ entry, status }: IntegrationCardProps) {
  const Icon = entry.icon;
  const tone = STATUS_TONE[status];
  const label = STATUS_LABEL[status];

  return (
    <Link
      to={entry.managePath}
      className={cn(
        "group flex flex-col gap-3 rounded-xl border border-tertiary/40 bg-base-secondary/40 p-5",
        "transition-colors hover:border-tertiary/60",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <span
            aria-hidden
            className="flex h-10 w-10 items-center justify-center rounded-lg bg-base text-content"
          >
            <Icon className="h-5 w-5" />
          </span>
          <div className="flex flex-col min-w-0">
            <span className="truncate text-sm font-semibold text-content">
              {entry.name}
            </span>
            <span className="truncate text-xs text-basic">
              {entry.description}
            </span>
          </div>
        </div>
        <StatusPill tone={tone}>{label}</StatusPill>
      </div>

      <span className="inline-flex items-center gap-1 self-end text-xs font-medium text-content/80 group-hover:text-content">
        Manage
        <ArrowUpRight className="h-3.5 w-3.5" aria-hidden />
      </span>
    </Link>
  );
}
