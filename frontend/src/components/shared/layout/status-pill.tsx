// Waspid AI OS
import type { ReactNode } from "react";
import { cn } from "#/utils/utils";

export type StatusPillTone =
  | "info"
  | "success"
  | "warning"
  | "danger"
  | "neutral";

interface StatusPillProps {
  tone: StatusPillTone;
  /** Whether to render a small leading dot. Defaults to true. */
  withDot?: boolean;
  className?: string;
  children: ReactNode;
}

const TONE_CLASSES: Record<StatusPillTone, { pill: string; dot: string }> = {
  info: { pill: "bg-blue/15 text-blue", dot: "bg-blue" },
  success: { pill: "bg-success/15 text-success", dot: "bg-success" },
  warning: { pill: "bg-primary/15 text-primary", dot: "bg-primary" },
  danger: { pill: "bg-danger/15 text-danger", dot: "bg-danger" },
  neutral: {
    pill: "bg-tertiary/40 text-basic",
    dot: "bg-basic",
  },
};

/**
 * Generic status pill used across enterprise surfaces (Agents,
 * Workflows, Monitoring, Integrations, ReadinessCard).
 *
 * Tone is the abstract intent; the concrete color is driven by the
 * Waspid design tokens (--color-success, --color-primary,
 * --color-danger, --color-blue, --color-basic). Keeping tone-driven
 * means a future theme adjustment is one tokens.css change.
 */
export function StatusPill({
  tone,
  withDot = true,
  className,
  children,
}: StatusPillProps) {
  const { pill, dot } = TONE_CLASSES[tone];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-medium",
        pill,
        className,
      )}
    >
      {withDot && (
        <span aria-hidden className={cn("h-1.5 w-1.5 rounded-full", dot)} />
      )}
      {children}
    </span>
  );
}
