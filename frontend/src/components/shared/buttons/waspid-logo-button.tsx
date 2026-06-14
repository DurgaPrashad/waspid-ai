// Waspid AI OS
import { NavLink } from "react-router";
import { useTranslation } from "react-i18next";
import { WaspidLogo } from "#/components/shared/branding/waspid-logo";
import { I18nKey } from "#/i18n/declaration";
import { StyledTooltip } from "#/components/shared/buttons/styled-tooltip";

export function WaspidLogoButton() {
  const { t } = useTranslation();

  const tooltipText = t(I18nKey.BRANDING$WASPID);
  const ariaLabel = t(I18nKey.BRANDING$WASPID_LOGO);

  return (
    <StyledTooltip content={tooltipText}>
      <NavLink to="/" aria-label={ariaLabel}>
        <WaspidLogo width={46} height={30} />
      </NavLink>
    </StyledTooltip>
  );
}
