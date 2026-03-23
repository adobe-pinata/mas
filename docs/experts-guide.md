# Mental Model System Guide

## What is the Mental Model System?

The mental model system gives every Claude agent working in this codebase a verified, domain-specific mental model before it plans or builds anything. It is not documentation — it is an operational memory layer that agents load at the start of a task.

The system has two physical parts:

### Living Knowledge Documents (expertise.yaml)

Each domain has an `expertise.yaml` file at `.claude/commands/mental-model/<domain>/expertise.yaml`. This file is the **mental model** for that domain. It records:

- Exact file paths (relative to project root), verified against the real codebase
- Real exported function names and signatures
- Architectural decisions and the reasoning behind them
- Recurring implementation patterns written as recipes
- Data shapes, storage keys, and schemas
- Integration contracts between this domain and other parts of the system
- Gotchas — non-obvious facts that trip up engineers, written as concrete warnings
- Best practices derived from actual code, not aspiration

Expertise files target 150–400 lines and are hard-capped at 1000 lines. Density is the goal: every line must be actionable. Generic prose is trimmed in favor of precise facts.

### Four Companion Commands Per Domain

Each domain also has four slash commands that consume the expertise file in different ways. The commands follow a consistent naming convention: `/mental-model:<domain>:<command>`.

---

## Available Mental Model Domains

### adw

**Scope:** Autonomous Developer Workflows — background multi-step agent orchestration with real-time WebSocket visualization. Covers workflow types (plan_build, plan_build_review, plan_build_review_fix), subprocess spawning, step lifecycle logging, WebSocket broadcasting, the swimlane frontend, database schema, and orchestrator tools (`start_adw`, `check_adw`).

**Key knowledge areas from expertise.yaml:**
- `overview` — fire-and-forget background process architecture; hybrid deterministic/non-deterministic design
- `workflow_types` — three built-in workflow compositions (plan_build, plan_build_review, plan_build_review_fix) with file paths and step flows
- `composability` — how each step (plan, build, review, fix) is deterministic in structure and non-deterministic in execution
- `core_implementation` — five ADW modules: `adw_agent_sdk`, `adw_logging`, `adw_websockets`, `adw_summarizer`, `adw_database`; workflow files; trigger files
- `orchestrator_integration` — `start_adw` tool (lines 638–742 in agent_manager.py), `check_adw` tool, database functions with line numbers
- `websocket_events` — five event types: `adw_created`, `adw_updated`, `adw_event`, `adw_step_change`, `adw_event_summary_update`
- `frontend_integration` — AdwSwimlanes.vue (1024 lines), adwService.ts, orchestratorStore.ts, TypeScript interfaces
- `slash_commands` — plan, build, review, fix and their output conventions
- `database_schema` — `ai_developer_workflows` and `agent_logs` tables with all columns
- `execution_flow` — end-to-end trigger-to-completion trace
- `gotchas` — three critical issues: CLAUDECODE env var blocking nested invocations, `model: opus` deadlock under stream-json, worktree branching from `origin/main` not local main
- `best_practices` — eight operational rules

**Commands:**

- `/mental-model:adw:plan` — Loads `expertise.yaml` and reads the critical ADW implementation files it references, then delegates to `/plan` with that context loaded. Ensures plans for ADW features respect workflow composition, WebSocket broadcasting, swimlane integration, and database schema. Accepts `[user_request]` as argument.

- `/mental-model:adw:question` — Read-only mode. Loads the expertise file, validates its claims against the codebase, and answers questions about ADW architecture, workflow triggers, swimlane UI, WebSocket events, orchestrator integration, and step composition. Does not write any files. Returns a direct answer with file and line references and diagrams where relevant.

- `/mental-model:adw:self-improve` — Validates the expertise file against the actual codebase. Reads key ADW files, runs Grep to verify function names, checks line numbers and file paths, identifies discrepancies, updates the expertise file, enforces the 1000-line limit (trimming least-critical content if needed), and validates YAML syntax. Accepts `[check_git_diff (true/false)]` and `[focus_area]` arguments.

- `/mental-model:adw:plan_build_improve` — End-to-end workflow. Spawns three sequential subagents: (1) runs `/mental-model:adw:plan` to produce a spec file, (2) runs `/build` against that spec, (3) runs `/mental-model:adw:self-improve true` to sync expertise with the changes made. Each subagent starts with full context. Returns a combined report of all three steps.

