# Skills Guide

## What is a Skill?

A Skill is a directory containing a `SKILL.md` file that packages instructions, metadata, and optional resources (scripts, templates, reference documents) that Claude loads automatically when relevant to a task.

The concept is modeled on writing an onboarding guide for a new team member. Instead of building custom one-off prompts for every recurring task, you capture domain-specific expertise once, and Claude discovers and applies it automatically in future conversations.

Skills differ from prompts in a key way: prompts are conversation-level instructions you provide each time. Skills live on the filesystem and load on demand — Claude knows they exist at startup (from their metadata), but only reads the full content when triggered by a matching task.

### Progressive Disclosure

Skills are designed around a three-level loading system that keeps context usage minimal. Claude loads only what each task actually requires.

**Level 1 — Metadata (always loaded, ~100 tokens per skill)**

The YAML frontmatter at the top of every `SKILL.md` is loaded into Claude's system prompt at startup. This is the only content Claude sees until a task triggers the skill.

```yaml
---
name: pdf-processing
description: Extracts text and tables from PDF files, fills forms, and merges documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
---
```

Claude uses just the `name` and `description` to decide whether to trigger the skill. Because only these ~100 tokens are loaded per skill, you can install many skills without a meaningful context penalty.

**Level 2 — Instructions (loaded when triggered, under 5k tokens ideally)**

When Claude determines a skill is relevant, it reads the full body of `SKILL.md` from the filesystem via bash. This is where workflows, best practices, command references, and guidance live.

**Level 3 — Resources (loaded as needed, effectively unlimited)**

Skills can bundle additional files — extra markdown docs, executable scripts, templates, schemas — inside the skill directory. Claude reads or runs these only when the task requires them. Because code executes without loading into context (only output is returned), and reference files are read on demand rather than upfront, there is no practical limit on bundled content.

| Level | When Loaded | Token Cost | Content |
|---|---|---|---|
| Metadata | Always (at startup) | ~100 tokens per skill | `name` and `description` from YAML frontmatter |
| Instructions | When skill is triggered | Under 5k tokens | SKILL.md body |
| Resources | As needed | Effectively unlimited | Bundled files, scripts, reference docs |

### Skill Locations

Three locations are supported in Claude Code:

- **Personal skills**: `~/.claude/skills/` — available across all your projects
- **Project skills**: `.claude/skills/` — checked into git and shared with the team
- **Plugin skills**: bundled with Claude Code plugins

---

## Available Skills

The following skills are installed in this project under `.claude/skills/`.

---

### meta-skill

**Purpose:** Creates new Agent Skills for AI agents by following a structured workflow based on best practices and progressive disclosure patterns.

**Trigger:** Activates when the user says things like "create a new skill ...", "use your meta skill to ...", or "wrap this CLI/API as a skill".

**Key capabilities:**
- Identifies the right skill type (CLI-first, script-based, or hybrid) based on what is being wrapped
- Discovers CLI capabilities via `--help` without reading source code
- Generates correctly structured `SKILL.md` with proper frontmatter
- Writes self-contained Python scripts (one per capability) for API-based skills
- Provides rules for frontmatter naming conventions and description writing

**Resources:**
- `docs/claude_code_agent_skills.md` — Complete guide to creating and managing skills
- `docs/claude_code_agent_skills_overview.md` — Architecture and how skills work
- `docs/blog_equipping_agents_with_skills.md` — Design principles and best practices

---

### skill-creator

**Purpose:** Creates new skills, modifies and improves existing skills, and measures skill performance through an iterative draft-test-evaluate-improve loop.

**Trigger:** Activates when users want to create a skill from scratch, edit or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy.

**Key capabilities:**
- Captures intent through structured interviews before writing anything
- Writes `SKILL.md` drafts and iterates based on test results
- Spawns parallel subagent runs (with-skill and baseline) to compare outputs
- Grades runs against quantitative assertions and surfaces them in an eval viewer
- Runs an automated description optimization loop (`scripts/run_loop.py`) to improve trigger accuracy
- Packages finished skills as `.skill` files for distribution
- Adapts workflow for Claude.ai (no subagents), Claude Code, and Cowork environments

