<!-- Waspid AI OS -->
# Contributing

Thanks for your interest in contributing to Waspid! Waspid is an enterprise AI workforce operating system, built on top of an upstream MIT-licensed open-source agent SDK (see [CREDITS.md](CREDITS.md)).

## Our Vision

Waspid is built around the belief that AI agents will fundamentally change how organizations operate — from support and sales to engineering and operations — and that running AI as infrastructure (rather than as a chatbot) is what makes that transformation real.

We believe the foundation should be open. That is why Waspid is built on, and contributes back to, the open-source agent SDK ecosystem it depends on (see [CREDITS.md](CREDITS.md)).

## Getting Started

### Quick Ways to Contribute

- **Use Waspid** and report issues you encounter
- **Give feedback** through the UI feedback controls in the dashboard
- **Improve docs** in this repository
- **Contribute upstream** to the agent SDK (links in [CREDITS.md](CREDITS.md)) when the change belongs in the agent runtime itself

### Set Up Your Development Environment

- **Requirements**: Linux/Mac/WSL, Docker, Python 3.12, Node.js 22+, Poetry 1.8+
- **Quick setup**: `make build`
- **Run locally**: `make run`
- **LLM setup (V1 web app)**: configure your model and API key in the Settings UI after the app starts

Full details in our [Development Guide](./Development.md).

### Find Your First Issue

- Browse the issue tracker for this Waspid repository
- For changes to the agent runtime itself, the upstream agent SDK is the right home — see [CREDITS.md](CREDITS.md)

## Understanding the Codebase

- **[Frontend](./frontend/README.md)** - React application
- **[App Server (V1)](./waspid/app_server/README.md)** - Current FastAPI application server and REST API modules
- **Evaluation** - Testing and benchmarks live in the upstream SDK ecosystem (see [CREDITS.md](CREDITS.md))

## What Can You Build?

### Frontend & UI/UX
- React & TypeScript development
- UI/UX improvements
- Mobile responsiveness
- Component libraries

For bigger changes, please open a discussion or design issue first so we can align before you invest significant time.

### Agent Development
- Prompt engineering
- New agent types
- Agent evaluation
- Multi-agent systems

For changes to the core agent loop, contribute upstream to the agent SDK (see [CREDITS.md](CREDITS.md)). The agent runtime is consumed here as a pinned package.

### Backend & Infrastructure
- Python development
- Runtime systems (Docker containers, sandboxes)
- Cloud integrations
- Performance optimization

### Testing & Quality Assurance
- Unit testing
- Integration testing
- Bug hunting
- Performance testing

### Documentation & Education
- Technical documentation
- Translation
- Community support

## Pull Request Process

### Small Improvements
- Quick review and approval
- Ensure CI tests pass
- Include clear description of changes

### Core Agent Changes
These are evaluated based on:
- **Accuracy** - Does it make the agent better at solving problems?
- **Efficiency** - Does it improve speed or reduce resource usage?
- **Code Quality** - Is the code maintainable and well-tested?

Discuss major changes in a GitHub issue before opening a PR.

## Sending Pull Requests to Waspid

You'll need to fork the Waspid repository to send a Pull Request. You can learn more
about how to fork a GitHub repo and open a PR with your changes in [this article](https://medium.com/swlh/forks-and-pull-requests-how-to-contribute-to-github-repos-8843fac34ce8).

If your change belongs in the agent runtime rather than the Waspid control plane, send it upstream to the agent SDK instead (see [CREDITS.md](CREDITS.md)).

### Pull Request Title Format

As described [here](https://github.com/commitizen/conventional-commit-types/blob/master/index.json), a valid PR title should begin with one of the following prefixes:

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code (white space, formatting, missing semicolons, etc.)
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `build`: Changes that affect the build system or external dependencies (example scopes: gulp, broccoli, npm)
- `ci`: Changes to our CI configuration files and scripts (example scopes: Travis, Circle, BrowserStack, SauceLabs)
- `chore`: Other changes that don't modify src or test files
- `revert`: Reverts a previous commit

For example, a PR title could be:
- `refactor: modify package path`
- `feat(frontend): xxxx`, where `(frontend)` means that this PR mainly focuses on the frontend component.

### Pull Request Description

- Explain what the PR does and why
- Link to related issues
- Include screenshots for UI changes
- If your changes are user-facing (e.g. a new feature in the UI, a change in behavior, or a bugfix),
  please include a short message that we can add to our changelog

## Becoming a Maintainer

For contributors who have made significant and sustained contributions to the project, there is a possibility of joining the maintainer team.
The process for this is as follows:

1. Any contributor who has made sustained and high-quality contributions to the codebase can be nominated by any maintainer. If you feel that you may qualify you can reach out to any of the maintainers that have reviewed your PRs and ask if you can be nominated.
2. Once a maintainer nominates a new maintainer, there will be a discussion period among the maintainers for at least 3 days.
3. If no concerns are raised the nomination will be accepted by acclamation, and if concerns are raised there will be a discussion and possible vote.

Note that just making many PRs does not immediately imply that you will become a maintainer. We will be looking at sustained high-quality contributions over a period of time, as well as good teamwork and adherence to our [Code of Conduct](./CODE_OF_CONDUCT.md).

## Need Help?

- **GitHub Issues**: open an issue on the Waspid repository
- **Upstream agent runtime**: see [CREDITS.md](CREDITS.md) for SDK-level changes
