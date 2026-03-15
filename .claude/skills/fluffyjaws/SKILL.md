---
name: fluffyjaws
description: Sends one-shot chat messages or starts an MCP server via the fj CLI. Use when the user wants to chat with FluffyJaws AI, query it with a question, or configure it as an MCP server for Cursor/Codex/Claude.
---

# fluffyjaws

AI chat and MCP server via the `fj` command.

**Auth:** `fj login` (browser flow) or set `FJ_SESSION_ID` env var.

## Commands
- `fj chat "question"` — One-shot chat query
- `fj mcp` — Start MCP stdio server for Cursor/Codex/Claude

## Key Options
- `--model <name>` — Fast-mode model (default: gpt-5.1)
- `--reasoning fast|thinking` — Reasoning mode (default: thinking)
- `--thinking` / `--fast` — Shortcut for reasoning mode
- `--api <url>` — API host (default: http://localhost:3000)
- `--session <id>` — Override session cookie

> Run `fj --help` for full reference.