**Resources:**
- `agents/grader.md` — Instructions for evaluating assertions against outputs
- `agents/comparator.md` — Instructions for blind A/B comparison between two outputs
- `agents/analyzer.md` — Instructions for analyzing why one version outperformed another
- `references/schemas.md` — JSON structures for `evals.json`, `grading.json`, `benchmark.json`
- `assets/eval_review.html` — Template for the trigger eval review UI
- `eval-viewer/generate_review.py` — Script that generates the qualitative review viewer
- `scripts/aggregate_benchmark.py` — Aggregates per-run grading into benchmark summary
- `scripts/run_loop.py` — Automated description optimization loop
- `scripts/package_skill.py` — Packages a skill directory as a `.skill` file

---

### fluffyjaws

**Purpose:** Sends one-shot chat messages or starts an MCP server via the `fj` CLI.

**Trigger:** Activates when the user wants to chat with FluffyJaws AI, query it with a question, or configure it as an MCP server for Cursor/Codex/Claude.

**Key capabilities:**
- One-shot chat queries: `fj chat "question"`
- Starts an MCP stdio server for use in Cursor, Codex, or Claude: `fj mcp`
- Configurable reasoning mode (fast or thinking) and model selection

**Resources:** None bundled. Run `fj --help` for full reference.

**Auth:** `fj login` (browser flow) or set `FJ_SESSION_ID` environment variable.

---

### aio

**Purpose:** Manages Adobe I/O App Builder apps, OpenWhisk Runtime actions, Developer Console projects, and Adobe Events via the `aio` CLI.

**Trigger:** Activates when the user asks about deploying, building, or running Adobe I/O apps, App Builder, runtime actions, activations, console workspaces, or Adobe Events.

**Key capabilities:**
- Full App Builder lifecycle: `aio app init`, `build`, `deploy`, `undeploy`, `run`, `dev`, `logs`
- Runtime/OpenWhisk actions, activations, packages, namespaces, triggers, and rules via `aio runtime`
- Developer Console navigation: orgs, projects, workspaces via `aio console`
- Adobe Events: providers, registrations, and event metadata via `aio event`
- Context inspection with `aio where`

**Resources:**
- `docs/workflow.md` — Auth through Console setup, Build, Deploy, Logs; common gotchas and `app.config.yaml` reference
- `docs/app-builder-overview.md` — App Builder concepts
- `docs/first-app-guide.md` — Step-by-step first app walkthrough
- `docs/runtime-using.md` — Runtime actions, web actions, triggers, rules
- `docs/aio-cli-readme.md` — Core CLI reference
- `docs/aio-cli-plugin-app.md` — `aio app` command details
- `docs/aio-cli-plugin-runtime.md` — `aio runtime` command details

**Auth:** `aio login` (IMS OAuth). Check current context with `aio where`.

---

### meta-experts

**Purpose:** Generates a complete expert set for a codebase domain — an `expertise.yaml` knowledge document plus four slash commands (`plan`, `question`, `self-improve`, `plan_build_improve`) under `.claude/commands/experts/<domain>/`.

**Trigger:** Activates when the user says "create an expert for...", "add experts for...", or "use meta-experts to...".

**Key capabilities:**
- Explores the real codebase (Glob, Grep) to collect actual file paths, function names, and architectural decisions — never invents facts
- Generates `expertise.yaml` with 150–400 lines of actionable knowledge: key files, patterns, gotchas, best practices
- Produces four command files following the ADW expert pattern
- Validates that every file path in `expertise.yaml` actually exists
- Reports coverage metrics on completion

**Resources:** Uses the `templates/` directory for canonical skeleton files and the `adw/` expert directory as a reference implementation.

**Allowed tools:** Read, Write, Glob, Grep, Bash, TodoWrite

