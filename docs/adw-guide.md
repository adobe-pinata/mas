# Developer Workflows (ADW) Guide

## Overview

Autonomous Developer Workflows (ADW) are fire-and-forget agent pipelines that implement GitHub issues end-to-end without human hand-holding at each step. The system is built on a single architectural insight: **deterministic Python code orchestrates non-deterministic Claude Code agents**.

The Python layer handles predictable, structural work — spawning processes, validating state, managing git operations, routing flags, and posting GitHub comments. The Claude Code layer handles creative, adaptive work — reasoning about what to implement, writing code, running tests, reviewing output, and generating documentation.

Neither layer alone is sufficient. A raw agent loses context over multi-step tasks and cannot reliably track whether a worktree exists. Raw code cannot adapt to novel implementation problems. Combining them yields a system that is both reliable (the scaffolding always runs the right steps in the right order) and capable (the agents can handle the full range of software engineering tasks).

Each workflow runs in an **isolated git worktree** under `trees/<adw-id>/`, meaning multiple issues can be worked on in parallel without branch conflicts or shared filesystem state.

---

## Workflow Types

All workflows are composed from the same set of phase scripts. The orchestrator in `adw_modules/orchestration.py` defines every supported combination.

| Workflow Name | Phases | ZTE | Available Flags | Use Case |
|---|---|---|---|---|
| `plan_build` | Plan, Build | No | (none) | Quick implementation without testing |
| `plan_build_test` | Plan, Build, Test | No | `--skip-e2e`, `--skip-frontend-typecheck` | Implementation with test validation |
| `plan_build_review` | Plan, Build, Review | No | `--skip-resolution` | Implementation with spec review |
| `plan_build_test_review` | Plan, Build, Test, Review | No | `--skip-e2e`, `--skip-resolution`, `--skip-frontend-typecheck` | Full quality pass without documentation |
| `plan_build_document` | Plan, Build, Document | No | (none) | Implementation with documentation update |
| `sdlc` | Plan, Build, Test, Review, Document | No | `--skip-e2e`, `--skip-resolution`, `--skip-frontend-typecheck` | Complete development lifecycle |
| `sdlc_zte` | Plan, Build, Test, Review, Document, Ship | Yes | `--skip-e2e`, `--skip-resolution`, `--skip-frontend-typecheck` | Full SDLC with automatic PR merge |

**ZTE (Zero Touch Execution)** workflows add a Ship phase that approves and merges the PR automatically if all prior phases pass. The test phase in `sdlc_zte` stops the entire workflow on failure (`continue_on_failure=False`), whereas in the plain `sdlc` workflow the test phase continues on failure to allow review and documentation to still run.

---

## How a Workflow Executes

### Entry Point

The canonical entry point for running any workflow is `adw_workflow_iso.py`:

```
uv run adws/adw_workflow_iso.py <workflow> <issue-number> [adw-id] [flags]
```

Legacy wrapper scripts (`adw_sdlc_iso.py`, `adw_plan_build_iso.py`, etc.) exist for backward compatibility and simply delegate to `run_workflow_phases()` from `adw_modules/workflow_ops.py`.

### Phase Execution Loop

`run_workflow_phases()` in `orchestration.py` drives execution:

1. Look up the `WorkflowConfig` for the named workflow from `WORKFLOW_CONFIGS`.
2. Call `ensure_adw_id()` to either create a new 8-character alphanumeric ADW ID or reuse the one supplied on the command line. This immediately creates `agents/<adw-id>/adw_state.json` with the issue number.
3. Resolve the worktree path as `trees/<adw-id>/` (used later for E2E auto-detection).
4. For ZTE workflows, fire the `on_zte_start` callback to post a GitHub comment.
5. Iterate through each `PhaseConfig` in the workflow's phase list:
   - Build the subprocess command: `uv run adws/<phase-script>.py <issue-number> <adw-id> [flags]`.
   - Auto-detect E2E skip: if `--skip-e2e` was not explicitly passed, inspect `git diff origin/main --name-only` in the worktree. If no `client/src` files or `.jsx`/`.tsx` files changed, append `--skip-e2e` automatically.
   - Run the phase via `subprocess.run()`.
   - If the phase exits non-zero:
     - If `phase.continue_on_failure` is `True` (document phase, and test phase in `sdlc`), log a warning but treat the result as success and continue.
     - Otherwise call `on_zte_failure` if applicable and call `sys.exit(1)`.
