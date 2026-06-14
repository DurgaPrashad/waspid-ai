// Waspid AI OS
import { useLocation } from "react-router";
import { SidebarNavItem } from "./sidebar-nav-item";
import { resolveActiveNavId, type NavGroup } from "#/constants/navigation";

interface SidebarNavGroupProps {
  group: NavGroup;
  /**
   * Whether to render a thin divider above this group. The first group
   * in the sidebar suppresses it; subsequent groups render the divider
   * so the IA reads as three distinct clusters at a glance.
   */
  showDivider?: boolean;
}

/**
 * A single cluster in the sidebar nav (e.g. "Workforce", "Operations",
 * "Platform"). Renders an ARIA-labelled group of nav items plus an
 * optional top divider to visually separate clusters in the
 * icon-only sidebar.
 *
 * The cluster label is rendered as `<span>` with `sr-only` so screen
 * readers announce the group, while the sighted visual cue is the
 * spacing + divider — keeps the 75px sidebar from looking cluttered.
 */
export function SidebarNavGroup({ group, showDivider }: SidebarNavGroupProps) {
  const { pathname } = useLocation();
  const activeId = resolveActiveNavId(pathname);

  return (
    <div
      role="group"
      aria-labelledby={`sidebar-nav-group-${group.id}`}
      className="flex flex-col items-center gap-1"
    >
      {showDivider && (
        <span aria-hidden className="my-2 h-px w-6 bg-tertiary/60" />
      )}
      <span id={`sidebar-nav-group-${group.id}`} className="sr-only">
        {group.label}
      </span>
      {group.items.map((item) => (
        <SidebarNavItem
          key={item.id}
          item={item}
          isActive={item.id === activeId}
        />
      ))}
    </div>
  );
}
