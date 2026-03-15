#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "requests", "slack-sdk"]
# ///

"""
ADW Test Iso - Developer Workflow for agentic testing in isolated worktrees

Usage:
  uv run adw_test_iso.py <issue-number> <adw-id> [--skip-e2e]

Workflow:
1. Load state and validate worktree exists
2. Find spec file from worktree
3. Run /test (syntax + acceptance criteria checks)
4. If --skip-e2e is NOT set: start dev server, run /test_e2e, stop server
5. Post results as comment on issue
6. Commit test results in worktree
7. Push and update PR

This workflow REQUIRES that adw_build_iso.py has been run first.
"""

import sys
import os
import json
import time
import logging
import subprocess
from typing import Optional, List, Tuple
from dotenv import load_dotenv

from adw_modules.state import ADWState
from adw_modules.git_ops import commit_changes, finalize_git_operations
from adw_modules.github import (
    fetch_issue,
    make_issue_comment,
    get_repo_url,
    extract_repo_path,
)
from adw_modules.workflow_ops import (
    create_commit,
    format_issue_message,
    find_spec_file,
    AGENT_PLANNER,
)
from adw_modules.utils import setup_logger, parse_json, check_env_vars
from adw_modules.data_types import (
    AgentTemplateRequest,
    TestResult,
    E2ETestResult,
    AgentPromptResponse,
)
from adw_modules.agent import execute_template
from adw_modules.worktree_ops import validate_worktree
from adw_modules.aio_files_uploader import AIOFilesUploader

AGENT_TESTER = "tester"
AGENT_E2E_TESTER = "e2e_tester"


def run_tests(
    spec_file: str,
    adw_id: str,
    logger: logging.Logger,
    working_dir: Optional[str] = None,
) -> Tuple[bool, List[TestResult]]:
    """Run /test command — syntax + acceptance criteria checks."""
    request = AgentTemplateRequest(
        agent_name=AGENT_TESTER,
        slash_command="/test",
        args=[adw_id, spec_file, AGENT_TESTER],
        adw_id=adw_id,
        working_dir=working_dir,
    )

    response = execute_template(request)

    if not response.success:
        logger.error(f"Test command failed: {response.output}")
        return False, []

    try:
        results = parse_json(response.output, List[TestResult])
        all_passed = all(r.passed for r in results)
        return all_passed, results
    except Exception as e:
        logger.error(f"Error parsing test results: {e}")
        # Treat parse failure as a single failed test
        return False, [TestResult(
            test_name="parse_test_output",
            passed=False,
            execution_command="/test",
            test_purpose="Parse test agent output",
            error=str(e),
        )]


