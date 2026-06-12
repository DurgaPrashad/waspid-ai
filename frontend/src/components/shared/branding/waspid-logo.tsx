import type { ComponentProps } from "react";
import waspidLogoSrc from "#/assets/branding/waspid-logo.png";

/**
 * Canonical Waspid brand mark.
 *
 * The source asset is a 2000×2000 PNG with a solid black background; the
 * brand mark is the gold "WASPID" wordmark on dark. Use `<WaspidLogo />`
 * wherever the previous `WaspidLogo` SVG component was used. Width
 * and height props match the original SVG-component contract so existing
 * sizing call sites continue to render at the same dimensions.
 *
 * `WaspidLogoWhite` is exported as an alias so callers that previously
 * imported `WaspidLogoWhite` (the inverted-on-light variant) keep
 * working. A dedicated light-theme variant can replace this alias once a
 * transparent / light-mode source asset is supplied.
 */
type WaspidLogoProps = Omit<ComponentProps<"img">, "src">;

export function WaspidLogo({
  alt = "Waspid",
  width,
  height,
  className,
  ...rest
}: WaspidLogoProps) {
  return (
    <img
      src={waspidLogoSrc}
      alt={alt}
      width={width}
      height={height}
      className={className}
      {...rest}
    />
  );
}

export const WaspidLogoWhite = WaspidLogo;
