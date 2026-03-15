# Agents Reference

## What are Agents?

Sub-agents are specialized Claude Code instances that the parent Claude session can spawn to handle a focused, bounded task. Each agent is defined by a markdown file in `.claude/agents/` with a YAML frontmatter block that declares its name, description, available tools, model tier, and optional lifecycle hooks.

### How agents differ from skills and commands

| Concept | Location | Purpose | Runs in |
|---------|----------|---------|---------|
| **Agent** | `.claude/agents/<name>.md` | Autonomous sub-task executor with its own tool set and context | Isolated sub-session |
| **Skill** | `.claude/skills/<name>/SKILL.md` | Reference documentation or a CLI usage guide the parent reads | Parent session |
| **Command** | `.claude/commands/<name>.md` | A reusable slash-command prompt template the parent executes | Parent session |

Agents receive only the context passed to them at invocation time, which keeps the parent conversation clean and prevents large intermediate outputs from inflating the parent's context window. Each agent can read files, run commands, call MCP tools, and write output — but only with the tools explicitly listed in its `tools:` frontmatter field.

---

## Available Agents

### adobe-spectrum

**Purpose:** Looks up Adobe Spectrum component documentation for both styled Spectrum 2 components and headless React Aria primitives.

**Tools available:** `Read`, `mcp__react-spectrum-s2__list_all_components`, `mcp__react-spectrum-s2__get_component`, `mcp__react-spectrum-s2__search_components`, `mcp__react-aria__list_react_aria_pages`, `mcp__react-aria__get_react_aria_page_info`, `mcp__react-aria__get_react_aria_page`

**Model:** sonnet

**When dispatched:** When the user asks about Spectrum 2, React Spectrum, React Aria, Adobe design system components, accessible UI patterns, or needs to find the right component for a UI task.

**Key behavior:**
- Covers 90 styled S2 components and 159 React Aria documentation pages via MCP tool sets.
- Prefers S2 styled components by default; falls through to React Aria when the user asks about headless patterns, accessibility hooks (`usePress`, `useFocusRing`, etc.), or a component not available in S2.
- Uses both layers when helping migrate from React Aria to S2.
- Always cites which layer (S2 or React Aria) an answer comes from so the user knows the correct import path.
- Returns concise answers: relevant props, a code example, and related components where applicable.

---

### agent-browser

**Purpose:** Automates multi-step browser flows via the `agent-browser` CLI and returns a structured validation report while isolating context from the parent conversation.

**Tools available:** `Bash`, `Skill`, `Write`

**Model:** sonnet

**When dispatched:** When the user needs to test web pages, validate login flows, fill forms, capture screenshots, or verify UI behavior without requiring MCP browser tools. Preferred for multi-step browser automation tasks.

**Key behavior:**
- Loads the `agent-browser` skill before issuing any CLI commands to obtain the full CLI reference.
- Always uses `--session <name>` on every command — never relies on the implicit default session, which can retain stale null-page state and cause failures.
- Takes a snapshot (`snapshot -i`) after every navigation or action before deciding the next step.
- Runs per-route deep checks on each navigated route: interactive element inventory, ARIA alert detection, API call counts with exact repetition counts, and browser console error capture.
- Saves all screenshots with sequential numbering to an absolute path under `$CLAUDE_PROJECT_DIR/.qa-reports/agent-browser/<timestamp>/`.
- Writes a `report.md` to the session directory containing a step log, route detail tables, summary table, issues list, and recommendations.
- Handles secure credential loading by sourcing `.env` files into shell variables before any auth commands — never exposes literal credential values.
- Closes the named session when finished (`agent-browser close --session <name>`).

---

### batch-fix

**Purpose:** Systematically implements all recommended fixes from a batch review report, processed in strict priority order: CRITICAL and HIGH first, then MEDIUM, then LOW.

**Tools available:** `Bash`, `Read`, `Write`, `Edit`, `Grep`, `Glob`

