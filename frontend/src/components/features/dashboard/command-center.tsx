import { useState } from "react";
import { useNavigate } from "react-router";
import {
  Activity,
  ArrowRight,
  Bot,
  Factory,
  Library,
  Plug,
  Sparkles,
  Workflow,
} from "lucide-react";

const EXAMPLE_OBJECTIVES = [
  "Build me a real estate lead generation company",
  "Build me a recruitment agency",
  "Build me an AI customer support team",
  "Build me a software development company",
  "Build me a research organization",
];

const COMMAND_CARDS = [
  {
    to: "/workforce",
    icon: Factory,
    title: "Workforce Builder",
    detail: "Design a complete AI workforce from one objective",
  },
  {
    to: "/agents",
    icon: Bot,
    title: "Active Workforces",
    detail: "The agents currently deployed in this workspace",
  },
  {
    to: "/workflows",
    icon: Workflow,
    title: "Running Workflows",
    detail: "Autonomous runs: hand-offs, approvals, final reports",
  },
  {
    to: "/monitoring",
    icon: Activity,
    title: "Monitoring",
    detail: "Every run with lifecycle, model, and cost",
  },
  {
    to: "/integrations",
    icon: Plug,
    title: "Integrations",
    detail: "Connected systems, tools, and credentials",
  },
  {
    to: "/workforce",
    icon: Library,
    title: "Blueprint Library",
    detail: "Saved workforce templates: clone, share, deploy",
  },
];

/**
 * Workforce Command Center — the primary entry experience.
 *
 * Waspid opens on workforce creation, not chat: a single prompt that
 * feeds the Workforce Architect, surrounded by the operational
 * surfaces of the platform. The objective is carried to the builder
 * via the `objective` search param.
 */
export function CommandCenter() {
  const navigate = useNavigate();
  const [objective, setObjective] = useState("");

  const goToBuilder = (text: string) => {
    const trimmed = text.trim();
    navigate(
      trimmed
        ? `/workforce?objective=${encodeURIComponent(trimmed)}`
        : "/workforce",
    );
  };

  return (
    <div data-testid="command-center" className="flex flex-col gap-6">
      <form
        className="rounded-2xl border border-tertiary/40 bg-base-secondary/30 p-6 md:p-8"
        onSubmit={(e) => {
          e.preventDefault();
          goToBuilder(objective);
        }}
      >
        <h2 className="text-lg font-semibold text-content">
          What would you like to build?
        </h2>
        <p className="mt-1 text-sm text-basic">
          Describe a business, team, or operation — the Workforce Architect
          designs the AI workforce that runs it.
        </p>
        <div className="mt-4 flex flex-col gap-3 md:flex-row">
          <input
            data-testid="command-center-objective"
            value={objective}
            onChange={(e) => setObjective(e.target.value)}
            placeholder='e.g. "Build me a real estate lead generation company"'
            className="flex-1 rounded-xl border border-tertiary/40 bg-base-secondary/20 px-4 py-3 text-sm text-content placeholder:text-basic focus:border-tertiary/70 focus:outline-none"
          />
          <button
            type="submit"
            data-testid="command-center-build"
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-tertiary/60 px-5 py-3 text-sm font-semibold text-content hover:border-tertiary"
          >
            <Sparkles className="h-4 w-4" aria-hidden />
            Build Workforce
          </button>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {EXAMPLE_OBJECTIVES.map((example) => (
            <button
              key={example}
              type="button"
              onClick={() => goToBuilder(example)}
              className="rounded-full border border-tertiary/30 px-3 py-1 text-[11px] text-basic hover:border-tertiary/60 hover:text-content"
            >
              {example}
            </button>
          ))}
        </div>
      </form>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {COMMAND_CARDS.map((card) => (
          <button
            key={card.title}
            type="button"
            data-testid="command-card"
            onClick={() => navigate(card.to)}
            className="group flex items-start gap-3 rounded-xl border border-tertiary/40 bg-base-secondary/20 p-4 text-left hover:border-tertiary/70"
          >
            <card.icon
              className="mt-0.5 h-5 w-5 shrink-0 text-basic"
              aria-hidden
            />
            <span className="min-w-0">
              <span className="flex items-center gap-1 text-sm font-medium text-content">
                {card.title}
                <ArrowRight
                  className="h-3.5 w-3.5 opacity-0 transition-opacity group-hover:opacity-100"
                  aria-hidden
                />
              </span>
              <span className="mt-0.5 block text-xs text-basic">
                {card.detail}
              </span>
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
