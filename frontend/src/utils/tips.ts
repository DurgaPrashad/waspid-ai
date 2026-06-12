import { I18nKey } from "#/i18n/declaration";

const DOCS_BASE = "https://github.com/DurgaPrashad/waspid-ai/blob/main/docs";

export interface Tip {
  key: I18nKey;
  link?: string;
}

export const TIPS: Tip[] = [
  {
    key: I18nKey.TIPS$CUSTOMIZE_MICROAGENT,
    link: `${DOCS_BASE}/AGENTS_GUIDE.md`,
  },
  {
    key: I18nKey.TIPS$SETUP_SCRIPT,
    link: `${DOCS_BASE}/AGENTS_GUIDE.md`,
  },
  { key: I18nKey.TIPS$VSCODE_INSTANCE },
  { key: I18nKey.TIPS$SAVE_WORK },
  {
    key: I18nKey.TIPS$SPECIFY_FILES,
    link: `${DOCS_BASE}/AGENTS_GUIDE.md`,
  },
  {
    key: I18nKey.TIPS$HEADLESS_MODE,
    link: `${DOCS_BASE}/CLI.md`,
  },
  {
    key: I18nKey.TIPS$CLI_MODE,
    link: `${DOCS_BASE}/CLI.md`,
  },
  {
    key: I18nKey.TIPS$GITHUB_HOOK,
    link: `${DOCS_BASE}/INTEGRATIONS_GUIDE.md`,
  },
  {
    key: I18nKey.TIPS$BLOG_SIGNUP,
    link: "https://github.com/DurgaPrashad/waspid-ai",
  },
  {
    key: I18nKey.TIPS$API_USAGE,
    link: `${DOCS_BASE}/API.md`,
  },
];

export function getRandomTip(): Tip {
  const randomIndex = Math.floor(Math.random() * TIPS.length);
  return TIPS[randomIndex];
}