---

### experience-server

**Scope:** Adobe App Builder (AIO Runtime / OpenWhisk) serverless backend for the QA platform. Covers the six HTTP action handlers, twelve service modules, three-layer storage abstraction, geo-orchestration with K8s dispatch, run lifecycle, cron scheduling, and webhook intake.

**Key knowledge areas from expertise.yaml:**
- `overview` — AIO Runtime architecture; core insight that this is NOT Express (every entry point is `export async function main(params)`, body is base64-encoded in `params.__ow_body`)
- `key_files.actions` — six actions: chat, plans, runs, schedules, settings, webhooks; each with key functions and purpose
- `key_files.services` — twelve services: storage, browser, oauth, adobe_io, osi_mapping, wcs, aos, planner, runner, scheduler, chat, price_checker, cta_validator, language_detector, vision, geo_orchestrator, k8s_runner
- `patterns` — `action_handler` (eight-step recipe every action follows), `three_layer_storage` (DB/KV/Blob with collections and key conventions), `step_dispatch` (runner.js switch on step.type), `geo_orchestration` (K8s parallel + local sequential fallback)
- `data_shapes` — TestPlan, TestRun, StepResult, MultiGeoResult, Settings, GeoMapping schemas
- `integration_points` — Claude API (oauth.js bearerClient), AIO Runtime, K8s, AEM webhooks, Jira, Slack
- `gotchas` — fourteen critical warnings including: NOT Express, base64 body decoding, `waitForCommerceReady()` requirement, Playwright context isolation, `aio-lib-db` Early Access instability, K8s mode suppressing side-effects, `web:'raw'` on the webhooks action, oat01 token `x-api-key` vs `Authorization: Bearer` distinction
- `best_practices` — eight rules including fire-and-forget pattern, cron validation before persist, no leading slashes in blob paths
- `key_file_locations` — quick-reference index for all actions and services

**Commands:**

- `/mental-model:experience-server:plan` — Accepts an optional `[prior_spec_path]` as a second argument. If provided, reads the upstream spec first (treating it as a contract for data shapes and API surfaces). Then loads the expertise file, reads relevant source files, and delegates to `/plan`. Ensures plans respect AIO Runtime patterns, three-layer storage conventions, fire-and-forget run execution, and all documented gotchas.

- `/mental-model:experience-server:question` — Read-only mode. Loads the expertise file, identifies the relevant sections, reads the source files for validation, and answers questions about QA server architecture, action patterns, service contracts, data shapes, and integration points. Returns a direct answer with file references and diagrams.

- `/mental-model:experience-server:self-improve` — Validates the expertise file against the codebase by reading every listed file and running Grep for all documented function names across all twelve services and six actions. Detects new env var names, new KV key patterns, changed function signatures, and removed features. Updates, trims, and YAML-validates the expertise file. Accepts `[check_git_diff]` and `[focus_area]`.

- `/mental-model:experience-server:plan_build_improve` — End-to-end workflow. Chains `/mental-model:experience-server:plan` → `/implement` → `/mental-model:experience-server:self-improve true` as sequential subagents. Returns a combined report of all three steps.

---

### frontend

**Scope:** React 18 SPA (Vite) frontend for the QA platform. Covers the chat-to-plan UI, multi-geo run launching and polling, run history, settings management, all `lib/api.js` fetch wrappers, the `RunObserver` polling class, component patterns (inline CSS, keyframe injection, Spectrum partial adoption), and routing.

