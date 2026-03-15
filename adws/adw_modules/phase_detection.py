"""Phase detection and resume functionality for ADW workflows.

Detects the last completed phase by analyzing state and filesystem,
allowing workflows to resume from the next phase instead of restarting.
"""

import os
import logging
from typing import Optional, Tuple, List
from enum import Enum
from adw_modules.state import ADWState


class Phase(Enum):
    """ADW workflow phases in execution order."""
    NOT_STARTED = 0
    PLAN = 1
    BUILD = 2
    TEST = 3
    REVIEW = 4
    DOCUMENT = 5
    SHIP = 6


class PhaseDetector:
    """Detects completed phases and determines next phase to execute."""

    def __init__(self, adw_id: str, issue_number: str, logger: Optional[logging.Logger] = None):
        self.adw_id = adw_id
        self.issue_number = issue_number
        self.logger = logger or logging.getLogger(__name__)
        self.state = ADWState.load(adw_id, logger=self.logger)

    def detect_last_completed_phase(self) -> Phase:
        """Detect the last successfully completed phase.

        Returns:
            Phase enum representing the last completed phase
        """
        if not self.state:
            self.logger.info("No state found - workflow not started")
            return Phase.NOT_STARTED

        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        agent_dir = os.path.join(project_root, "agents", self.adw_id)

        # Check phases in reverse order (highest to lowest)

        # Check SHIP phase - PR merged to main
        if self._check_pr_merged():
            self.logger.info("✅ Ship phase completed - PR merged")
            return Phase.SHIP

        # Check DOCUMENT phase - documenter output exists
        # Try both naming conventions: documenter and sdlc_documenter
        documenter_dirs = [
            os.path.join(agent_dir, "documenter"),
            os.path.join(agent_dir, "sdlc_documenter")
        ]
        for doc_dir in documenter_dirs:
            if os.path.exists(doc_dir) and self._has_output_files(doc_dir):
                self.logger.info("✅ Document phase completed")
                return Phase.DOCUMENT

        # Check REVIEW phase - reviewer output exists
        reviewer_dirs = [
            os.path.join(agent_dir, "reviewer"),
            os.path.join(agent_dir, "sdlc_reviewer")
        ]
        for rev_dir in reviewer_dirs:
            if os.path.exists(rev_dir) and self._has_output_files(rev_dir):
                self.logger.info("✅ Review phase completed")
                return Phase.REVIEW

        # Check TEST phase - tester output exists
        tester_dirs = [
            os.path.join(agent_dir, "tester"),
            os.path.join(agent_dir, "sdlc_tester"),
            os.path.join(agent_dir, "test_runner")
        ]
        for test_dir in tester_dirs:
            if os.path.exists(test_dir) and self._has_output_files(test_dir):
                self.logger.info("✅ Test phase completed")
                return Phase.TEST

        # Check BUILD phase - implementor output exists
        implementor_dirs = [
            os.path.join(agent_dir, "implementor"),
            os.path.join(agent_dir, "sdlc_implementor")
        ]
        for impl_dir in implementor_dirs:
            if os.path.exists(impl_dir) and self._has_output_files(impl_dir):
                self.logger.info("✅ Build phase completed")
                return Phase.BUILD

        # Check PLAN phase - plan file exists and worktree created
        plan_file = self.state.get("plan_file")
        worktree_path = self.state.get("worktree_path")

        # Check if plan file exists - try both absolute and worktree paths
        plan_exists = False
        if plan_file:
            if os.path.exists(plan_file):
                plan_exists = True
            elif worktree_path and not os.path.isabs(plan_file):
                # Try plan file in worktree
                worktree_plan = os.path.join(worktree_path, plan_file)
                if os.path.exists(worktree_plan):
                    plan_exists = True

        # Also check for planner directory existence as fallback
        planner_dirs = [
            os.path.join(agent_dir, "planner"),
            os.path.join(agent_dir, "sdlc_planner")
        ]
        planner_exists = any(
            os.path.exists(p_dir) and self._has_output_files(p_dir)
            for p_dir in planner_dirs
        )

        if (plan_exists or planner_exists) and worktree_path:
            self.logger.info("✅ Plan phase completed")
            return Phase.PLAN

        # State exists but no phases completed
        self.logger.info("State exists but no phases completed yet")
        return Phase.NOT_STARTED

    def get_next_phase(self, current_phase: Phase) -> Optional[Phase]:
        """Get the next phase to execute after the current phase.

        Args:
            current_phase: The last completed phase

        Returns:
            Next Phase enum or None if workflow is complete
        """
        if current_phase == Phase.SHIP:
            return None  # Workflow complete

        # Return next phase in sequence
        next_value = current_phase.value + 1
        return Phase(next_value)

    def get_resume_command(self) -> Tuple[Optional[str], str]:
        """Get the command to resume the workflow from the next phase.

        Returns:
            Tuple of (script_name, description) or (None, reason) if cannot resume
        """
        last_phase = self.detect_last_completed_phase()
        next_phase = self.get_next_phase(last_phase)

        if next_phase is None:
            return None, "Workflow already completed (shipped)"

        # Map phases to scripts
        phase_scripts = {
            Phase.PLAN: ("adw_plan_iso.py", "Create worktree and generate plan"),
            Phase.BUILD: ("adw_build_iso.py", "Implement the solution"),
            Phase.TEST: ("adw_test_iso.py", "Run tests"),
            Phase.REVIEW: ("adw_review_iso.py", "Review implementation"),
            Phase.DOCUMENT: ("adw_document_iso.py", "Generate documentation"),
            Phase.SHIP: ("adw_ship_iso.py", "Approve and merge PR"),
        }

        if next_phase not in phase_scripts:
            return None, f"Unknown phase: {next_phase}"

        script, description = phase_scripts[next_phase]

        # Entry point workflows (create worktree) only need issue number
        if next_phase == Phase.PLAN:
            return script, description

        # Dependent workflows need both issue number and ADW ID
        return script, description

    def format_resume_info(self) -> str:
        """Format a human-readable resume information string.

        Returns:
            Formatted string with phase status and resume command
        """
        last_phase = self.detect_last_completed_phase()
        script, description = self.get_resume_command()

        lines = [
            f"📊 ADW Phase Status for {self.adw_id}",
            f"Issue: #{self.issue_number}",
            "",
            f"Last Completed Phase: {last_phase.name}",
        ]

        if script:
            lines.extend([
                "",
                f"Next Phase: {description}",
                f"Resume Command:",
                ""
            ])

            # Entry point vs dependent workflow
            if last_phase == Phase.NOT_STARTED:
                lines.append(f"  uv run {script} {self.issue_number}")
            else:
                lines.append(f"  uv run {script} {self.issue_number} {self.adw_id}")
        else:
            lines.extend([
                "",
                f"Status: {description}",
            ])

        return "\n".join(lines)

    def _has_output_files(self, directory: str) -> bool:
        """Check if directory contains output files (raw_output.jsonl or similar).

        Args:
            directory: Path to check

        Returns:
            True if output files exist
        """
        if not os.path.exists(directory):
            return False

        # Look for common output file patterns
        output_patterns = ["raw_output.jsonl", "output.json", "results.json"]

        for filename in os.listdir(directory):
            if any(pattern in filename for pattern in output_patterns):
                return True

        return False

    def _check_pr_merged(self) -> bool:
        """Check if the PR for this workflow has been merged.

        Returns:
            True if PR is merged to main
        """
        # This would require checking GitHub API or git history
        # For now, we'll use a simpler check - if documenter exists, assume not shipped yet
        # A more robust implementation would use the GitHub API
        return False


