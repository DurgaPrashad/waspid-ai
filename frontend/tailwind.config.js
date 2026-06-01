/** @type {import('tailwindcss').Config} */
import typography from "@tailwindcss/typography";

/*
 * Waspid Tailwind config.
 *
 * Design tokens (colors, typography, radii) now live in
 * frontend/src/styles/tokens.css and are consumed via Tailwind 4's
 * @theme mechanism. The previous `modal.*` and `org.*` color objects
 * defined here have moved to that file as --color-modal-* and
 * --color-org-* tokens, which Tailwind auto-exposes as the same
 * `bg-modal-background`, `text-org-text` (etc.) utility class names.
 *
 * Keep this file plugin-only.
 */

export default {
  darkMode: "class",
  plugins: [typography],
};