**Model:** sonnet

**When dispatched:** After a `batch-review` report has been produced and all identified issues need to be resolved in the Adobe Experience QA Platform codebase.

**Key behavior:**
- Always fixes CRITICAL and HIGH issues — these are non-negotiable.
- MEDIUM fixes are applied when straightforward; skipped only with documented rationale.
- LOW fixes are applied when trivial (typos, missing JSDoc); skipped with rationale if they risk unnecessary churn.
- Never modifies spec files (`specs/experience-qa-platform-build.md`, `specs/experience-qa-ui-ux.md`), which are treated as the source of truth.
- Never modifies integration tests unless adding coverage for newly created service files.
- Prefers `Edit` over `Write` for existing files to minimize diff size.
- After all fixes, runs a cross-file consistency check using `Grep` to find broken or unused imports and verifies ESM `export` statements on all newly created files.
- Writes a timestamped fix report to `/Users/rivero/ai/experience-qa/app_fix_reports/fix_<timestamp>.md` documenting every fix applied, skipped issue, file changed, and file created.
- Project-specific: targets the Adobe App Builder (AIO Runtime / OpenWhisk) project at `/Users/rivero/ai/experience-qa`; all source files use Node.js ESM (`"type": "module"`).

---

### batch-review

**Purpose:** Runs a four-phase quality gate after each agent batch completes and produces a structured PASS/FAIL verdict before proceeding to the next batch.

**Tools available:** `Bash`, `Read`, `Grep`, `Glob`

**Model:** opus

**When dispatched:** After completing an agent batch in the Adobe Experience QA Platform project to verify integration tests, git diff, and spec compliance before committing and moving on.

**Key behavior:**
- Strictly read-only — never modifies, writes, edits, or deletes any file.
- Detects the batch layer (server, client, or mixed) from `STAGE_PATH` or changed file paths before running validation.
- Phase 1 — Build/Syntax Validation: runs `node --check` on modified server JS files or a full Vite production build for client files; treats build errors as CRITICAL risk.
- Phase 2 — Git Diff Analysis: runs four `git` commands to understand unstaged changes, staged changes, file status, and recent commit history.
- Phase 3 — Spec Comparison: reads the relevant batch section from both spec files and categorizes each deliverable as DONE, PARTIAL, or MISSING.
- Phase 4 — Risk-Tiered Report: synthesizes findings into a structured markdown report with Integration Tests, Spec Coverage, Risk Assessment (CRITICAL/HIGH/MEDIUM/LOW), Verdict, and Recommended Fixes sections.
- Final verdict is always an unambiguous PASS or FAIL — PASS only when zero CRITICAL and zero HIGH risks exist.
- If integration tests cannot run (missing `.env`, missing test file), flags the gap as MEDIUM risk and continues with remaining phases.

---

### browser-automation

**Purpose:** Automates browser interactions for web testing, form filling, screenshots, and user flow validation using the `agent-browser` CLI.

**Tools available:** `Bash`, `Read`, `Write`, `Edit`

**Model:** sonnet

**When dispatched:** When the user needs to test web pages, validate login flows, fill forms, or verify UI behavior with automated browser testing.

**Key behavior:**
- Sets desktop viewport (`1920x1080`) immediately after opening the browser on every session.
- Uses `--headed` flag only when encountering rendering issues, bot detection, or when visual debugging is needed; defaults to headless.
- Always takes a snapshot (`agent-browser snapshot -i --json`) before every interaction to obtain fresh `@eX` element references — never guesses selectors.
- Re-snapshots after any navigation or state change because `@eX` references are page-specific.
- For pages using `?maslibs=local`, automatically launches with `--disable-web-security,--disable-gpu,--disable-features=PrivateNetworkAccessRespectPreflightResults` to bypass CORS/mixed content blocking for localhost component loading.
- Handles secure credential loading: always `source apps/mas/.env` before any auth commands; uses variable references (`$IMS_EMAIL`, `$IMS_PASS`) in commands, never literal values. Skips screenshots during login steps unless authentication is the test objective.
- Saves screenshots with sequential naming to a timestamped directory under `$CLAUDE_PROJECT_DIR/.qa-reports/`.
- Writes a detailed `test-report.md` to the session directory including the execution step log, validation results, screenshot inventory, command log, and recommendations.
- Never includes actual credentials in reports — only references the source file location.

