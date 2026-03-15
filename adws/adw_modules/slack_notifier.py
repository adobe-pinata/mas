#!/usr/bin/env python3
"""Slack notification support for ADWS workflows - Minimalist Design.

Notification Format Pattern:
    Line 1: emoji #issue • type • session
    Line 2: status_emoji Status Name • duration/details
    Line 3+: Optional additional info (minimal)

Design Principles:
    - Information Density: Pack more meaning into fewer characters
    - Scanability: User should understand status in <2 seconds
    - Consistency: All messages follow same structural pattern
    - Visual Hierarchy: Emojis + formatting guide the eye to key info
    - Progressive Disclosure: Critical info first, details available but not intrusive

Example Minimalist Format:
    BEFORE (verbose):
        :rocket: *ADWS Notification*
        :file_folder: Repository: `owner/repo`
        :clipboard: Session: `a954f660`
        :link: View Issue
        :speech_balloon: :rocket: *Started Workflow*
        Issue #207: Improve Slack UX
        :label: Type: `/chore`

    AFTER (minimalist):
        🚀 #207 • /chore • a954f660
        ⏱️ Workflow Started
"""

import os
import logging

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
except ImportError:
    WebClient = None
    SlackApiError = None

logger = logging.getLogger(__name__)


def send_slack_notification(message: str, session_id: str = "unknown", emoji: str = ":robot_face:",
                           thread_ts: str = None, repo_name: str = "", issue_url: str = "",
                           issue_number: int = 0, issue_type: str = "") -> tuple[bool, str]:
    """
    Send minimalist Slack notification from ADWS workflow.

    Format: emoji #issue • type • session
            Details...

    Args:
        message: Notification message (pre-formatted by caller)
        session_id: ADW session ID (8-char hex, e.g., "a954f660")
        emoji: Emoji prefix for message type (default: :robot_face:)
        thread_ts: Thread timestamp for threading messages (optional)
        repo_name: Repository name (only used for first message in thread)
        issue_url: GitHub issue URL
        issue_number: GitHub issue number
        issue_type: Issue classification (/bug, /feature, /chore)

    Returns:
        tuple[bool, str]: (success, thread_ts) - success status and thread timestamp

    Example:
        >>> send_slack_notification(
        ...     message="⏱️ Build Complete • 2m 11s",
        ...     session_id="a954f660",
        ...     emoji="🔨",
        ...     issue_number=207,
        ...     issue_type="/chore"
        ... )
        (True, "1234567890.123456")
    """
    if not WebClient:
        return (False, "")

    bot_token = os.getenv('SLACK_BOT_TOKEN')
    channel_id = os.getenv('SLACK_CHANNEL_ID')

    if not bot_token or not channel_id:
        logger.debug("Slack credentials not configured, skipping notification")
        return (False, "")

    logger.debug(f"Sending minimalist Slack notification for issue #{issue_number}")

    try:
        client = WebClient(token=bot_token, timeout=5)

        # Minimalist header format
        header_parts = []
        if issue_number:
            header_parts.append(f"#{issue_number}")
        if issue_type:
            header_parts.append(issue_type)
        header_parts.append(session_id[:8])  # Truncate to 8 chars

        slack_message = f"{emoji} {' • '.join(header_parts)}"

        # Repository only in thread parent (first message)
        if not thread_ts and repo_name:
            slack_message += f"\n📁 `{repo_name}`"

        # Add main message content
        slack_message += f"\n{message}"

        # Issue link (if provided)
        if issue_url:
            slack_message += f"\n🔗 <{issue_url}|View Issue>"

        response = client.chat_postMessage(
            channel=channel_id,
            text=slack_message,
            thread_ts=thread_ts,
            mrkdwn=True
        )

        # Capture thread timestamp from response
        new_thread_ts = response.get("thread_ts") or response.get("ts")
        return (response.get("ok", False), new_thread_ts or "")
    except (SlackApiError, Exception):
        return (False, "")  # Silent fail


def notify_workflow_start(issue_number: int, adw_id: str, issue_title: str = "",
                         issue_command: str = "", github_url: str = "",
                         thread_ts: str = None) -> tuple[bool, str]:
    """Notify that workflow has started.

    Minimalist Format:
        🚀 #207 • /chore • a954f660
        📁 `owner/repo`
        ⏱️ Workflow Started
        🔗 View Issue

    Args:
        issue_number: GitHub issue number
        adw_id: ADW session ID
        issue_title: Issue title (not displayed in minimalist format)
        issue_command: Issue classification (/bug, /feature, /chore)
        github_url: GitHub issue URL
        thread_ts: Thread timestamp (usually None for start)

    Returns:
        tuple[bool, str]: (success, thread_ts)
    """
    # Extract repo name from URL (only for first message)
    repo_name = ""
    if github_url and not thread_ts:  # Only extract for thread parent
        logger.debug(f"notify_workflow_start received github_url: {github_url}")
        parts = github_url.replace("https://github.com/", "").split("/")
        if len(parts) >= 2:
            repo_name = f"{parts[0]}/{parts[1]}"
            logger.debug(f"Extracted repo_name: {repo_name}")

    message = "⏱️ Workflow Started"

    return send_slack_notification(
        message,
        session_id=adw_id,
        emoji="🚀",
        thread_ts=thread_ts,
        repo_name=repo_name,
        issue_url=github_url,
        issue_number=issue_number,
        issue_type=issue_command
    )


