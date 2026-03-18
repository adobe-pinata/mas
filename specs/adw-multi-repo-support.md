# Plan: ADW Multi-Repo Support via GITHUB_REPO Env Var

## Context

The agentic harness and app repos are now separate git repositories. The ADW trigger system currently auto-detects its target repo from `git remote get-url origin`, which resolves to `joaquinrivero/agentic-harness`. This means issues, comments, labels, and PRs all land in the wrong repo. The app (e.g. `content-qa`) has its own GitHub repo and should be the target for the full ADW lifecycle: issue polling, worktree creation, branch pushes, and PRs.

A single env var — `GITHUB_REPO=owner/repo` — should act as the control knob for all three affected layers.

## Objective

When `GITHUB_REPO=joaquinrivero/content-qa` is set, the ADW system:
1. Polls issues from the app repo (not the agentic harness)
2. Creates worktrees by cloning the app repo (not the agentic harness)
3. Pushes branches and opens PRs against the app repo
4. Posts comments and labels on the app repo's issues

All changes must be backward compatible — without `GITHUB_REPO`, behavior is unchanged.

## Relevant Files

- `adws/adw_modules/github.py` — `make_issue_comment` and `mark_issue_in_progress` derive `repo_path` internally via `get_repo_url()`; needs a centralized override helper
- `adws/adw_triggers/trigger_cron.py` — sets `REPO_PATH` at module level from `get_repo_url()`; needs env var override
- `adws/adw_modules/worktree_ops.py` — creates git worktrees of the agentic harness via `git worktree add`; needs to clone the app repo when `GITHUB_REPO` is set
- `adws/adw_modules/data_types.py` — `ADWStateData` has no `target_repo` field; needs one to persist the target repo across restarts
- `adws/adw_modules/state.py` — `core_fields` list and `save()`; needs `target_repo` plumbed through
- `adws/adw_test_iso.py` — `start_dev_server()` hardcodes `apps/experience-qa/client`; needs auto-detection for app-repo-root layout

## Implementation Phases

### Phase 1: Foundation — centralize repo resolution in `github.py`

Add `_get_effective_repo_path()` helper so all internal GitHub operations respect `GITHUB_REPO` without each function needing to be touched individually.

### Phase 2: Core Implementation — trigger, worktrees, state

Wire `GITHUB_REPO` into `trigger_cron.py`, `worktree_ops.py`, `data_types.py`, and `state.py`.

### Phase 3: Integration & Polish — client path detection, validation

Fix the hardcoded `experience-qa` path in `adw_test_iso.py` and validate the full flow end-to-end.

## Step by Step Tasks

### 1. Add `_get_effective_repo_path()` to `github.py`

- Add helper at top of `github.py` (after `extract_repo_path`, ~line 82):
  ```python
  def _get_effective_repo_path() -> str:
      """GITHUB_REPO env var takes precedence over git remote origin."""
      override = os.getenv("GITHUB_REPO")
      if override:
          return override
      return extract_repo_path(get_repo_url())
  ```
- In `make_issue_comment()` (lines 198-199): replace the two-line `get_repo_url()` + `extract_repo_path()` block with a single call to `_get_effective_repo_path()`
- In `mark_issue_in_progress()` (lines 239-240): same replacement

### 2. Update `trigger_cron.py` to respect `GITHUB_REPO`

- Replace the module-level `REPO_PATH` initialization (lines 57-59):
  ```python
  # Before
  GITHUB_REPO_URL = get_repo_url()
  REPO_PATH = extract_repo_path(GITHUB_REPO_URL)

  # After
  _GITHUB_REPO_OVERRIDE = os.getenv("GITHUB_REPO")
  if _GITHUB_REPO_OVERRIDE:
      REPO_PATH = _GITHUB_REPO_OVERRIDE
  else:
      GITHUB_REPO_URL = get_repo_url()
      REPO_PATH = extract_repo_path(GITHUB_REPO_URL)
  ```
- Update `display_header()` to show `[GITHUB_REPO override]` indicator when active, so the operator knows which repo is being watched

### 3. Add `target_repo` field to `ADWStateData` and `state.py`

- In `data_types.py` — add to `ADWStateData` model (~line 238):
  ```python
  target_repo: Optional[str] = None   # e.g. "joaquinrivero/content-qa"
  ```
- In `state.py` — add `"target_repo"` to `core_fields` set (line 37)
- In `state.py` `save()` — include `target_repo=self.data.get("target_repo")` in the `ADWStateData` constructor call

### 4. Update `worktree_ops.py` to clone app repo when `GITHUB_REPO` is set