---

### build-agent

**Purpose:** Implements one specific file based on detailed instructions and context as part of a parallel build workflow.

**Tools available:** `Write`, `Read`, `Edit`, `Grep`, `Glob`, `Bash`, `TodoWrite`

**Model:** sonnet

**When dispatched:** When a single file needs to be written as part of a broader parallel build, or whenever isolated, production-quality file implementation is needed based on a detailed specification.

**Key behavior:**
- Focused on writing exactly one file per invocation — sole responsibility is implementing that file correctly.
- Approaches each task as a new engineer: reads and analyzes the spec thoroughly before writing any code, reads all referenced example files, and studies the codebase structure to match conventions.
- Gathers context via `Read`, `Grep`, and `Glob` to understand import styles, naming conventions, error handling patterns, and documentation standards in the existing codebase.
- Verifies the implementation after writing: runs type checks (`tsc --noEmit` for TypeScript), linters, and any provided test commands.
- Produces a structured report covering: Implementation Summary, Specification Compliance checklist, Quality Checks (type safety, linting), and Issues & Concerns (dependencies, integration points, recommendations).

---

### csv-edit-agent

**Purpose:** Makes modifications to or reports on CSV files, with automatic validation after every read, edit, or write operation.

**Tools available:** `Glob`, `Grep`, `Read`, `Edit`, `Write`

**Model:** opus

**When dispatched:** Only when directly requested by name — invoke as `csv-edit-agent`.

**Key behavior:**
- Determines the target CSV file and the required modification or report from the user's prompt.
- Has a `PostToolUse` lifecycle hook that automatically runs `.claude/hooks/validators/csv-single-validator.py` after every `Read`, `Edit`, or `Write` tool call, ensuring CSV integrity is validated continuously throughout the task.

---

### docs-scraper

**Purpose:** Fetches documentation from URLs and saves it as properly formatted markdown files for offline reference and analysis.

**Tools available:** `mcp__firecrawl-mcp__firecrawl_scrape`, `WebFetch`, `Write`, `Edit`

**Model:** sonnet

**When dispatched:** Proactively when the user needs to fetch and save documentation from a URL.

**Key behavior:**
- Uses `mcp__firecrawl-mcp__firecrawl_scrape` (markdown format) as the primary fetching tool; falls back to `WebFetch` if Firecrawl is unavailable.
- Saves output to `ai_docs/` by default.
- Derives a kebab-case filename from the URL path or page title (e.g., `api-reference.md`, `getting-started.md`).
- Never modifies the content of the scraped documentation — writes it exactly as scraped.
- Cleans up redundant navigation elements and website chrome while preserving all substantive content, code examples, tables, and formatting.
- Verifies completeness to ensure the full documentation was captured, not just a summary or excerpt.
- Reports back with a success/failure indicator, the saved file path, and the original source URL.

---

### fluffyjaws-agent

**Purpose:** Queries FluffyJaws AI via the `fj` CLI and returns a concise, distilled answer while isolating FluffyJaws context consumption from the parent conversation.

**Tools available:** `Bash`, `Skill`

**Model:** haiku

**When dispatched:** Whenever the parent needs to consult FluffyJaws for knowledge, answers, or research without polluting the main conversation context.

