"""Phase initialization and finalization utilities for ADW workflows."""

import sys
import logging
from dataclasses import dataclass
from typing import Optional


@dataclass
class PhaseContext:
    """Context returned by phase initialization."""
    issue_number: str
    adw_id: str
    state: "ADWState"  # Forward reference to avoid circular import
    logger: logging.Logger
    worktree_path: str
    backend_port: str
    frontend_port: str
    repo_path: str


def initialize_phase(
    phase_name: str,
    script_name: str,
    required_args: int = 3,
    usage_suffix: str = "",
) -> PhaseContext:
    """Common initialization for all phase scripts.

    Args:
        phase_name: Human-readable phase name (e.g., "build", "test", "review")
        script_name: Script filename for logging (e.g., "adw_build_iso")
        required_args: Minimum number of required arguments (default: 3 for issue + adw_id)
        usage_suffix: Additional usage text for flags (e.g., "[--skip-e2e]")

    Returns:
        PhaseContext with all initialized objects

    Raises:
        SystemExit on validation failures
    """
    from dotenv import load_dotenv
    from adw_modules.state import ADWState
    from adw_modules.utils import setup_logger, check_env_vars
    from adw_modules.worktree_ops import validate_worktree
    from adw_modules.github import make_issue_comment, get_repo_url, extract_repo_path
    from adw_modules.workflow_ops import format_issue_message

    # Load environment variables
    load_dotenv()

    # Check arguments
    if len(sys.argv) < required_args:
        usage = f"Usage: uv run {script_name}.py <issue-number> <adw-id>"
        if usage_suffix:
            usage += f" {usage_suffix}"
        print(usage)
        print("\nError: adw-id is required to locate the worktree")
        print("Run adw_plan_iso.py or adw_patch_iso.py first to create the worktree")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2]

    # Try to load existing state
    temp_logger = setup_logger(adw_id, script_name)
    state = ADWState.load(adw_id, temp_logger)

    if not state:
        temp_logger.error(f"No state found for ADW ID: {adw_id}")
        temp_logger.error("Run adw_plan_iso.py or adw_patch_iso.py first to create the worktree and state")
        print(f"\nError: No state found for ADW ID: {adw_id}")
        print("Run adw_plan_iso.py or adw_patch_iso.py first to create the worktree and state")
        sys.exit(1)

    # Use issue number from state if available
    issue_number = state.get("issue_number", issue_number)

    # Post initial comment
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "ops", f"Starting {phase_name}")
    )

    # Track that this ADW workflow has run
    state.append_adw_id(script_name)

    # Set up logger
    logger = setup_logger(adw_id, script_name)
    logger.info(f"ADW {phase_name.capitalize()} Iso starting - ID: {adw_id}, Issue: {issue_number}")

    # Validate environment
    check_env_vars(logger)

    # Validate worktree exists
    valid, error = validate_worktree(adw_id, state)
    if not valid:
        logger.error(f"Worktree validation failed: {error}")
        logger.error("Run adw_plan_iso.py or adw_patch_iso.py first")
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id, "ops",
                f"Worktree validation failed: {error}\nRun adw_plan_iso.py or adw_patch_iso.py first"
            )
        )
        sys.exit(1)

    # Get worktree path and ports
    worktree_path = state.get("worktree_path")
    backend_port = state.get("backend_port", "9100")
    frontend_port = state.get("frontend_port", "9200")

    logger.info(f"Using worktree at: {worktree_path}")

    # Get repo information
    try:
        github_repo_url = get_repo_url()
        repo_path = extract_repo_path(github_repo_url)
    except ValueError as e:
        logger.error(f"Error getting repository URL: {e}")
        sys.exit(1)

    return PhaseContext(
        issue_number=issue_number,
        adw_id=adw_id,
        state=state,
        logger=logger,
        worktree_path=worktree_path,
        backend_port=backend_port,
        frontend_port=frontend_port,
        repo_path=repo_path,
    )


def finalize_phase(
    ctx: PhaseContext,
    agent_name: str,
    commit_prefix: str = "",
) -> None:
    """Common finalization for all phase scripts.

    Args:
        ctx: Phase context from initialize_phase()
        agent_name: Name of the agent for commit message
        commit_prefix: Optional prefix for completion message
    """
    from adw_modules.git_ops import commit_changes, finalize_git_operations
    from adw_modules.github import fetch_issue, make_issue_comment
    from adw_modules.workflow_ops import format_issue_message, create_commit

    # Fetch issue data for commit message generation
    ctx.logger.info("Fetching issue data for commit message")
    issue = fetch_issue(ctx.issue_number, ctx.repo_path)

    # Get issue classification from state
    issue_command = ctx.state.get("issue_class", "/feature")

    # Create commit message
    ctx.logger.info(f"Creating {agent_name} commit")
    commit_msg, error = create_commit(
        agent_name, issue, issue_command, ctx.adw_id, ctx.logger, ctx.worktree_path
    )

    if error:
        ctx.logger.error(f"Error creating commit message: {error}")
        make_issue_comment(
            ctx.issue_number,
            format_issue_message(ctx.adw_id, agent_name, f"Error creating commit message: {error}")
        )
        sys.exit(1)

    # Commit changes
    success, error = commit_changes(commit_msg, cwd=ctx.worktree_path)

    if not success:
        ctx.logger.error(f"Error committing: {error}")
        make_issue_comment(
            ctx.issue_number,
            format_issue_message(ctx.adw_id, agent_name, f"Error committing: {error}")
        )
        sys.exit(1)

    ctx.logger.info(f"Committed: {commit_msg}")
    make_issue_comment(
        ctx.issue_number,
        format_issue_message(ctx.adw_id, agent_name, f"{commit_prefix}Committed")
    )

    # Finalize git operations (push and PR)
    finalize_git_operations(ctx.state, ctx.logger, cwd=ctx.worktree_path)

    ctx.logger.info(f"Isolated {agent_name} phase completed successfully")
    make_issue_comment(
        ctx.issue_number,
        format_issue_message(ctx.adw_id, "ops", f"Isolated {agent_name} phase completed")
    )

    # Save final state
    ctx.state.save(agent_name)

    # Post final state summary
    make_issue_comment(
        ctx.issue_number,
        format_issue_message(ctx.adw_id, "ops", f"{agent_name.capitalize()} complete\n\n{ctx.state.format_for_github()}")
    )


def post_phase_start(ctx: PhaseContext, phase_name: str, extra_info: str = "") -> None:
    """Post phase start message with worktree info.

    Args:
        ctx: Phase context
        phase_name: Human-readable phase name
        extra_info: Additional info lines to include
    """
    from adw_modules.github import make_issue_comment
    from adw_modules.workflow_ops import format_issue_message

    message = (
        f"Starting isolated {phase_name} phase\n"
        f"Worktree: {ctx.worktree_path}\n"
        f"Ports - Backend: {ctx.backend_port}, Frontend: {ctx.frontend_port}"
    )

    if extra_info:
        message += f"\n{extra_info}"

    make_issue_comment(
        ctx.issue_number,
        format_issue_message(ctx.adw_id, "ops", message)
    )
