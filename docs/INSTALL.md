# Installing Waspid

Waspid is the enterprise AI workforce operating system. This guide covers
installing and running it from source on macOS, Linux, or Windows (WSL).
For Docker-based installs see [SELF_HOSTING.md](SELF_HOSTING.md).

## Prerequisites

| Requirement | Version |
| --- | --- |
| Python | 3.12 or 3.13 |
| Node.js | 22.x (see `.nvmrc`) |
| Poetry | 2.x |
| Docker | required for sandboxed agent runtimes |
| make, tmux | required for local development |

Run `waspid doctor` (or `make check-dependencies`) at any time to verify
your environment.

## Install from source

```bash
git clone https://github.com/DurgaPrashad/waspid-ai.git
cd waspid-ai
make build        # installs Python deps, frontend deps, builds the frontend
```

## Start Waspid

```bash
make run
# or, once the package is installed:
waspid start
```

Then open http://localhost:3001 (development) or http://localhost:3000
(`waspid start`, which serves the built frontend from the backend).

## API keys

Waspid talks to LLM providers through a provider-abstraction layer
(LiteLLM). You only need a provider name and an API key — no code changes.

Two ways to configure a provider:

1. **Settings UI** (recommended): open *Settings → LLM*, pick a provider
   and model, paste your API key.
2. **CLI**: store a key that is exported automatically by `waspid start`:

   ```bash
   waspid provider add anthropic sk-ant-...
   waspid provider list
   ```

Supported providers include OpenAI, Anthropic, Google Gemini, Grok (xAI),
OpenRouter, DeepSeek, Ollama, Azure OpenAI, and AWS Bedrock. Where you get
a key:

| Provider | Where to get a key |
| --- | --- |
| OpenAI | https://platform.openai.com/api-keys |
| Anthropic | https://platform.console.anthropic.com/settings/keys |
| Google Gemini | https://aistudio.google.com/apikey |
| OpenRouter | https://openrouter.ai/keys |
| DeepSeek | https://platform.deepseek.com/api_keys |
| xAI (Grok) | https://console.x.ai |
| Ollama | no key — set `OLLAMA_BASE_URL` |
| Azure OpenAI | Azure portal → your OpenAI resource |
| AWS Bedrock | AWS IAM credentials |

## Troubleshooting

- `nc: command not found` on backend start → install `netcat-openbsd`.
- Local runtime browser features need Playwright:
  `poetry run playwright install chromium`.
- See [Development.md](../Development.md) for full per-OS development
  setup, and run `waspid doctor` for an automated environment check.
