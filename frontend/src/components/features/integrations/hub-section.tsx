// Waspid AI OS
import { useState } from "react";
import {
  Activity,
  CheckCircle2,
  Plug,
  RefreshCw,
  Trash2,
  XCircle,
} from "lucide-react";
import {
  ProviderStatus,
  ToolSpec,
} from "#/api/integrations-hub/integrations-hub.types";
import {
  useCheckHubConnection,
  useCreateHubConnection,
  useDeleteHubConnection,
  useHubProviders,
  useHubToolCalls,
} from "#/hooks/query/use-integrations-hub";

const EXECUTION_LABELS: Record<string, string> = {
  server: "Runs on Waspid",
  sandbox: "Runs in agent sandbox",
  mcp: "Via MCP server",
};

function ProviderCard({ provider }: { provider: ProviderStatus }) {
  const { spec, connection } = provider;
  const [showConnect, setShowConnect] = useState(false);
  const [credential, setCredential] = useState("");
  const [baseUrl, setBaseUrl] = useState("");

  const create = useCreateHubConnection();
  const remove = useDeleteHubConnection();
  const check = useCheckHubConnection();

  const CREDENTIAL_LABELS: Record<string, string> = {
    webhook_url: "Webhook URL",
    oauth_token: "Access token",
    api_key: "API key",
  };
  const credentialLabel =
    CREDENTIAL_LABELS[spec.credential_kind] ?? "Credential";

  return (
    <li
      data-testid="hub-provider-card"
      className="rounded-xl border border-tertiary/40 bg-base-secondary/20 p-4"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-sm font-semibold text-content">{spec.name}</p>
          <p className="text-[11px] text-basic">{spec.category}</p>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          {connection ? (
            <>
              {connection.last_check_ok != null &&
                (connection.last_check_ok ? (
                  <span className="inline-flex items-center gap-1 text-[11px] text-success">
                    <CheckCircle2 className="h-3 w-3" aria-hidden /> healthy
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-[11px] text-danger">
                    <XCircle className="h-3 w-3" aria-hidden /> failing
                  </span>
                ))}
              <button
                type="button"
                title="Check connection"
                data-testid="hub-check-button"
                onClick={() => check.mutate(connection.id)}
                disabled={check.isPending}
                className="rounded p-1.5 text-basic hover:bg-tertiary/30 hover:text-content disabled:opacity-50"
              >
                <RefreshCw className="h-3.5 w-3.5" aria-hidden />
              </button>
              <button
                type="button"
                title="Disconnect"
                data-testid="hub-disconnect-button"
                onClick={() => remove.mutate(connection.id)}
                disabled={remove.isPending}
                className="rounded p-1.5 text-basic hover:bg-red-500/20 hover:text-red-400 disabled:opacity-50"
              >
                <Trash2 className="h-3.5 w-3.5" aria-hidden />
              </button>
            </>
          ) : (
            <button
              type="button"
              data-testid="hub-connect-button"
              onClick={() => setShowConnect(!showConnect)}
              className="inline-flex items-center gap-1 rounded-md border border-tertiary/50 px-2 py-1 text-[11px] font-medium text-content/90 hover:border-tertiary/70"
            >
              <Plug className="h-3 w-3" aria-hidden />
              Connect
            </button>
          )}
        </div>
      </div>

      {showConnect && !connection && (
        <form
          className="mt-3 flex flex-col gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            if (!credential.trim()) return;
            create.mutate(
              {
                provider: spec.id,
                credential: credential.trim(),
                base_url: baseUrl.trim() || undefined,
              },
              { onSuccess: () => setShowConnect(false) },
            );
          }}
        >
          <input
            data-testid="hub-credential-input"
            type="password"
            value={credential}
            onChange={(e) => setCredential(e.target.value)}
            placeholder={credentialLabel}
            className="rounded-md border border-tertiary/40 bg-base-secondary/20 px-3 py-1.5 text-xs text-content placeholder:text-basic focus:border-tertiary/70 focus:outline-none"
          />
          {spec.base_url_required && (
            <input
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="Base URL (e.g. https://yourorg.example.com)"
              className="rounded-md border border-tertiary/40 bg-base-secondary/20 px-3 py-1.5 text-xs text-content placeholder:text-basic focus:border-tertiary/70 focus:outline-none"
            />
          )}
          <div className="flex items-center gap-2">
            <button
              type="submit"
              data-testid="hub-save-connection-button"
              disabled={create.isPending || !credential.trim()}
              className="rounded-md border border-tertiary/50 px-3 py-1.5 text-xs font-medium text-content/90 hover:border-tertiary/70 disabled:opacity-50"
            >
              {create.isPending ? "Connecting…" : "Save connection"}
            </button>
            {create.error instanceof Error && (
              <span className="text-[11px] text-red-400">
                {create.error.message}
              </span>
            )}
          </div>
          {spec.notes && <p className="text-[11px] text-basic">{spec.notes}</p>}
        </form>
      )}

      <details className="mt-3 text-xs">
        <summary className="cursor-pointer text-basic hover:text-content">
          {spec.tools.length} tools
        </summary>
        <ul className="mt-2 flex flex-col gap-1.5">
          {spec.tools.map((tool: ToolSpec) => (
            <li
              key={tool.name}
              className="rounded bg-base-secondary/30 px-2 py-1.5"
            >
              <span className="font-medium text-content/90">{tool.name}</span>
              <span className="ml-2 text-basic">{tool.description}</span>
              <span className="ml-2 rounded bg-tertiary/30 px-1 py-0.5 text-[10px] text-content/70">
                {EXECUTION_LABELS[tool.execution]}
              </span>
            </li>
          ))}
        </ul>
        {spec.sandbox_env_var && (
          <p className="mt-2 text-[11px] text-basic">
            Sandbox tools: add your credential as a custom secret named{" "}
            <code>{spec.sandbox_env_var}</code> under Settings → Secrets so
            agents can use it.
          </p>
        )}
      </details>
    </li>
  );
}

