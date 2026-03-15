# Commands Reference

Quick reference for all slash commands available in the agentic-harness.

---

## Core Workflow Commands

---

### Workflow

#### /prime
**Purpose:** Load project context for the Adobe Experience QA Platform at the start of any session.
**Usage:** `/prime`
**Key behavior:**
1. Loads `CLAUDE.md`, `specs/PROGRESS.md`, and `specs/DECISIONS.md` as the always-on core context.
2. Offers task-specific expansions: orientation docs, domain expert pipe patterns, spec auditing files.
3. Reports project state, architecture summary, key constraints, storage notes, open items, and task-relevant context.

---

#### /prime_cc
**Purpose:** Gain understanding of this project's Claude Code configuration and available skills.
**Usage:** `/prime_cc`
**Key behavior:**
1. Delegates to `/prime` first for project context.
2. Reads `CLAUDE.md` and `.claude/settings.json`.
3. Lists available commands and skills on demand (only reads what the task needs).
4. Reports project rules, available commands/skills, and configuration relevant to the current task.

---

#### /planing
**Purpose:** Create a detailed engineering implementation plan from user requirements and save it to `specs/`.
**Usage:** `/planing "[user prompt]"`
**Key behavior:**
1. Analyzes the user prompt, determines task type and complexity.
2. Explores the codebase for existing patterns and architecture.
3. Produces a structured markdown plan (problem statement, phases, step-by-step tasks, acceptance criteria, validation commands).
4. Saves to `specs/<descriptive-name>.md` and reports the file path and key components.

---

#### /implement
**Purpose:** Implement a plan file directly, then report what changed.
**Usage:** `/implement [path to plan file or inline plan text]`
**Key behavior:**
1. Reads the provided plan (inline via `$ARGUMENTS` or from a file path).
2. Thinks through the plan and implements it in full.
3. Reports a concise bullet-point summary and `git diff --stat` of files changed.

---

#### /done
**Purpose:** Mark a feature or task as complete — updates `PROGRESS.md`, optionally archives its plan spec, and suggests expert self-improve.
**Usage:** `/done "<what you just finished>" [spec_file_path]`
**Key behavior:**
1. Reads `specs/PROGRESS.md` and moves the matching item from open to completed (changes status emoji).
2. Archives the plan spec file to `specs/archive/` if provided (or suggests a candidate).
3. Determines which domain expert(s) should be re-synced based on what changed and prints the self-improve command (does not run it automatically).

---

#### /conditional_docs
**Purpose:** Index of documentation files and the conditions under which they should be loaded.
**Usage:** Referenced automatically by `/document` and `/patch`; read manually to decide what context to load.
**Key behavior:**
- Provides a catalog of `app_docs/` files each paired with a list of conditions (feature area, component, issue type) that should trigger loading that doc.
- Not an executable workflow — it is a reference index consumed by other commands.

---

### Git

#### /commit
**Purpose:** Generate and apply a conventional-commit message for staged changes.
**Usage:** `/commit`
**Key behavior:**
1. Runs `git status` and `git diff --staged` to inspect changes.
2. Stages all changes with `git add -A`, then commits using `<type>(<scope>): <description>` format.
3. After a successful commit, scans changed files and suggests `/done` if any tracked open items match.
4. Returns only the commit message used (plus any `/done` suggestion).

---

#### /pull_request
**Purpose:** Create a GitHub pull request for the current branch, linked to an issue.
**Usage:** `/pull_request "<issue number> <summary of changes>"`
**Key behavior:**
1. Gets the current branch and recent commits.
2. Creates the PR using `gh pr create` with a conventional-commit-style title, a summary, an issue-close reference, and a test plan checklist.
3. Outputs the PR URL on completion.

---

#### /rebase
**Purpose:** Rebase the current branch from the correct upstream for either the `mas` or `milo` project.
**Usage:** `/rebase [mas|milo]`
**Key behavior:**
1. Validates the argument is `mas` or `milo`.
2. Changes directory to `apps/$PROJECT` and checks the repo is in a clean state.
3. Fetches the latest remote changes, then rebases: `mas` → from `main`; `milo` → from `stage/upstream`.
4. Handles conflicts by giving user instructions; reports final branch state.