6. After all phases, print the completion summary and call `on_zte_success` for ZTE workflows.

### State Management

Every phase reads from and writes to `agents/<adw-id>/adw_state.json`. This file is the sole persistent link between phases.

**State file structure** (defined by `ADWStateData` in `data_types.py`):

```json
{
  "adw_id": "a1b2c3d4",
  "issue_number": "42",
  "issue_url": "https://github.com/owner/repo/issues/42",
  "issue_title": "Add dark mode toggle",
  "branch_name": "feature-issue-42-adw-a1b2c3d4-dark-mode-toggle",
  "plan_file": "specs/issue-42-adw-a1b2c3d4-sdlc_planner-dark-mode-toggle.md",
  "issue_class": "/feature",
  "worktree_path": "/abs/path/to/project/trees/a1b2c3d4",
  "backend_port": 9103,
  "frontend_port": 9203,
  "model_set": "base",
  "all_adws": ["adw_plan_iso", "adw_build_iso"],
  "slack_thread_ts": "1234567890.123456",
  "schema_validation_result": null
}
```

The `ADWState` class in `adw_modules/state.py` manages reads and writes. It validates all fields through `ADWStateData` (a Pydantic model) before writing to disk, guaranteeing schema consistency across phases.

`ADWState` also supports piping state as JSON through stdin/stdout (`from_stdin()` / `to_stdout()`), though the file-based approach is used by all current phase scripts.

### Worktree Isolation and Port Allocation

The plan phase creates a dedicated git worktree for each ADW workflow:

1. `find_next_available_ports()` deterministically assigns backend and frontend ports by converting the first 8 characters of the ADW ID from base 36 and taking modulo 15, producing values in the range `9100–9114` for backend and `9200–9214` for frontend. If those ports are in use, it searches sequentially through the range.
2. `create_worktree()` runs `git fetch origin` then `git worktree add -b <branch> trees/<adw-id> origin/main`, creating a fresh checkout from the remote main branch.
3. `setup_worktree_environment()` writes a `.ports.env` file into the worktree root with `BACKEND_PORT`, `FRONTEND_PORT`, and `VITE_BACKEND_URL` values, then runs `npm install` in the worktree.
4. The `/install_worktree` slash command is executed to perform any project-specific environment setup in the worktree.
5. The `worktree_path`, `backend_port`, and `frontend_port` are saved to state so all subsequent phases can find the environment.

Worktree validation is a three-way check: state must have `worktree_path`, the directory must exist on disk, and `git worktree list` must include it. If any check fails, the phase exits with an error pointing back to the plan phase.

---

## Phase Scripts

### adw_plan_iso.py

**What it does:** The entry point for all new workflows. Creates the worktree, classifies the issue, generates a branch name, builds the implementation plan (spec), commits the spec, and opens a draft PR.

**Inputs:**
- `<issue-number>` — GitHub issue number (required)
- `[adw-id]` — optional; if omitted a new 8-character ID is generated

**Outputs / state written:**
- `adw_state.json` fields: `issue_url`, `issue_title`, `issue_class`, `branch_name`, `worktree_path`, `backend_port`, `frontend_port`, `plan_file`, `slack_thread_ts`
- Spec file committed to worktree: `specs/issue-<N>-adw-<id>-sdlc_planner-<slug>.md`
- Git branch created in worktree
- PR opened (draft) against main

**Step-by-step:**
1. Call `ensure_adw_id()` to get or create the ADW ID and initialize state.
2. Check if a worktree already exists (idempotent re-entry).
3. If no worktree: allocate ports, store in state, create worktree, set up environment, run `/install_worktree`.
4. Fetch the GitHub issue via `gh issue view`.
5. Classify the issue with `/classify_issue` — produces `/bug`, `/feature`, or `/chore`.
6. Fire `notify_workflow_start()` which posts to GitHub and creates a Slack thread.
7. Generate branch name with `/generate_branch_name`.
8. Build the implementation plan with the appropriate slash command (`/bug`, `/feature`, or `/chore`). The agent writes a Markdown spec file into `specs/` inside the worktree.
9. Extract the spec file path from the agent response using a regex pattern.
10. Generate and commit the plan using `/commit`.
11. Push the branch and create a PR via `finalize_git_operations()`.
12. Post the final state summary to the GitHub issue.

---

### adw_build_iso.py

**What it does:** Implements the solution described in the spec file. Reads the plan path from state and invokes `/implement` on it in the worktree context.