/**
 * Integration Hub: connected accounts, the tool registry browser, and
 * tool-call observability. Connections are credential-based (API key /
 * webhook URL / pasted OAuth token); each provider's tools declare how
 * they execute (server-side, agent sandbox, or MCP).
 */
export function HubSection() {
  const { data: providers, isLoading, error } = useHubProviders();
  const { data: toolCalls } = useHubToolCalls();

  if (isLoading) {
    return <p className="text-xs text-basic">Loading integration hub…</p>;
  }
  if (error || !providers) {
    return (
      <p className="text-xs text-red-400">
        Could not load the integration hub. Try again later.
      </p>
    );
  }

  const stats = toolCalls?.stats;

  return (
    <div data-testid="hub-section" className="flex flex-col gap-4">
      {stats && stats.total > 0 && (
        <div
          data-testid="hub-stats"
          className="flex flex-wrap items-center gap-4 rounded-lg border border-tertiary/30 bg-base-secondary/10 px-4 py-2 text-xs text-basic"
        >
          <span className="inline-flex items-center gap-1.5">
            <Activity className="h-3.5 w-3.5" aria-hidden />
            {stats.total} tool calls
          </span>
          <span>{stats.failures} failures</span>
          {stats.avg_latency_ms != null && (
            <span>{Math.round(stats.avg_latency_ms)} ms avg latency</span>
          )}
        </div>
      )}

      <ul className="grid grid-cols-1 gap-3 lg:grid-cols-2">
        {providers.map((provider) => (
          <ProviderCard key={provider.spec.id} provider={provider} />
        ))}
      </ul>

      {toolCalls && toolCalls.items.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-medium text-content">
            Recent tool calls
          </p>
          <ul
            data-testid="hub-tool-call-log"
            className="flex max-h-48 flex-col gap-1 overflow-y-auto text-[11px] text-basic"
          >
            {toolCalls.items.map((call) => (
              <li key={call.id} className="flex items-center gap-2">
                {call.ok ? (
                  <CheckCircle2
                    className="h-3 w-3 shrink-0 text-success"
                    aria-hidden
                  />
                ) : (
                  <XCircle
                    className="h-3 w-3 shrink-0 text-danger"
                    aria-hidden
                  />
                )}
                <span className="text-content/80">
                  {call.provider}.{call.tool}
                </span>
                {call.agent_name && <span>by {call.agent_name}</span>}
                {call.latency_ms != null && <span>{call.latency_ms} ms</span>}
                {call.error && (
                  <span className="truncate text-red-400">{call.error}</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
