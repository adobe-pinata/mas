"""Workflow orchestration utilities for ADW workflows."""

import os
import subprocess
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Callable


@dataclass
class PhaseConfig:
    """Configuration for a workflow phase."""
    name: str
    script: str
    # Flags this phase accepts
    accepts_flags: List[str] = field(default_factory=list)
    # Special behavior flags
    continue_on_failure: bool = False
    always_skip_e2e: bool = False  # For test phase in SDLC workflows


@dataclass
class WorkflowConfig:
    """Configuration for a complete workflow."""
    name: str
    description: str
    phases: List[PhaseConfig]
    # Whether this is a ZTE (Zero Touch Execution) workflow
    is_zte: bool = False
    # Flags this workflow accepts
    available_flags: List[str] = field(default_factory=list)


# Phase definitions
PHASE_PLAN = PhaseConfig(
    name="plan",
    script="adw_plan_iso.py",
)

PHASE_BUILD = PhaseConfig(
    name="build",
    script="adw_build_iso.py",
)

PHASE_TEST = PhaseConfig(
    name="test",
    script="adw_test_iso.py",
    accepts_flags=["--skip-e2e", "--skip-frontend-typecheck"],
)

PHASE_TEST_SDLC = PhaseConfig(
    name="test",
    script="adw_test_iso.py",
    accepts_flags=["--skip-e2e", "--skip-frontend-typecheck"],
    always_skip_e2e=False,  # Auto-detected: E2E runs when client files changed
    continue_on_failure=True,  # Non-ZTE SDLC continues on test failure
)

PHASE_TEST_ZTE = PhaseConfig(
    name="test",
    script="adw_test_iso.py",
    accepts_flags=["--skip-e2e", "--skip-frontend-typecheck"],
    always_skip_e2e=False,  # Auto-detected: E2E runs when client files changed
    continue_on_failure=False,  # ZTE stops on test failure
)

PHASE_REVIEW = PhaseConfig(
    name="review",
    script="adw_review_iso.py",
    accepts_flags=["--skip-resolution"],
)

PHASE_DOCUMENT = PhaseConfig(
    name="document",
    script="adw_document_iso.py",
    continue_on_failure=True,  # Documentation failure shouldn't block shipping
)

PHASE_SHIP = PhaseConfig(
    name="ship",
    script="adw_ship_iso.py",
)


# Workflow definitions
WORKFLOW_CONFIGS: Dict[str, WorkflowConfig] = {
    "plan_build": WorkflowConfig(
        name="plan_build",
        description="Plan and Build workflow",
        phases=[PHASE_PLAN, PHASE_BUILD],
    ),
    "plan_build_test": WorkflowConfig(
        name="plan_build_test",
        description="Plan, Build, and Test workflow",
        phases=[PHASE_PLAN, PHASE_BUILD, PHASE_TEST],
        available_flags=["--skip-e2e", "--skip-frontend-typecheck"],
    ),
    "plan_build_review": WorkflowConfig(
        name="plan_build_review",
        description="Plan, Build, and Review workflow",
        phases=[PHASE_PLAN, PHASE_BUILD, PHASE_REVIEW],
        available_flags=["--skip-resolution"],
    ),
    "plan_build_test_review": WorkflowConfig(
        name="plan_build_test_review",
        description="Plan, Build, Test, and Review workflow",
        phases=[PHASE_PLAN, PHASE_BUILD, PHASE_TEST, PHASE_REVIEW],
        available_flags=["--skip-e2e", "--skip-resolution", "--skip-frontend-typecheck"],
    ),
    "plan_build_document": WorkflowConfig(
        name="plan_build_document",
        description="Plan, Build, and Document workflow",
        phases=[PHASE_PLAN, PHASE_BUILD, PHASE_DOCUMENT],
    ),
    "sdlc": WorkflowConfig(
        name="sdlc",
        description="Complete Software Development Life Cycle",
        phases=[PHASE_PLAN, PHASE_BUILD, PHASE_TEST_SDLC, PHASE_REVIEW, PHASE_DOCUMENT],
        available_flags=["--skip-e2e", "--skip-resolution", "--skip-frontend-typecheck"],
    ),
    "sdlc_zte": WorkflowConfig(
        name="sdlc_zte",
        description="Complete SDLC with Zero Touch Execution (automatic shipping)",
        phases=[PHASE_PLAN, PHASE_BUILD, PHASE_TEST_ZTE, PHASE_REVIEW, PHASE_DOCUMENT, PHASE_SHIP],
        is_zte=True,
        available_flags=["--skip-e2e", "--skip-resolution", "--skip-frontend-typecheck"],
    ),
}


def parse_workflow_flags(known_flags: List[str]) -> Dict[str, bool]:
    """Extract and remove known flags from sys.argv.

    Args:
        known_flags: List of flag names (e.g., ["--skip-e2e", "--skip-resolution"])

    Returns:
        Dictionary mapping flag names (without --) to boolean values
    """
    result = {}
    for flag in known_flags:
        flag_present = flag in sys.argv
        result[flag.lstrip("-").replace("-", "_")] = flag_present
        if flag_present:
            sys.argv.remove(flag)
    return result


def _has_client_changes(worktree_path: str) -> bool:
    """Return True if the worktree has any client/src file changes vs origin/main."""
    try:
        result = subprocess.run(
            ["git", "diff", "origin/main", "--name-only"],
            cwd=worktree_path,
            capture_output=True,
            text=True,
        )
        changed = result.stdout.strip().splitlines()
        return any("client/src" in f or f.endswith((".jsx", ".tsx")) for f in changed)
    except Exception:
        return False