---

#### /generate_branch_name
**Purpose:** Generate a clean, standardized git branch name from an issue number, type, and title.
**Usage:** `/generate_branch_name "<issue-number> <issue-type> <issue-title>"`
**Key behavior:**
- Applies the format `{type}-{issue_number}-{slug}` (e.g. `feat-42-add-schedule-management-ui`).
- Maps `/feature` → `feat`, `/bug` → `fix`, `/chore` → `chore`.
- Outputs only the branch name string — no explanation or markdown.

---

#### /delete_pr
**Purpose:** Close a GitHub PR and optionally delete its branch.
**Usage:** `/delete_pr <pr-number> [--delete-branch]`
**Key behavior:**
- Delegates to `./scripts/delete_pr.sh` which shows PR details and prompts for confirmation before closing.
- Pass `--delete-branch` as the second argument to also delete the associated branch.

---

### Planning

#### /feature
**Purpose:** Create an implementation plan for a new feature (ADW pipeline planning phase).
**Usage:** `/feature "<issue_number> <adw_id> <issue_json>"`
**Key behavior:**
1. Parses the issue title and body from `ISSUE_JSON`.
2. Reads `specs/DECISIONS.md` for applicable stack constraints (no TypeScript, no Redux, inline CSS).
3. Explores the relevant codebase area.
4. Saves a plan to `specs/issue-{N}-adw-{ID}-sdlc_planner-<slug>.md` and prints only the relative path.

---

#### /bug
**Purpose:** Create an implementation plan to fix a bug (ADW pipeline planning phase).
**Usage:** `/bug "<issue_number> <adw_id> <issue_json>"`
**Key behavior:**
1. Parses the issue from `ISSUE_JSON`.
2. Reads `specs/DECISIONS.md` for applicable gotchas.
3. Traces the error path to find the root cause.
4. Saves a focused fix plan to `specs/issue-{N}-adw-{ID}-sdlc_planner-<slug>.md` and prints only the relative path.

---

#### /chore
**Purpose:** Create an implementation plan for a maintenance, documentation, or cleanup task (ADW pipeline planning phase).
**Usage:** `/chore "<issue_number> <adw_id> <issue_json>"`
**Key behavior:**
1. Parses the issue from `ISSUE_JSON` and reads `specs/PROGRESS.md` for context.
2. Explores relevant files; writes a minimal, focused chore plan.
3. Saves to `specs/issue-{N}-adw-{ID}-sdlc_planner-<slug>.md` and prints only the relative path.
4. Rules: no new patterns, no refactoring of working code, no TypeScript.

---

#### /patch
**Purpose:** Create a focused patch plan to resolve a specific review issue with minimal code changes.
**Usage:** `/patch "<adw_id> <review_change_request> [spec_path] [agent_name] [issue_screenshots]"`
**Key behavior:**
1. Reads the original spec (if provided) and inspects `git diff --stat` for current state.
2. Creates a scoped patch plan in `specs/patch/patch-adw-{id}-{name}.md` covering only the `review_change_request`.
3. Validates against the spec's validation steps (or falls back to `test.md` test sequence).
4. Returns exclusively the path to the patch plan file — nothing else.

---

### Testing

#### /test
**Purpose:** Run syntax and unit checks on changed files (ADW test phase, no browser or servers required).
**Usage:** `/test "<adw_id> <spec_file> <agent_name>"`
**Key behavior:**
1. Reads the spec file for acceptance criteria and validation commands.
2. Identifies changed JS/JSX files since the last two commits.
3. Runs `node --check` on `.js` files; verifies `.jsx` files are readable (skips JSX for `node --check`).
4. Checks acceptance criteria against actual code.
5. Outputs a JSON array of `TestResult` objects as the final and only output — nothing after the JSON block.

---

