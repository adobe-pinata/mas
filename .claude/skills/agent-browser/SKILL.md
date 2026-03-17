---
name: agent-browser
description: Automates browser interactions for AI agents via the agent-browser CLI. Token-efficient snapshots (~200-400 tokens). No MCP needed. Use when asked to navigate pages, click elements, fill forms, take screenshots, or validate web UI behavior.
---

# agent-browser

AI-optimized headless browser automation via the `agent-browser` command (Rust-based client-daemon architecture).

**Install:** `npm install -g agent-browser` then `agent-browser install`

**Core pattern:** `open` → `snapshot -i` (get `@refs`) → act with `@ref` → `screenshot` → repeat.

## Session (always use)
- `--session <name>` — Isolated browser instance (cookies, storage, history). Always pass on every command to avoid stale state.
- `--profile <path>` — Persistent state across restarts (cookies, localStorage, IndexedDB)
- `--state <path>` — Load pre-saved auth from JSON file

## Navigation
- `agent-browser open <url>` — Navigate to URL (also: `goto`, `navigate`)
- `agent-browser close` — Close browser

## Snapshot (read page state)
- `agent-browser snapshot -i` — Interactive elements with @refs (buttons, links, inputs)
- `agent-browser snapshot -i -c` — Compact (removes empty structural nodes)
- `agent-browser snapshot -i -d <n>` — Limit tree depth
- `agent-browser snapshot -i -s <sel>` — Scope to CSS selector

## Element selection (4 mechanisms)
- `@e1`, `@e2` — Refs from snapshot (preferred, AI-stable)
- `#id`, `.class`, `div > button` — CSS selectors
- `find role button` / `find label "Email"` / `find text "Sign In"` — Semantic/accessibility locators
- `text=Submit` / `xpath=//button` — Direct match

## Actions
- `agent-browser click <@ref|sel>` — Click element
- `agent-browser fill <@ref|sel> <text>` — Clear and fill input
- `agent-browser type <@ref|sel> <text>` — Type without clearing
- `agent-browser press <key>` — Keyboard key (Enter, Tab, Escape)
- `agent-browser hover <@ref|sel>` — Hover over element
- `agent-browser scroll <up|down|left|right>` — Scroll viewport
- `agent-browser upload <@ref|sel> <file>` — File input upload
- `agent-browser dialog accept [text]` / `dialog dismiss` — Handle browser dialogs

## Get page info
- `agent-browser get text <@ref|sel>` — Visible text
- `agent-browser get html <@ref|sel>` — Inner HTML
- `agent-browser get value <@ref|sel>` — Input field value
- `agent-browser get title` — Page title
- `agent-browser get url` — Current URL
- `agent-browser get box <@ref|sel>` — Element dimensions
- `agent-browser get styles <@ref|sel>` — Computed CSS

## Screenshot
- `agent-browser screenshot [path]` — Viewport capture
- `agent-browser screenshot [path] --full` — Full-page capture
- `agent-browser screenshot [path] --annotate` — Overlay numbered labels on interactive elements
- `--screenshot-dir <path>` — Output directory
- `--screenshot-format jpeg|png` — Image format
- `--screenshot-quality 0-100` — JPEG quality

## Wait
- `agent-browser wait <selector>` — Wait for element visibility
- `agent-browser wait <ms>` — Wait for duration
- `agent-browser wait --text "string"` — Wait for content to appear
- `agent-browser wait --url "**/pattern"` — Wait for navigation
- `agent-browser wait --fn "expression"` — Wait for JS condition

## JavaScript
- `agent-browser eval <js>` — Run JavaScript and return result

## Diff / regression detection
- `agent-browser diff snapshot` — Compare accessibility tree to last snapshot
- `agent-browser diff snapshot --baseline <file>` — Compare to saved baseline
- `agent-browser diff screenshot --baseline <file>` — Visual pixel comparison
- `agent-browser diff url <url1> <url2>` — Compare two pages

## Cookies & Storage
- `agent-browser cookies` — List cookies
- `agent-browser cookies set <name> <val>` — Set cookie
- `agent-browser cookies clear` — Clear all cookies
- `agent-browser storage local` / `storage session` — Read storage
- `agent-browser storage local set <key> <val>` — Write to localStorage

## Tabs & Windows
- `agent-browser tab` — List tabs
- `agent-browser tab new` — New tab
- `agent-browser tab <n>` — Switch to tab N
- `agent-browser window new` — New window

## Browser config
- `agent-browser set viewport <w> <h>` — Set dimensions
- `agent-browser set device <name>` — Emulate device (e.g. "iPhone 14")
- `agent-browser set geo <lat> <lng>` — Set geolocation
- `agent-browser set offline [on|off]` — Toggle offline mode
- `agent-browser set media dark|light` — Color scheme
- `agent-browser set headers <json>` — HTTP headers
- `agent-browser set credentials <user> <pass>` — Basic auth

## Debugging
- `agent-browser console` — Browser console messages
- `agent-browser errors` — Uncaught exceptions
- `agent-browser highlight <sel>` — Visually mark element
- `agent-browser trace start [path]` / `trace stop` — Record interaction trace
- `agent-browser profiler start` / `profiler stop` — CPU profiling

## Network
- `agent-browser network route <url> --abort` — Block requests
- `agent-browser network route <url> --body <json>` — Mock response

## Global flags
- `--session <name>` — Isolated session
- `--headed` — Show browser window
- `--json` — Machine-readable output
- `--full` — Full-page screenshot
- `--args "<chromium-args>"` — Pass Chromium launch args (comma-separated)
- `AGENT_BROWSER_ARGS` env var — Alternative to `--args`
- `AGENT_BROWSER_DEFAULT_TIMEOUT` — Timeout in ms (default: 25000)

> For any command not listed above, run `agent-browser <command> --help` before guessing.