**Key knowledge areas from expertise.yaml:**
- `overview` — no Redux, local state only; polling (not SSE/WebSocket) via RunObserver at 4s interval; Adobe React Spectrum used only for Toast; inline CSS objects throughout
- `key_files.entry` — main.jsx (ReactDOM entry, Spectrum Provider, BrowserRouter) and App.jsx (route tree with React.lazy)
- `key_files.api` — `lib/api.js` (all fetch wrappers, base URL from `VITE_API_URL`) and `lib/runObserver.js` (polling class with `start`, `stop`, `_poll`)
- `key_files.pages` — ChatPage (conversation, plan response, run launch), HistoryPage (paginated runs, client-side filters), SettingsPage (collapsible grouped form, `DEFAULT_SETTINGS` fallback), RunDetailPage
- `key_files.components` — layout (Sidebar, ErrorBoundary, Toast), chat (MessageList, MessageInput, PlanCard), run (RunProgress, RunSummary, StepResult, BatchProgress)
- `patterns` — `api_call` (loading/error/finally pattern with cancelled boolean), `run_polling` (single-geo RunObserver vs multi-geo BatchProgress), `spectrum_adoption` (Toast only), `routing` (React.lazy + ErrorBoundary + Suspense), `inline_css` (module-scope style objects + keyframe injection guard), `session_storage_conversation` (sessionStorage sync across ChatPage and Sidebar via custom events)
- `data_shapes` — Message (local UI), TestPlan, PlanStep, TestRun, StepResult, StartRunResponse, ConversationPreview, Settings
- `integration_points` — full `api.js` function-to-endpoint mapping, Spectrum/Provider contract, Vite proxy
- `gotchas` — thirteen warnings including: no Redux state sharing, inline CSS hover requiring JS state, Spectrum partial adoption risk, `conversationId` in sessionStorage not context, `startRun` 202 response being incomplete, BatchProgress stale closure pattern, PlanCard `localPlan` sync-on-id-change-only, `?c=` useEffect empty dep array intentional
- `best_practices` — eight rules including cancelled boolean ref, null-safe API destructuring, toast vs inline error conventions

**Commands:**

- `/mental-model:experience-frontend:plan` — Accepts an optional `[prior_spec_path]`. If set, reads the upstream spec first (typically from an experience-server plan) to extract server API shapes that the client must consume. Then loads the expertise file, reads the relevant source files, and delegates to `/plan`. Ensures plans respect inline CSS conventions, polling patterns, Spectrum adoption rules, and no-Redux constraint.

- `/mental-model:experience-frontend:question` — Read-only mode. Loads the expertise file, reads relevant source files, and answers questions about React component patterns, api.js contracts, run polling, routing, Spectrum adoption, and inline CSS. Returns a direct answer with file references and diagrams.

- `/mental-model:experience-frontend:self-improve` — Validates the expertise file by reading all listed files and running Grep for all documented function names, prop shapes, and constants (including `xqa_conversation_id` session key, `TERMINAL_STATUSES` set membership, api.js exports). Fixes discrepancies, enforces 1000-line limit, and validates YAML syntax. Accepts `[check_git_diff]` and `[focus_area]` (e.g., `components`, `api`, `pages`).

- `/mental-model:experience-frontend:plan_build_improve` — End-to-end workflow. Chains `/mental-model:experience-frontend:plan` → `/implement` → `/mental-model:experience-frontend:self-improve true` as sequential subagents. Returns a combined report of all three steps.

---

### experience-integrations

**Scope:** Server-only external service integrations for the QA platform — never called directly from the client. Covers WCS/AOS price APIs, OSI mapping, Adobe I/O Events signature verification, AEM webhook handling, Jira issue creation, and Slack Block Kit notifications.

**Key knowledge areas from expertise.yaml:**
- `overview` — thin stateless service modules; credentials read from `process.env` at call time; all integrations called exclusively by server services (`runner.js`, webhooks action)
- `key_files.adobe_commerce` — wcs.js (`getExpectedPrice`), aos.js (`getCanonicalPrice`), osi-mapping.js (`lookupOSI`, `upsertMappings`)
- `key_files.adobe_platform` — adobe-io.js (`verifySignature`, `mapAEMPathToURL`), webhooks/index.js (nine documented functions)
- `key_files.notifications` — jira.js (`createIssue` with Atlassian Document Format, severity→priority map, screenshot attachment), slack.js (`postRunStarted`, `postRunSummary` with Block Kit)
- `patterns` — `price_validation_flow` (six-step pipeline from `_executeStep` through WCS comparison), `geo_url_resolution` (GeoMapping KV lookup, locale format rules), `webhook_trigger` (AEM ContentPublished → auto QA run, nine-step flow), `jira_on_failure` (filter → createIssue → attach screenshot), `slack_alert` (run start/complete lifecycle)
- `data_shapes` — WCSExpectedPrice, AOSCanonicalPrice, OSIMapping, JiraIssueInput, JiraIssueOutput, SlackRunSummaryInput, AEMWebhookEvent, WCSAPIRequest
- `integration_points` — exact caller-to-service relationships; storage dependencies; AIO Runtime config (`web:'raw'`, `require-adobe-auth:false`)
- `env_vars` — complete list for WCS, AOS, Jira, Slack, webhooks, and RUNNER_MODE with notes on optional vs required
- `gotchas` — twelve warnings including: OSI vs offerId distinction, OSI locale underscore format vs GeoMapping hyphen format, `webhooks/index.js` inlining its own copies of `adobe-io.js` functions, `WEBHOOK_SECRET` vs `AIO_EVENTS_WEBHOOK_SECRET` naming mismatch, Jira/Slack suppression under `RUNNER_MODE=k8s`, AEM challenge handshake must precede signature verification
- `best_practices` — eight rules

