import type { ReactNode } from "react";
import { cn } from "#/utils/utils";

interface TopBarProps {
  /** Leading area — typically breadcrumbs or a back affordance. */
  leading?: ReactNode;
  /** Centered area — typically the org switcher or a page title. */
  center?: ReactNode;
  /** Trailing area — typically notifications, status, or user controls. */
  trailing?: ReactNode;
  className?: string;
}

/**
 * Opt-in top-of-page horizontal chrome.
 *
 * The current `root-layout` does NOT render a topbar — pages flow
 * directly under the sidebar. `TopBar` is provided as a reusable
 * primitive so future surfaces (Workforce dashboard, Monitoring,
 * Deployments) can opt into a consistent topbar with leading/center/
 * trailing slots without each page re-rolling its own bar.
 *
 * Adopt incrementally on a per-route basis; do not retrofit existing
 * routes blindly.
 */
export function TopBar({ leading, center, trailing, className }: TopBarProps) {
  return (
    <div
      className={cn(
        "flex h-12 w-full items-center justify-between gap-4 border-b border-tertiary/40 bg-base px-6",
        className,
      )}
    >
      <div className="flex items-center gap-2 min-w-0">{leading}</div>
      <div className="flex items-center gap-2 min-w-0">{center}</div>
      <div className="flex items-center gap-2 min-w-0">{trailing}</div>
    </div>
  );
}