**Inputs:**
- `<issue-number>` and `<adw-id>` (both required; `adw_plan_iso.py` must have run first)

**Outputs / state written:**
- Implementation code committed to the worktree branch
- PR updated with new commits

**Step-by-step:**
1. Call `initialize_phase("build", ...)` which loads state, validates the worktree, posts a GitHub start comment, and returns a `PhaseContext`.
2. Verify `branch_name` and `plan_file` are present in state.
3. Check out the branch in the worktree via `git checkout <branch>`.
4. Call `implement_plan(plan_file, ...)` which invokes `/implement <spec-path>` in the worktree.
5. Notify build complete with timing via `notify_phase_complete()`.
6. Call `finalize_phase()` which generates a commit message via `/commit`, commits all changes, pushes, and updates the PR.

---

### adw_test_iso.py

**What it does:** Runs unit/syntax tests and optionally E2E browser tests against the implemented code.

**Inputs:**
- `<issue-number>` `<adw-id>` `[--skip-e2e]`
- E2E skip is also applied automatically by the orchestrator when no `client/src` files changed.

**Outputs / state written:**
- Test results posted as GitHub comment
- Test artifacts committed to worktree branch
- `schema_validation_result` written to state if schema validation is performed

**Step-by-step:**
1. Load state and validate the worktree exists.
2. Find the spec file (from `plan_file` in state, or by scanning `git diff origin/main --name-only` for `specs/*.md` files).
3. Run `/test <adw-id> <spec-file> tester` — the agent runs syntax checks and validates acceptance criteria. Returns a JSON array of `TestResult` objects.
4. If `--skip-e2e` is not set:
   a. Start the Vite dev server in `apps/experience-qa/client` on the allocated `frontend_port`.
   b. Run `/test_e2e <adw-id> <frontend-port> <spec-file>` — the agent uses browser automation. Returns `E2ETestResult` objects.
   c. Stop the dev server.
   d. Upload E2E screenshots via `AIOFilesUploader`.
5. Post a formatted test summary to the GitHub issue.
6. Commit results and push.
7. Exit non-zero only if unit tests failed. E2E failures are advisory in `sdlc` mode (the test phase has `continue_on_failure=True`).

---

### adw_review_iso.py

**What it does:** Reviews the implementation against the spec, captures screenshots, and resolves blocker issues by creating and applying patch plans.

**Inputs:**
- `<issue-number>` `<adw-id>` `[--skip-resolution]`

**Outputs / state written:**
- Review summary with screenshot URLs posted to GitHub
- Patch commits for any resolved blockers

**Step-by-step:**
1. Load state and validate the worktree.
2. Find the spec file.
3. Enter a retry loop (maximum 3 attempts):
   a. Run `/review <adw-id> <spec-file> reviewer` in the worktree (which has Playwright MCP configured). Returns a `ReviewResult` with `review_issues` classified as `blocker`, `tech_debt`, or `skippable`.
   b. If there are `blocker` issues and `--skip-resolution` is not set: call `resolve_blocker_issues()` which creates a `/patch` plan for each blocker and implements it.
   c. Retry the review after resolution.
4. Upload screenshots via `AIOFilesUploader` (primary) or GitHub raw URLs (fallback).
5. Post a formatted review summary to GitHub.
6. Commit the review results and push.

---

### adw_document_iso.py

**What it does:** Generates or updates feature documentation based on the changes in the worktree. Also tracks agentic KPIs before finalizing.

**Inputs:**
- `<issue-number>` `<adw-id>`

**Outputs / state written:**
- Documentation file at `app_docs/<slug>.md` inside the worktree (if changes warrant it)
- KPI metrics updated

**Step-by-step:**
1. Load state and validate the worktree.
2. Run `git diff origin/main --stat` in the worktree. If there are no changes, skip documentation generation and return early.
3. Find the spec file.
4. Run `/document <spec-file>` in the worktree. The agent decides whether documentation is needed and creates a file in `app_docs/`.
5. If documentation was created, validate the file path and confirm it exists.
6. Post the documentation result to GitHub.
7. Run `track_agentic_kpis()` via `/track_agentic_kpis` — this never fails the workflow (all exceptions are caught).
8. Commit and push.

Note: This phase has `continue_on_failure=True` in the orchestrator — documentation failure never blocks the next phase.

---

### adw_workflow_iso.py (Orchestrator Entry Point)

**What it does:** The unified entry point that replaces all the individual composite workflow scripts.