**Commands:**

- `/mental-model:experience-integrations:plan` — Accepts an optional `[prior_spec_path]`. If set, reads the upstream spec as a contract before loading expertise. Then reads the expertise file and the relevant integration source files, surfaces applicable gotchas (especially OSI vs offerId confusion and env var naming issues), and delegates to `/plan`.

- `/mental-model:experience-integrations:question` — Read-only mode. Loads the expertise file and reads the seven integration source files to validate claims. Answers questions about WCS/AOS price pipeline, OSI mapping, Adobe I/O webhook flow, Jira ticket creation, Slack notifications, env var requirements, and caller contracts.

- `/mental-model:experience-integrations:self-improve` — Validates the expertise file by reading every listed integration file and running Grep for all documented function names. Verifies env var names against actual `process.env` reads in the code. Checks caller relationships, data shapes, and `app.config.yaml` settings. Fixes discrepancies, enforces 1000-line limit, validates YAML. Accepts `[check_git_diff]` and `[focus_area]` (e.g., `jira`, `webhooks`, `wcs`).

- `/mental-model:experience-integrations:plan_build_improve` — End-to-end workflow. Chains `/mental-model:experience-integrations:plan` → `/implement` → `/mental-model:experience-integrations:self-improve true` as sequential subagents. Returns a combined report of all three steps.

---

## How Expertise Files Work

### YAML Structure and Sections

All expertise files follow the same section order, defined by `templates/expertise-template.yaml`:

```
overview          — description, core_insight, architecture_pattern, value_proposition
key_files         — grouped by logical area; each entry has file path, purpose, key_functions/key_classes
patterns          — multi-line recipes for recurring implementation patterns
data_shapes       — DB schemas, request/response shapes, KV formats, config structures
integration_points — how this domain connects to other parts of the system
gotchas           — non-obvious facts written as concrete warnings (wrong assumption → correct behavior)
best_practices    — verified patterns from actual code
key_file_locations — quick-reference flat index of the most important files
```

Not every domain uses every section. The `adw` domain adds `workflow_types`, `composability`, `websocket_events`, `frontend_integration`, `database_schema`, and `execution_flow`. The `experience-integrations` domain adds `env_vars`. Sections are adapted to what the domain actually needs; the template defines the vocabulary, not a rigid schema.

### How Agents Consume Expertise Files During Planning

When a `plan` command runs, it follows a two-step Higher Order Prompt (HOP) pattern:

1. **Context loading step** — The agent reads `expertise.yaml` to build its mental model of the domain. It then identifies which files listed in the expertise are directly relevant to the user's request and reads those files to verify current implementation state. This grounds the agent in reality before any planning begins.

2. **Delegation step** — The agent calls `/plan` with the user request as the argument. Because the expertise and source files are now in context, the planning agent reasons with accurate knowledge of file paths, function signatures, patterns, and gotchas — without needing to re-explore the codebase from scratch.

The `experience-server`, `experience-frontend`, and `experience-integrations` plan commands also accept an optional `prior_spec_path` second argument. When provided, the upstream spec is read first and treated as a binding contract (data shapes, API surfaces, endpoint definitions). This enables cross-domain chaining: an experience-server mental model plan can feed an experience-frontend plan that consumes the same API contract.

### The Self-Improvement Cycle

Expertise files are living documents. They drift from reality whenever code changes. The `self-improve` command is the correction mechanism:

