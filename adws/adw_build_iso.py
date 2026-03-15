#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "slack-sdk"]
# ///

"""
ADW Build Iso - Developer Workflow for agentic building in isolated worktrees

Usage:
  uv run adw_build_iso.py <issue-number> <adw-id>

Workflow:
1. Load state and validate worktree exists
2. Find existing plan (from state)
3. Implement the solution based on plan in worktree
4. Commit implementation in worktree
5. Push and update PR

This workflow REQUIRES that adw_plan_iso.py or adw_patch_iso.py has been run first
to create the worktree. It cannot create worktrees itself.
"""

import sys
import os
import subprocess
import time

# Add the parent directory to Python path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adw_modules.workflow_ops import (
    initialize_phase,
    finalize_phase,
    post_phase_start,
    implement_plan,
    format_issue_message,
    AGENT_IMPLEMENTOR,
)
from adw_modules.github import make_issue_comment
from adw_modules.notifications import (
    notify_phase_start,
    notify_phase_complete,
    notify_error,
    BuildDetails,
)

# Agent name constant
AGENT_NAME = "sdlc_implementor"


def main():
    """Main entry point."""
    # Initialize phase - handles all common setup
    ctx = initialize_phase(
        phase_name="build",
        script_name="adw_build_iso",
    )

    # Validate required state fields
    if not ctx.state.get("branch_name"):
        error_msg = "No branch name in state - run adw_plan_iso.py first"
        ctx.logger.error(error_msg)
        notify_error(ctx.issue_number, ctx.adw_id, error_msg, "state validation")
        sys.exit(1)

    if not ctx.state.get("plan_file"):
        error_msg = "No plan file in state - run adw_plan_iso.py first"
        ctx.logger.error(error_msg)
        notify_error(ctx.issue_number, ctx.adw_id, error_msg, "state validation")
        sys.exit(1)

    # Checkout the branch in the worktree
    branch_name = ctx.state.get("branch_name")
    result = subprocess.run(
        ["git", "checkout", branch_name],
        capture_output=True,
        text=True,
        cwd=ctx.worktree_path
    )
    if result.returncode != 0:
        ctx.logger.error(f"Failed to checkout branch {branch_name} in worktree: {result.stderr}")
        make_issue_comment(
            ctx.issue_number,
            format_issue_message(ctx.adw_id, "ops", f"❌ Failed to checkout branch {branch_name} in worktree")
        )
        sys.exit(1)
    ctx.logger.info(f"Checked out branch in worktree: {branch_name}")

    # Get the plan file from state
    plan_file = ctx.state.get("plan_file")
    ctx.logger.info(f"Using plan file: {plan_file}")

    # Post phase start message
    post_phase_start(ctx, "building")

    # Notify build phase start
    notify_phase_start(ctx.issue_number, ctx.adw_id, "building")

    make_issue_comment(
        ctx.issue_number,
        format_issue_message(
            ctx.adw_id, "ops",
            f"🏠 Worktree: {ctx.worktree_path}\n"
            f"🔌 Ports - Backend: {ctx.backend_port}, Frontend: {ctx.frontend_port}"
        )
    )

    # Implement the plan (executing in worktree)
    ctx.logger.info("Implementing solution in worktree")
    build_start_time = time.time()

    implement_response = implement_plan(plan_file, ctx.adw_id, ctx.logger, working_dir=ctx.worktree_path)

    if not implement_response.success:
        ctx.logger.error(f"Error implementing solution: {implement_response.output}")
        notify_error(ctx.issue_number, ctx.adw_id, f"Error implementing solution: {implement_response.output}", "implementation")
        sys.exit(1)

    ctx.logger.debug(f"Implementation response: {implement_response.output}")

    # Notify build complete
    build_duration = time.time() - build_start_time
    build_details = BuildDetails(success=True, duration=build_duration)
    notify_phase_complete(ctx.issue_number, ctx.adw_id, "building", build_details, state=ctx.state)

    # Finalize phase - handles commit, push, and final messages
    finalize_phase(ctx, AGENT_IMPLEMENTOR, commit_prefix="Implementation ")


if __name__ == "__main__":
    main()