---

### agent-browser

**Purpose:** Automates browser interactions for AI agents via the `agent-browser` CLI with token-efficient snapshots (~200–400 tokens). No MCP server required.

**Trigger:** Activates when asked to navigate pages, click elements, fill forms, take screenshots, or validate web UI behavior.

**Key capabilities:**
- Navigate to URLs, capture interactive-element snapshots with `@ref` handles
- Click, fill, type, press keys, scroll, and evaluate JavaScript
- Capture screenshots (full-page or viewport)
- Extract text, URL, and title from the current page
- Run isolated concurrent sessions with `--session`
- Set geolocation for geo-specific content

**Core interaction pattern:** `open` → `snapshot -i` (get `@refs`) → act with `@ref` → `screenshot` → repeat.

**Resources:** None bundled. Run `agent-browser <command> --help` for any command not listed in the skill.

**Auth:** None. Run `agent-browser install` once to install browser binaries.

---

### react-aria

**Purpose:** Looks up React Aria component documentation — props, examples, usage patterns, and accessibility guidance.

**Trigger:** Activates when building or modifying UI components with React Aria.

**Key capabilities:**
- Lists all available documentation pages with optional descriptions
- Retrieves page metadata (description and section list) before loading full content
- Fetches full component docs or a single named section (e.g., "Props", "Examples", "Accessibility")
- Covers both component pages (`Button`, `ComboBox`, `DatePicker`) and concept pages (`collections`, `styling`, `forms`)

**Resources:** Delivered entirely via MCP tools — no bundled files.

**MCP server:** `react-aria` (must be running — registered in `mcp/.mcp.react-aria.json`).

---

### react-spectrum-s2

**Purpose:** Looks up React Spectrum 2 (S2) component documentation — props, examples, categories, and design patterns for Adobe's Spectrum 2 design system.

**Trigger:** Activates when building or modifying UI with React Spectrum, Spectrum 2, S2 components, or Adobe's design system. Also activates when migrating from Spectrum 1 to S2, searching for the right component for a UI pattern, or checking S2-specific props and styling.

**Key capabilities:**
- Lists all 90 S2 components, optionally filtered by one of 8 categories (Actions, Forms, Collections, Overlays, Content, Status, Navigation, Layout)
- Searches components by name, description, category, or props
- Retrieves full component docs including props, examples, and description

**Resources:** Delivered entirely via MCP tools — no bundled files.

**MCP server:** `react-spectrum-s2` (must be running — registered in `mcp/.mcp.react-spectrum-s2.json`).

**Distinction from react-aria:** Use `react-spectrum-s2` for styled, ready-to-use Adobe design system components. Use `react-aria` for headless, unstyled accessibility primitives when building custom components.

---

## Creating New Skills

### When to Create a Skill

A skill is the right choice when:
- You find yourself giving Claude the same domain context or workflow instructions repeatedly
- A task requires procedural knowledge (sequences of steps, specific commands, error patterns) that Claude doesn't have built in
- You want to share expertise across multiple conversations or with a team via git

### Directory Structure

Every skill requires at minimum:

```
.claude/skills/<skill-name>/
└── SKILL.md
```

For skills that bundle additional content:

```
.claude/skills/<skill-name>/
├── SKILL.md                  (required)
├── scripts/                  (executable code)
│   └── capability.py
├── references/               (docs loaded into context as needed)
│   └── api-reference.md
└── assets/                   (files used in output: templates, icons)
    └── template.docx
```

### SKILL.md Frontmatter Format

Every `SKILL.md` must begin with YAML frontmatter. Only `name` and `description` are required:

```yaml
---
name: skill-name-here
description: What this skill does and when Claude should use it. Written in third person.
---
```

An optional `allowed-tools` field restricts which tools Claude can use when the skill is active:

```yaml
---
name: skill-name-here
description: ...
allowed-tools: Read, Grep, Glob, Bash
---
```

**Frontmatter constraints:**

