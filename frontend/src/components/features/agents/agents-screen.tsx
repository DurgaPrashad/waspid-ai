// Waspid AI OS
import { Link } from "react-router";
import { Bot, Settings as SettingsIcon } from "lucide-react";
import { usePaginatedConversations } from "#/hooks/query/use-paginated-conversations";
import { useSettings } from "#/hooks/query/use-settings";
import { PageShell, PageHeader, Section } from "#/components/shared/layout";
import { AgentCard } from "./agent-card";
import { cn } from "#/utils/utils";

/**
 * Waspid Agents surface.
 *
 * Real-data composition only:
 *   - "Active fleet"  ← real V1AppConversation items from
 *                       usePaginatedConversations (first page).
 *   - "Default agent" ← settings.agent (real string) and the related
 *                       agent-settings route.
 *
 * No fabricated agent counts, no synthetic health/load metrics.
 * When the workspace has no conversations yet, the surface renders
 * an honest empty state rather than a placeholder fleet.
 */
export function AgentsScreen() {
  const {
    data: conversationsList,
    isFetching,
    error,
  } = usePaginatedConversations(12);
  const { data: settings } = useSettings();

  const conversations =
    conversationsList?.pages.flatMap((page) => page.items) ?? [];
  const hasConversations = conversations.length > 0;
  const isInitialLoading = isFetching && !conversationsList;

  return (
    <div data-testid="agents-screen" className="h-full">
      <PageShell
        width="wide"
        header={
          <PageHeader
            eyebrow="Workforce"
            title="Agents"
            subtitle="Deploy, configure, and monitor the AI agents that run on Waspid."
            actions={
              <Link
                to="/settings/agent"
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-md border border-tertiary/40 px-3 py-1.5 text-sm",
                  "text-content/90 hover:border-tertiary/70 hover:text-content",
                )}
              >
                <SettingsIcon className="h-4 w-4" aria-hidden />
                Agent settings
              </Link>
            }
          />
        }
      >
        <Section
          title="Active fleet"
          description="Agents currently provisioned in this workspace, sourced live from the conversation runtime."
        >
          {error && (
            <p className="text-sm text-danger" data-testid="agents-error">
              {error.message}
            </p>
          )}

          {isInitialLoading && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div
                  key={i}
                  className="h-[156px] rounded-xl border border-tertiary/30 bg-base-secondary/30 animate-pulse"
                />
              ))}
            </div>
          )}

          {!isInitialLoading && !error && !hasConversations && (
            <div
              data-testid="agents-empty"
              className="rounded-xl border border-dashed border-tertiary/40 bg-base-secondary/20 px-6 py-10 text-center"
            >
              <Bot className="mx-auto mb-3 h-8 w-8 text-basic" aria-hidden />
              <p className="text-sm text-content">No agents are running yet.</p>
              <p className="mt-1 text-xs text-basic">
                Start an operation from the Operations Center to provision your
                first agent.
              </p>
              <Link
                to="/"
                className="mt-4 inline-flex items-center text-xs font-medium text-primary hover:underline"
              >
                Go to Operations Center
              </Link>
            </div>
          )}

          {!isInitialLoading && hasConversations && (
            <div
              data-testid="agents-fleet"
              className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3"
            >
              {conversations.map((conversation) => (
                <AgentCard key={conversation.id} conversation={conversation} />
              ))}
            </div>
          )}
        </Section>

        <Section
          title="Default agent configuration"
          description="The agent template applied to new operations in this workspace."
        >
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="rounded-xl border border-tertiary/40 bg-base-secondary/40 p-5">
              <div className="text-xs text-basic">Agent kind</div>
              <div className="mt-1 text-sm font-semibold text-content">
                {settings?.agent || "—"}
              </div>
            </div>
            <div className="rounded-xl border border-tertiary/40 bg-base-secondary/40 p-5">
              <div className="text-xs text-basic">Model</div>
              <div
                className="mt-1 truncate text-sm font-semibold text-content"
                title={settings?.llm_model ?? ""}
              >
                {settings?.llm_model || "—"}
              </div>
            </div>
            <div className="rounded-xl border border-tertiary/40 bg-base-secondary/40 p-5">
              <div className="text-xs text-basic">Confirmation mode</div>
              <div className="mt-1 text-sm font-semibold text-content">
                {settings?.confirmation_mode ? "Required" : "Disabled"}
              </div>
            </div>
          </div>
        </Section>
      </PageShell>
    </div>
  );
}