1. Optionally checks `git diff` to identify recently changed files (controlled by `check_git_diff` argument)
2. Reads the current expertise file in full
3. Reads every file listed in the expertise and runs Grep to verify every documented function name, class, and constant actually exists at the stated location
4. Identifies discrepancies: missing new code, stale line numbers, changed signatures, removed features, wrong env var names
5. Updates the expertise file in place with correct information
6. Enforces the 1000-line hard cap — if the file exceeds the limit after updates, it trims the least-critical content (verbose prose, redundant examples, low-priority edge cases) until the count is within limit
7. Validates YAML syntax by running `python3 -c "import yaml; yaml.safe_load(...)"` and fixes any parse errors

The recommended practice is to run `/mental-model:<domain>:self-improve` after every change to the domain's code. The `plan_build_improve` command automates this — its third subagent always runs self-improve with `check_git_diff=true` so that any changes made during the build step are immediately captured in the expertise file.

---

## Creating New Mental Model Domains

### Using the meta-mental-model Skill

New mental model domains are generated by the `meta-mental-model` skill at `.claude/skills/meta-mental-model/SKILL.md`. Invoke it by telling Claude: "create a mental model for...", "add mental models for...", or "use meta-mental-model to...".

The skill takes two variables:
- `DOMAIN` — the domain identifier used in file paths and command names (e.g., `experience-server`, `adw`)
- `SCOPE` — a plain-English description of what the mental model covers

It uses the `adw` domain as the canonical reference and the `templates/` directory for skeleton structure.

### Template Structure

The skill provides two templates in `.claude/skills/meta-mental-model/templates/`:

**`expertise-template.yaml`** — The skeleton for the expertise file. Placeholder tokens like `{{DOMAIN}}`, `{{TAGLINE}}`, `{{ONE_SENTENCE_DESCRIPTION}}`, and `{{GOTCHA_1}}` are replaced with real content discovered from the codebase. The template's section order is the canonical order.

**`commands-template.md`** — Contains all four command files in a single document, separated by section headers. Each command is a complete frontmatter + body template with `{{DOMAIN}}`, `{{SCOPE}}`, and `{{EXPERTISE_PATH}}` tokens. The four sections produce `plan.md`, `question.md`, `self-improve.md`, and `plan_build_improve.md`.

### Workflow the Skill Follows

**Step 1 — Load the ADW pattern.** Reads all five ADW expert files as the canonical reference for what good expertise looks like: accurate file paths, real function names, architectural decisions — not generic descriptions.

**Step 2 — Explore the codebase for the domain.** Uses Glob and Grep to discover actual files, exported function names, data shapes, architectural patterns, integration points, and known gotchas for the given SCOPE. Nothing is invented — only what exists is documented.

**Step 3 — Generate expertise.yaml.** Writes `.claude/commands/mental-model/<DOMAIN>/expertise.yaml`. Every file path listed must have been verified in Step 2. Target is 150–400 lines.

**Step 4 — Generate the four command files.** Writes `plan.md`, `question.md`, `self-improve.md`, and `plan_build_improve.md` under `.claude/commands/mental-model/<DOMAIN>/`, adapting the templates to reference the new domain's expertise path and relevant source areas.

**Step 5 — Validate.** Confirms all five files exist, validates YAML syntax, checks that the line count is under 1000, and prints the skill registration block for the user to add to their skills config.

### Best Practices for New Domains

- **Verify every file path.** The self-improve command will fail to find undocumented functions and silently mislead future agents if paths are invented. Run the skill against a real codebase area, not a planned one.
- **Write gotchas as concrete warnings.** The format is: wrong assumption → correct behavior → where to look. Vague warnings are ignored.
- **Keep patterns as recipes.** Write patterns as numbered steps that an engineer can follow, not as conceptual prose. The adw `action_handler` pattern and the experience-integrations `price_validation_flow` are good models.
- **Group key_files by logical area.** Flat lists are hard to scan. Group by layer (actions vs services), by feature cluster (adobe_commerce vs notifications), or by lifecycle stage (entry vs pages vs components).
- **Run self-improve immediately after the first build.** The first generation captures the codebase at a point in time. Any changes made during the build step that follows are not reflected until self-improve runs. The `plan_build_improve` command handles this automatically.
- **Register the domain in your skills config** using the block the skill prints at the end of Step 6. Without registration, the `/mental-model:<domain>:*` commands are not discoverable by name.