- In `create_worktree()` (or `create_isolated_environment()`), after determining `worktree_path`:
  ```python
  app_repo = os.getenv("GITHUB_REPO")
  if app_repo:
      # Clone the app repo directly — origin will point at the app repo
      clone_url = f"https://github.com/{app_repo}.git"
      result = subprocess.run(
          ["git", "clone", clone_url, worktree_path],
          capture_output=True, text=True
      )
      if result.returncode != 0:
          logger.error(f"Failed to clone {clone_url}: {result.stderr}")
          return None
      # Create the ADW branch in the clone
      subprocess.run(
          ["git", "checkout", "-b", branch_name],
          capture_output=True, text=True, cwd=worktree_path
      )
  else:
      # Existing git worktree add behavior (unchanged)
      ...
  ```
- Write `target_repo` into state after worktree is created:
  ```python
  state.data["target_repo"] = app_repo  # None for agentic harness worktrees
  state.save()
  ```
- Write `.ports.env` to the worktree root (same as existing logic)

### 5. Fix `start_dev_server()` in `adw_test_iso.py`

- Replace hardcoded `client_path` (line 105) with auto-detection:
  ```python
  # Try app-repo-root layout (content-qa, etc.) then agentic-harness layout
  candidates = [
      os.path.join(worktree_path, "client"),
      os.path.join(worktree_path, "apps", "experience-qa", "client"),
  ]
  client_path = next((p for p in candidates if os.path.exists(p)), None)
  if not client_path:
      logger.warning(f"No client directory found in {worktree_path} — skipping E2E")
      return None
  ```
- This is backward compatible: agentic-harness worktrees still find `apps/experience-qa/client`; app-repo clones find `client/` at root

### 6. Update `.env.example` at agentic harness root

- Add documentation for `GITHUB_REPO`:
  ```env
  # ADW target repo — overrides git remote origin for issue polling, worktrees, and PRs
  # Set when the ADW should operate on an app repo separate from the agentic harness
  # Format: owner/repo  (e.g. joaquinrivero/content-qa)
  GITHUB_REPO=
  ```

### 7. Validate end-to-end

- Run trigger with override: `GITHUB_REPO=joaquinrivero/content-qa uv run adws/adw_triggers/trigger_cron.py status`
- Verify `REPO_PATH` resolves correctly in header output
- Create a test issue in `content-qa` repo, comment `adw`, verify trigger fires
- Verify worktree is cloned from content-qa (check `trees/{adw_id}/.git/config` — remote origin should be `github.com/joaquinrivero/content-qa`)
- Verify PR is opened against content-qa, not agentic-harness

## Testing Strategy

- Unit: Mock `os.getenv("GITHUB_REPO")` in tests for `_get_effective_repo_path()` — verify it returns override when set, falls back to `get_repo_url()` when not
- Integration: Run `trigger_cron.py status` with and without `GITHUB_REPO` set — compare `REPO_PATH` in output
- Manual smoke: Create issue in content-qa with `adw` comment → verify ADW spins up, clones content-qa, opens PR there

## Acceptance Criteria

- [ ] `GITHUB_REPO=joaquinrivero/content-qa uv run trigger_cron.py` polls issues from content-qa
- [ ] `make_issue_comment` and `mark_issue_in_progress` post to content-qa when `GITHUB_REPO` is set
- [ ] `create_worktree()` clones content-qa into `trees/{adw_id}/` — `origin` is content-qa
- [ ] `git push -u origin <branch>` inside the worktree pushes to content-qa
- [ ] `gh pr create` inside the worktree opens PR against content-qa
- [ ] `start_dev_server()` finds `client/` at worktree root for app-repo clones
- [ ] Without `GITHUB_REPO`, all existing behavior is unchanged
- [ ] `target_repo` persisted in `agents/{adw_id}/adw_state.json`

## Validation Commands

```bash
# Verify env var override works in trigger
GITHUB_REPO=joaquinrivero/content-qa uv run adws/adw_triggers/trigger_cron.py status

# Syntax check all modified Python files
uv run python -m py_compile adws/adw_modules/github.py
uv run python -m py_compile adws/adw_triggers/trigger_cron.py
uv run python -m py_compile adws/adw_modules/worktree_ops.py
uv run python -m py_compile adws/adw_modules/data_types.py
uv run python -m py_compile adws/adw_modules/state.py
uv run python -m py_compile adws/adw_test_iso.py

# Verify worktree origin after creation
cat trees/<adw_id>/.git/config | grep url
# Expected: url = https://github.com/joaquinrivero/content-qa.git

# Verify state persists target_repo
cat agents/<adw_id>/adw_state.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('target_repo'))"
# Expected: joaquinrivero/content-qa
```

## Notes

- `git_ops.py` requires **no changes** — pushes use hardcoded `origin`, which will correctly resolve to the app repo once the worktree is a clone of it
- `workflow_ops.create_pull_request()` requires **no changes** — `gh pr create` runs in the worktree CWD where `origin` is the app repo
- The `GITHUB_REPO` value should match exactly the `gh` CLI format: `owner/repo` (no URL, no `.git`)
- For HTTPS clone to work in CI/non-interactive environments, `GITHUB_PAT` should be set and will be picked up by `get_github_env()` in `github.py`
