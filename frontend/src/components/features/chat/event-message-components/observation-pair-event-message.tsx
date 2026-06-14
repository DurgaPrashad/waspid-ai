// Waspid AI OS
import React from "react";
import { WaspidAction } from "#/types/core/actions";
import { isWaspidAction } from "#/types/core/guards";
import { ChatMessage } from "../chat-message";

const hasThoughtProperty = (
  obj: Record<string, unknown>,
): obj is { thought: string } => "thought" in obj && !!obj.thought;

interface ObservationPairEventMessageProps {
  event: WaspidAction;
}

export function ObservationPairEventMessage({
  event,
}: ObservationPairEventMessageProps) {
  if (!isWaspidAction(event)) {
    return null;
  }

  if (hasThoughtProperty(event.args) && event.action !== "think") {
    return (
      <div>
        <ChatMessage type="agent" message={event.args.thought} />
      </div>
    );
  }

  return null;
}
