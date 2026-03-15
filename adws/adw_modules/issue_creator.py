"""Issue creation with screenshot upload support for ADWS."""

import os
import logging
import subprocess
from typing import Dict, List, Optional
from pathlib import Path

from adw_modules.aio_files_uploader import AIOFilesUploader
from adw_modules.data_types import IssueCreationRequest, IssueCreationResult


def upload_issue_screenshots(
    screenshot_paths: List[str],
    adw_id: str,
    logger: logging.Logger
) -> Dict[str, str]:
    """
    Upload screenshots via AIO Files for issue creation.

    Args:
        screenshot_paths: List of local screenshot file paths
        adw_id: ADW workflow ID for organizing uploads
        logger: Logger instance

    Returns:
        Dict mapping local paths to AIO Files CDN URLs (or original paths if upload failed)

    Example:
        >>> urls = upload_issue_screenshots(
        ...     ["agents/adw-123/screenshot1.png", "screenshot2.png"],
        ...     "adw-123",
        ...     logger
        ... )
        >>> urls
        {
            "agents/adw-123/screenshot1.png": "https://...azureedge.net/adw/adw-123/issues/screenshot1.png",
            "screenshot2.png": "https://...azureedge.net/adw/adw-123/issues/screenshot2.png"
        }
    """
    if not screenshot_paths:
        return {}

    logger.info(f"Uploading {len(screenshot_paths)} screenshots for issue creation")
    uploader = AIOFilesUploader(logger)

    url_mapping = {}
    for local_path in screenshot_paths:
        if not local_path:
            continue

        # Convert to absolute path if relative
        abs_path = local_path if os.path.isabs(local_path) else os.path.abspath(local_path)

        # Check if file exists
        if not os.path.exists(abs_path):
            logger.warning(f"Screenshot not found: {abs_path}")
            url_mapping[local_path] = local_path  # Keep original path as fallback
            continue

        # Upload with organized path: adw/{adw_id}/issues/{filename}
        filename = Path(abs_path).name
        remote_path = f"adw/{adw_id}/issues/{filename}"

        url = uploader.upload_file(abs_path, remote_path)

        if url:
            url_mapping[local_path] = url
            logger.info(f"Uploaded screenshot to: {url}")
        else:
            logger.warning(f"Failed to upload screenshot, using local path: {local_path}")
            url_mapping[local_path] = local_path

    return url_mapping


def generate_issue_body_with_screenshots(
    body: str,
    screenshot_url_mapping: Dict[str, str],
    adw_id: str
) -> str:
    """
    Generate issue body with embedded screenshot markdown and ADW metadata.

    Args:
        body: Original issue body text
        screenshot_url_mapping: Dict mapping local paths to public URLs
        adw_id: ADW workflow ID for tracking and workflow continuity

    Returns:
        Formatted markdown string with embedded images and ADW metadata

    Example:
        >>> body = "This is a bug report"
        >>> urls = {"screenshot1.png": "https://domain.com/screenshot1.png"}
        >>> result = generate_issue_body_with_screenshots(body, urls, "abc12345")
        >>> print(result)
        This is a bug report

        ---

        **ADW Metadata**: `ADW ID: abc12345`

        ## Screenshots

        ![Screenshot 1](https://domain.com/screenshot1.png)
    """
    # Build ADW metadata section
    # Format: "ADW ID: {adw_id}" - parseable by extract_adw_info()
    adw_metadata = f"\n\n---\n\n**ADW Metadata**: `ADW ID: {adw_id}`\n"

    # Build screenshot section
    screenshot_section = ""
    if screenshot_url_mapping:
        screenshot_section = "\n\n## Screenshots\n\n"

        for i, (local_path, url) in enumerate(screenshot_url_mapping.items(), 1):
            filename = Path(local_path).stem.replace("_", " ").replace("-", " ").title()
            screenshot_section += f"![Screenshot {i}: {filename}]({url})\n\n"

    return body + adw_metadata + screenshot_section


def create_issue_with_screenshots(
    request: IssueCreationRequest,
    logger: logging.Logger
) -> IssueCreationResult:
    """
    Create a GitHub issue with screenshot uploads.

    Args:
        request: Issue creation request with title, body, and screenshots
        logger: Logger instance

    Returns:
        Result containing success status, issue details, and screenshot URLs

    Example:
        >>> request = IssueCreationRequest(
        ...     title="Bug: Login button not working",
        ...     body="The login button does not respond to clicks",
        ...     screenshot_paths=["bug_screenshot.png"],
        ...     adw_id="adw-abc123"
        ... )
        >>> result = create_issue_with_screenshots(request, logger)
        >>> result.success
        True
        >>> result.issue_number
        42
    """
    try:
        # Upload screenshots if provided
        screenshot_urls = []
        if request.screenshot_paths:
            url_mapping = upload_issue_screenshots(
                request.screenshot_paths,
                request.adw_id,
                logger
            )
            screenshot_urls = list(url_mapping.values())

            # Generate formatted issue body with embedded images and ADW metadata
            formatted_body = generate_issue_body_with_screenshots(
                request.body,
                url_mapping,
                request.adw_id
            )
        else:
            # Even without screenshots, embed ADW metadata for workflow continuity
            formatted_body = generate_issue_body_with_screenshots(
                request.body,
                {},
                request.adw_id
            )

        # Create GitHub issue using gh CLI
        logger.info(f"Creating GitHub issue: {request.title}")

        cmd = ["gh", "issue", "create", "--title", request.title, "--body", formatted_body]

        # Add repository flag if specified
        if request.repository_path:
            cmd.extend(["--repo", request.repository_path])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        # Extract issue URL from output
        issue_url = result.stdout.strip()

        # Extract issue number from URL (e.g., https://github.com/user/repo/issues/42)
        issue_number = None
        if issue_url:
            parts = issue_url.rstrip("/").split("/")
            if len(parts) > 0 and parts[-1].isdigit():
                issue_number = int(parts[-1])

        logger.info(f"Successfully created issue #{issue_number}: {issue_url}")

        return IssueCreationResult(
            success=True,
            issue_number=issue_number,
            issue_url=issue_url,
            screenshot_urls=screenshot_urls
        )

    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to create GitHub issue: {e.stderr}"
        logger.error(error_msg)
        return IssueCreationResult(
            success=False,
            error=error_msg
        )
    except Exception as e:
        error_msg = f"Unexpected error creating issue: {str(e)}"
        logger.error(error_msg)
        return IssueCreationResult(
            success=False,
            error=error_msg
        )
