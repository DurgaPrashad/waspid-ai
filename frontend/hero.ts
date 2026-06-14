// Waspid AI OS
import { heroui } from "@heroui/react";

/*
 * Waspid HeroUI theme.
 *
 * The HeroUI "primary" now resolves through --color-primary (defined
 * in frontend/src/styles/tokens.css), unifying it with the Tailwind
 * primary used elsewhere in the app. Previously HeroUI primary was a
 * hard-coded blue (#4465DB) that contradicted the gold Tailwind
 * primary — Phase 5 consolidation eliminates that conflict.
 *
 * Layout radii mirror the --radius-small / --radius-large tokens.
 */
export default heroui({
  defaultTheme: "dark",
  layout: {
    radius: {
      small: "5px",
      large: "20px",
    },
  },
  themes: {
    dark: {
      colors: {
        primary: "var(--color-primary)",
      },
    },
  },
});
