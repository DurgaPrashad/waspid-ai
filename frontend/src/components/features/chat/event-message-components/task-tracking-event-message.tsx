// Waspid AI OS
import { WaspidObservation } from "#/types/core/observations";
import { isTaskTrackingObservation } from "#/types/core/guards";
import { TaskTrackingObservationContent } from "../task-tracking-observation-content";
import { ConfirmationButtons } from "#/components/shared/buttons/confirmation-buttons";

interface TaskTrackingEventMessageProps {
  event: WaspidObservation;
  shouldShowConfirmationButtons: boolean;
}

export function TaskTrackingEventMessage({
  event,
  shouldShowConfirmationButtons,
}: TaskTrackingEventMessageProps) {
  if (!isTaskTrackingObservation(event)) {
    return null;
  }

  return (
    <div>
      <TaskTrackingObservationContent event={event} />
      {shouldShowConfirmationButtons && <ConfirmationButtons />}
    </div>
  );
}