def run_phase(
    phase: PhaseConfig,
    issue_number: str,
    adw_id: str,
    script_dir: str,
    flags: Dict[str, bool],
    worktree_path: str = "",
) -> Tuple[bool, str]:
    """Run a single workflow phase.

    Args:
        phase: The phase configuration
        issue_number: GitHub issue number
        adw_id: ADW workflow ID
        script_dir: Directory containing the phase scripts
        flags: Dictionary of parsed flags

    Returns:
        Tuple of (success, message)
    """
    # Build the command
    cmd = [
        "uv",
        "run",
        os.path.join(script_dir, phase.script),
        issue_number,
        adw_id,
    ]

    # Determine whether to skip E2E:
    # - explicit --skip-e2e flag always wins
    # - otherwise auto-detect: skip if no client/src files changed
    explicit_skip_e2e = flags.get("skip_e2e", False)
    if "--skip-e2e" in phase.accepts_flags:
        if explicit_skip_e2e:
            cmd.append("--skip-e2e")
        elif worktree_path and not _has_client_changes(worktree_path):
            print(f"[orchestration] No client/src changes detected — skipping E2E")
            cmd.append("--skip-e2e")
        else:
            print(f"[orchestration] Client/src changes detected — running E2E")

    for flag in phase.accepts_flags:
        if flag == "--skip-e2e":
            continue  # handled above
        flag_key = flag.lstrip("-").replace("-", "_")
        if flags.get(flag_key, False):
            cmd.append(flag)

    # Print phase header
    phase_name_upper = phase.name.upper()
    print(f"\n=== ISOLATED {phase_name_upper} PHASE ===")
    print(f"Running: {' '.join(cmd)}")

    # Run the phase
    result = subprocess.run(cmd)

    if result.returncode != 0:
        message = f"Isolated {phase.name} phase failed"
        print(message)
        if phase.continue_on_failure:
            print(f"WARNING: {phase.name.capitalize()} phase failed but continuing with next phase")
            return True, message  # Return success=True to continue
        return False, message

    return True, f"{phase.name.capitalize()} phase completed successfully"


def run_workflow_phases(
    workflow_name: str,
    issue_number: str,
    adw_id: Optional[str] = None,
    flags: Optional[Dict[str, bool]] = None,
    on_zte_start: Optional[Callable[[str], None]] = None,
    on_zte_failure: Optional[Callable[[str, str], None]] = None,
    on_zte_success: Optional[Callable[[str], None]] = None,
) -> bool:
    """Run a complete workflow by executing phases in sequence.

    Args:
        workflow_name: Name of the workflow (e.g., "sdlc", "plan_build")
        issue_number: GitHub issue number
        adw_id: Optional ADW ID (will be created if not provided)
        flags: Optional dictionary of parsed flags
        on_zte_start: Optional callback for ZTE start notification
        on_zte_failure: Optional callback for ZTE failure notification (phase_name, adw_id)
        on_zte_success: Optional callback for ZTE success notification

    Returns:
        True if workflow completed successfully, False otherwise
    """
    # Import here to avoid circular imports
    from adw_modules.workflow_ops import ensure_adw_id

    # Get workflow configuration
    config = WORKFLOW_CONFIGS.get(workflow_name)
    if not config:
        print(f"Unknown workflow: {workflow_name}")
        print(f"Available workflows: {', '.join(WORKFLOW_CONFIGS.keys())}")
        return False

    # Ensure ADW ID exists
    adw_id = ensure_adw_id(issue_number, adw_id)
    print(f"Using ADW ID: {adw_id}")

    # Initialize flags if not provided
    if flags is None:
        flags = {}

    # Get script directory (adws/)
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Post ZTE start notification
    if config.is_zte and on_zte_start:
        on_zte_start(issue_number)

    # Resolve worktree path for E2E auto-detection
    project_root = os.path.dirname(script_dir)
    worktree_path = os.path.join(project_root, "trees", adw_id)

    # Run each phase
    for phase in config.phases:
        success, message = run_phase(phase, issue_number, adw_id, script_dir, flags, worktree_path)

        if not success:
            # For ZTE workflows, notify on failure
            if config.is_zte and on_zte_failure:
                on_zte_failure(phase.name, issue_number)
            sys.exit(1)

    # Print completion message
    print(f"\n=== ISOLATED {'ZTE ' if config.is_zte else ''}WORKFLOW COMPLETED ===")
    print(f"ADW ID: {adw_id}")
    print(f"All phases completed successfully!")

    if config.is_zte:
        print(f"Code has been shipped to production!")
        if on_zte_success:
            on_zte_success(issue_number)

    print(f"\nWorktree location: trees/{adw_id}/")
    print(f"To clean up: ./scripts/purge_tree.sh {adw_id}")

    return True


def get_workflow_names() -> List[str]:
    """Get list of available workflow names."""
    return list(WORKFLOW_CONFIGS.keys())


def get_workflow_help(workflow_name: str) -> str:
    """Get help text for a specific workflow."""
    config = WORKFLOW_CONFIGS.get(workflow_name)
    if not config:
        return f"Unknown workflow: {workflow_name}"

    phases_list = ", ".join([p.name.capitalize() for p in config.phases])
    flags_list = " ".join(config.available_flags) if config.available_flags else "(none)"

    return f"""
{config.name}: {config.description}
  Phases: {phases_list}
  Flags: {flags_list}
  ZTE: {'Yes (auto-ships to production)' if config.is_zte else 'No'}
"""
