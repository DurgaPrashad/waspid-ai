import { useTranslation } from "react-i18next";
import { BaseModalTitle } from "#/components/shared/modals/confirmation-modals/base-modal";
import { Typography } from "#/ui/typography";
import { cn } from "#/utils/utils";

interface SystemMessageHeaderProps {
  agentClass: string | null;
  waspidVersion: string | null;
}

export function SystemMessageHeader({
  agentClass,
  waspidVersion,
}: SystemMessageHeaderProps) {
  const { t } = useTranslation();

  return (
    <div
      className={cn(
        "flex flex-col gap-6 w-full",
        !!agentClass && !!waspidVersion ? "gap-6" : "gap-0",
      )}
    >
      <BaseModalTitle title={t("SYSTEM_MESSAGE_MODAL$TITLE")} />
      <div className="flex flex-col gap-2">
        {agentClass && (
          <div className="text-sm">
            <Typography.Text className="font-semibold text-gray-300">
              {t("SYSTEM_MESSAGE_MODAL$AGENT_CLASS")}
            </Typography.Text>{" "}
            <Typography.Text className="font-medium text-gray-100">
              {agentClass}
            </Typography.Text>
          </div>
        )}
        {waspidVersion && (
          <div className="text-sm">
            <Typography.Text className="font-semibold text-gray-300">
              {t("SYSTEM_MESSAGE_MODAL$WASPID_VERSION")}
            </Typography.Text>{" "}
            <Typography.Text className="text-gray-100">
              {waspidVersion}
            </Typography.Text>
          </div>
        )}
      </div>
    </div>
  );
}
