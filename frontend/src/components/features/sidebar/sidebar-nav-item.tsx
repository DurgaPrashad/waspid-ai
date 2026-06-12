import { NavLink } from "react-router";
import { StyledTooltip } from "#/components/shared/buttons/styled-tooltip";
import { cn } from "#/utils/utils";
import type { NavItem } from "#/constants/navigation";

interface SidebarNavItemProps {
  item: NavItem;
  isActive: boolean;
}

/**
 * One row in the primary sidebar nav.
 *
 * Visual contract:
 *   - Icon-only (the sidebar is 75px wide).
 *   - Tooltip on hover shows the label + short description, and the
 *     "Coming soon" hint for planned items.
 *   - Active items show a gold left-edge accent and brighter icon.
 *   - Planned items render as a non-interactive button with reduced
 *     opacity and a small "Soon" indicator dot.
 */
export function SidebarNavItem({ item, isActive }: SidebarNavItemProps) {
  const Icon = item.icon;
  const isPlanned = item.status === "planned";

  const tooltipContent = (
    <div className="flex flex-col gap-0.5 max-w-[220px]">
      <div className="flex items-center gap-2">
        <span className="font-medium text-sm">{item.label}</span>
        {isPlanned && (
          <span className="text-[10px] uppercase tracking-wide rounded-sm px-1.5 py-0.5 bg-primary/15 text-primary">
            Soon
          </span>
        )}
      </div>
      <span className="text-xs text-neutral-600">{item.description}</span>
    </div>
  );

  const baseClasses = cn(
    "relative flex h-10 w-10 items-center justify-center rounded-md transition-colors",
    "outline-none focus-visible:ring-2 focus-visible:ring-primary/60",
  );

  const accent = isActive ? (
    <span
      aria-hidden
      className="absolute left-[-12px] top-1.5 h-7 w-[3px] rounded-r-full bg-primary"
    />
  ) : null;

  const iconNode = (
    <Icon
      aria-hidden
      className={cn(
        "h-5 w-5",
        isActive ? "text-content" : isPlanned ? "text-basic/60" : "text-basic",
        !isPlanned && "group-hover:text-content",
      )}
    />
  );

  if (isPlanned || item.to == null) {
    return (
      <StyledTooltip content={tooltipContent} placement="right">
        <button
          type="button"
          disabled
          aria-disabled
          aria-label={`${item.label} — coming soon`}
          className={cn(
            baseClasses,
            "group cursor-not-allowed opacity-60 hover:bg-base-secondary/40",
          )}
        >
          {iconNode}
          <span
            aria-hidden
            className="absolute right-1 top-1 h-1.5 w-1.5 rounded-full bg-primary/70"
          />
        </button>
      </StyledTooltip>
    );
  }

  return (
    <StyledTooltip content={tooltipContent} placement="right">
      <NavLink
        to={item.to}
        aria-label={item.label}
        aria-current={isActive ? "page" : undefined}
        className={cn(
          baseClasses,
          "group hover:bg-base-secondary",
          isActive && "bg-base-secondary",
        )}
      >
        {accent}
        {iconNode}
      </NavLink>
    </StyledTooltip>
  );
}