def notify_planning_complete(issue_number: int, adw_id: str, plan_file_path: str = "",
                            planning_duration: float = 0.0, thread_ts: str = None,
                            github_url: str = "") -> tuple[bool, str]:
    """Notify that planning phase is complete.

    Minimalist Format:
        📝 #207 • /chore • a954f660
        ✅ Planning Complete • 3m 42s

    Args:
        issue_number: GitHub issue number
        adw_id: ADW session ID
        plan_file_path: Path to plan file (not displayed in minimalist format)
        planning_duration: Duration in seconds
        thread_ts: Thread timestamp for threading
        github_url: GitHub issue URL

    Returns:
        tuple[bool, str]: (success, thread_ts)
    """
    duration_str = f"{int(planning_duration // 60)}m {int(planning_duration % 60)}s" if planning_duration else ""
    message = f"✅ Planning Complete"
    if duration_str:
        message += f" • {duration_str}"

    return send_slack_notification(
        message,
        session_id=adw_id,
        emoji="📝",
        thread_ts=thread_ts,
        repo_name="",  # No repo name in threaded messages
        issue_url=github_url if not thread_ts else "",  # Issue URL only in thread parent
        issue_number=issue_number,
        issue_type=""
    )


def notify_build_complete(issue_number: int, adw_id: str, thread_ts: str = None,
                         github_url: str = "", build_duration: float = 0.0) -> tuple[bool, str]:
    """Notify that build phase is complete.

    Minimalist Format:
        🔨 #207 • /chore • a954f660
        ✅ Build Complete • 2m 11s

    Args:
        issue_number: GitHub issue number
        adw_id: ADW session ID
        thread_ts: Thread timestamp for threading
        github_url: GitHub issue URL
        build_duration: Build duration in seconds

    Returns:
        tuple[bool, str]: (success, thread_ts)
    """
    duration_str = f"{int(build_duration // 60)}m {int(build_duration % 60)}s" if build_duration else ""
    message = f"✅ Build Complete"
    if duration_str:
        message += f" • {duration_str}"

    return send_slack_notification(
        message,
        session_id=adw_id,
        emoji="🔨",
        thread_ts=thread_ts,
        repo_name="",
        issue_url=github_url if not thread_ts else "",
        issue_number=issue_number,
        issue_type=""
    )


def notify_tests_complete(issue_number: int, adw_id: str, passed: bool, thread_ts: str = None,
                         github_url: str = "", test_details: str = "") -> tuple[bool, str]:
    """Notify about test results.

    Minimalist Format (passed):
        ✅ #207 • /chore • a954f660
        ✅ Tests Passed • 12/12

    Minimalist Format (failed):
        ❌ #207 • /chore • a954f660
        ❌ Tests Failed • 3/12

    Args:
        issue_number: GitHub issue number
        adw_id: ADW session ID
        passed: Whether tests passed
        thread_ts: Thread timestamp for threading
        github_url: GitHub issue URL
        test_details: Additional test details (e.g., "12/12 passed")

    Returns:
        tuple[bool, str]: (success, thread_ts)
    """
    emoji = "✅" if passed else "❌"
    status = "Passed" if passed else "Failed"
    message = f"{emoji} Tests {status}"
    if test_details:
        message += f" • {test_details}"

    return send_slack_notification(
        message,
        session_id=adw_id,
        emoji=emoji,
        thread_ts=thread_ts,
        repo_name="",
        issue_url=github_url if not thread_ts else "",
        issue_number=issue_number,
        issue_type=""
    )


def notify_pr_created(issue_number: int, adw_id: str, pr_url: str, thread_ts: str = None,
                     github_url: str = "", pr_number: str = "") -> tuple[bool, str]:
    """Notify that PR has been created.

    Minimalist Format:
        🎉 #207 • /chore • a954f660
        📬 PR Created • #123
        🔗 View Pull Request

    Args:
        issue_number: GitHub issue number
        adw_id: ADW session ID
        pr_url: Pull request URL
        thread_ts: Thread timestamp for threading
        github_url: GitHub issue URL
        pr_number: Pull request number

    Returns:
        tuple[bool, str]: (success, thread_ts)
    """
    message = f"📬 PR Created"
    if pr_number:
        message += f" • #{pr_number}"
    if pr_url:
        message += f"\n🔗 <{pr_url}|View Pull Request>"

    return send_slack_notification(
        message,
        session_id=adw_id,
        emoji="🎉",
        thread_ts=thread_ts,
        repo_name="",
        issue_url=github_url if not thread_ts else "",
        issue_number=issue_number,
        issue_type=""
    )