**Usage:**
```
uv run adws/adw_workflow_iso.py <workflow-name> <issue-number> [adw-id] [flags]
uv run adws/adw_workflow_iso.py help <workflow-name>
```

It calls `run_workflow_phases()` with the appropriate ZTE callbacks wired in for `sdlc_zte`.

---

## Key Modules

| Module | Purpose |
|---|---|
| `orchestration.py` | Defines `PhaseConfig`, `WorkflowConfig`, and `WORKFLOW_CONFIGS`. Implements `run_phase()` and `run_workflow_phases()`. The single source of truth for what phases belong to which workflow and what flags each phase accepts. |
| `data_types.py` | All Pydantic models: `ADWStateData`, `GitHubIssue`, `ReviewResult`, `TestResult`, `E2ETestResult`, `AgentTemplateRequest`, `AgentPromptResponse`, and the `SLASH_COMMAND_MODEL_MAP` constant defining model selection per command. |
| `state.py` | `ADWState` class. Loads and saves `adw_state.json`. Provides `update()`, `get()`, `save()`, `load()`, `from_stdin()`, `to_stdout()`, and `format_for_github()`. |
| `agent.py` | Wraps the Claude Code CLI (`claude -p`). `execute_template()` is the primary entry point: it selects the right model, constructs the slash command prompt, runs Claude with `--output-format stream-json --dangerously-skip-permissions`, and returns an `AgentPromptResponse`. Includes retry logic (`prompt_claude_code_with_retry`) with delays of 1, 3, 5 seconds. Parses JSONL output and extracts the `result` message. |
| `workflow_ops.py` | A facade module that re-exports from all focused modules for backward compatibility. Also contains `ensure_adw_id()`, `create_commit()`, `create_pull_request()`, and `format_issue_message()`. |
| `worktree_ops.py` | Creates, validates, and removes git worktrees under `trees/<adw-id>/`. Handles port allocation: `get_ports_for_adw()` (deterministic), `is_port_available()`, and `find_next_available_ports()` (falls back sequentially through the range 9100–9114 / 9200–9214). |
| `phase_utils.py` | `initialize_phase()` and `finalize_phase()` — boilerplate shared by build, test, review, and document phases. `initialize_phase()` parses args, loads state, validates the worktree, posts a start comment, and returns a `PhaseContext`. `finalize_phase()` generates a commit message, commits, pushes, creates/updates the PR, and posts the final state summary. |
| `git_ops.py` | Low-level git operations: `commit_changes()`, `push_branch()`, `check_pr_exists()`, `create_branch()`, `approve_pr()`, `merge_pr()`, and `finalize_git_operations()` (push + PR create/update). |
| `github.py` | All GitHub CLI interactions: `fetch_issue()`, `make_issue_comment()`, `fetch_open_issues()`, `fetch_issue_comments()`, `mark_issue_in_progress()`. Also provides `ADW_BOT_IDENTIFIER = "[ADW-AGENTS]"` used to filter bot comments and prevent webhook loops. |
| `notifications.py` | High-level notification functions. Routes milestones (phase complete, tests done) to both GitHub and Slack. Routes progress updates (analyzing files, state transitions) to GitHub only. Never propagates exceptions — all functions implement silent failure. Slack notifications are threaded using `slack_thread_ts` stored in state. |
| `classification.py` | `classify_issue()` runs `/classify_issue` to categorize an issue as `/bug`, `/feature`, or `/chore`. `extract_adw_info()` runs `/classify_adw` to extract a workflow name and ADW ID from freeform text (used by the cron trigger). |
| `planning.py` | `build_plan()` runs the issue classification slash command to create a spec. `implement_plan()` runs `/implement`. `find_spec_file()` locates the spec by state, git diff, or branch name pattern. `create_and_implement_patch()` creates a patch plan via `/patch` and implements it. |
| `branching.py` | `generate_branch_name()` runs `/generate_branch_name`. `find_existing_branch_for_issue()` scans git branches for a pattern match. `create_or_find_branch()` checks state, then existing branches, then creates a new one. |

---

## Triggering Workflows

### Direct CLI

The canonical approach:

