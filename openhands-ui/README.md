<!-- Waspid AI OS -->
# @waspid/ui

The shared React component library used by the Waspid frontend. Built with TypeScript and Tailwind CSS.

> The npm package is currently named `@waspid/ui` for upstream-compatibility reasons. A rename to a Waspid-scoped package is a future migration; do not rename it here without coordinating the npm publish flow.

## Installation

Choose your preferred package manager:

```bash
# npm
npm install @waspid/ui

# yarn
yarn add @waspid/ui

# pnpm
pnpm add @waspid/ui

# bun
bun add @waspid/ui
```

## Quick Start

```tsx
import { Button, Typography } from "@waspid/ui";
import "@waspid/ui/styles";

function App() {
  return (
    <div>
      <Typography.H1>Hello World</Typography.H1>
      <Button variant="primary">Get Started</Button>
    </div>
  );
}
```

## Components

| Component         | Description                               |
| ----------------- | ----------------------------------------- |
| `Button`          | Interactive button with multiple variants |
| `Checkbox`        | Checkbox input with label support         |
| `Chip`            | Display tags or labels                    |
| `Divider`         | Visual separator                          |
| `Icon`            | Icon wrapper component                    |
| `Input`           | Text input field                          |
| `InteractiveChip` | Clickable chip component                  |
| `RadioGroup`      | Radio button group                        |
| `RadioOption`     | Individual radio option                   |
| `Scrollable`      | Scrollable container                      |
| `Toggle`          | Toggle switch                             |
| `Tooltip`         | Tooltip overlay                           |
| `Typography`      | Text components (H1-H6, Text, Code)       |

## Development

Use your preferred package manager to install dependencies and run the development server. We recommend using [Bun](https://bun.sh) for a fast development experience.

**Note**: If you plan to make dependency changes and submit a PR, you must use Bun during development.

```bash
# Install dependencies
bun install

# Start Storybook
bun run dev

# Build package
bun run build
```

### Testing Locally Without Publishing

To test the package in another project without publishing to npm:

```bash
# Build the package:
bun run build

# Create a local package:
# This generates a `.tgz` file in the current directory.
bun pm pack

# Install in your target project:
# Replace `path/to/waspid-ui-x.x.x.tgz` with the actual path to the generated `.tgz` file.
npm install path/to/waspid-ui-x.x.x.tgz
```

## Publishing

This package is automatically published to npm **when a version bump is merged to the main branch**. See [PUBLISHING.md](./PUBLISHING.md) for detailed information about the publishing process.

## License

MIT
