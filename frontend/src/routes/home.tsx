// Waspid AI OS
import React from "react";
import { PrefetchPageLinks } from "react-router";
import { RepoConnector } from "#/components/features/home/repo-connector";
import { NewConversation } from "#/components/features/home/new-conversation/new-conversation";
import { RecentConversations } from "#/components/features/home/recent-conversations/recent-conversations";
import { TaskSuggestions } from "#/components/features/home/tasks/task-suggestions";
import { HomepageCTA } from "#/components/features/home/homepage-cta";
import { PlatformReadinessGrid } from "#/components/features/dashboard/platform-readiness-grid";
import { CommandCenter } from "#/components/features/dashboard/command-center";
import { PageShell, PageHeader, Section } from "#/components/shared/layout";
import { useAppMode } from "#/hooks/use-app-mode";
import { isCTADismissed } from "#/utils/local-storage";
import type { GitRepository } from "#/types/git";

/**
 * Waspid Operations Center — the `/` surface.
 *
 * The enterprise AI workforce control center. Composes the app-shell
 * primitives (`PageShell`, `PageHeader`, `Section`) with the existing
 * real-data feature components (`RepoConnector`, `NewConversation`,
 * `RecentConversations`, `TaskSuggestions`) and the new
 * `PlatformReadinessGrid`.
 *
 * Every signal on this page derives from REAL application state:
 *   - Platform readiness  ← useSettings / useConfig / useUserProviders
 *   - Source control      ← provider_tokens_set (settings)
 *   - Recent activity     ← usePaginatedConversations
 *   - Suggested work      ← useSuggestedTasks (filtered by selected repo)
 *
 * No fake metrics, no placeholder agents, no fabricated workflows.
 * Surfaces that don't have backing data are not on this page — they
 * are reached from the sidebar's "Soon" nav items once their real
 * routes ship.
 */
export default function HomeScreen() {
  const { isEnterpriseCloud } = useAppMode();
  const [selectedRepo, setSelectedRepo] = React.useState<GitRepository | null>(
    null,
  );
  const [shouldShowCTA, setShouldShowCTA] = React.useState(
    () => !isCTADismissed("homepage"),
  );

  return (
    <>
      <PrefetchPageLinks page="/conversations/:conversationId" />

      <div data-testid="home-screen" className="h-full">
        <PageShell
          width="wide"
          header={
            <PageHeader
              eyebrow="Enterprise AI Workforce Operating System"
              title="Workforce Command Center"
              subtitle="Build, deploy, and orchestrate AI workers for enterprise operations — agents, workflows, integrations, and monitoring in one control plane."
            />
          }
        >
          <CommandCenter />

          <Section
            title="Platform readiness"
            description="Live system state derived from your connected services and configuration."
          >
            <PlatformReadinessGrid />
          </Section>

          <Section
            title="Direct agent dispatch"
            description="Run a single agent on a repository task — the unit operation underneath every workforce."
          >
            <div
              data-testid="home-screen-new-conversation-section"
              className="grid grid-cols-1 gap-4 md:grid-cols-2"
            >
              <RepoConnector
                onRepoSelection={(repo) => setSelectedRepo(repo)}
              />
              <NewConversation />
            </div>
          </Section>

          <Section
            title="Recent operations"
            description="Active and recent agent runs, plus suggested work from your connected repositories."
          >
            <div
              data-testid="home-screen-recent-conversations-section"
              className="grid grid-cols-1 gap-4 md:grid-cols-2"
            >
              <RecentConversations />
              <TaskSuggestions filterFor={selectedRepo} />
            </div>
          </Section>
        </PageShell>
      </div>

      {isEnterpriseCloud && shouldShowCTA && (
        <div className="fixed bottom-4 right-8 z-50 md:bottom-6 md:right-12">
          <HomepageCTA setShouldShowCTA={setShouldShowCTA} />
        </div>
      )}
    </>
  );
}