def notify_workflow_complete(issue_number: int, adw_id: str, success: bool, thread_ts: str = None,
                            github_url: str = "", duration: float = 0.0) -> tuple[bool, str]:
    """Notify that workflow is complete.

    Minimalist Format (success):
        ✅ #207 • /chore • a954f660
        🏁 Workflow Complete • 15m 32s

    Minimalist Format (failed):
        ❌ #207 • /chore • a954f660
        🏁 Workflow Failed • 8m 12s

    Args:
        issue_number: GitHub issue number
        adw_id: ADW session ID
        success: Whether workflow completed successfully
        thread_ts: Thread timestamp for threading
        github_url: GitHub issue URL
        duration: Total workflow duration in seconds

    Returns:
        tuple[bool, str]: (success, thread_ts)
    """
    emoji = "✅" if success else "❌"
    status = "Complete" if success else "Failed"
    message = f"🏁 Workflow {status}"

    if duration > 0:
        duration_mins = int(duration // 60)
        duration_secs = int(duration % 60)
        message += f" • {duration_mins}m {duration_secs}s"

    return send_slack_notification(
        message,
        session_id=adw_id,
        emoji=emoji,
        thread_ts=thread_ts,
        repo_name="",
        issue_url=github_url if not thread_ts else "",
        issue_number=issue_number,
        issue_type=""
    )


def notify_error(issue_number: int, adw_id: str, error_message: str, thread_ts: str = None,
                github_url: str = "", phase: str = "") -> tuple[bool, str]:
    """Notify about workflow error.

    Minimalist Format:
        🚨 #207 • /chore • a954f660
        ❌ Error in testing
        ```error details (truncated to 300 chars)```

    Args:
        issue_number: GitHub issue number
        adw_id: ADW session ID
        error_message: Error message text
        thread_ts: Thread timestamp for threading
        github_url: GitHub issue URL
        phase: Workflow phase where error occurred (e.g., "building", "testing")

    Returns:
        tuple[bool, str]: (success, thread_ts)
    """
    message = f"❌ Error"
    if phase:
        message += f" in {phase}"

    # Truncate error message to 300 chars (more aggressive than before)
    truncated_error = error_message[:300] + "..." if len(error_message) > 300 else error_message
    message += f"\n```{truncated_error}```"

    return send_slack_notification(
        message,
        session_id=adw_id,
        emoji="🚨",
        thread_ts=thread_ts,
        repo_name="",
        issue_url=github_url if not thread_ts else "",
        issue_number=issue_number,
        issue_type=""
    )


def notify_review_complete(issue_number: int, adw_id: str, thread_ts: str = None,
                           github_url: str = "", screenshot_count: int = 0) -> tuple[bool, str]:
    """Notify that review phase is complete.

    Minimalist Format:
        👀 #207 • /chore • a954f660
        ✅ Review Complete • 3 screenshots

    Args:
        issue_number: GitHub issue number
        adw_id: ADW session ID
        thread_ts: Thread timestamp for threading
        github_url: GitHub issue URL
        screenshot_count: Number of screenshots taken

    Returns:
        tuple[bool, str]: (success, thread_ts)
    """
    message = f"✅ Review Complete"
    if screenshot_count > 0:
        message += f" • {screenshot_count} screenshots"

    return send_slack_notification(
        message,
        session_id=adw_id,
        emoji="👀",
        thread_ts=thread_ts,
        repo_name="",
        issue_url=github_url if not thread_ts else "",
        issue_number=issue_number,
        issue_type=""
    )


def notify_shipped(issue_number: int, adw_id: str, thread_ts: str = None,
                   github_url: str = "", pr_merged: bool = False) -> tuple[bool, str]:
    """Notify that issue has been shipped to production.

    Minimalist Format:
        🚀 #207 • /chore • a954f660
        ✅ Shipped • PR merged

    Args:
        issue_number: GitHub issue number
        adw_id: ADW session ID
        thread_ts: Thread timestamp for threading
        github_url: GitHub issue URL
        pr_merged: Whether PR was merged

    Returns:
        tuple[bool, str]: (success, thread_ts)
    """
    message = f"✅ Shipped"
    if pr_merged:
        message += f" • PR merged"

    return send_slack_notification(
        message,
        session_id=adw_id,
        emoji="🚀",
        thread_ts=thread_ts,
        repo_name="",
        issue_url=github_url if not thread_ts else "",
        issue_number=issue_number,
        issue_type=""
    )
