import type { ReactNode } from "react";
import { cn } from "#/utils/utils";
import { SectionHeader } from "./section-header";

interface SectionProps {
  /** Optional title. When supplied, renders a SectionHeader above the body. */
  title?: string;
  description?: string;
  actions?: ReactNode;
  /** Tag override — defaults to `<section>`. */
  as?: keyof Pick<JSX.IntrinsicElements, "section" | "div" | "article">;
  className?: string;
  bodyClassName?: string;
  children: ReactNode;
}

/**
 * A clustered region inside a page.
 *
 * `Section` pairs an optional `SectionHeader` with a body slot using
 * the standard rhythm. Pages compose multiple sections inside a
 * `PageShell` to organize content without re-inventing spacing.
 */
export function Section({
  title,
  description,
  actions,
  as: As = "section",
  className,
  bodyClassName,
  children,
}: SectionProps) {
  return (
    <As className={cn("flex flex-col", className)}>
      {title && (
        <SectionHeader
          title={title}
          description={description}
          actions={actions}
        />
      )}
      <div className={cn("flex flex-col gap-4", bodyClassName)}>{children}</div>
    </As>
  );
}