def detect_phase_and_resume(issue_number: str, adw_id: Optional[str] = None, logger: Optional[logging.Logger] = None) -> Tuple[Optional[str], Optional[str], str]:
    """Convenience function to detect phase and get resume command.

    Args:
        issue_number: GitHub issue number
        adw_id: ADW ID (optional, will be discovered if not provided)
        logger: Logger instance

    Returns:
        Tuple of (script_name, adw_id, description) or (None, None, error_message)
    """
    if not logger:
        logger = logging.getLogger(__name__)

    # If no ADW ID provided, try to discover it
    if not adw_id:
        adw_id = _discover_adw_id_for_issue(issue_number, logger)
        if not adw_id:
            return None, None, f"No existing ADW workflow found for issue #{issue_number}"

    detector = PhaseDetector(adw_id, issue_number, logger)
    script, description = detector.get_resume_command()

    if not script:
        return None, adw_id, description

    return script, adw_id, description


def _discover_adw_id_for_issue(issue_number: str, logger: logging.Logger) -> Optional[str]:
    """Try to discover an existing ADW ID for a given issue number.

    Searches agents/ directory for state files matching the issue number.

    Args:
        issue_number: GitHub issue number
        logger: Logger instance

    Returns:
        ADW ID if found, None otherwise
    """
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    agents_dir = os.path.join(project_root, "agents")

    if not os.path.exists(agents_dir):
        return None

    # Search for state files matching this issue
    for adw_id in os.listdir(agents_dir):
        state_file = os.path.join(agents_dir, adw_id, "adw_state.json")
        if os.path.exists(state_file):
            state = ADWState.load(adw_id, logger)
            if state and state.get("issue_number") == str(issue_number):
                logger.info(f"Found existing ADW {adw_id} for issue #{issue_number}")
                return adw_id

    return None
