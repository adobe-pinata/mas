"""Shared Developer Workflow (ADW) operations.

This module serves as a facade that re-exports functions from focused modules
for backward compatibility. New code should import directly from the specific modules.

Modules:
    - classification: Issue classification (classify_issue, extract_adw_info)
    - planning: Plan management (build_plan, implement_plan, find_spec_file)
    - branching: Branch operations (generate_branch_name, create_or_find_branch)
    - orchestration: Workflow orchestration (run_workflow_phases, WORKFLOW_CONFIGS)
    - phase_utils: Phase initialization (initialize_phase, finalize_phase)
"""

import json
import logging
import os
from typing import Tuple, Optional

from adw_modules.data_types import (
    AgentTemplateRequest,
    GitHubIssue,
    AgentPromptResponse,
    IssueClassSlashCommand,
)
from adw_modules.agent import execute_template
from adw_modules.github import ADW_BOT_IDENTIFIER
from adw_modules.state import ADWState

# =============================================================================
# RE-EXPORTS FROM FOCUSED MODULES
# =============================================================================

# Classification module
from adw_modules.classification import (
    extract_adw_info,
    classify_issue,
    AGENT_CLASSIFIER,
    AVAILABLE_ADW_WORKFLOWS,
)

# Planning module
from adw_modules.planning import (
    build_plan,
    implement_plan,
    ensure_plan_exists,
    find_plan_for_issue,
    find_spec_file,
    create_and_implement_patch,
    AGENT_PLANNER,
    AGENT_IMPLEMENTOR,
)

# Branching module
from adw_modules.branching import (
    generate_branch_name,
    find_existing_branch_for_issue,
    create_or_find_branch,
    AGENT_BRANCH_GENERATOR,
)

# Orchestration module
from adw_modules.orchestration import (
    PhaseConfig,
    WorkflowConfig,
    WORKFLOW_CONFIGS,
    PHASE_PLAN,
    PHASE_BUILD,
    PHASE_TEST,
    PHASE_TEST_SDLC,
    PHASE_TEST_ZTE,
    PHASE_REVIEW,
    PHASE_DOCUMENT,
    PHASE_SHIP,
    parse_workflow_flags,
    run_phase,
    run_workflow_phases,
    get_workflow_names,
    get_workflow_help,
)

# Phase utilities module
from adw_modules.phase_utils import (
    PhaseContext,
    initialize_phase,
    finalize_phase,
    post_phase_start,
)


# =============================================================================
# CORE UTILITIES (kept in this module)
# =============================================================================

# Agent name constant for PR creation
AGENT_PR_CREATOR = "pr_creator"


def format_issue_message(
    adw_id: str, agent_name: str, message: str, session_id: Optional[str] = None
) -> str:
    """Format a message for issue comments with ADW tracking and bot identifier.

    Args:
        adw_id: ADW workflow ID
        agent_name: Name of the agent
        message: Message content
        session_id: Optional session ID

    Returns:
        Formatted message string
    """
    if session_id:
        return f"{ADW_BOT_IDENTIFIER} {adw_id}_{agent_name}_{session_id}: {message}"
    return f"{ADW_BOT_IDENTIFIER} {adw_id}_{agent_name}: {message}"


def ensure_adw_id(
    issue_number: str,
    adw_id: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
) -> str:
    """Get ADW ID or create a new one and initialize state.

    Args:
        issue_number: The issue number to find/create ADW ID for
        adw_id: Optional existing ADW ID to use
        logger: Optional logger instance

    Returns:
        The ADW ID (existing or newly created)
    """
    # If ADW ID provided, check if state exists
    if adw_id:
        state = ADWState.load(adw_id, logger)
        if state:
            if logger:
                logger.info(f"Found existing ADW state for ID: {adw_id}")
            else:
                print(f"Found existing ADW state for ID: {adw_id}")
            return adw_id
        # ADW ID provided but no state exists, create state
        state = ADWState(adw_id)
        state.update(adw_id=adw_id, issue_number=issue_number)
        state.save("ensure_adw_id")
        if logger:
            logger.info(f"Created new ADW state for provided ID: {adw_id}")
        else:
            print(f"Created new ADW state for provided ID: {adw_id}")
        return adw_id

    # No ADW ID provided, create new one with state
    from adw_modules.utils import make_adw_id

    new_adw_id = make_adw_id()
    state = ADWState(new_adw_id)
    state.update(adw_id=new_adw_id, issue_number=issue_number)
    state.save("ensure_adw_id")
    if logger:
        logger.info(f"Created new ADW ID and state: {new_adw_id}")
    else:
        print(f"Created new ADW ID and state: {new_adw_id}")
    return new_adw_id