#### /test_e2e
**Purpose:** Run browser E2E tests against the running dev server using the `agent-browser` skill (ADW e2e test phase).
**Usage:** `/test_e2e "<adw_id> <frontend_port> <spec_file>"`
**Key behavior:**
1. Reads the spec for acceptance criteria.
2. Opens a browser session `e2e-{ADW_ID}` against `http://localhost:{FRONTEND_PORT}`.
3. For each acceptance criterion, performs the browser action, takes a screenshot, and records pass/fail.
4. Writes a `agents/{ADW_ID}/e2e_tester/report.md` summary.
5. Outputs a JSON array of `E2ETestResult` objects as the final output.

---

### Review

#### /review
**Purpose:** Review a completed ADW implementation against a spec file and output a structured `ReviewResult` JSON block.
**Usage:** `/review "<adw_id> <spec_file> <agent_name>"`
**Key behavior:**
1. Reads the spec to extract requirements and acceptance criteria.
2. Analyzes git changes (`git diff HEAD~1`) and inspects all modified files.
3. If client files changed, attempts browser screenshots via `agent-browser`.
4. Categorizes issues as `blocker`, `tech_debt`, or `skippable`.
5. Writes a markdown report then emits exactly one `ReviewResult` JSON block as the very last output (PASS = no blockers; FAIL = any blocker exists).

---

#### /fix
**Purpose:** Fix issues identified in a code review report by implementing recommended solutions.
**Usage:** `/fix "[user prompt]" [path to plan file] [path to review report]"`
**Key behavior:**
1. Reads the review report and the original plan to understand scope and intent.
2. Fixes issues in priority order: Blockers → High Risk → Medium Risk → Low Risk.
3. Runs all validation commands from the plan after each batch of fixes.
4. Writes a comprehensive fix report to `app_fix_reports/fix_<timestamp>.md` documenting every change and its verification.

---

#### /spectrum-check
**Purpose:** Scan client files for opportunities to replace custom HTML/CSS with Adobe React Spectrum S2 components.
**Usage:** `/spectrum-check [file paths | component description | (no args = scan all)]`
**Key behavior:**
1. Reads each target file and finds custom `<button>`, `<input>`, `<select>`, `<dialog>`, etc.
2. Delegates to the `adobe-spectrum` subagent to check whether an S2 component exists for each pattern.
3. Outputs one finding per line in `SPECTRUM_CHECK <severity> <file>:<line> <current> → <s2_component>` format.
4. Severities: `ADOPT` (direct replacement), `CONSIDER` (migration needs refactoring), `OK` (already using S2 or no equivalent).

---

### Utility

#### /classify_issue
**Purpose:** Classify a GitHub issue as `/feature`, `/bug`, or `/chore` for ADW workflow routing.
**Usage:** `/classify_issue "<issue title and body>"`
**Key behavior:**
- Applies classification rules to the issue text.
- Outputs only one of `/feature`, `/bug`, or `/chore` on a single line — no explanation, no markdown.

---

#### /classify_adw
**Purpose:** Extract ADW workflow command and configuration from issue or comment text.
**Usage:** `/classify_adw "<issue or comment text>"`
**Key behavior:**
- Parses the text for a workflow name, an 8-char hex ADW ID, and a model set.
- Applies defaults when fields are missing: workflow = `adw_plan_build_iso`, adw_id = null, model_set = `base`.
- Outputs only valid JSON — no explanation.

---

#### /clear_issue_comments
**Purpose:** Delete all comments from a GitHub issue to prepare for a re-run.
**Usage:** `/clear_issue_comments <issue-number>`
**Key behavior:**
- Delegates to `./scripts/clear_issue_comments.sh <issue-number>` and shows the output.

---

#### /csv-edit
**Purpose:** Make modifications to, or report on, a CSV file.
**Usage:** `/csv-edit [csv_file] [user_request]`
**Key behavior:**
1. Reads the target CSV file.
2. Applies the requested modification or generates the requested report.
3. After each Read/Edit/Write, a post-tool hook runs `csv-single-validator.py` to keep the file valid.
4. Reports the results.

---

#### /document
**Purpose:** Generate concise markdown documentation for an implemented feature based on git diff analysis and an optional spec file.
**Usage:** `/document "<adw_id> [spec_path] [documentation_screenshots_dir]"`
**Key behavior:**
1. Runs `git diff origin/main` to identify changed files and implementation details.
2. Reads the spec (if provided) to frame documentation against original requirements.
3. Copies screenshots (if provided) to `app_docs/assets/` and references them in the doc.
4. Creates `app_docs/feature-{adw_id}-{name}.md` following a standard format.
5. Appends a conditional-load entry to `.claude/commands/conditional_docs.md`.
6. Returns exclusively the path to the documentation file — nothing else.