**Key behavior:**
- Loads the `fluffyjaws` skill before the first query to obtain the full `fj` CLI reference (commands, options, environment variables).
- Consolidates multiple sub-questions into a single query where possible — maximum two `fj chat` calls per invocation.
- Uses `--fast` flag for factual lookups; uses `--thinking` flag for complex reasoning tasks.
- If `fj chat` fails (auth error, timeout), reports the error immediately without retrying.
- Returns only the essential distilled answer, stripped of boilerplate, with a confidence level (High/Medium/Low).
- Deliberately kept short — the entire purpose of this agent is context isolation, so responses are minimal.
- Does not add opinions or interpretations beyond what FluffyJaws returned.

---

### meta-gentic-agent

**Purpose:** Generates a new, complete Claude Code sub-agent configuration file from a user's natural-language description.

**Tools available:** `Write`, `WebFetch`, `mcp__firecrawl-mcp__firecrawl_scrape`, `mcp__firecrawl-mcp__firecrawl_search`, `MultiEdit`

**Model:** opus

**When dispatched:** Proactively when the user asks to create a new sub-agent.

**Key behavior:**
- Generates a complete, ready-to-use agent file and writes it to `.claude/agents/<name>.md`.
- Enforces strict output format: real YAML frontmatter (between `---` delimiters, not inside a code block), followed by exactly four sections: Purpose, Instructions, Workflow, Report.
- Selects the minimal set of tools the generated agent needs — avoids over-provisioning.
- Uses action-oriented `description` fields that tell Claude *when* to delegate to the generated agent.
- Uses comma-separated tool lists in frontmatter (not YAML list syntax).
- Names agents using `kebab-case`.
- Refuses to add extra sections (no "Example", "Execution", "Agent Configuration", etc.) beyond the required four.

---

### planner

**Purpose:** Creates structured plans and breaks tasks into steps by delegating to the `/plan` slash command.

**Tools available:** `SlashCommand`, `Read`, `Glob`

**Model:** opus

**When dispatched:** When the user wants to create a structured plan, break down a task into steps, or needs strategic planning for a feature or project.

**Key behavior:**
- Acts as a lightweight pass-through wrapper: passes the user's prompt directly to `/plan` without modification.
- Uses `SlashCommand` as the primary mechanism — reads files only when additional context is needed to clarify planning scope.
- Returns the plan output exactly as generated by the `/plan` command, preserving its original formatting and structure.

---

### playwright-validator

**Purpose:** Executes and validates specific user actions on web pages using Playwright MCP tools, capturing screenshots and producing comprehensive validation reports.

**Tools available:** Full suite of `mcp__playwright__browser_*` tools (navigate, snapshot, screenshot, click, type, fill form, wait, evaluate, select, hover, press, scroll, cookie management, reload, back, forward, set viewport), `Write`, `Edit`

**Model:** sonnet

**When dispatched:** Proactively when web interactions need to be tested, UI behaviors need to be verified with visual evidence, or when Playwright MCP tools are available and preferred over the `agent-browser` CLI.

**Key behavior:**
- Creates a timestamped session directory (`./.qa-reports/playwright/YYYY-MM-DD_HH-MM-SS/`) for all output.
- Takes a "before" snapshot and "after" screenshot for every individual action in the sequence, numbered sequentially.
- Runs per-route deep checks on every validated route: interactive element inventory (tag, text, disabled state), ARIA alert detection with exact text, network API call counts with exact repetition numbers (not just "repeated"), and browser console error capture with quoted exact messages.
- Handles errors by capturing an error screenshot immediately, documenting the exact failure point, and trying alternative selectors before reporting failure.
- Writes a `playwright-report-<summary_of_request>.md` file containing a step execution table, per-route check table, summary table across all routes, issues list with exact counts/messages, and recommendations.
- Reports final status as PASS, PARTIAL PASS, or FAIL.

---

### scout-report-suggest

**Purpose:** Investigates codebase problems or research requests, identifies exact issue locations, analyzes root causes, and provides detailed reports with suggested resolutions — without modifying any files.

**Tools available:** `Read`, `Glob`, `Grep`

