---
name: agent-browser
description: Automates browser interactions for AI agents via the agent-browser CLI. Token-efficient snapshots (~200-400 tokens). No MCP needed. Use when asked to navigate pages, click elements, fill forms, take screenshots, or validate web UI behavior.
---

# agent-browser

AI-optimized headless browser automation via the `agent-browser` command.

**Auth:** None. Run `agent-browser install` once to install browser binaries.

**Core pattern:** `open` → `snapshot -i` (get `@refs`) → act with `@ref` → `screenshot` → repeat.

## Commands
- `agent-browser open <url>` — Navigate to URL
- `agent-browser snapshot -i` — Interactive elements with @refs (compact, AI-readable)
- `agent-browser click <@ref|sel>` — Click element
- `agent-browser fill <@ref|sel> <text>` — Clear and fill input
- `agent-browser type <@ref|sel> <text>` — Type into element
- `agent-browser press <key>` — Keyboard press (Enter, Tab, Escape)
- `agent-browser screenshot [path]` — Capture screenshot
- `agent-browser get text|url|title [sel]` — Extract content
- `agent-browser wait <sel|ms>` — Wait for element or time
- `agent-browser eval <js>` — Run JavaScript
- `agent-browser scroll <up|down> [px]` — Scroll page
- `agent-browser set geo <lat> <lng>` — Set geolocation (for geo-specific content)
- `agent-browser close` — Close browser

## Key Options
- `--session <name>` — Isolated session for concurrent runs
- `--full` — Full-page screenshot
- `--json` — Structured output
- `--headed` — Show browser window

> For commands not listed above, run `agent-browser <command> --help` before guessing.
