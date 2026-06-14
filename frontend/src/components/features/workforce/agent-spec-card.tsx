// Waspid AI OS
import { Bot, Play } from "lucide-react";
import { AgentSpec } from "#/api/workforce-service/workforce.types";

interface AgentSpecCardProps {
  agent: AgentSpec;
  onLaunch: (agent: AgentSpec) => void;
  isLaunching: boolean;
}

export function AgentSpecCard({
  agent,
  onLaunch,
  isLaunching,
}: AgentSpecCardProps) {
  return (
    <div
      data-testid="agent-spec-card"
      className="rounded-xl border border-tertiary/40 bg-base-secondary/20 p-4 flex flex-col gap-3"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <Bot className="h-4 w-4 shrink-0 text-basic" aria-hidden />
          <div className="min-w-0">
            <p className="text-sm font-semibold text-content truncate">
              {agent.name}
            </p>
            <p className="text-xs text-basic truncate">{agent.role}</p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => onLaunch(agent)}
          disabled={isLaunching}
          className="inline-flex items-center gap-1.5 rounded-md border border-tertiary/50 px-2.5 py-1.5 text-xs font-medium text-content/90 hover:border-tertiary/70 hover:text-content disabled:opacity-50"
        >
          <Play className="h-3 w-3" aria-hidden />
          {isLaunching ? "Launching…" : "Launch"}
        </button>
      </div>

      {agent.reports_to && (
        <p className="text-[11px] text-basic">
          Reports to <span className="text-content/80">{agent.reports_to}</span>
        </p>
      )}

      {agent.tools.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {agent.tools.map((tool) => (
            <span
              key={tool}
              className="rounded bg-tertiary/30 px-1.5 py-0.5 text-[10px] text-content/80"
            >
              {tool}
            </span>
          ))}
        </div>
      )}

      {agent.responsibilities.length > 0 && (
        <ul className="list-disc pl-4 text-xs text-basic space-y-0.5">
          {agent.responsibilities.slice(0, 6).map((r) => (
            <li key={r}>{r}</li>
          ))}
        </ul>
      )}

      <details className="text-xs">
        <summary className="cursor-pointer text-basic hover:text-content">
          System prompt
        </summary>
        <pre className="mt-2 whitespace-pre-wrap rounded bg-base-secondary/40 p-2 text-[11px] text-content/80">
          {agent.system_prompt}
        </pre>
      </details>
    </div>
  );
}
