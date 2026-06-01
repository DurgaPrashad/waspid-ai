import type { ReactNode } from "react";
import { Typography } from "#/ui/typography";
import { cn } from "#/utils/utils";

interface PageHeaderProps {
  /**
   * Short uppercase context label rendered above the title — e.g.
   * "Workforce" on the Agents page, "Operations" on Monitoring.
   * Optional; omit for a flush-aligned title.
   */
  eyebrow?: string;
  title: string;
  /** Single-paragraph description displayed under the title. */
  subtitle?: string;
  /** Action slot (typically <BrandButton/>s) right-aligned on desktop. */
  actions?: ReactNode;
  /**
   * If true, the header renders without a bottom divider — use for
   * pages where the next section already provides visual separation.
   */
  flush?: boolean;
  className?: string;
}

/**
 * Standardized header for top-level feature pages.
 *
 * Renders the title hierarchy + optional actions in the same rhythm
 * across every future surface (Agents, Workflows, Monitoring, etc.).
 * Eyebrow + subtitle are both optional; pages can use as much or as
 * little chrome as they need.
 */
export function PageHeader({
  eyebrow,
  title,
  subtitle,
  actions,
  flush = false,
  className,
}: PageHeaderProps) {
  return (
    <header
      className={cn(
        "flex flex-col gap-4 pb-6 md:flex-row md:items-end md:justify-between",
        !flush && "border-b border-tertiary/40 mb-8",
        className,
      )}
    >
      <div className="flex flex-col gap-1.5 min-w-0">
        {eyebrow && (
          <span className="text-xs font-medium uppercase tracking-[0.18em] text-primary/90">
            {eyebrow}
          </span>
        )}
        <Typography.H1 className="text-2xl font-semibold leading-tight md:text-3xl">
          {title}
        </Typography.H1>
        {subtitle && (
          <Typography.Text className="max-w-3xl text-sm text-basic">
            {subtitle}
          </Typography.Text>
        )}
      </div>
      {actions && (
        <div className="flex items-center gap-2 flex-shrink-0">{actions}</div>
      )}
    </header>
  );
}
