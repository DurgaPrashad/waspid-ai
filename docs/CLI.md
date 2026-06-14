<!-- Waspid AI OS -->
# Waspid CLI

The `waspid` command is installed with the Python package
(`pip install -e .` or `make build`) and works on macOS, Linux, and
Windows.

## Commands

| Command | What it does |
| --- | --- |
| `waspid start [--host H] [--port P]` | Start the Waspid server (backend + built frontend) |
| `waspid dev` | Run backend and frontend in development mode (`make run`) |
| `waspid build` | Install dependencies and build the frontend (`make build`) |
| `waspid doctor` | Check Python/Node/Docker/provider configuration |
| `waspid update` | `git pull --ff-only` a source checkout |
| `waspid deploy [-d]` | Start the Docker Compose stack |
| `waspid provider list` | Show supported LLM providers and their status |
| `waspid provider add <provider> <key>` | Save a provider API key |
| `waspid provider remove <provider>` | Remove a saved key |
| `waspid agents [--port P]` | Open the Agents dashboard in your browser |
| `waspid workflows [--port P]` | Open the Workflows dashboard in your browser |
| `waspid version` | Print the version |

## Provider credentials

`waspid provider add` writes the provider's environment variable to
`~/.waspid/waspid.env` (mode 0600). `waspid start` exports these into
the server environment, where the LiteLLM-based provider layer picks them
up. Keys configured in the Settings UI take precedence per user.

Supported providers: `openai`, `anthropic`, `gemini`, `grok`,
`openrouter`, `deepseek`, `ollama`, `azure`, `bedrock`.

## Headless / scripted use

The backend is a FastAPI app; everything the UI does is available over
the REST API (see [API.md](API.md)). `waspid start` plus the API is the
supported headless mode.
