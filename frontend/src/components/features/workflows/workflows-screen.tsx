import { Link } from "react-router";
import { Workflow as WorkflowIcon, Zap } from "lucide-react";
import {
  PageShell,
  PageHeader,
  Section,
} from "#/components/shared/layout";
import { ENABLE_AUTOMATIONS } from "#/utils/feature-flags";

/**
 * Waspid Workflows surface.
 *
 * Workflows are an orchestration primitive that does not yet have a
 * backend resource. This surface therefore renders an HONEST
 * not-yet-available state — no fabricated workflow list, no synthetic
 * run history.
 *
 * If the `ENABLE_AUTOMATIONS` feature flag is on the surface routes
 * the user to the existing automations entry instead of pretending
 * Workflows is the same thing. When the workflows backend ships, the
 * empty state is replaced by the real list; the page shell, route,
 * and type contract (workflows/types.ts) are already in place.
 */
export function WorkflowsScreen() {
  const automationsEnabled = ENABLE_AUTOMATIONS();

  return (
    <div data-testid="workflows-screen" className="h-full">
      <PageShell
        width="wide"
        header={
          <PageHeader
            eyebrow="Operations"
            title="Workflows"
            subtitle="Orchestrate multi-agent automations and long-running operations."
          />
        }
      >
        <Section title="Workflow runs" description="Active and historical orchestration runs across this workspace.">
          <div
            data-testid="workflows-empty"
            className="rounded-xl border border-dashed border-tertiary/40 bg-base-secondary/20 px-6 py-12 text-center"
          >
            <WorkflowIcon
              className="mx-auto mb-3 h-8 w-8 text-basic"
              aria-hidden
            />
            <p className="text-sm font-medium text-content">
              Workflows are not yet wired up on this deployment.
            </p>
            <p className="mt-1 mx-auto max-w-md text-xs text-basic">
              When the workflows runtime is connected, this surface will list
              active runs, trigger types (schedule, webhook, manual), and
              step-by-step execution history. The type contract for that data
              already lives in <code>features/workflows/types.ts</code>.
            </p>

            {automationsEnabled && (
              <Link
                to="/"
                className="mt-5 inline-flex items-center gap-1.5 rounded-md border border-tertiary/50 px-3 py-1.5 text-xs font-medium text-content/90 hover:border-tertiary/70 hover:text-content"
              >
                <Zap className="h-3.5 w-3.5" aria-hidden />
                Open Automations
              </Link>
            )}
          </div>
        </Section>
      </PageShell>
    </div>
  );
}