```bash
# Run complete SDLC
uv run adws/adw_workflow_iso.py sdlc 42

# Run with an existing ADW ID (resume or re-run a phase)
uv run adws/adw_workflow_iso.py sdlc 42 a1b2c3d4

# Skip E2E tests
uv run adws/adw_workflow_iso.py sdlc 42 --skip-e2e

# Zero Touch Execution (auto-merge if all phases pass)
uv run adws/adw_workflow_iso.py sdlc_zte 42

# Run only planning
uv run adws/adw_plan_iso.py 42

# Run only a specific phase (requires prior plan to have run)
uv run adws/adw_build_iso.py 42 a1b2c3d4
uv run adws/adw_test_iso.py 42 a1b2c3d4 --skip-e2e
uv run adws/adw_review_iso.py 42 a1b2c3d4 --skip-resolution
uv run adws/adw_document_iso.py 42 a1b2c3d4
```

### The Cron Trigger

`adw_triggers/trigger_cron.py` is a long-running polling process that monitors GitHub issues every 20 seconds.

**Start / stop:**
```bash
uv run adws/adw_triggers/trigger_cron.py          # start
uv run adws/adw_triggers/trigger_cron.py stop     # stop running instance
uv run adws/adw_triggers/trigger_cron.py status   # check if running
```

**Trigger conditions** (evaluated in priority order):

1. **Label-based (highest priority):** Issues with GitHub labels matching `LABEL_WORKFLOW_MAP` are processed first:
   - Label `ZTE` → runs `adw_sdlc_zte_iso.py`
   - Label `SDLC` → runs `adw_sdlc_iso.py`
   - Labels are matched case-insensitively; first match wins.

2. **Comment-based:** If the latest comment on an issue is exactly `adw` (after stripping whitespace), the issue is queued for processing with the default `adw_plan_build_iso.py` workflow. If the issue body or comment contains `adw_<workflow>` text, `/classify_adw` is called to extract the specific workflow and an optional ADW ID.

3. **New issues (no comments):** Issues without any comments are checked. If the issue body contains `adw_` text, `/classify_adw` extracts the workflow. If no workflow is found, the default plan+build workflow is used. Issues created by the ADW bot (body contains `[ADW-AGENTS]`) are skipped to prevent loops.

**Deduplication:** The cron checks `agents/` for existing `adw_state.json` files matching the issue number. If a state file exists with a non-null `worktree_path`, the issue is skipped. Placeholder states without a `worktree_path` (created by the `/report_issue` workflow) do not block processing.

### Resume Functionality

`adw_resume.py` detects what phase last completed and runs the next one:

```bash
# Auto-discover ADW ID from agents/ directory
uv run adws/adw_resume.py 42

# Specify ADW ID explicitly
uv run adws/adw_resume.py 42 a1b2c3d4
```

`adw_check_phase.py` reports the current phase status without executing anything:

```bash
uv run adws/adw_check_phase.py 42
uv run adws/adw_check_phase.py 42 a1b2c3d4
```

Both scripts use `PhaseDetector` from `adw_modules/phase_detection.py`. The phase detector inspects `state.get("all_adws")` — the list of phase script names that have appended themselves on execution — to determine the last completed phase.

---

## Model Selection

Every slash command call goes through `execute_template()` in `agent.py`. Before invoking Claude, the function loads the ADW state, reads `model_set` (`"base"` or `"heavy"`), and looks up the model in `SLASH_COMMAND_MODEL_MAP`.

### Base Model Set (default)

All commands use `sonnet`.

### Heavy Model Set

Commands that benefit from the most capable model use `opus`. Commands that are fast or simple stay on `sonnet`.

| Slash Command | Base | Heavy |
|---|---|---|
| `/classify_issue` | sonnet | sonnet |
| `/classify_adw` | sonnet | sonnet |
| `/generate_branch_name` | sonnet | sonnet |
| `/implement` | sonnet | **opus** |
| `/test` | sonnet | sonnet |
| `/resolve_failed_test` | sonnet | **opus** |
| `/test_e2e` | sonnet | sonnet |
| `/resolve_failed_e2e_test` | sonnet | **opus** |
| `/review` | sonnet | sonnet |
| `/reproduce_issue` | sonnet | sonnet |
| `/document` | sonnet | **opus** |
| `/commit` | sonnet | sonnet |
| `/pull_request` | sonnet | sonnet |
| `/chore` | sonnet | **opus** |
| `/bug` | sonnet | **opus** |
| `/feature` | sonnet | **opus** |
| `/patch` | sonnet | **opus** |
| `/install_worktree` | sonnet | sonnet |
| `/track_agentic_kpis` | sonnet | sonnet |

To run a workflow with the heavy model set, set `model_set: "heavy"` in `adw_state.json` before running the workflow, or use the `/classify_adw` extraction if the issue body specifies it.