def create_commit(
    agent_name: str,
    issue: GitHubIssue,
    issue_class: IssueClassSlashCommand,
    adw_id: str,
    logger: logging.Logger,
    working_dir: str,
) -> Tuple[Optional[str], Optional[str]]:
    """Create a git commit with a properly formatted message.

    Args:
        agent_name: Name of the agent creating the commit
        issue: GitHub issue
        issue_class: Issue classification
        adw_id: ADW workflow ID
        logger: Logger instance
        working_dir: Working directory

    Returns:
        Tuple of (commit_message, error_message)
    """
    # Remove the leading slash from issue_class
    issue_type = issue_class.replace("/", "")

    # Create unique committer agent name by suffixing '_committer'
    unique_agent_name = f"{agent_name}_committer"

    # Use minimal payload
    minimal_issue_json = issue.model_dump_json(
        by_alias=True, include={"number", "title", "body"}
    )

    request = AgentTemplateRequest(
        agent_name=unique_agent_name,
        slash_command="/commit",
        args=[agent_name, issue_type, minimal_issue_json],
        adw_id=adw_id,
        working_dir=working_dir,
    )

    response = execute_template(request)

    if not response.success:
        return None, response.output

    commit_message = response.output.strip()
    logger.info(f"Created commit message: {commit_message}")
    return commit_message, None


def create_pull_request(
    branch_name: str,
    issue: Optional[GitHubIssue],
    state: ADWState,
    logger: logging.Logger,
    working_dir: str,
) -> Tuple[Optional[str], Optional[str]]:
    """Create a pull request for the implemented changes.

    Args:
        branch_name: Git branch name
        issue: GitHub issue (optional)
        state: ADW state object
        logger: Logger instance
        working_dir: Working directory

    Returns:
        Tuple of (pr_url, error_message)
    """
    # Get plan file from state (may be None for test runs)
    plan_file = state.get("plan_file") or "No plan file (test run)"
    adw_id = state.get("adw_id")

    # If we don't have issue data, try to construct minimal data
    if not issue:
        issue_data = state.get("issue", {})
        issue_json = json.dumps(issue_data) if issue_data else "{}"
    elif isinstance(issue, dict):
        try:
            issue_model = GitHubIssue(**issue)
            issue_json = issue_model.model_dump_json(
                by_alias=True, include={"number", "title", "body"}
            )
        except Exception:
            issue_json = json.dumps(issue, default=str)
    else:
        issue_json = issue.model_dump_json(
            by_alias=True, include={"number", "title", "body"}
        )

    request = AgentTemplateRequest(
        agent_name=AGENT_PR_CREATOR,
        slash_command="/pull_request",
        args=[branch_name, issue_json, plan_file, adw_id],
        adw_id=adw_id,
        working_dir=working_dir,
    )

    response = execute_template(request)

    if not response.success:
        return None, response.output

    pr_url = response.output.strip()
    logger.info(f"Created pull request: {pr_url}")
    return pr_url, None


# =============================================================================
# EXPORTS LIST (for explicit documentation of public API)
# =============================================================================

__all__ = [
    # Classification
    "extract_adw_info",
    "classify_issue",
    "AGENT_CLASSIFIER",
    "AVAILABLE_ADW_WORKFLOWS",
    # Planning
    "build_plan",
    "implement_plan",
    "ensure_plan_exists",
    "find_plan_for_issue",
    "find_spec_file",
    "create_and_implement_patch",
    "AGENT_PLANNER",
    "AGENT_IMPLEMENTOR",
    # Branching
    "generate_branch_name",
    "find_existing_branch_for_issue",
    "create_or_find_branch",
    "AGENT_BRANCH_GENERATOR",
    # Orchestration
    "PhaseConfig",
    "WorkflowConfig",
    "WORKFLOW_CONFIGS",
    "PHASE_PLAN",
    "PHASE_BUILD",
    "PHASE_TEST",
    "PHASE_TEST_SDLC",
    "PHASE_TEST_ZTE",
    "PHASE_REVIEW",
    "PHASE_DOCUMENT",
    "PHASE_SHIP",
    "parse_workflow_flags",
    "run_phase",
    "run_workflow_phases",
    "get_workflow_names",
    "get_workflow_help",
    # Phase utilities
    "PhaseContext",
    "initialize_phase",
    "finalize_phase",
    "post_phase_start",
    # Core utilities
    "format_issue_message",
    "ensure_adw_id",
    "create_commit",
    "create_pull_request",
    "AGENT_PR_CREATOR",
]
