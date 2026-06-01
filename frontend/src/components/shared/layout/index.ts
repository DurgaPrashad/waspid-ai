/**
 * Waspid shared layout primitives — the application-shell building
 * blocks that future feature pages compose with.
 *
 *   PageShell        — outer container with optional TopBar/PageHeader.
 *   PageHeader       — standardized page title + subtitle + actions.
 *   PageContainer    — max-width + padding rhythm.
 *   Section          — clustered region with optional SectionHeader.
 *   SectionHeader    — sub-section title + description + actions.
 *   TopBar           — opt-in horizontal app-level chrome.
 *
 * These primitives are intentionally additive: no existing route is
 * migrated to use them. Adopt incrementally, page-by-page, with
 * validation between each migration.
 */
export { PageShell } from "./page-shell";
export { PageHeader } from "./page-header";
export { PageContainer } from "./page-container";
export { Section } from "./section";
export { SectionHeader } from "./section-header";
export { TopBar } from "./top-bar";
