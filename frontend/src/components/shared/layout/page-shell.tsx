import type { ReactNode } from "react";
import { cn } from "#/utils/utils";
import { PageContainer } from "./page-container";

interface PageShellProps {
  /** Optional top-of-page chrome (typically a `<TopBar />`). */
  topBar?: ReactNode;
  /** Optional `<PageHeader />`. */
  header?: ReactNode;
  /** Container width passed through to the inner PageContainer. */
  width?: "narrow" | "default" | "wide" | "full";
  className?: string;
  contentClassName?: string;
  children: ReactNode;
}

/**
 * Top-level shell for a Waspid feature page.
 *
 * Composes the standard chrome (optional `TopBar` + optional
 * `PageHeader`) with a `PageContainer` body. Pages adopt this shell
 * to inherit consistent spacing, max-widths, and scroll behavior
 * across the platform.
 *
 * Example:
 *   <PageShell
 *     header={<PageHeader title="Workforce" subtitle="..." />}
 *   >
 *     <Section title="Recent activity">...</Section>
 *   </PageShell>
 */
export function PageShell({
  topBar,
  header,
  width = "default",
  className,
  contentClassName,
  children,
}: PageShellProps) {
  return (
    <div className={cn("flex h-full flex-col", className)}>
      {topBar}
      <div className="flex-1 overflow-y-auto custom-scrollbar-always">
        <PageContainer width={width}>
          <div className={cn("flex flex-col py-8", contentClassName)}>
            {header}
            <div className="flex flex-col gap-10">{children}</div>
          </div>
        </PageContainer>
      </div>
    </div>
  );
}