**Model:** opus

**When dispatched:** Proactively to scout codebase issues, identify problem locations, and suggest resolutions before any fix work begins.

**Key behavior:**
- Operates in strict READ-ONLY mode — cannot modify any files.
- Accepts a problem description or research request, then uses `Glob` to find relevant files and `Grep` to search for specific patterns, keywords, or error signatures.
- Tracks exact file paths and line numbers for every finding; captures relevant code snippets.
- Categorizes root causes across: logic errors, missing error handling, performance bottlenecks, security vulnerabilities, code quality issues, and architecture problems.
- Produces a structured SCOUT REPORT containing: Problem Statement, Search Scope, Executive Summary, Findings (affected files with line numbers), Detailed Analysis (code snippets and root cause), Suggested Resolution (step-by-step approach and specific recommended changes per file), Additional Context (related patterns, best practices), and Priority Level.
- Uses the `opus` model for thorough analysis.

---

### scout-report-suggest-fast

**Purpose:** Identical in function to `scout-report-suggest` — investigates codebase issues and provides detailed reports with suggested resolutions — but uses a faster, lighter model.

**Tools available:** `Read`, `Glob`, `Grep`

**Model:** haiku

**When dispatched:** Proactively to scout codebase issues and suggest resolutions when speed is preferred over the deepest possible analysis, or for straightforward scouting tasks where full `opus` reasoning is not required.

**Key behavior:**
- All workflow steps and report format are identical to `scout-report-suggest`.
- READ-ONLY mode — cannot modify any files.
- Differentiated only by model: uses `haiku` instead of `opus`, making it faster and less expensive for routine or time-sensitive scouting tasks.
- Produces the same structured SCOUT REPORT format with Problem Statement, Search Scope, Executive Summary, Findings, Detailed Analysis, Suggested Resolution, Additional Context, and Priority Level.

---

## Agent Categories

### Analysis and Reporting (Read-Only)

These agents investigate, analyze, and report without modifying the codebase.

| Agent | Model | Primary Function |
|-------|-------|-----------------|
| `scout-report-suggest` | opus | Deep codebase investigation and root-cause analysis |
| `scout-report-suggest-fast` | haiku | Faster codebase investigation for routine tasks |
| `batch-review` | opus | Four-phase quality gate for batch builds with PASS/FAIL verdict |

### Building and Implementation

These agents write or modify code files.

| Agent | Model | Primary Function |
|-------|-------|-----------------|
| `build-agent` | sonnet | Implements a single file based on a detailed spec |
| `batch-fix` | sonnet | Systematically applies all fixes from a batch-review report |
| `csv-edit-agent` | opus | Modifies or reports on CSV files with continuous validation |

### Planning and Meta-Generation

These agents produce plans or generate other agents.

| Agent | Model | Primary Function |
|-------|-------|-----------------|
| `planner` | opus | Generates structured plans via the `/plan` slash command |
| `meta-gentic-agent` | opus | Generates new sub-agent definition files |

### Browser Automation and UI Testing

These agents drive browser interactions and validate web UI.

| Agent | Model | Primary Function |
|-------|-------|-----------------|
| `agent-browser` | sonnet | Multi-step browser automation via `agent-browser` CLI with context isolation |
| `browser-automation` | sonnet | Full-featured browser automation via `agent-browser` CLI with detailed reporting |
| `playwright-validator` | sonnet | Browser validation using Playwright MCP tools with screenshot evidence |

### Documentation and Research

These agents fetch, scrape, or look up documentation and external knowledge.

| Agent | Model | Primary Function |
|-------|-------|-----------------|
| `docs-scraper` | sonnet | Scrapes and saves documentation from URLs as markdown files |
| `adobe-spectrum` | sonnet | Looks up Adobe Spectrum S2 and React Aria component documentation |
| `fluffyjaws-agent` | haiku | Queries FluffyJaws AI via the `fj` CLI in an isolated context |
