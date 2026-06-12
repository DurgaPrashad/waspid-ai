import { WaspidAction } from "./actions";
import { WaspidObservation } from "./observations";
import { WaspidVariance } from "./variances";

/**
 * @deprecated Will be removed once we fully transition to v1 events
 */
export type WaspidParsedEvent =
  | WaspidAction
  | WaspidObservation
  | WaspidVariance;
