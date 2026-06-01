import type { ReactNode } from "react";
import { Typography } from "#/ui/typography";
import { cn } from "#/utils/utils";

interface SectionHeaderProps {
  title: string;
  description?: string;
  actions?: ReactNode;
  className?: string;
}

/**
 * Header for a sub-section within a page (one level below `PageHeader`).
 *
 * Use for clusters like "Recent Agents" inside the Dashboard, or
 * "Connected Providers" inside Integrations.
 */
export function SectionHeader({
  title,
  description,
  actions,
  className,
}: SectionHeaderProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-2 mb-4 md:flex-row md:items-start md:justify-between",
        className,
      )}
    >
      <div className="flex flex-col gap-1 min-w-0">
        <Typography.H3 className="text-lg font-semibold leading-snug">
          {title}
        </Typography.H3>
        {description && (
          <Typography.Text className="text-sm text-basic">
            {description}
          </Typography.Text>
        )}
      </div>
      {actions && (
        <div className="flex items-center gap-2 flex-shrink-0">{actions}</div>
      )}
    </div>
  );
}