---

#### /meta_prompt
**Purpose:** Create a new prompt (custom slash command) based on a user's request.
**Usage:** `/meta_prompt "[user prompt request]"`
**Key behavior:**
1. Fetches the slash commands and custom command documentation from `code.claude.com`.
2. Designs and writes a new prompt to `.claude/commands/<name>.md` in the canonical format (frontmatter, Variables, Instructions, Workflow, Report sections).
3. Respects static vs dynamic variable ordering; prefers `$1`/`$2` over `$ARGUMENTS` notation.

---

#### /meta-prompt-template
**Purpose:** Provide the canonical template format used by `/meta_prompt` for creating new prompts.
**Usage:** Internal reference — the file defines the `Specified Format` that all generated prompts must follow.
**Key behavior:**
- Not invoked directly; its `Specified Format` section is the standard template enforced by `/meta_prompt`.

---

### Worktree Management

#### /install_worktree
**Purpose:** Set up an isolated git worktree for a given ADW ID to enable parallel ADW execution.
**Usage:** `/install_worktree <adw_id>`
**Key behavior:**
1. Generates or accepts an ADW ID; calls `create_isolated_environment` from `adw_modules.worktree_ops`.
2. Creates `trees/<adw_id>/` with deterministic port allocation (Studio 3100–3114, Web-Components 3200–3214, AEM/Libs 3300–3314).
3. Verifies the worktree exists, ports are written to `.ports.env`, and node_modules are installed.
4. Provides optional steps to copy `.mcp.json` and start dev servers via `./scripts/start_worktree.sh`.

---

#### /worktrees_cleanup
**Purpose:** Remove all isolated worktrees, their branches, and any processes on isolated ports.
**Usage:** `/worktrees_cleanup`
**Key behavior:**
1. Checks current port status with `./scripts/check_ports.sh`.
2. Previews what will be removed via `./scripts/cleanup_worktrees.sh --dry-run`.
3. Runs the real cleanup, then verifies via `git worktree list` and `ls trees/`.
4. Kills processes on ports 3100–3314, removes all `trees/` worktrees and branches matching `*-adw-*`, `feature-issue-*`, `fix-issue-*`, and runs git garbage collection.

---

## Expert Commands

The `experts/` subdirectory contains domain expert command sets. Each domain has four commands that form a composable pattern: `plan`, `question`, `self-improve`, and `plan_build_improve`.

---

### ADW Experts (`/experts:adw:*`)

#### /experts:adw:plan
**Purpose:** Create implementation plans for Developer Workflow features, informed by ADW domain expertise.
**Usage:** `/experts:adw:plan "[user_request]"`
**Key behavior:**
1. Reads `.claude/commands/experts/adw/expertise.yaml` (the ADW mental model) and relevant codebase files.
2. Delegates to `/plan` with the user request — planning is now enriched with ADW architecture context.
3. Report is generated by `/plan`.

---

#### /experts:adw:question
**Purpose:** Answer read-only questions about Developer Workflow architecture, triggers, WebSocket events, and orchestrator integration.
**Usage:** `/experts:adw:question "[question]"`
**Key behavior:**
1. Reads `expertise.yaml` then validates claims against the real codebase before answering.
2. Returns a direct answer, supporting evidence with file/line references, conceptual explanations, and diagrams where helpful.
3. Makes zero file writes.

---

#### /experts:adw:self-improve
**Purpose:** Validate and update the ADW expertise file to stay synchronized with the actual codebase.
**Usage:** `/experts:adw:self-improve [true|false] [focus_area]`
**Key behavior:**
1. Optionally runs `git diff` to identify recent ADW-related changes (controlled by first argument).
2. Reads the expertise file and validates every documented element (workflow types, file paths, function signatures, WebSocket events, DB functions) against the real code.
3. Updates the expertise file, enforces a 1000-line limit (trimming least-critical content), and validates YAML syntax.
4. Reports discrepancies found/remedied, line counts, and validation results.

