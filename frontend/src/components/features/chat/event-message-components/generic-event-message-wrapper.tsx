import React from "react";
import { WaspidAction } from "#/types/core/actions";
import { WaspidObservation } from "#/types/core/observations";
import { isWaspidAction, isWaspidObservation } from "#/types/core/guards";
import { ChatMessage } from "../chat-message";
import { GenericEventMessage } from "../generic-event-message";
import { ConfirmationButtons } from "#/components/shared/buttons/confirmation-buttons";
import { getEventContent } from "../event-content-helpers/get-event-content";
import { getObservationResult } from "../event-content-helpers/get-observation-result";

const hasThoughtProperty = (
  obj: Record<string, unknown>,
): obj is { thought: string } => "thought" in obj && !!obj.thought;

interface GenericEventMessageWrapperProps {
  event: WaspidAction | WaspidObservation;
  shouldShowConfirmationButtons: boolean;
}

export function GenericEventMessageWrapper({
  event,
  shouldShowConfirmationButtons,
}: GenericEventMessageWrapperProps) {
  return (
    <div>
      {isWaspidAction(event) &&
        hasThoughtProperty(event.args) &&
        event.action !== "think" && (
          <ChatMessage type="agent" message={event.args.thought} />
        )}

      <GenericEventMessage
        title={getEventContent(event).title}
        details={getEventContent(event).details}
        success={
          isWaspidObservation(event)
            ? getObservationResult(event)
            : undefined
        }
      />

      {shouldShowConfirmationButtons && <ConfirmationButtons />}
    </div>
  );
}
