# MCP (Model Context Protocol) Guide

## What is MCP?

Model Context Protocol (MCP) is an open standard that allows Claude to connect to external services and data sources through a structured server/client protocol. Each MCP server exposes a set of **tools** that Claude can call during a session — enabling capabilities that go beyond the built-in toolset.

In this project, MCP servers are used to extend Claude with access to AEM content services, browser automation via Playwright, and Adobe design-system component documentation via React Aria and React Spectrum.

---

## Available MCP Servers

### aem-content-services

**Config file:** `mcp/.mcp.aem.json`

**Purpose:** Connects Claude to Adobe Experience Manager (AEM) Cloud Services via the Odin/Loki MCP endpoint. This allows Claude to read, search, and manage AEM content fragments, models, localization, and publication workflows without leaving the Claude session.

**Configuration:**

```json
{
  "mcpServers": {
    "aem-content-services": {
      "command": "bash",
      "args": ["mcp/aem-mcp-bridge.sh"]
    }
  }
}
```

The server is launched by running `aem-mcp-bridge.sh` (see the [Bridge Script](#the-aem-mcp-bridgesh-script) section below). The script sources credentials from the project `.env` file and proxies requests to `https://mcp.adobeaemcloud.com/adobe/mcp/loki/prod` over HTTP using `mcp-remote`.

**Required environment variables (in `.env`):**

| Variable | Description |
|---|---|
| `AEM_ACCESS_TOKEN` | Adobe IMS bearer token for authentication |
| `AEM_AUTHOR_URL` | AEM author instance URL, e.g. `https://author-p22655-e155390.adobeaemcloud.com` |

**Tools provided:**

- Search and list content fragment models
- Get content fragments and their data
- Search content fragments
- Preview content delivery
- Manage localization and translations
- Handle publication workflows

---

### playwright

**Config file:** `mcp/.mcp.playwright.json`

**Purpose:** Provides browser automation and end-to-end testing capabilities directly within a Claude session. Claude can navigate pages, interact with UI elements, take screenshots, and record video of test runs.

**Configuration:**

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "@playwright/mcp@latest",
        "--isolated",
        "--config",
        "./mcp/.mcp.playwright.config.json"
      ]
    }
  }
}
```

The `--isolated` flag ensures each session gets a fresh browser context. Browser behavior is controlled by the companion config file `mcp/.mcp.playwright.config.json`:

```json
{
  "browser": {
    "browserName": "chromium",
    "launchOptions": {
      "headless": true
    },
    "contextOptions": {
      "recordVideo": {
        "dir": ".qa-reports/playwright/videos",
        "size": { "width": 1920, "height": 1080 }
      },
      "viewport": { "width": 1920, "height": 1080 }
    }
  }
}
```

Key settings:

- **Browser:** Chromium, headless mode
- **Viewport:** 1920x1080
- **Video recording:** Enabled; output written to `.qa-reports/playwright/videos/`

**Tools provided:** Navigation, element interaction, screenshot capture, form filling, assertion helpers, and video-recorded test runs.

---

### fluffyjaws

**Config file:** `mcp/.mcp.fluffy.json`

**Purpose:** Connects to the internal FluffyJaws service at `https://fluffyjaws.adobe.com`. This is an Adobe-internal MCP endpoint exposed via the `fj` CLI binary.

**Configuration:**

```json
{
  "mcpServers": {
    "fluffyjaws": {
      "command": "fj",
      "args": ["mcp", "--api", "https://fluffyjaws.adobe.com"]
    }
  }
}
```

**Prerequisite:** The `fj` CLI must be installed and available on `$PATH`.

**Tools provided:** Determined by the FluffyJaws service API. Consult the FluffyJaws internal documentation for the full tool listing.

---

### react-aria

**Config file:** `mcp/.mcp.react-aria.json`

**Purpose:** Provides Claude with access to React Aria component documentation, API references, and usage patterns. Useful when building or testing accessible UI components.

**Configuration:**

```json
{
  "mcpServers": {
    "react-aria": {
      "command": "npx",
      "args": ["@react-aria/mcp@latest"]
    }
  }
}
```

**Tools provided:** React Aria component lookup, prop documentation, accessibility guidance, and usage examples.

---

### react-spectrum-s2

**Config file:** `mcp/.mcp.react-spectrum-s2.json`

**Purpose:** Provides Claude with access to React Spectrum Spectrum 2 (S2) component documentation and design tokens. Useful when working with Adobe's design system.

**Configuration:**

```json
{
  "mcpServers": {
    "react-spectrum-s2": {
      "command": "npx",
      "args": ["@react-spectrum/mcp@latest"]
    }
  }
}
```

