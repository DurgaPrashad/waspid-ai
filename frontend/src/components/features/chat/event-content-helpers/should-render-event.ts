import { WaspidAction } from "#/types/core/actions";
import { WaspidEventType } from "#/types/core/base";
import {
  isCommandAction,
  isCommandObservation,
  isWaspidAction,
  isWaspidObservation,
} from "#/types/core/guards";
import { WaspidObservation } from "#/types/core/observations";

const COMMON_NO_RENDER_LIST: WaspidEventType[] = [
  "system",
  "agent_state_changed",
  "change_agent_state",
];

const ACTION_NO_RENDER_LIST: WaspidEventType[] = ["recall"];

const OBSERVATION_NO_RENDER_LIST: WaspidEventType[] = ["think"];

export const shouldRenderEvent = (
  event: WaspidAction | WaspidObservation,
) => {
  if (isWaspidAction(event)) {
    if (isCommandAction(event) && event.source === "user") {
      // For user commands, we always hide them from the chat interface
      return false;
    }

    const noRenderList = COMMON_NO_RENDER_LIST.concat(ACTION_NO_RENDER_LIST);
    return !noRenderList.includes(event.action);
  }

  if (isWaspidObservation(event)) {
    if (isCommandObservation(event) && event.source === "user") {
      // For user commands, we always hide them from the chat interface
      return false;
    }

    const noRenderList = COMMON_NO_RENDER_LIST.concat(
      OBSERVATION_NO_RENDER_LIST,
    );
    return !noRenderList.includes(event.observation);
  }

  return true;
};

export const hasUserEvent = (
  events: (WaspidAction | WaspidObservation)[],
) =>
  events.some((event) => isWaspidAction(event) && event.source === "user");
