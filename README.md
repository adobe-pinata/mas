# agentic-harness

Autonomous Developer Workflow (ADW) orchestration platform that combines deterministic Python orchestration with Claude Code AI agents to execute end-to-end software development workflows — from planning through building, testing, reviewing, documenting, and shipping — all running in isolated git worktrees for parallel execution.

## Architecture

| Layer | What it does |
|---|---|
| `adws/` | Python orchestration — spawns Claude agents through phases (plan → build → test → review → document → ship) with persistent state per workflow |
| `.claude/commands/` | 30+ slash command templates that Claude executes (`/feature`, `/implement`, `/review`, `/test`, etc.) |
| `.claude/commands/experts/` | Domain expertise YAML files (ADW, QA server, QA client, integrations) — living knowledge docs that inform planning |
| `.claude/skills/` | 8 agent capabilities (browser automation, React Spectrum, Adobe I/O, meta-skill creation, etc.) |
| `.claude/hooks/` | Event interceptors — blocks dangerous commands, logs tool calls, sends notifications, auto-formats code |
| `.claude/agents/` | 14 specialized sub-agent definitions (batch-fix, playwright-validator, build-agent, etc.) |
| `mcp/` | Model Context Protocol configs for Playwright, React Spectrum, AEM, etc. |
| `scripts/` | Shell utilities for port checking, worktree cleanup, PR management |

## How ADW Works

A user triggers a workflow (e.g. `plan_build_review`) on a GitHub issue → Python orchestrator creates an isolated worktree → spawns Claude agents phase-by-phase → each phase reads/writes persistent state → commits, pushes, creates PRs — all autonomously with real-time WebSocket visibility.

```
Issue #207: "Improve Slack UX"

uv run adws/adw_plan_iso.py 207 a954f660
  ├─ Fetch issue from GitHub
  ├─ Create worktree: trees/a954f660/
  ├─ Classify issue → /feature
  ├─ Run /feature agent → generates spec
  ├─ Commit plan, create PR
  └─ Save state to agents/a954f660/adw_state.json

uv run adws/adw_build_iso.py 207 a954f660
  ├─ Load state (has plan file path)
  ├─ Run /implement agent with spec
  ├─ Commit changes, update PR
  └─ Save state

uv run adws/adw_review_iso.py 207 a954f660
  ├─ Run /review agent against spec
  ├─ Capture screenshots, generate risk report
  └─ Post results as GitHub comment
```

## Workflow Types

| Workflow | Phases | Use Case |
|----------|--------|----------|
| `plan_build` | Plan → Build | Quick features |
| `plan_build_test` | Plan → Build → Test | Quality-focused |
| `plan_build_review` | Plan → Build → Review | Risk assessment |
| `plan_build_test_review` | Plan → Build → Test → Review | Comprehensive QA |
| `plan_build_document` | Plan → Build → Document | With docs |
| `sdlc` | Plan → Build → Test → Review → Document | Full SDLC |
| `sdlc_zte` | Plan → Build → Test → Review → Document → Ship | Full + auto-deploy |

## Key Design Decisions

- **Isolated worktrees** — each ADW gets its own `git worktree` under `trees/{adw_id}/` enabling parallel execution without conflicts
- **Persistent state** — `agents/{adw_id}/adw_state.json` tracks issue, branch, plan file, ports, model config across phases
- **Model selection** — Sonnet for most tasks, Opus for complex planning/review/fix
- **Deterministic + non-deterministic** — Python handles predictable orchestration; Claude agents handle creative reasoning
- **Domain expertise** — `expertise.yaml` files capture architecture, patterns, and gotchas so agents plan with full context

## Setup

```bash
cp .env.example .env
# Fill in required values (see comments in .env.example)
npm install
```

## Tech Stack

- **Orchestration:** Python 3.8+, uv, Pydantic
- **AI:** Claude Code CLI, Model Context Protocol (MCP)
- **Git:** Worktrees, GitHub CLI (`gh`)
- **Notifications:** Slack SDK, GitHub API
- **Infrastructure:** Adobe App Builder (AIO Runtime / OpenWhisk)