---

#### /experts:adw:plan_build_improve
**Purpose:** End-to-end ADW implementation — plan, build, then sync expertise in a single automated workflow.
**Usage:** `/experts:adw:plan_build_improve "[adw_implementation_request]" [human_in_the_loop]`
**Key behavior:**
1. Step 1: Spawns a subagent to run `/experts:adw:plan` — retrieves plan file path.
2. Step 2: Spawns a subagent to run `/implement` against that plan — retrieves build report.
3. Step 3: Spawns a subagent to run `/experts:adw:self-improve true` — retrieves self-improve report.
4. Compiles and returns a final workflow summary from all three steps.

---

### QA Server Experts (`/experts:qa-server:*`)

#### /experts:qa-server:plan
**Purpose:** Create implementation plans for QA server features (actions, services, storage, geo-orchestration, run lifecycle) with domain expertise loaded.
**Usage:** `/experts:qa-server:plan "[user_request]" [prior_spec_path]`
**Key behavior:**
1. If `prior_spec_path` is provided, reads it first as the upstream contract (data shapes, routes, storage schemas).
2. Reads the qa-server expertise file and relevant source files to confirm current state.
3. Delegates to `/plan` — AIO Runtime patterns, storage conventions, and service contracts are respected.

---

#### /experts:qa-server:question
**Purpose:** Answer read-only questions about QA server architecture, action patterns, service contracts, and data shapes.
**Usage:** `/experts:qa-server:question "[question]"`
**Key behavior:**
1. Reads `expertise.yaml`, identifies relevant sections, reads the corresponding source files to validate.
2. Returns a direct answer with file:line references, conceptual explanations, and diagrams.
3. Zero file writes.

---

#### /experts:qa-server:self-improve
**Purpose:** Validate and update the qa-server expertise file against the actual server codebase.
**Usage:** `/experts:qa-server:self-improve [true|false] [focus_area]`
**Key behavior:**
1. Optionally checks `git diff` for recent server changes.
2. Verifies all documented files exist and all function names (action handlers, storage, browser, runner, planner, scheduler, etc.) are present via Grep.
3. Updates the expertise file, enforces 1000-line limit, and validates YAML syntax.

---

#### /experts:qa-server:plan_build_improve
**Purpose:** End-to-end qa-server implementation — plan, build, sync expertise.
**Usage:** `/experts:qa-server:plan_build_improve "[implementation_request]" [human_in_the_loop]`
**Key behavior:** Same three-step chain as the ADW variant — plan → implement → self-improve — using the qa-server expert at each step.

---

### QA Client Experts (`/experts:qa-client:*`)

#### /experts:qa-client:plan
**Purpose:** Create implementation plans for QA client features (chat UI, run progress, history, settings, api.js, routing) with domain expertise loaded.
**Usage:** `/experts:qa-client:plan "[user_request]" [prior_spec_path]`
**Key behavior:**
1. If `prior_spec_path` is provided, reads it first as the upstream server API contract.
2. Reads the qa-client expertise file; focuses on inline CSS conventions, polling patterns, no-Redux rule, Spectrum partial adoption, and api.js signatures.
3. Delegates to `/plan`.

---

#### /experts:qa-client:question
**Purpose:** Answer read-only questions about QA client architecture, React patterns, api.js contracts, routing, and Spectrum adoption.
**Usage:** `/experts:qa-client:question "[question]"`
**Key behavior:**
1. Reads expertise file, validates against real client source files.
2. Returns direct answer with file:line references, conceptual explanations, and diagrams.
3. Zero file writes.

---

#### /experts:qa-client:self-improve
**Purpose:** Validate and update the qa-client expertise file against the actual client codebase.
**Usage:** `/experts:qa-client:self-improve [true|false] [focus_area]`
**Key behavior:**
1. Optionally checks `git diff apps/experience-qa/client/` for recent changes.
2. Verifies all documented files, function names, props, sessionStorage key usage, and api.js exports via Grep.
3. Updates the expertise file, enforces 1000-line limit, validates YAML syntax.

---

