---
name: creating-new-skills
description: Creates new Agent Skills for AI Agents following best practices and documentation. Use when the user wants prompts 'create a new skill ...', 'use your meta skill to ...', or 'wrap this CLI/API as a skill'.
---

# Purpose

Create new Agent Skills for AI Agents by following a structured workflow based on best practices and progressive disclosure patterns.

## Instructions

Before starting, read the comprehensive documentation files in the [docs/](docs/) directory for complete context:

1. [docs/claude_code_agent_skills.md](docs/claude_code_agent_skills.md) - Complete guide to creating and managing skills
2. [docs/claude_code_agent_skills_overview.md](docs/claude_code_agent_skills_overview.md) - Architecture and how skills work
3. [docs/blog_equipping_agents_with_skills.md](docs/blog_equipping_agents_with_skills.md) - Design principles and best practices

### Understanding Skills

What is a Skill?
- A directory containing a SKILL.md file with YAML frontmatter
- Instructions that Claude loads on-demand when relevant
- Optional supporting files (scripts, documentation, templates)

Three Sources of Skills:
1. Personal Skills: ~/.claude/skills/ - Available across all projects
2. Project Skills: .claude/skills/ - Shared with team via git
3. Plugin Skills: Bundled with Claude Code plugins

Progressive Disclosure (3 Levels):
1. Metadata (always loaded): name and description in YAML frontmatter
2. Instructions (loaded when triggered): Main body of SKILL.md
3. Resources (loaded as needed): Additional files, scripts, --help output

---

## Step 1 — Determine the Source Type

Before creating anything, identify what you're wrapping:

### Path A: Existing CLI Tool
The tool already has a CLI with --help support.
- Run <tool> --help to discover capabilities
- Run <tool> <subcommand> --help for each useful subcommand
- Do NOT create Python wrapper scripts — invoke the CLI directly via bash
- SKILL.md teaches the agent to use the CLI; agent discovers flags via --help at runtime
- Only create scripts/ if a task requires orchestrating multiple CLI commands together

→ Follow the CLI-First Workflow (Step 2A)

### Path B: Raw API (No CLI Exists)
You're wrapping an HTTP API, SDK, or service with no existing CLI.
- Create Python scripts in scripts/, one per capability
- Each script is self-contained with --help, --json, and inline uv dependencies
- SKILL.md lists scripts; agent discovers usage via --help

→ Follow the Script-Based Workflow (Step 2B)

### Path C: Complex Workflow (Multiple Tools/APIs)
Combines multiple CLIs, APIs, or multi-step orchestration.
- Mix of direct CLI commands and custom scripts
- Scripts only for orchestration that combines multiple steps
- SKILL.md maps conditions to tools/scripts

→ Follow the Hybrid Workflow (Step 2C)

---

## Step 2A — CLI-First Workflow

### Discover
<tool> --help
<tool> <subcommand> --help   # for each subcommand
### Filter Commands
Identify which commands an agent would actually use. Skip:
- Interactive/TUI commands (repl, interactive modes)
- Admin commands (login, logout, update, version)
- Meta commands (mcp, config, setup)
- Anything that requires human interaction

### Create the Skill
mkdir -p .claude/skills/<cli-name>
SKILL.md format:
---
name: <cli-name>
description: <What it does and when to use it — written in third person. Include trigger words.>
---
# <CLI Name>

<One-line purpose.>

**Auth:** <requirements, or "None">

## Commands
- `<cli> <cmd>` — <one-line description>
- `<cli> <cmd>` — <one-line description>

## Key Options
- `--flag` — <what it does>

> Run `<cli> --help` for full reference.
Rules for CLI-First skills:
- Keep SKILL.md under 30 lines — the agent runs --help when it needs more detail
- No Python wrappers unless orchestrating multiple commands
- Write description in third person for skill discovery
- Include auth requirements if the CLI needs login/tokens

---

## Step 2B — Script-Based Workflow

### Discover the API
Review API documentation, endpoints, authentication requirements.

### Create the Skill Structure
mkdir -p .claude/skills/<skill-name>/scripts
### Write Scripts
Each script must:
- Handle ONE capability (single responsibility)
- Be fully self-contained (no shared imports between scripts)
- Include inline uv dependency metadata:
# /// script
  # requires-python = ">=3.10"
  # dependencies = ["httpx"]
  # ///
- Implement --help with: purpose, all arguments, at least one example
- Implement --json flag for structured output:
  - Success: {"result": ...}
  - Failure: {"error": "<message>", "exit_code": N} with sys.exit(N)