| Field | Rules |
|---|---|
| `name` | Max 64 characters. Lowercase letters, numbers, and hyphens only. Use gerund form: `processing-pdfs`, `querying-api`. Cannot contain "anthropic" or "claude". |
| `description` | Max 1024 characters. Must be written in third person (it is injected into the system prompt). Include both what it does AND when to use it, with specific trigger words. |

**Description example — correct:**
```
Queries the Kalshi prediction market API for market prices, event odds, and trade history. Use when the user asks about markets, predictions, event odds, or trading data.
```

**Description example — incorrect:**
```
I can help you query markets and get predictions.
```

### Choosing the Right Skill Type

**Path A — CLI-First (preferred when a CLI already exists)**

If the capability has an existing CLI with `--help` support, invoke it directly. Do not write Python wrappers around it.

- Keep `SKILL.md` under 30 lines
- List the commands the agent would actually use; skip interactive, admin, and meta commands
- Tell Claude to run `<cli> --help` at runtime for flag details

**Path B — Script-Based (when wrapping a raw API)**

If there is no CLI — only an HTTP API, SDK, or service — write Python scripts in `scripts/`, one per capability.

Each script must:
- Handle one capability (single responsibility)
- Be fully self-contained (no shared imports between scripts)
- Include inline `uv` dependency metadata (`# /// script` block)
- Implement `--help` with purpose, arguments, and at least one example
- Implement `--json` for structured output (`{"result": ...}` on success, `{"error": "...", "exit_code": N}` on failure)
- Be made executable: `chmod +x scripts/*.py`

In `SKILL.md`, list each script with a one-line description and include the instruction:
```
Do NOT read script source code. Run `uv run scripts/<name>.py --help` to discover usage.
```

**Path C — Hybrid (CLI + orchestration scripts)**

When a task combines multiple CLIs, APIs, or multi-step sequences, use direct CLI commands for simple operations and custom scripts only for orchestration that spans multiple steps.

### Best Practices

**Keep SKILL.md concise.** Target under 30 lines for CLI-first skills, under 500 lines for complex skills. If you approach 500 lines, add another layer of hierarchy and reference the detail in a separate file.

**Explain the why.** Skills work better when they explain the reasoning behind instructions rather than issuing rigid commands. Claude can apply reasoning when it understands the purpose; it can only follow rules when it does not.

**Write descriptions that trigger reliably.** The description is the primary mechanism controlling when a skill fires. Write it to include the specific words and phrases a real user would type. Be slightly "pushy" — list the contexts where the skill should apply rather than the minimal definition of what it does.

**Use progressive disclosure actively.** If certain reference material is only needed for a subset of tasks, put it in a separate file and reference it from `SKILL.md` with guidance on when to read it. Claude will skip it when not needed.

**One skill, one capability.** Don't combine unrelated tasks. A skill that does too many things has a description that is hard to write well and a body that grows bloated.

**Test the trigger, not just the output.** After writing the skill, test it with the kinds of prompts a real user would type. If Claude is not triggering the skill when it should, refine the description. If Claude is using the skill when it should not, tighten the description's "when to use" language.

**Validate paths before shipping.** Every file path referenced in a skill must actually exist. Broken references silently fail.

**Use relative paths with forward slashes.** Always write `scripts/helper.py`, never `./scripts/helper.py` or a platform-specific backslash variant.

### Testing and Iteration

After creating a skill:

1. Verify the directory structure: `ls -la .claude/skills/<skill-name>/`
2. Check the frontmatter parses correctly: `head -5 .claude/skills/<skill-name>/SKILL.md`
3. Test with prompts that should and should not trigger the skill
4. Use the `skill-creator` skill for a structured eval-and-improve loop if the skill needs to be reliable at scale

### Committing a Skill

Project skills live in `.claude/skills/` and should be committed to git so the whole team shares them:

```bash
git add .claude/skills/<skill-name>
git commit -m "Add <skill-name> skill"
```