**Tools provided:** React Spectrum S2 component lookup, design token references, theming guidance, and component API documentation.

---

### spectrum (combined)

**Config file:** `mcp/.mcp.spectrum.json`

**Purpose:** A convenience configuration that enables both `react-aria` and `react-spectrum-s2` servers in a single file. Use this when working on tasks that require both design system libraries simultaneously.

**Configuration:**

```json
{
  "mcpServers": {
    "react-aria": {
      "command": "npx",
      "args": ["@react-aria/mcp@latest"]
    },
    "react-spectrum-s2": {
      "command": "npx",
      "args": ["@react-spectrum/mcp@latest"]
    }
  }
}
```

**Tools provided:** All tools from both `react-aria` and `react-spectrum-s2` servers.

---

## Configuration

### How MCP servers are enabled in settings.json

The project-level Claude settings file is at `.claude/settings.json`. It contains:

```json
"enableAllProjectMcpServers": true
```

This flag tells Claude Code to automatically activate any MCP server registered in the active MCP config file. No additional per-server opt-in is required once a config file is loaded.

The `settings.json` file does not hardcode specific MCP server entries — the active servers are controlled entirely by whichever `--mcp-config` file is passed at session start.

### How to switch between configs

Pass the desired config file with the `--mcp-config` flag when starting Claude Code:

```bash
# AEM Content Services only
claude --mcp-config mcp/.mcp.aem.json

# Playwright only
claude --mcp-config mcp/.mcp.playwright.json

# React Aria + React Spectrum S2 together
claude --mcp-config mcp/.mcp.spectrum.json

# FluffyJaws
claude --mcp-config mcp/.mcp.fluffy.json

# Combine multiple configs in one session
claude --mcp-config mcp/.mcp.aem.json --mcp-config mcp/.mcp.playwright.json
```

Only configs explicitly passed via `--mcp-config` are active for that session. There is no always-on default MCP server.

### The aem-mcp-bridge.sh script

The AEM config does not call `npx` directly. Instead it delegates to `mcp/aem-mcp-bridge.sh`, which handles credential injection:

```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Source .env variables
set -a
source "$PROJECT_DIR/.env"
set +a

exec npx -y mcp-remote@latest \
  "https://mcp.adobeaemcloud.com/adobe/mcp/loki/prod" \
  --transport http-only \
  --header "Authorization: Bearer ${AEM_ACCESS_TOKEN}" \
  --header "X-AEM-Author-URL: ${AEM_AUTHOR_URL}"
```

The script:

1. Resolves the project root relative to its own location (so it works regardless of the working directory Claude was started from).
2. Sources the project `.env` file using `set -a` / `set +a` so all variables are exported to the child process environment.
3. Uses `mcp-remote` to bridge the local stdio MCP protocol to the remote HTTP endpoint, injecting the `Authorization` and `X-AEM-Author-URL` headers on every request.

This pattern keeps credentials out of the JSON config file and out of source control.

---

## Adding New MCP Servers

### JSON config format

Create a new file in `mcp/` named `.mcp.<name>.json`. The structure follows the standard MCP server config schema:

```json
{
  "mcpServers": {
    "<server-name>": {
      "command": "<executable>",
      "args": ["<arg1>", "<arg2>"],
      "env": {
        "OPTIONAL_ENV_VAR": "value"
      }
    }
  }
}
```

Fields:

| Field | Required | Description |
|---|---|---|
| `command` | Yes | Executable to run (e.g. `npx`, `node`, `bash`, a CLI binary) |
| `args` | Yes | Array of arguments passed to `command` |
| `env` | No | Key/value pairs injected into the server process environment |

If the server requires credentials, prefer the bridge-script pattern used by AEM: put a shell script in `mcp/` that sources `.env` and execs the real command. Reference the script in `args` from the JSON config.

### Combining multiple servers

A single JSON config file can register multiple servers under `mcpServers`. See `.mcp.spectrum.json` for an example that bundles `react-aria` and `react-spectrum-s2` together.

### Registration in settings

No changes to `.claude/settings.json` are needed. The `"enableAllProjectMcpServers": true` setting already activates every server defined in whichever config file is passed to `--mcp-config`. Simply pass the new file path when starting Claude Code:

```bash
claude --mcp-config mcp/.mcp.<name>.json
```

### Security guidelines

- Never hardcode tokens or passwords in `.json` config files.
- Add `.env` to `.gitignore` and use `.env.sample` to document required variables.
- Rotate `AEM_ACCESS_TOKEN` regularly.
- Use the bridge-script pattern for any server that needs credentials loaded from the environment.
