#!/usr/bin/env python3
"""Domain-level notification functions for ADWS workflows.

This module provides semantic, high-level notification functions that understand
WHAT is being communicated (milestone vs progress) and intelligently route to
appropriate channels:

- Milestones (phase complete, tests done) → GitHub + Slack
- Critical events (errors, PR creation) → GitHub + Slack
- Progress updates (analyzing files) → GitHub only

Architecture:
    High Level: notifications.py (THIS) - semantic functions
        ↓
    Mid Level: routing logic - decides GitHub only vs GitHub + Slack
        ↓
    Low Level: github.py (make_issue_comment) + slack_notifier.py

Benefits:
- KISS: Each function has ONE clear purpose at right abstraction
- DRY: No repeated "post to GitHub, then Slack" patterns
- Modular: Easy to add channels by editing ONE file
- Self-Documenting: Function names clearly express intent

Thread Management:
All Slack notifications for a workflow are threaded together using Slack's
thread_ts. The first notification creates the thread, subsequent messages
reply to it. This keeps channels organized.

Silent Failure:
All functions implement silent failure - they catch exceptions, log them,
and never propagate errors to calling workflows. This ensures notifications
are "nice to have" and never break workflows.
"""

import logging
from typing import Optional, Dict, Any, Tuple, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from adw_modules.state import ADWState

from adw_modules.github import make_issue_comment
from adw_modules.slack_notifier import (
    notify_workflow_start as slack_workflow_start,
    notify_planning_complete as slack_planning_complete,
    notify_build_complete as slack_build_complete,
    notify_tests_complete as slack_tests_complete,
    notify_pr_created as slack_pr_created,
    notify_workflow_complete as slack_workflow_complete,
    notify_error as slack_error,
)

logger = logging.getLogger(__name__)

# =============================================================================
# Thread Management
# Thread timestamps are now stored in ADWState for persistence across scripts
# =============================================================================


def create_workflow_thread(issue_id: str, adw_id: str, issue_title: str = "",
                          issue_command: str = "", github_url: str = "") -> str:
    """Create a new thread for workflow notifications.

    This is typically called at workflow start and returns the thread_ts
    that should be used for all subsequent notifications.

    Note: The returned thread_ts should be saved to ADWState by the caller.

    Args:
        issue_id: GitHub issue number
        adw_id: ADW session ID
        issue_title: Issue title
        issue_command: Issue classification
        github_url: GitHub issue URL

    Returns:
        thread_ts for the new thread
    """
    try:
        success, thread_ts = slack_workflow_start(
            int(issue_id),
            adw_id,
            issue_title=issue_title,
            issue_command=issue_command,
            github_url=github_url,
            thread_ts=None  # Start new thread
        )
        if success and thread_ts:
            return thread_ts
        return ""
    except Exception as e:
        logger.warning(f"Failed to create workflow thread: {e}")
        return ""


# =============================================================================
# Phase Milestone Notifications (GitHub + Slack)
# =============================================================================

@dataclass
class PhaseDetails:
    """Details about a workflow phase completion."""
    duration: float = 0.0
    files_modified: int = 0
    output_file: str = ""
    additional_info: Dict[str, Any] = None


def notify_phase_start(issue_id: str, adw_id: str, phase: str) -> bool:
    """Notify that a workflow phase is starting.

    Routes to:
    - GitHub: Simple phase start message
    - Slack: NOT sent (avoid spam, only milestones)

    Args:
        issue_id: GitHub issue number
        adw_id: ADW session ID
        phase: Phase name (e.g., "planning", "building", "testing")

    Returns:
        True if GitHub notification succeeded
    """
    try:
        # GitHub: Simple confirmation
        emoji = {
            "planning": "📋",
            "building": "🔨",
            "testing": "🧪",
            "reviewing": "👀",
            "documenting": "📝",
            "shipping": "🚀"
        }.get(phase.lower(), "▶️")

        make_issue_comment(issue_id, f"{emoji} Starting {phase} phase...")
        return True

    except Exception as e:
        logger.warning(f"Failed to send phase start notification: {e}")
        return False