def start_dev_server(
    worktree_path: str,
    frontend_port: int,
    logger: logging.Logger,
) -> Optional[subprocess.Popen]:
    """Start the Vite dev server in the worktree. Returns process or None on failure."""
    client_path = os.path.join(worktree_path, "apps", "experience-qa", "client")
    if not os.path.exists(client_path):
        logger.warning(f"Client path not found: {client_path} — skipping E2E")
        return None

    env = {**os.environ, "PORT": str(frontend_port)}
    try:
        proc = subprocess.Popen(
            ["npm", "run", "dev", "--", "--port", str(frontend_port), "--strictPort"],
            cwd=client_path,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        # Give the server a moment to start
        time.sleep(8)
        if proc.poll() is not None:
            logger.error("Dev server exited immediately")
            return None
        logger.info(f"Dev server started on port {frontend_port} (pid {proc.pid})")
        return proc
    except Exception as e:
        logger.error(f"Failed to start dev server: {e}")
        return None


def stop_dev_server(proc: subprocess.Popen, logger: logging.Logger) -> None:
    """Terminate the dev server process."""
    try:
        proc.terminate()
        proc.wait(timeout=10)
        logger.info("Dev server stopped")
    except Exception as e:
        logger.warning(f"Error stopping dev server: {e}")
        try:
            proc.kill()
        except Exception:
            pass


def run_e2e_tests(
    spec_file: str,
    adw_id: str,
    frontend_port: int,
    logger: logging.Logger,
    working_dir: Optional[str] = None,
) -> Tuple[bool, List[E2ETestResult]]:
    """Run /test_e2e command — browser automation via agent-browser."""
    request = AgentTemplateRequest(
        agent_name=AGENT_E2E_TESTER,
        slash_command="/test_e2e",
        args=[adw_id, str(frontend_port), spec_file],
        adw_id=adw_id,
        working_dir=working_dir,
    )

    response = execute_template(request)

    if not response.success:
        logger.error(f"E2E test command failed: {response.output}")
        return False, []

    try:
        results = parse_json(response.output, List[E2ETestResult])
        all_passed = all(r.passed for r in results)
        return all_passed, results
    except Exception as e:
        logger.error(f"Error parsing E2E test results: {e}")
        return False, [E2ETestResult(
            test_name="parse_e2e_output",
            status="failed",
            test_path="",
            error=str(e),
        )]


def format_test_summary(
    unit_results: List[TestResult],
    e2e_results: List[E2ETestResult],
    screenshot_urls: Optional[dict] = None,
) -> str:
    """Format test results as a GitHub comment, embedding screenshot URLs when available."""
    lines = []
    screenshot_urls = screenshot_urls or {}

    if unit_results:
        passed = sum(1 for r in unit_results if r.passed)
        lines.append(f"**Unit/syntax tests:** {passed}/{len(unit_results)} passed")
        for r in unit_results:
            icon = "✅" if r.passed else "❌"
            lines.append(f"  {icon} `{r.test_name}`" + (f" — {r.error}" if r.error else ""))

    if e2e_results:
        passed = sum(1 for r in e2e_results if r.passed)
        lines.append(f"**E2E tests:** {passed}/{len(e2e_results)} passed")
        for r in e2e_results:
            icon = "✅" if r.passed else "❌"
            lines.append(f"  {icon} `{r.test_name}`" + (f" — {r.error}" if r.error else ""))
            for shot in r.screenshots:
                url = screenshot_urls.get(shot, shot)
                if url.startswith("http"):
                    lines.append(f"  ![{r.test_name}]({url})")

    return "\n".join(lines) if lines else "No test results"


def main():
    load_dotenv()

    skip_e2e = "--skip-e2e" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if len(args) < 2:
        print("Usage: uv run adw_test_iso.py <issue-number> <adw-id> [--skip-e2e]")
        sys.exit(1)

    issue_number = args[0]
    adw_id = args[1]

    logger = setup_logger(adw_id, "adw_test_iso")
    logger.info(f"ADW Test Iso starting — ID: {adw_id}, Issue: {issue_number}, skip_e2e={skip_e2e}")

    check_env_vars(logger)

    # Load state
    state = ADWState.load(adw_id, logger)
    if not state:
        logger.error(f"No state found for ADW ID: {adw_id}")
        sys.exit(1)

    state.append_adw_id("adw_test_iso")

    # Validate worktree
    valid, error = validate_worktree(adw_id, state)
    if not valid:
        logger.error(f"Worktree invalid: {error}")
        sys.exit(1)

    worktree_path = state.get("worktree_path")
    frontend_port = state.get("frontend_port", 9200)

    # Get repo info
    try:
        from adw_modules.github import get_repo_url, extract_repo_path
        repo_path = extract_repo_path(get_repo_url())
    except Exception as e:
        logger.error(f"Error getting repo URL: {e}")
        sys.exit(1)

    # Find spec file
    spec_file = state.get("plan_file") or find_spec_file(adw_id, worktree_path, logger)
    if not spec_file:
        logger.error("No spec file found — cannot run tests")
        sys.exit(1)

    make_issue_comment(issue_number, format_issue_message(adw_id, AGENT_TESTER, "Running tests"))

    # --- Unit / syntax tests ---
    logger.info("Running unit/syntax tests")
    unit_passed, unit_results = run_tests(spec_file, adw_id, logger, working_dir=worktree_path)
    logger.info(f"Unit tests: {'PASS' if unit_passed else 'FAIL'} ({len(unit_results)} results)")

    # --- E2E tests (optional) ---
    e2e_passed = True
    e2e_results: List[E2ETestResult] = []

    if not skip_e2e:
        logger.info("Starting dev server for E2E tests")
        make_issue_comment(issue_number, format_issue_message(adw_id, AGENT_E2E_TESTER, "Running E2E browser tests"))

        server_proc = start_dev_server(worktree_path, frontend_port, logger)
        if server_proc:
            try:
                e2e_passed, e2e_results = run_e2e_tests(
                    spec_file, adw_id, frontend_port, logger, working_dir=worktree_path
                )
                logger.info(f"E2E tests: {'PASS' if e2e_passed else 'FAIL'} ({len(e2e_results)} results)")
            finally:
                stop_dev_server(server_proc, logger)
        else:
            logger.warning("Dev server could not start — skipping E2E tests")
            e2e_results = [E2ETestResult(
                test_name="dev_server_start",
                status="failed",
                test_path="",
                error="Dev server could not start in worktree",
            )]
            e2e_passed = False
    else:
        logger.info("Skipping E2E tests (--skip-e2e)")

    # --- Upload E2E screenshots to AIO Files ---
    screenshot_urls = {}
    if e2e_results:
        uploader = AIOFilesUploader(logger)
        all_shots = [s for r in e2e_results for s in r.screenshots]
        if all_shots:
            screenshot_urls = uploader.upload_screenshots(all_shots, adw_id, base_dir=worktree_path)
            uploaded = sum(1 for v in screenshot_urls.values() if v.startswith("http"))
            logger.info(f"Uploaded {uploaded}/{len(all_shots)} E2E screenshots to AIO Files")

    # --- Post results ---
    summary = format_test_summary(unit_results, e2e_results, screenshot_urls)
    overall = unit_passed and e2e_passed
    status_icon = "✅" if overall else "❌"
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_TESTER, f"{status_icon} Test phase complete\n\n{summary}"),
    )

    # --- Commit results ---
    issue = fetch_issue(issue_number, repo_path)
    issue_class = state.get("issue_class", "/feature")

    commit_msg, err = create_commit(AGENT_TESTER, issue, issue_class, adw_id, logger, worktree_path)
    if not err:
        commit_changes(commit_msg, cwd=worktree_path)

    finalize_git_operations(state, logger, cwd=worktree_path)

    state.save("adw_test_iso")
    logger.info("Test phase completed")

    # Exit non-zero only if unit tests fail (E2E failure is advisory in SDLC mode)
    if not unit_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
