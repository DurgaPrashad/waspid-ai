// Waspid AI OS
import { Copy, Download, FolderOpen, Trash2 } from "lucide-react";
import { WorkforceBlueprint } from "#/api/workforce-service/workforce.types";
import { useWorkforceBlueprints } from "#/hooks/query/use-workforce-blueprints";
import {
  useCloneBlueprint,
  useDeleteBlueprint,
} from "#/hooks/mutation/use-blueprint-mutations";
import { downloadBlueprint } from "./blueprint-file";

interface BlueprintLibraryProps {
  onLoad: (blueprint: WorkforceBlueprint) => void;
}

export function BlueprintLibrary({ onLoad }: BlueprintLibraryProps) {
  const { data, isLoading, error } = useWorkforceBlueprints();
  const deleteBlueprint = useDeleteBlueprint();
  const cloneBlueprint = useCloneBlueprint();

  const blueprints = data?.items ?? [];

  if (isLoading) {
    return <p className="text-xs text-basic">Loading blueprints…</p>;
  }
  if (error) {
    return (
      <p className="text-xs text-red-400">
        Could not load blueprints. Try again later.
      </p>
    );
  }
  if (blueprints.length === 0) {
    return (
      <p data-testid="blueprint-library-empty" className="text-xs text-basic">
        No saved blueprints yet. Generate a workforce and save it to reuse it
        later.
      </p>
    );
  }

  return (
    <ul data-testid="blueprint-library" className="flex flex-col gap-2">
      {blueprints.map((blueprint) => (
        <li
          key={blueprint.id}
          className="flex items-center justify-between gap-3 rounded-lg border border-tertiary/40 bg-base-secondary/20 px-3 py-2"
        >
          <div className="min-w-0">
            <p className="text-sm font-medium text-content truncate">
              {blueprint.name}
            </p>
            <p className="text-[11px] text-basic truncate">
              {blueprint.definition.agents.length} agents ·{" "}
              {blueprint.definition.workflows.length} handoffs
            </p>
          </div>
          <div className="flex items-center gap-1.5 shrink-0">
            <button
              type="button"
              title="Load into builder"
              onClick={() => onLoad(blueprint)}
              className="rounded p-1.5 text-basic hover:bg-tertiary/30 hover:text-content"
            >
              <FolderOpen className="h-4 w-4" aria-hidden />
            </button>
            <button
              type="button"
              title="Clone"
              onClick={() => cloneBlueprint.mutate(blueprint.id)}
              disabled={cloneBlueprint.isPending}
              className="rounded p-1.5 text-basic hover:bg-tertiary/30 hover:text-content disabled:opacity-50"
            >
              <Copy className="h-4 w-4" aria-hidden />
            </button>
            <button
              type="button"
              title="Export JSON"
              onClick={() =>
                downloadBlueprint(blueprint.name, blueprint.definition)
              }
              className="rounded p-1.5 text-basic hover:bg-tertiary/30 hover:text-content"
            >
              <Download className="h-4 w-4" aria-hidden />
            </button>
            <button
              type="button"
              title="Delete"
              onClick={() => deleteBlueprint.mutate(blueprint.id)}
              disabled={deleteBlueprint.isPending}
              className="rounded p-1.5 text-basic hover:bg-red-500/20 hover:text-red-400 disabled:opacity-50"
            >
              <Trash2 className="h-4 w-4" aria-hidden />
            </button>
          </div>
        </li>
      ))}
    </ul>
  );
}
