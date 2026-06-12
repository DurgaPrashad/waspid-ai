import { useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { Download, Rocket, Save, Sparkles, Upload } from "lucide-react";
import {
  AgentSpec,
  WorkforceBlueprint,
  WorkforceDefinition,
} from "#/api/workforce-service/workforce.types";
import { useGenerateWorkforce } from "#/hooks/mutation/use-generate-workforce";
import {
  useCreateBlueprint,
  useImportBlueprint,
} from "#/hooks/mutation/use-blueprint-mutations";
import { useCreateConversation } from "#/hooks/mutation/use-create-conversation";
import { useStartWorkflowRun } from "#/hooks/mutation/use-workflow-run-mutations";
import { PageShell, PageHeader, Section } from "#/components/shared/layout";
import { WorkforceGraph } from "./workforce-graph";
import { AgentSpecCard } from "./agent-spec-card";
import { BlueprintLibrary } from "./blueprint-library";
import { downloadBlueprint, parseBlueprintFile } from "./blueprint-file";

/**
 * Deploy failures carry a structured payload when requirements are not
 * satisfied (HTTP 409): surface the missing pieces and where to fix them.
 */
function describeDeployError(error: unknown): string {
  const detail = (error as { response?: { data?: { detail?: unknown } } })
    ?.response?.data?.detail;
  if (detail && typeof detail === "object") {
    const req = detail as {
      llm_configured?: boolean;
      missing_integrations?: string[];
    };
    const parts: string[] = [];
    if (req.llm_configured === false) {
      parts.push("configure an LLM under Settings → LLM");
    }
    if (req.missing_integrations?.length) {
      parts.push(
        `connect ${req.missing_integrations.join(", ")} on the Integrations page`,
      );
    }
    if (parts.length) {
      return `Before deploying: ${parts.join(" and ")}.`;
    }
  }
  return error instanceof Error ? error.message : "Deploy failed.";
}

const EXAMPLE_OBJECTIVES = [
  "Build me a real estate lead generation business",
  "Build me a software development agency",
  "Run customer support for a SaaS product",
];

/**
 * Workforce Builder — the agent factory surface.
 *
 * Describe an objective in plain English; the Workforce Architect
 * (backed by the user's configured LLM) designs the workforce: agents,
 * roles, system prompts, reporting lines, and workflow handoffs.
 * Definitions can be saved as reusable blueprints, exported/imported as
 * JSON, and each agent can be launched as a real Waspid conversation.
 */
export function WorkforceBuilderScreen() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // The Command Center hands its prompt over via ?objective=…
  const [objective, setObjective] = useState(
    () => searchParams.get("objective") ?? "",
  );
  const [definition, setDefinition] = useState<WorkforceDefinition | null>(
    null,
  );
  const [blueprintName, setBlueprintName] = useState("");
  const [launchingAgent, setLaunchingAgent] = useState<string | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);

  const generate = useGenerateWorkforce();
  const saveBlueprint = useCreateBlueprint();
  const importBlueprint = useImportBlueprint();
  const createConversation = useCreateConversation();
  const startRun = useStartWorkflowRun();

  const onGenerate = () => {
    if (!objective.trim()) return;
    generate.mutate(
      { objective: objective.trim() },
      {
        onSuccess: (generated) => {
          setDefinition(generated);
          setBlueprintName(generated.objective.slice(0, 80));
        },
      },
    );
  };

  const onLoadBlueprint = (blueprint: WorkforceBlueprint) => {
    setDefinition(blueprint.definition);
    setObjective(blueprint.definition.objective);
    setBlueprintName(blueprint.name);
  };

  const onImportFile = async (file: File) => {
    setFileError(null);
    try {
      const parsed = parseBlueprintFile(await file.text());
      importBlueprint.mutate(parsed, {
        onSuccess: (blueprint) => onLoadBlueprint(blueprint),
      });
    } catch {
      setFileError("That file is not a valid Waspid blueprint.");
    }
  };

  const onLaunchAgent = (agent: AgentSpec) => {
    setLaunchingAgent(agent.name);
    const kickoff =
      `You are being launched as part of the workforce "${definition?.objective ?? ""}". ` +
      `Begin acting in your role now. Introduce your plan, then start on your first responsibility.`;
    createConversation.mutate(
      {
        query: kickoff,
        conversationInstructions: `${agent.system_prompt}\n\nRole: ${agent.role}\nResponsibilities:\n${agent.responsibilities.map((r) => `- ${r}`).join("\n")}`,
      },
      {
        onSuccess: (data) => navigate(`/conversations/${data.conversation_id}`),
        onSettled: () => setLaunchingAgent(null),
      },
    );
  };

  const generateError =
    generate.error instanceof Error ? generate.error.message : null;

  return (
    <div data-testid="workforce-builder-screen" className="h-full">
      <PageShell
        width="wide"
        header={
          <PageHeader
            eyebrow="Workforce"
            title="Workforce Builder"
            subtitle="Describe a business objective and the Workforce Architect designs the AI team: agents, prompts, and workflows."
          />
        }
      >
        <Section
          title="Objective"
          description="What should this workforce accomplish?"
        >
          <div className="flex flex-col gap-3">
            <textarea
              data-testid="workforce-objective-input"
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              rows={3}
              placeholder='e.g. "Build me a real estate lead generation business"'
              className="w-full rounded-lg border border-tertiary/40 bg-base-secondary/20 p-3 text-sm text-content placeholder:text-basic focus:border-tertiary/70 focus:outline-none"
            />
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                data-testid="workforce-generate-button"
                onClick={onGenerate}
                disabled={generate.isPending || !objective.trim()}
                className="inline-flex items-center gap-1.5 rounded-md border border-tertiary/50 px-3 py-1.5 text-xs font-medium text-content/90 hover:border-tertiary/70 hover:text-content disabled:opacity-50"
              >
                <Sparkles className="h-3.5 w-3.5" aria-hidden />
                {generate.isPending
                  ? "Designing workforce…"
                  : "Generate workforce"}
              </button>
              {EXAMPLE_OBJECTIVES.map((example) => (
                <button
                  key={example}
                  type="button"
                  onClick={() => setObjective(example)}
                  className="rounded-full border border-tertiary/30 px-2.5 py-1 text-[11px] text-basic hover:border-tertiary/60 hover:text-content"
                >
                  {example}
                </button>
              ))}
            </div>
            {generateError && (
              <p
                data-testid="workforce-generate-error"
                className="text-xs text-red-400"
              >
                {generateError}
              </p>
            )}
          </div>
        </Section>

        {definition && (
          <>
            <Section
              title="Workforce structure"
              description={definition.summary || definition.objective}
            >
              <WorkforceGraph
                agents={definition.agents}
                workflows={definition.workflows}
              />
              {definition.workflows.length > 0 && (
                <ul className="mt-3 flex flex-col gap-1 text-xs text-basic">
                  {definition.workflows.map((edge, i) => (
                    <li key={i}>
                      <span className="text-content/80">{edge.from_agent}</span>
                      {" → "}
                      <span className="text-content/80">{edge.to_agent}</span>
                      {edge.trigger && <> — {edge.trigger}</>}
                    </li>
                  ))}
                </ul>
              )}
            </Section>

            <Section
              title="Deploy"
              description="Run the whole workforce autonomously: agents execute, hand off to each other, and the supervisor returns a final report on the Workflows page."
            >
              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  data-testid="workforce-deploy-button"
                  onClick={() =>
                    startRun.mutate(
                      {
                        definition,
                        name: blueprintName.trim() || definition.objective,
                      },
                      { onSuccess: () => navigate("/workflows") },
                    )
                  }
                  disabled={startRun.isPending}
                  className="inline-flex items-center gap-1.5 rounded-md border border-tertiary/50 px-3 py-1.5 text-xs font-medium text-content/90 hover:border-tertiary/70 hover:text-content disabled:opacity-50"
                >
                  <Rocket className="h-3.5 w-3.5" aria-hidden />
                  {startRun.isPending ? "Deploying…" : "Deploy & run workforce"}
                </button>
                {startRun.error != null && (
                  <span
                    data-testid="workforce-deploy-error"
                    className="text-xs text-red-400"
                  >
                    {describeDeployError(startRun.error)}
                  </span>
                )}
              </div>
            </Section>

            <Section
              title={`Agents (${definition.agents.length})`}
              description="Review each agent, or launch one individually as a live Waspid run."
            >
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
                {definition.agents.map((agent) => (
                  <AgentSpecCard
                    key={agent.name}
                    agent={agent}
                    onLaunch={onLaunchAgent}
                    isLaunching={launchingAgent === agent.name}
                  />
                ))}
              </div>
            </Section>

            <Section
              title="Save blueprint"
              description="Store this workforce for reuse, cloning, and sharing."
            >
              <div className="flex flex-wrap items-center gap-2">
                <input
                  data-testid="blueprint-name-input"
                  value={blueprintName}
                  onChange={(e) => setBlueprintName(e.target.value)}
                  placeholder="Blueprint name"
                  className="w-64 rounded-md border border-tertiary/40 bg-base-secondary/20 px-3 py-1.5 text-xs text-content placeholder:text-basic focus:border-tertiary/70 focus:outline-none"
                />
                <button
                  type="button"
                  data-testid="blueprint-save-button"
                  onClick={() =>
                    saveBlueprint.mutate({
                      name: blueprintName.trim() || definition.objective,
                      definition,
                    })
                  }
                  disabled={saveBlueprint.isPending}
                  className="inline-flex items-center gap-1.5 rounded-md border border-tertiary/50 px-3 py-1.5 text-xs font-medium text-content/90 hover:border-tertiary/70 hover:text-content disabled:opacity-50"
                >
                  <Save className="h-3.5 w-3.5" aria-hidden />
                  {saveBlueprint.isPending ? "Saving…" : "Save blueprint"}
                </button>
                <button
                  type="button"
                  onClick={() =>
                    downloadBlueprint(
                      blueprintName.trim() || definition.objective,
                      definition,
                    )
                  }
                  className="inline-flex items-center gap-1.5 rounded-md border border-tertiary/50 px-3 py-1.5 text-xs font-medium text-content/90 hover:border-tertiary/70 hover:text-content"
                >
                  <Download className="h-3.5 w-3.5" aria-hidden />
                  Export JSON
                </button>
                {saveBlueprint.isSuccess && (
                  <span className="text-xs text-basic">Saved.</span>
                )}
              </div>
            </Section>
          </>
        )}

        <Section
          title="Blueprint library"
          description="Saved workforce templates: load, clone, export, or delete."
        >
          <div className="flex flex-col gap-3">
            <div>
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="inline-flex items-center gap-1.5 rounded-md border border-tertiary/50 px-3 py-1.5 text-xs font-medium text-content/90 hover:border-tertiary/70 hover:text-content"
              >
                <Upload className="h-3.5 w-3.5" aria-hidden />
                Import blueprint JSON
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".json,application/json"
                className="hidden"
                onChange={(e) => {
                  const input = e.currentTarget;
                  const file = input.files?.[0];
                  if (file) onImportFile(file);
                  input.value = "";
                }}
              />
              {fileError && (
                <p className="mt-1 text-xs text-red-400">{fileError}</p>
              )}
            </div>
            <BlueprintLibrary onLoad={onLoadBlueprint} />
          </div>
        </Section>
      </PageShell>
    </div>
  );
}
