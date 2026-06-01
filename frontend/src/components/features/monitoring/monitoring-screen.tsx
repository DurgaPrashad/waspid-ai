import { useMemo } from "react";
import { Activity } from "lucide-react";
import { usePaginatedConversations } from "#/hooks/query/use-paginated-conversations";
import { useInfiniteScroll } from "#/hooks/use-infinite-scroll";
import {
  PageShell,
  PageHeader,
  Section,
} from "#/components/shared/layout";
import { RunRow } from "./run-row";
import { toMonitoringRun } from "./types";

/**
 * Waspid Monitoring surface.
 *
 * Treats every V1AppConversation as a "run" and lists them with
 * runtime-published state: lifecycle, model, cost, last activity.
 * No fake throughput, no synthetic SLOs.
 *
 * Pagination uses the same `usePaginatedConversations` infinite-scroll
 * machinery the Operations Center uses — so /monitoring scales to a
 * workspace's full run history without re-implementing fetching.
 */
export function MonitoringScreen() {
  const {
    data,
    isFetching,
    isFetchingNextPage,
    error,
    hasNextPage,
    fetchNextPage,
  } = usePaginatedConversations(25);

  const scrollContainerRef = useInfiniteScroll({
    hasNextPage: !!hasNextPage,
    isFetchingNextPage,
    fetchNextPage,
    threshold: 240,
  });

  const runs = useMemo(
    () => data?.pages.flatMap((p) => p.items.map(toMonitoringRun)) ?? [],
    [data],
  );

  const isInitialLoading = isFetching && !data;
  const isEmpty = !isInitialLoading && !error && runs.length === 0;

  return (
    <div data-testid="monitoring-screen" className="h-full">
      <PageShell
        width="wide"
        header={
          <PageHeader
            eyebrow="Operations"
            title="Monitoring"
            subtitle="Realtime visibility into every agent run across this workspace."
          />
        }
      >
        <Section
          title="Recent runs"
          description="Live and historical agent runs, paginated as you scroll."
        >
          {error && (
            <p className="text-sm text-danger" data-testid="monitoring-error">
              {error.message}
            </p>
          )}

          {isInitialLoading && (
            <div className="flex flex-col">
              {Array.from({ length: 8 }).map((_, i) => (
                <div
                  key={i}
                  className="h-12 border-b border-tertiary/30 bg-base-secondary/20 animate-pulse"
                />
              ))}
            </div>
          )}

          {isEmpty && (
            <div
              data-testid="monitoring-empty"
              className="rounded-xl border border-dashed border-tertiary/40 bg-base-secondary/20 px-6 py-12 text-center"
            >
              <Activity className="mx-auto mb-3 h-8 w-8 text-basic" aria-hidden />
              <p className="text-sm text-content">No runs to monitor yet.</p>
              <p className="mt-1 text-xs text-basic">
                Once an agent run starts, it will appear here with live status,
                model, and cost.
              </p>
            </div>
          )}

          {!isInitialLoading && runs.length > 0 && (
            <div
              ref={scrollContainerRef}
              className="rounded-xl border border-tertiary/40 bg-base-secondary/30 overflow-hidden"
            >
              <div
                role="row"
                className="grid grid-cols-12 gap-3 px-4 py-2 border-b border-tertiary/40 bg-base-secondary/50 text-[11px] uppercase tracking-wide text-basic"
              >
                <div className="col-span-12 sm:col-span-4">Run</div>
                <div className="col-span-6 sm:col-span-2">Status</div>
                <div className="col-span-6 sm:col-span-2">Model</div>
                <div className="col-span-6 sm:col-span-2">Cost</div>
                <div className="col-span-6 sm:col-span-2">Updated</div>
              </div>
              <div className="flex flex-col">
                {runs.map((run) => (
                  <RunRow key={run.id} run={run} />
                ))}
                {isFetchingNextPage && (
                  <div className="px-4 py-3 text-xs text-basic">
                    Loading more runs…
                  </div>
                )}
              </div>
            </div>
          )}
        </Section>
      </PageShell>
    </div>
  );
}
