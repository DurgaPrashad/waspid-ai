// Waspid AI OS
import {
  BlueprintExport,
  WorkforceDefinition,
} from "#/api/workforce-service/workforce.types";

export const BLUEPRINT_EXPORT_VERSION = 1;

/** Trigger a client-side download of a blueprint as a portable JSON file. */
export function downloadBlueprint(
  name: string,
  definition: WorkforceDefinition,
) {
  const payload: BlueprintExport = {
    version: BLUEPRINT_EXPORT_VERSION,
    name,
    definition,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${name.replace(/[^a-z0-9-_]+/gi, "-").toLowerCase()}.waspid.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}

/** Parse an imported blueprint file, throwing on malformed content. */
export function parseBlueprintFile(text: string): BlueprintExport {
  const data = JSON.parse(text);
  if (
    typeof data !== "object" ||
    data === null ||
    typeof data.name !== "string" ||
    typeof data.definition !== "object" ||
    !Array.isArray(data.definition?.agents)
  ) {
    throw new Error("Not a valid Waspid blueprint file");
  }
  return {
    version: typeof data.version === "number" ? data.version : 1,
    name: data.name,
    definition: data.definition,
  };
}
