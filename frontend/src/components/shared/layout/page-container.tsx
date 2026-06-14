// Waspid AI OS
import type { ReactNode } from "react";
import { cn } from "#/utils/utils";

type ContainerWidth = "narrow" | "default" | "wide" | "full";

interface PageContainerProps {
  /** Controls horizontal max-width. */
  width?: ContainerWidth;
  /** Disable the default horizontal padding (caller takes over). */
  noPadding?: boolean;
  className?: string;
  children: ReactNode;
}

const WIDTH_CLASSES: Record<ContainerWidth, string> = {
  narrow: "max-w-3xl",
  default: "max-w-6xl",
  wide: "max-w-screen-2xl",
  full: "max-w-none",
};

/**
 * Horizontal-bounded content wrapper for feature pages.
 *
 * Owns the consistent max-width + outer padding behavior so every
 * future page can drop into the shell at the right rhythm without
 * hand-rolling its own layout numbers.
 */
export function PageContainer({
  width = "default",
  noPadding = false,
  className,
  children,
}: PageContainerProps) {
  return (
    <div
      className={cn(
        "mx-auto w-full",
        WIDTH_CLASSES[width],
        !noPadding && "px-6 lg:px-10",
        className,
      )}
    >
      {children}
    </div>
  );
}