#### /experts:qa-client:plan_build_improve
**Purpose:** End-to-end qa-client implementation — plan, build, sync expertise.
**Usage:** `/experts:qa-client:plan_build_improve "[implementation_request]" [human_in_the_loop]`
**Key behavior:** Same three-step chain — plan → implement → self-improve — using the qa-client expert at each step.

---

### QA Integrations Experts (`/experts:qa-integrations:*`)

#### /experts:qa-integrations:plan
**Purpose:** Create implementation plans for QA integrations (WCS, AOS, OSI mapping, Adobe I/O, webhooks, Jira, Slack) with domain expertise loaded.
**Usage:** `/experts:qa-integrations:plan "[user_request]" [prior_spec_path]`
**Key behavior:**
1. If `prior_spec_path` is provided, reads it first as the upstream contract.
2. Reads the integrations expertise file and relevant source files (wcs.js, aos.js, osi-mapping.js, adobe-io.js, jira.js, slack.js, webhooks/index.js).
3. Surfaces env var names, data shape contracts, caller isolation rules, and gotchas before delegating to `/plan`.

---

#### /experts:qa-integrations:question
**Purpose:** Answer read-only questions about QA integration architecture — WCS/AOS price pipeline, OSI mapping, Adobe I/O webhook flow, Jira, Slack, and env var requirements.
**Usage:** `/experts:qa-integrations:question "[question]"`
**Key behavior:**
1. Reads expertise file and validates against all six integration source files.
2. Returns direct answer with file references, integration flow explanations, and diagrams.
3. Zero file writes.

---

#### /experts:qa-integrations:self-improve
**Purpose:** Validate and update the QA integrations expertise file against the actual codebase.
**Usage:** `/experts:qa-integrations:self-improve [true|false] [focus_area]`
**Key behavior:**
1. Optionally checks `git diff` for recent integration file changes.
2. Verifies all documented function names (wcs, aos, osi-mapping, adobe-io, jira, slack, webhooks), env var names, data shapes, and caller relationships via Grep.
3. Updates the expertise file, enforces 1000-line limit, validates YAML syntax.

---

#### /experts:qa-integrations:plan_build_improve
**Purpose:** End-to-end QA integrations implementation — plan, build, sync expertise.
**Usage:** `/experts:qa-integrations:plan_build_improve "[implementation_request]" [human_in_the_loop]`
**Key behavior:** Same three-step chain — plan → implement → self-improve — using the qa-integrations expert at each step.

---

## Orchestration Commands

---

#### /batch-orchestrator
**Purpose:** Orchestrate a single implementation batch through a build → review → fix loop → commit cycle.
**Usage:** `/batch-orchestrator "x \"<batch-number> <spec description>\"" [stage_path]`
**Key behavior:**
1. Parses `BATCH_SPEC` to extract `BATCH_NUMBER` (first token) and `SPEC_DESCRIPTION` (remainder).
2. Dispatches `build-agent` with the full spec description.
3. For client-layer batches (STAGE_PATH contains `client/`): starts the Vite dev server, runs `agent-browser` visual smoke tests, captures `QA_REPORT`.
4. Dispatches `batch-review`; if PASS goes straight to commit; if FAIL dispatches `batch-fix` and re-reviews (max 2 fix iterations).
5. If still FAIL after 2 iterations: surfaces the report and stops without committing.
6. Commits with `git add STAGE_PATH` (never `git add -A`); message format: `batch <N>: <short description>`.

---

#### /build-qa-experts
**Purpose:** Generate all three QA domain expert sets (qa-server, qa-client, qa-integrations) from the codebase in one orchestrated run.
**Usage:** `/build-qa-experts`
**Key behavior:**
1. Step 1 (sequential): Spawns a Task agent to generate the qa-server expert (5 files) — must complete first as it defines the API contracts.
2. Step 2 (parallel): Spawns two simultaneous Task agents — one for qa-client, one for qa-integrations — both reading qa-server's expertise.yaml as upstream context.
3. Step 3: Validates all 15 files exist, confirms YAML syntax valid for all three, checks line counts (all must be ≤ 1000).
4. Step 4: Commits all three expert directories with `git commit`.