- Embed all shared logic (HTTP client, auth, formatting) inline — duplication is acceptable for isolation
- Be executable: chmod +x scripts/*.py
- Skip wrapping operations that are trivial one-liners with no structured output need

### Write SKILL.md
---
name: <skill-name>
description: <What it does and when to use it — written in third person.>
---
# <Skill Name>

<One-line purpose.>

**Auth:** <env var, login command, or "None">

## Scripts
- `scripts/status.py` — <one-line description>
- `scripts/list.py` — <one-line description>
- `scripts/get.py` — <one-line description>

> Do NOT read script source code. Run `uv run scripts/<name>.py --help`
> to discover usage only when needed.
Rules for Script-Based skills:
- Name scripts as <verb_or_capability>.py (not `script_1.py`)
- Keep SKILL.md under 30 lines
- Agent discovers scripts via --help only when needed (progressive disclosure)

---

## Step 2C — Hybrid Workflow

For complex workflows that combine CLI tools and custom scripts:

1. Map conditions to tools:
   - "When user asks about X" → cli-tool command
   - "When user needs Y" → scripts/orchestrate_y.py

2. Direct CLI commands for simple operations
3. Scripts only for multi-step orchestration or when the CLI doesn't support an operation

SKILL.md structure:
## CLI Commands
- `tool cmd` — <description>

## Scripts (for complex operations)
- `scripts/workflow.py` — <description>

> For CLI: run `tool --help`. For scripts: run `uv run scripts/<name>.py --help`.
---

## Step 3 — Frontmatter Requirements

- `name`: Required. Max 64 chars. Lowercase letters, numbers, hyphens only. Use gerund form: processing-pdfs, querying-api.
- `description`: Required. Max 1024 chars. Must be third person. Include BOTH what it does AND when to use it. Mention trigger words/phrases.
  - ✅ "Queries the Kalshi prediction market API. Use when user asks about markets, predictions, or event odds."
  - ❌ "I help you query markets"
- `allowed-tools` (optional): Restrict which tools Claude can use (e.g., `Read, Grep, Glob`)

---

## Step 4 — Test the Skill

1. Verify structure:
ls -la .claude/skills/<skill-name>/
2. Check frontmatter:
head -5 .claude/skills/<skill-name>/SKILL.md
3. Test with queries that should trigger the skill
4. Verify Claude discovers and uses it correctly
5. Iterate: refine description if skill doesn't trigger, clarify instructions if Claude struggles

---

## Step 5 — Commit
git add .claude/skills/<skill-name>
git commit -m "Add <skill-name> skill"
---

## Best Practices Summary

Choosing the right path:
- CLI exists → Path A (CLI-First). Always prefer this — zero wrapper overhead.
- No CLI, just API → Path B (Script-Based). One script per capability.
- Multiple tools/APIs → Path C (Hybrid). CLI for simple, scripts for orchestration.

Context efficiency:
- MCP server: ~10,000 tokens loaded upfront
- CLI-First skill: ~15-30 lines (~200 tokens)
- Script-Based skill: ~15-30 lines + --help on demand
- The goal: agent loads minimal context, discovers details progressively

Description writing:
- Always third person (descriptions are injected into system prompt)
- Include trigger words the user would say
- Be specific: "Queries Stripe billing data" > "Helps with payments"

Skill scope:
- One skill = one tool/capability
- Don't combine unrelated tasks
- Keep SKILL.md under 30 lines (CLI) or 500 lines (complex)

File references:
- Use relative paths: [file.md](file.md)
- Always forward slashes: scripts/helper.py

---

## Examples

### Example 1: CLI-First (wrapping gh CLI)
/create-skill gh
Discovery: gh --help → subcommands: issue, pr, run, api, repo...

Generated .claude/skills/github-cli/SKILL.md:
---
name: github-cli
description: Manages GitHub repos, issues, PRs, and CI via the gh CLI. Use when user asks about GitHub operations, pull requests, issues, or CI status.
---

# GitHub CLI

GitHub operations via the `gh` command.

**Auth:** `gh auth login`

## Commands
- `gh issue list` — List issues with filters
- `gh issue create` — Create a new issue
- `gh pr list` — List pull requests
- `gh pr create` — Create a pull request
- `gh pr merge` — Merge a pull request
- `gh run list` — List CI workflow runs
- `gh run view` — View CI run details
- `gh api` — Raw GitHub API calls

> Run `gh <command> --help` for full usage.
### Example 2: Script-Based (wrapping a REST API)

Discovery: API docs show endpoints for /status, /markets, /trades

Generated .claude/skills/trading-api/SKILL.md:
---
name: trading-api
description: Queries the trading platform API for market data, trades, and account status. Use when user asks about markets, positions, or trading data.
---

# Trading API

Market data and trading operations.

**Auth:** Set `TRADING_API_KEY` environment variable.

## Scripts
- `scripts/status.py` — Check exchange status
- `scripts/markets.py` — List/filter markets
- `scripts/trades.py` — Recent trade history
- `scripts/search.py` — Search markets by keyword

> Do NOT read script source. Run `uv run scripts/<name>.py --help` to discover usage.

### Example 3: Hybrid (CLI + orchestration scripts)
---
name: deploy-pipeline
description: Manages deployment pipeline via kubectl and custom scripts. Use when user asks about deployments, rollbacks, or cluster status.
---

# Deploy Pipeline

Kubernetes deployments with orchestration.

**Auth:** `kubectl` configured with cluster access.

## CLI Commands
- `kubectl get pods` — List running pods
- `kubectl logs <pod>` — View pod logs
- `kubectl rollout status` — Check rollout progress

## Scripts (multi-step operations)
- `scripts/deploy.py` — Full deploy: build → push → apply → verify
- `scripts/rollback.py` — Rollback with health check

> CLI: `kubectl --help`. Scripts: `uv run scripts/<name>.py --help`.