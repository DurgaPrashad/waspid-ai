import { Link } from "react-router";
import { ArrowUpRight, type LucideIcon } from "lucide-react";
import { cn } from "#/utils/utils";
import { Typography } from "#/ui/typography";

export type ReadinessStatus = "ok" | "warning" | "needs-setup";

interface ReadinessCardProps {
  icon: LucideIcon;
  title: string;
  /**
   * Single-line summary of the real state — e.g. the configured model
   * name, the count of connected providers, the user's email address.
   * NO fabricated numbers, no fake metrics.
   */
  detail: string;
  status: ReadinessStatus;
  /** Status label shown in the status pill. */
  statusLabel: string;
  /** Optional deep-link to the settings surface that owns this concern. */
  cta?: {
    label: string;
    to: string;
  };
}

const STATUS_CONFIG: Record<
  ReadinessStatus,
  { dot: string; pill: string; label: string }
> = {
  ok: {
    dot: "bg-success",
    pill: "bg-success/15 text-success",
    label: "Ready",
  },
  warning: {
    dot: "bg-primary",
    pill: "bg-primary/15 text-primary",
    label: "Action recommended",
  },
  "needs-setup": {
    dot: "bg-danger",
    pill: "bg-danger/15 text-danger",
    label: "Needs setup",
  },
};

/**
 * Visual primitive for the Workforce Dashboard's Platform Readiness
 * section. Each card surfaces ONE real, verifiable piece of system
 * state — never a fabricated metric.
 *
 * Sources of `detail` and `status` are always real application state:
 *   - settings.llm_api_key_set / llm_model
 *   - useUserProviders().providers
 *   - settings.email_verified / email
 *   - settings.mcp_config entries
 */
export function ReadinessCard({
  icon: Icon,
  title,
  detail,
  status,
  statusLabel,
  cta,
}: ReadinessCardProps) {
  const config = STATUS_CONFIG[status];

  return (
    <div
      className={cn(
        "flex flex-col gap-4 rounded-xl border border-tertiary/40 bg-base-secondary/40 p-5",
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
            <Typography.Text className="text-sm font-semibold text-content">
              {title}
            </Typography.Text>
            <span className="truncate text-xs text-basic">{detail}</span>
          </div>
        </div>
        <span
          className={cn(
            "shrink-0 inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-medium",
            config.pill,
          )}
        >
          <span
            aria-hidden
            className={cn("h-1.5 w-1.5 rounded-full", config.dot)}
          />
          {statusLabel || config.label}
        </span>
      </div>

      {cta && (
        <Link
          to={cta.to}
          className={cn(
            "inline-flex items-center gap-1.5 self-start text-xs font-medium",
            "text-content/80 hover:text-content underline-offset-2 hover:underline",
          )}
        >
          {cta.label}
          <ArrowUpRight className="h-3.5 w-3.5" aria-hidden />
        </Link>
      )}
    </div>
  );
}
