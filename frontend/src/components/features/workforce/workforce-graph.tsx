import { useMemo } from "react";
import {
  AgentSpec,
  WorkflowEdge,
} from "#/api/workforce-service/workforce.types";

const NODE_W = 190;
const NODE_H = 58;
const H_GAP = 28;
const V_GAP = 64;
const PADDING = 16;

interface Positioned {
  agent: AgentSpec;
  x: number;
  y: number;
}

/**
 * Layered org-chart layout:
 *   level 0 — agents with no (valid) supervisor,
 *   level n — agents reporting to a level n-1 agent.
 * Reporting lines are solid; workflow handoffs are dashed.
 */
function layout(agents: AgentSpec[]): {
  nodes: Map<string, Positioned>;
  width: number;
  height: number;
} {
  const names = new Set(agents.map((a) => a.name));
  const levelOf = new Map<string, number>();

  const resolveLevel = (agent: AgentSpec, seen: Set<string>): number => {
    if (levelOf.has(agent.name)) return levelOf.get(agent.name)!;
    if (
      !agent.reports_to ||
      !names.has(agent.reports_to) ||
      seen.has(agent.name)
    ) {
      levelOf.set(agent.name, 0);
      return 0;
    }
    seen.add(agent.name);
    const manager = agents.find((a) => a.name === agent.reports_to)!;
    const level = resolveLevel(manager, seen) + 1;
    levelOf.set(agent.name, level);
    return level;
  };
  agents.forEach((a) => resolveLevel(a, new Set()));

  const rows: AgentSpec[][] = [];
  agents.forEach((a) => {
    const level = levelOf.get(a.name) ?? 0;
    rows[level] = rows[level] ?? [];
    rows[level].push(a);
  });

  const maxRow = Math.max(1, ...rows.map((r) => r?.length ?? 0));
  const width = PADDING * 2 + maxRow * NODE_W + (maxRow - 1) * H_GAP;
  const height = PADDING * 2 + rows.length * NODE_H + (rows.length - 1) * V_GAP;

  const nodes = new Map<string, Positioned>();
  rows.forEach((row, level) => {
    const rowWidth = row.length * NODE_W + (row.length - 1) * H_GAP;
    const startX = (width - rowWidth) / 2;
    row.forEach((agent, i) => {
      nodes.set(agent.name, {
        agent,
        x: startX + i * (NODE_W + H_GAP),
        y: PADDING + level * (NODE_H + V_GAP),
      });
    });
  });

  return { nodes, width, height };
}

interface WorkforceGraphProps {
  agents: AgentSpec[];
  workflows: WorkflowEdge[];
}

export function WorkforceGraph({ agents, workflows }: WorkforceGraphProps) {
  const { nodes, width, height } = useMemo(() => layout(agents), [agents]);

  if (agents.length === 0) return null;

  const center = (name: string) => {
    const node = nodes.get(name);
    if (!node) return null;
    return { cx: node.x + NODE_W / 2, cy: node.y + NODE_H / 2 };
  };

  return (
    <div
      data-testid="workforce-graph"
      className="w-full overflow-x-auto rounded-xl border border-tertiary/40 bg-base-secondary/20 p-2"
    >
      <svg
        viewBox={`0 0 ${width} ${height}`}
        width="100%"
        style={{ minWidth: Math.min(width, 900), maxHeight: 480 }}
        role="img"
        aria-label="Workforce structure graph"
      >
        <defs>
          <marker
            id="workflow-arrow"
            viewBox="0 0 8 8"
            refX="7"
            refY="4"
            markerWidth="7"
            markerHeight="7"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 8 4 L 0 8 z" fill="currentColor" opacity={0.7} />
          </marker>
        </defs>

        {/* reporting lines */}
        {agents.map((agent) => {
          if (!agent.reports_to) return null;
          const from = center(agent.name);
          const to = center(agent.reports_to);
          if (!from || !to) return null;
          return (
            <line
              key={`report-${agent.name}`}
              x1={from.cx}
              y1={from.cy - NODE_H / 2}
              x2={to.cx}
              y2={to.cy + NODE_H / 2}
              stroke="currentColor"
              strokeOpacity={0.25}
            />
          );
        })}

        {/* workflow handoffs */}
        {workflows.map((edge, i) => {
          const from = center(edge.from_agent);
          const to = center(edge.to_agent);
          if (!from || !to) return null;
          const midY = (from.cy + to.cy) / 2 + 18;
          return (
            <g key={`flow-${i}`} className="text-content">
              <path
                d={`M ${from.cx} ${from.cy + NODE_H / 2} Q ${(from.cx + to.cx) / 2} ${midY + 30} ${to.cx} ${to.cy + NODE_H / 2}`}
                fill="none"
                stroke="currentColor"
                strokeOpacity={0.45}
                strokeDasharray="5 4"
                markerEnd="url(#workflow-arrow)"
              >
                <title>
                  {edge.trigger || `${edge.from_agent} → ${edge.to_agent}`}
                </title>
              </path>
            </g>
          );
        })}

        {/* nodes */}
        {[...nodes.values()].map(({ agent, x, y }) => (
          <g key={agent.name}>
            <rect
              x={x}
              y={y}
              width={NODE_W}
              height={NODE_H}
              rx={10}
              className="fill-base-secondary stroke-tertiary/60"
            />
            <text
              x={x + NODE_W / 2}
              y={y + 24}
              textAnchor="middle"
              className="fill-content"
              fontSize={12}
              fontWeight={600}
            >
              {agent.name.length > 26
                ? `${agent.name.slice(0, 25)}…`
                : agent.name}
            </text>
            <text
              x={x + NODE_W / 2}
              y={y + 42}
              textAnchor="middle"
              className="fill-basic"
              fontSize={10}
            >
              {agent.role.length > 32
                ? `${agent.role.slice(0, 31)}…`
                : agent.role}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}