def notify_phase_complete(issue_id: str, adw_id: str, phase: str,
                         details: Optional[PhaseDetails] = None,
                         state: Optional["ADWState"] = None) -> bool:
    """Notify that a workflow phase completed - important milestone.

    Routes to:
    - GitHub: Terse confirmation with duration
    - Slack: Rich notification with details, threaded

    Args:
        issue_id: GitHub issue number
        adw_id: ADW session ID
        phase: Phase name (e.g., "planning", "building", "testing")
        details: Optional PhaseDetails with duration, files, etc.
        state: Optional ADWState for thread persistence

    Returns:
        True if at least one channel succeeded
    """
    if details is None:
        details = PhaseDetails()

    github_success = False
    slack_success = False

    try:
        # GitHub: Terse confirmation
        emoji = {
            "planning": "✅📋",
            "building": "✅🔨",
            "testing": "✅🧪",
            "reviewing": "✅👀",
            "documenting": "✅📝",
            "shipping": "✅🚀"
        }.get(phase.lower(), "✅")

        message = f"{emoji} {phase.capitalize()} phase completed"

        if details.duration > 0:
            mins = int(details.duration // 60)
            secs = int(details.duration % 60)
            message += f" ({mins}m {secs}s)"

        if details.output_file:
            message += f"\nOutput: `{details.output_file}`"

        make_issue_comment(issue_id, message)
        github_success = True

    except Exception as e:
        logger.warning(f"Failed to send GitHub phase complete notification: {e}")

    try:
        # Slack: Rich notification with threading
        thread_ts = state.get("slack_thread_ts") if state else None
        github_url = state.get("issue_url", "") if state else ""
        logger.debug(f"notify_phase_complete: Retrieved issue_url from state: {github_url if github_url else 'EMPTY/NONE'}")

        # Use appropriate Slack function based on phase
        if phase.lower() == "planning":
            success, new_thread_ts = slack_planning_complete(
                int(issue_id),
                adw_id,
                plan_file_path=details.output_file or "",
                planning_duration=details.duration,
                thread_ts=thread_ts,
                github_url=github_url
            )
            if success and new_thread_ts and state:
                state.update(slack_thread_ts=new_thread_ts)
                state.save()
            slack_success = success
        elif phase.lower() == "building":
            success, new_thread_ts = slack_build_complete(
                int(issue_id),
                adw_id,
                thread_ts=thread_ts,
                github_url=github_url,
                build_duration=details.duration
            )
            if success and new_thread_ts and state:
                state.update(slack_thread_ts=new_thread_ts)
                state.save()
            slack_success = success
        else:
            # Generic phase complete for other phases
            slack_success = True  # Placeholder

    except Exception as e:
        logger.warning(f"Failed to send Slack phase complete notification: {e}")

    return github_success or slack_success


def notify_workflow_start(issue_id: str, adw_id: str, issue_title: str = "",
                         issue_command: str = "", github_url: str = "",
                         state: Optional["ADWState"] = None) -> bool:
    """Notify that entire workflow is starting.

    Routes to:
    - GitHub: Simple workflow start message
    - Slack: Creates new thread for workflow notifications

    Args:
        issue_id: GitHub issue number
        adw_id: ADW session ID
        issue_title: Issue title
        issue_command: Issue classification (/bug, /feature, /chore)
        github_url: GitHub issue URL
        state: Optional ADWState for thread persistence

    Returns:
        True if at least one channel succeeded
    """
    github_success = False
    slack_success = False

    try:
        # GitHub: Simple start message
        message = f"🚀 ADWS workflow started"
        if issue_command:
            message += f" ({issue_command})"
        make_issue_comment(issue_id, message)
        github_success = True

    except Exception as e:
        logger.warning(f"Failed to send GitHub workflow start notification: {e}")

    try:
        # Slack: Create thread for workflow
        thread_ts = create_workflow_thread(
            issue_id, adw_id, issue_title, issue_command, github_url
        )
        slack_success = bool(thread_ts)

        # Save thread_ts to state
        if thread_ts and state:
            state.update(slack_thread_ts=thread_ts)
            state.save()

    except Exception as e:
        logger.warning(f"Failed to send Slack workflow start notification: {e}")

    return github_success or slack_success


def notify_workflow_complete(issue_id: str, adw_id: str, success: bool,
                            duration: float = 0.0,
                            state: Optional["ADWState"] = None) -> bool:
    """Notify that workflow is complete.

    Routes to:
    - GitHub: Simple completion message with status
    - Slack: Completion notification in thread

    Args:
        issue_id: GitHub issue number
        adw_id: ADW session ID
        success: Whether workflow succeeded
        duration: Total workflow duration in seconds
        state: Optional ADWState for thread persistence

    Returns:
        True if at least one channel succeeded
    """
    github_success = False
    slack_success = False

    try:
        # GitHub: Simple completion message
        emoji = "✅" if success else "❌"
        status = "completed successfully" if success else "failed"
        message = f"{emoji} Workflow {status}"

        if duration > 0:
            mins = int(duration // 60)
            secs = int(duration % 60)
            message += f" ({mins}m {secs}s total)"

        make_issue_comment(issue_id, message)
        github_success = True

    except Exception as e:
        logger.warning(f"Failed to send GitHub workflow complete notification: {e}")

    try:
        # Slack: Completion in thread
        thread_ts = state.get("slack_thread_ts") if state else None
        github_url = state.get("issue_url", "") if state else ""
        success_result, new_thread_ts = slack_workflow_complete(
            int(issue_id), adw_id, success, thread_ts=thread_ts,
            github_url=github_url, duration=duration
        )
        if success_result and new_thread_ts and state:
            state.update(slack_thread_ts=new_thread_ts)
            state.save()
        slack_success = success_result

    except Exception as e:
        logger.warning(f"Failed to send Slack workflow complete notification: {e}")

    return github_success or slack_success


# =============================================================================
# Test Result Notifications (GitHub + Slack)
# =============================================================================

@dataclass
class TestResults:
    """Test execution results."""
    passed: int
    failed: int
    total: int
    duration: float = 0.0
    details: str = ""

    @property
    def success(self) -> bool:
        """Whether all tests passed."""
        return self.failed == 0 and self.total > 0


def notify_tests_complete(issue_id: str, adw_id: str, results: TestResults,
                         state: Optional["ADWState"] = None) -> bool:
    """Notify about test results - important milestone.

    Routes to:
    - GitHub: Summary (e.g., "✅ 12/12 tests passed")
    - Slack: Detailed results with breakdown, threaded

    Args:
        issue_id: GitHub issue number
        adw_id: ADW session ID
        results: TestResults with passed, failed, total, etc.
        state: Optional ADWState for thread persistence

    Returns:
        True if at least one channel succeeded
    """
    github_success = False
    slack_success = False

    try:
        # GitHub: Summary
        emoji = "✅" if results.success else "❌"
        message = f"{emoji} Tests: {results.passed}/{results.total} passed"

        if results.failed > 0:
            message += f", {results.failed} failed"

        if results.duration > 0:
            mins = int(results.duration // 60)
            secs = int(results.duration % 60)
            message += f" ({mins}m {secs}s)"

        if results.details:
            message += f"\n{results.details}"

        make_issue_comment(issue_id, message)
        github_success = True

    except Exception as e:
        logger.warning(f"Failed to send GitHub test notification: {e}")

    try:
        # Slack: Detailed results
        thread_ts = state.get("slack_thread_ts") if state else None
        github_url = state.get("issue_url", "") if state else ""
        test_summary = f"{results.passed}/{results.total} passed"
        success_result, new_thread_ts = slack_tests_complete(
            int(issue_id), adw_id, results.success, thread_ts=thread_ts,
            github_url=github_url, test_details=test_summary
        )
        if success_result and new_thread_ts and state:
            state.update(slack_thread_ts=new_thread_ts)
            state.save()
        slack_success = success_result

    except Exception as e:
        logger.warning(f"Failed to send Slack test notification: {e}")

    return github_success or slack_success


def notify_test_failure(issue_id: str, adw_id: str, test_name: str,
                       error_message: str, attempt: int = 1) -> bool:
    """Notify about test failure with details.

    Routes to:
    - GitHub: Test failure details
    - Slack: NOT sent (would be too spammy, wait for summary)

    Args:
        issue_id: GitHub issue number
        adw_id: ADW session ID
        test_name: Name of failed test
        error_message: Error details
        attempt: Attempt number (for retries)

    Returns:
        True if GitHub notification succeeded
    """
    try:
        # GitHub: Failure details
        message = f"❌ Test failed: `{test_name}`"
        if attempt > 1:
            message += f" (attempt {attempt})"
        message += f"\n```\n{error_message[:500]}\n```"

        make_issue_comment(issue_id, message)
        return True

    except Exception as e:
        logger.warning(f"Failed to send test failure notification: {e}")
        return False


# =============================================================================
# Critical Event Notifications (GitHub + Slack)
# =============================================================================

def notify_error(issue_id: str, adw_id: str, error_message: str,
                context: str = "", state: Optional["ADWState"] = None) -> bool:
    """Notify about critical error - urgent.

    Routes to:
    - GitHub: Error details
    - Slack: Urgent notification with alert formatting, threaded

    Args:
        issue_id: GitHub issue number
        adw_id: ADW session ID
        error_message: Error description
        context: Additional context (phase, operation, etc.)
        state: Optional ADWState for thread persistence

    Returns:
        True if at least one channel succeeded
    """
    github_success = False
    slack_success = False

    try:
        # GitHub: Error details
        message = f"🚨 Error"
        if context:
            message += f" during {context}"
        message += f"\n```\n{error_message[:1000]}\n```"

        make_issue_comment(issue_id, message)
        github_success = True

    except Exception as e:
        logger.warning(f"Failed to send GitHub error notification: {e}")

    try:
        # Slack: Urgent error notification
        thread_ts = state.get("slack_thread_ts") if state else None
        github_url = state.get("issue_url", "") if state else ""
        success_result, new_thread_ts = slack_error(
            int(issue_id), adw_id, error_message, thread_ts=thread_ts,
            github_url=github_url, phase=context
        )
        if success_result and new_thread_ts and state:
            state.update(slack_thread_ts=new_thread_ts)
            state.save()
        slack_success = success_result

    except Exception as e:
        logger.warning(f"Failed to send Slack error notification: {e}")

    return github_success or slack_success


def notify_pr_created(issue_id: str, adw_id: str, pr_url: str,
                     pr_number: str = "", state: Optional["ADWState"] = None) -> bool:
    """Notify that PR has been created - important milestone.

    Routes to:
    - GitHub: PR link
    - Slack: PR notification with link, threaded

    Args:
        issue_id: GitHub issue number
        adw_id: ADW session ID
        pr_url: Pull request URL
        pr_number: PR number
        state: Optional ADWState for thread persistence

    Returns:
        True if at least one channel succeeded
    """
    github_success = False
    slack_success = False

    try:
        # GitHub: PR link
        message = "🎉 Pull request created"
        if pr_number:
            message += f" #{pr_number}"
        message += f"\n{pr_url}"

        make_issue_comment(issue_id, message)
        github_success = True

    except Exception as e:
        logger.warning(f"Failed to send GitHub PR notification: {e}")

    try:
        # Slack: PR notification
        thread_ts = state.get("slack_thread_ts") if state else None
        github_url = state.get("issue_url", "") if state else ""
        success_result, new_thread_ts = slack_pr_created(
            int(issue_id), adw_id, pr_url, thread_ts=thread_ts,
            github_url=github_url, pr_number=pr_number
        )
        if success_result and new_thread_ts and state:
            state.update(slack_thread_ts=new_thread_ts)
            state.save()
        slack_success = success_result

    except Exception as e:
        logger.warning(f"Failed to send Slack PR notification: {e}")

    return github_success or slack_success


# =============================================================================
# Progress Notifications (GitHub ONLY - No Slack Spam)
# =============================================================================

def notify_progress(issue_id: str, message: str) -> bool:
    """Notify about progress update - low priority, GitHub only.

    Routes to:
    - GitHub: Progress message
    - Slack: NOT sent (avoid spam)

    Use this for:
    - Analyzing files
    - Checking out branches
    - Starting operations
    - State transitions

    Args:
        issue_id: GitHub issue number
        message: Progress message

    Returns:
        True if GitHub notification succeeded
    """
    try:
        make_issue_comment(issue_id, message)
        return True

    except Exception as e:
        logger.warning(f"Failed to send progress notification: {e}")
        return False


def notify_state_transition(issue_id: str, from_state: str, to_state: str) -> bool:
    """Notify about workflow state transition - GitHub only.

    Routes to:
    - GitHub: State transition message
    - Slack: NOT sent

    Args:
        issue_id: GitHub issue number
        from_state: Previous state
        to_state: New state

    Returns:
        True if GitHub notification succeeded
    """
    try:
        message = f"🔄 State: {from_state} → {to_state}"
        make_issue_comment(issue_id, message)
        return True

    except Exception as e:
        logger.warning(f"Failed to send state transition notification: {e}")
        return False


# =============================================================================
# Build Notifications (GitHub + Slack)
# =============================================================================

@dataclass
class BuildDetails:
    """Build execution details."""
    duration: float = 0.0
    files_built: int = 0
    success: bool = True
    output_file: str = ""
    error_message: str = ""


def notify_build_start(issue_id: str, adw_id: str) -> bool:
    """Notify that build is starting.

    Routes to:
    - GitHub: Simple build start message
    - Slack: NOT sent (avoid spam)

    Args:
        issue_id: GitHub issue number
        adw_id: ADW session ID

    Returns:
        True if GitHub notification succeeded
    """
    return notify_phase_start(issue_id, adw_id, "building")


def notify_build_complete(issue_id: str, adw_id: str,
                         details: Optional[BuildDetails] = None) -> bool:
    """Notify that build completed - milestone.

    Routes to:
    - GitHub: Build summary
    - Slack: Build results, threaded

    Args:
        issue_id: GitHub issue number
        adw_id: ADW session ID
        details: Optional BuildDetails

    Returns:
        True if at least one channel succeeded
    """
    if details is None:
        details = BuildDetails()

    phase_details = PhaseDetails(
        duration=details.duration,
        files_modified=details.files_built,
        output_file=details.output_file
    )

    return notify_phase_complete(issue_id, adw_id, "building", phase_details)


# =============================================================================
# Documentation and Review Notifications (GitHub + Slack)
# =============================================================================

def notify_document_complete(issue_id: str, adw_id: str, document_path: str = "",
                            duration: float = 0.0) -> bool:
    """Notify that documentation generation completed.

    Routes to:
    - GitHub: Documentation completion message
    - Slack: Documentation notification, threaded

    Args:
        issue_id: GitHub issue number
        adw_id: ADW session ID
        document_path: Path to generated documentation
        duration: Generation duration

    Returns:
        True if at least one channel succeeded
    """
    details = PhaseDetails(
        duration=duration,
        output_file=document_path
    )

    return notify_phase_complete(issue_id, adw_id, "documenting", details)


def notify_review_complete(issue_id: str, adw_id: str, screenshot_count: int = 0,
                          findings: str = "", duration: float = 0.0) -> bool:
    """Notify that review phase completed.

    Routes to:
    - GitHub: Review summary
    - Slack: Review results, threaded

    Args:
        issue_id: GitHub issue number
        adw_id: ADW session ID
        screenshot_count: Number of screenshots taken
        findings: Review findings summary
        duration: Review duration

    Returns:
        True if at least one channel succeeded
    """
    github_success = False

    try:
        # GitHub: Review summary
        message = "✅👀 Review phase completed"

        if duration > 0:
            mins = int(duration // 60)
            secs = int(duration % 60)
            message += f" ({mins}m {secs}s)"

        if screenshot_count > 0:
            message += f"\n📸 Screenshots: {screenshot_count}"

        if findings:
            message += f"\n{findings}"

        make_issue_comment(issue_id, message)
        github_success = True

    except Exception as e:
        logger.warning(f"Failed to send review notification: {e}")

    # For now, no dedicated Slack function, use generic phase complete
    return github_success


# =============================================================================
# Utility Functions
# =============================================================================

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "2m 30s")
    """
    if seconds < 60:
        return f"{int(seconds)}s"

    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}m {secs}s"
