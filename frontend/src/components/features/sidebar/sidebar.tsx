import React from "react";
import { useLocation } from "react-router";
import { useTranslation } from "react-i18next";
import { useGitUser } from "#/hooks/query/use-git-user";
import { UserActions } from "./user-actions";
import { SidebarNavGroup } from "./sidebar-nav-group";
import { WaspidLogoButton } from "#/components/shared/buttons/waspid-logo-button";
import { NewProjectButton } from "#/components/shared/buttons/new-project-button";
import { ConversationPanelButton } from "#/components/shared/buttons/conversation-panel-button";
import { AutomationsButton } from "#/components/shared/buttons/automations-button";
import { SettingsModal } from "#/components/shared/modals/settings/settings-modal";
import { useSettings } from "#/hooks/query/use-settings";
import { ConversationPanel } from "../conversation-panel/conversation-panel";
import { ConversationPanelWrapper } from "../conversation-panel/conversation-panel-wrapper";
import { useConfig } from "#/hooks/query/use-config";
import { displayErrorToast } from "#/utils/custom-toast-handlers";
import { I18nKey } from "#/i18n/declaration";
import { cn } from "#/utils/utils";
import { ENABLE_AUTOMATIONS } from "#/utils/feature-flags";
import { PRIMARY_NAV } from "#/constants/navigation";

/**
 * Waspid app-shell sidebar.
 *
 * The sidebar carries two concerns layered into a single column:
 *   1. Quick conversation actions (logo, new conversation, recent
 *      conversation drawer, automations toggle). These pre-date the
 *      enterprise IA and remain wired against the existing handlers.
 *   2. The primary product nav (Dashboard, Agents, Workflows, …,
 *      Settings) sourced from `PRIMARY_NAV`. Items marked `planned`
 *      render as disabled with a "Soon" indicator — no fake routes
 *      are wired up.
 *
 * Width is intentionally 75px (icon-only) for now. The IA reads
 * through grouping, tooltips, and active-state accents. Widening
 * the sidebar to a labelled nav (~220px) is a follow-up turn that
 * needs to validate against the conversation panel portal and the
 * conversation route's flex layout.
 *
 * Mobile (`<md`) collapses to the original horizontal action bar —
 * the desktop-only nav clusters are hidden to keep the bar compact.
 */
export function Sidebar() {
  const { t } = useTranslation();
  const { pathname } = useLocation();
  const user = useGitUser();
  const { data: config } = useConfig();
  const {
    data: settings,
    error: settingsError,
    isError: settingsIsError,
    isFetching: isFetchingSettings,
  } = useSettings();

  const [settingsModalIsOpen, setSettingsModalIsOpen] = React.useState(false);
  const [conversationPanelIsOpen, setConversationPanelIsOpen] =
    React.useState(false);

  React.useEffect(() => {
    if (pathname === "/settings") {
      setSettingsModalIsOpen(false);
    } else if (
      !isFetchingSettings &&
      settingsIsError &&
      settingsError?.status !== 404
    ) {
      // We don't show toast errors for settings in the global error handler
      // because we have a special case for 404 errors
      displayErrorToast(
        "Something went wrong while fetching settings. Please reload the page.",
      );
    } else if (
      config?.app_mode === "oss" &&
      settingsError?.status === 404 &&
      !config?.feature_flags?.hide_llm_settings
    ) {
      setSettingsModalIsOpen(true);
    }
  }, [
    pathname,
    isFetchingSettings,
    settingsIsError,
    settingsError,
    config?.app_mode,
    config?.feature_flags?.hide_llm_settings,
  ]);

  const isEmailUnverified = settings?.email_verified === false;

  return (
    <>
      <aside
        aria-label={t(I18nKey.SIDEBAR$NAVIGATION_LABEL)}
        className={cn(
          "h-[54px] p-3 md:p-0 md:h-[40px] md:h-auto flex flex-row md:flex-col gap-1 bg-base md:w-[75px] md:min-w-[75px] sm:pt-0 sm:px-2 md:pt-[14px] md:px-0",
          pathname === "/" && "md:pt-6.5 md:pb-3",
        )}
      >
        <nav className="flex flex-row md:flex-col items-center justify-between w-full h-auto md:w-auto md:h-full">
          {/* Top cluster: brand + quick actions (visible on all viewports) */}
          <div className="flex flex-row md:flex-col items-center gap-[26px] md:gap-4">
            <div className="flex items-center justify-center">
              <WaspidLogoButton />
            </div>
            <div className="flex items-center justify-center">
              <NewProjectButton disabled={isEmailUnverified} />
            </div>
            <ConversationPanelButton
              isOpen={conversationPanelIsOpen}
              onClick={() =>
                isEmailUnverified
                  ? null
                  : setConversationPanelIsOpen((prev) => !prev)
              }
              disabled={isEmailUnverified}
            />
            {ENABLE_AUTOMATIONS() && (
              <AutomationsButton disabled={isEmailUnverified} />
            )}
          </div>

          {/* Middle cluster: primary product navigation (desktop only).
              Scrolls if vertical space is tight. Mobile keeps the
              original compact action bar — primary nav is reachable
              from desktop today; a mobile drawer is a future turn. */}
          <div
            className={cn(
              "hidden md:flex md:flex-col md:items-center md:flex-1",
              "md:gap-3 md:mt-6 md:overflow-y-auto md:py-2 md:custom-scrollbar",
            )}
          >
            {PRIMARY_NAV.map((group, index) => (
              <SidebarNavGroup
                key={group.id}
                group={group}
                showDivider={index > 0}
              />
            ))}
          </div>

          {/* Bottom cluster: user actions */}
          <div className="flex flex-row md:flex-col md:items-center gap-[26px]">
            <UserActions
              user={
                user.data ? { avatar_url: user.data.avatar_url } : undefined
              }
              isLoading={user.isFetching}
            />
          </div>
        </nav>

        {conversationPanelIsOpen && (
          <ConversationPanelWrapper isOpen={conversationPanelIsOpen}>
            <ConversationPanel
              onClose={() => setConversationPanelIsOpen(false)}
            />
          </ConversationPanelWrapper>
        )}
      </aside>

      {settingsModalIsOpen && (
        <SettingsModal
          settings={settings}
          onClose={() => setSettingsModalIsOpen(false)}
        />
      )}
    </>
  );
}