---

## Troubleshooting

### Common Issues (from expertise.yaml)

**Symptom: `raw_output.jsonl` stays empty; subprocess hangs silently with no output**

Cause: The `CLAUDECODE` environment variable is inherited from a parent Claude Code session. When `claude -p` detects it is being invoked inside another Claude Code session, it refuses to run.

Fix: `get_safe_subprocess_env()` in `adw_modules/utils.py` must explicitly pop `CLAUDECODE` from the environment before passing it to subprocesses. Verify that line exists:
```python
filtered.pop('CLAUDECODE', None)
```

**Symptom: `claude -p` hangs for 20+ minutes; `raw_output.jsonl` produces 0 lines**

Cause: A slash command's frontmatter contains `model: opus`. Under `--output-format stream-json --dangerously-skip-permissions`, Opus can deadlock on token-heavy prompts.

Fix: Remove `model: opus` from slash command frontmatter in `.claude/commands/`. Let `SLASH_COMMAND_MODEL_MAP` in `agent.py` control model selection. The default is `sonnet` for all commands in base mode.

**Symptom: Agent reports "Unknown skill: feature" or newly committed slash commands are missing from the worktree**

Cause: `create_worktree()` runs `git fetch` then branches from `origin/main`. If local changes (such as new slash commands) have been committed locally but not pushed, the worktree does not see them.

Fix: Always run `git push origin main` before starting an ADW workflow.

**Symptom: Build or test phase exits immediately with "No state found for ADW ID"**

Cause: The build, test, review, and document phases all require prior state written by `adw_plan_iso.py`. Running them without a prior plan phase will always fail.

Fix: Run `adw_plan_iso.py` first, or use a composite workflow script that starts with the plan phase.

**Symptom: Review blocked by consent prompt for database operation**

Cause: `prepare_app.md` (the app startup script) is triggering an interactive consent request for database reset.

Fix: Ensure `prepare_app.md` detects the ADW context (presence of `.ports.env` in the worktree) and skips consent prompts when running under automation.

**Symptom: Port already in use error during plan phase**

The deterministic port assignment is a best-effort starting point. `find_next_available_ports()` searches through the full range (9100–9114, 9200–9214) and raises `RuntimeError` only if all 15 slots are occupied. If that error occurs, some worktrees are still running and need to be cleaned up.

Clean up stale worktrees with:
```bash
./scripts/purge_tree.sh <adw-id>
```

### Health Check

`health_check.py` validates system prerequisites before running workflows:

```bash
uv run adws/health_check.py
uv run adws/health_check.py 42   # also posts results to issue #42
```

Checks performed:
- **Environment variables:** Confirms `CLAUDE_CODE_PATH` is set (defaults to `claude`). Reports optional variables that are not configured (`GITHUB_PAT`, `ANTHROPIC_API_KEY`, `E2B_API_KEY`, `CLOUDFLARED_TUNNEL_TOKEN`, `AIO_STATE_NAMESPACE`, `AIO_STATE_API_KEY`).
- **Git repository:** Confirms `git remote get-url origin` succeeds. Warns if the remote still points to `disler` (the upstream template).
- **GitHub CLI:** Confirms `gh` is installed and `gh auth status` succeeds.
- **Claude Code:** If `ANTHROPIC_API_KEY` is set, runs a test prompt (`What is 2+2?`) against `claude-3-5-haiku-20241022` and verifies the response contains `4`. Skipped if the API key is absent.

The health check returns exit code 0 on success and 1 on any failure.

### Reviewing Agent Output

Each phase writes raw JSONL output to `agents/<adw-id>/<agent-name>/raw_output.jsonl` and a parsed JSON array to `agents/<adw-id>/<agent-name>/raw_output.json`. Prompts sent to Claude are saved at `agents/<adw-id>/<agent-name>/prompts/<command-name>.txt`.

To inspect what an agent did during a phase:
```bash
# Read the final result message
cat agents/<adw-id>/sdlc_implementor/raw_output.json | \
  python3 -c "import json,sys; msgs=json.load(sys.stdin); \
  print([m for m in msgs if m.get('type')=='result'][0]['result'])"

# Read the prompt that was sent
cat agents/<adw-id>/sdlc_planner/prompts/feature.txt
```

### Checking Workflow Phase Status

```bash
# Check what phase an issue is at
uv run adws/adw_check_phase.py 42

# Resume from last completed phase
uv run adws/adw_resume.py 42
```
