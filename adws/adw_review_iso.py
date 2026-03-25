#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "boto3>=1.26.0", "slack-sdk", "PyJWT", "cryptography"]
# ///

"""
ADW Review Iso - Developer Workflow for agentic review in isolated worktrees

Usage:
  uv run adw_review_iso.py <issue-number> <adw-id> [--skip-resolution]

Workflow:
1. Load state and validate worktree exists
2. Find spec file from worktree
3. Review implementation against specification in worktree
4. Capture screenshots of critical functionality
5. If issues found and --skip-resolution not set:
   - Create patch plans for issues
   - Implement resolutions
6. Post results as commit message
7. Commit review results in worktree
8. Push and update PR

This workflow REQUIRES that adw_plan_iso.py or adw_patch_iso.py has been run first
to create the worktree. It cannot create worktrees itself.
"""

import sys
import os
import logging
import json
import re
from typing import Optional, List
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
    implement_plan,
    find_spec_file,
)
from adw_modules.utils import setup_logger, parse_json, check_env_vars
from adw_modules.data_types import (
    AgentTemplateRequest,
    ReviewResult,
    ReviewIssue,
    AgentPromptResponse,
)
from adw_modules.agent import execute_template
from adw_modules.r2_uploader import R2Uploader
from adw_modules.app_config import get_app_config_value
from adw_modules.github_raw_uploader import upload_screenshots_as_raw_urls
from adw_modules.worktree_ops import validate_worktree

# Agent name constants
AGENT_REVIEWER = "reviewer"
AGENT_REVIEW_PATCH_PLANNER = "review_patch_planner"
AGENT_REVIEW_PATCH_IMPLEMENTOR = "review_patch_implementor"

# Maximum number of review retry attempts after resolution
MAX_REVIEW_RETRY_ATTEMPTS = 3




def run_review(
    spec_file: str,
    adw_id: str,
    logger: logging.Logger,
    working_dir: Optional[str] = None,
) -> ReviewResult:
    """Run the review using the /review command."""
    request = AgentTemplateRequest(
        agent_name=AGENT_REVIEWER,
        slash_command="/review",
        args=[adw_id, spec_file, AGENT_REVIEWER],
        adw_id=adw_id,
        working_dir=working_dir,
    )

    logger.debug(f"review_request: {request.model_dump_json(indent=2, by_alias=True)}")

    response = execute_template(request)

    logger.debug(f"review_response: {response.model_dump_json(indent=2, by_alias=True)}")

    if not response.success:
        logger.error(f"Review failed: {response.output}")

        # Detect consent prompt blocking
        output_lower = response.output.lower()
        consent_keywords = ["consent", "permission", "i need to perform", "database reset requires"]

        if any(keyword in output_lower for keyword in consent_keywords):
            error_msg = (
                "Review blocked by consent prompt for database operation. "
                "This indicates prepare_app.md triggered an interactive consent request. "
                "Verify that prepare_app.md detects ADWS context (.ports.env) and skips consent prompts."
            )
            logger.error(error_msg)
            return ReviewResult(
                success=False,
                review_summary=error_msg,
                review_issues=[],
                screenshots=[],
                screenshot_urls=[],
            )

        # Generic failure
        return ReviewResult(
            success=False,
            review_summary=f"Review failed: {response.output}",
            review_issues=[],
            screenshots=[],
            screenshot_urls=[],
        )

    # Parse the review result
    try:
        result = parse_json(response.output, ReviewResult)
        return result
    except Exception as e:
        logger.error(f"Error parsing review result: {e}")
        return ReviewResult(
            success=False,
            review_summary=f"Error parsing review result: {e}",
            review_issues=[],
            screenshots=[],
            screenshot_urls=[],
        )


def create_review_patch_plan(
    issue: ReviewIssue,
    issue_num: int,
    adw_id: str,
    logger: logging.Logger,
    working_dir: Optional[str] = None,
) -> AgentPromptResponse:
    """Create a patch plan for a review issue."""
    # Build patch command with issue details
    patch_args = [
        f"Issue #{issue_num}: {issue.issue_description}",
        f"Resolution: {issue.issue_resolution}",
        f"Severity: {issue.issue_severity}",
    ]

    request = AgentTemplateRequest(
        agent_name=AGENT_REVIEW_PATCH_PLANNER,
        slash_command="/patch",
        args=patch_args,
        adw_id=adw_id,
        working_dir=working_dir,
    )

    return execute_template(request)


def upload_review_screenshots(
    review_result: ReviewResult,
    adw_id: str,
    worktree_path: str,
    logger: logging.Logger,
    branch_name: Optional[str] = None,
) -> None:
    """Upload screenshots and update review result with public URLs.

    Strategy:
    1. Try AIO Files (if AIO runtime credentials are present in env).
    2. If AIO Files is disabled or any upload fails, fall back to committing
       screenshots to the worktree branch and using raw.githubusercontent.com URLs.

    Args:
        review_result: Review result containing screenshot paths
        adw_id: ADW workflow ID
        worktree_path: Path to the worktree
        logger: Logger instance
        branch_name: Git branch name for the GitHub Raw URL fallback.
            If None, will be detected from the worktree automatically.

    Note:
        This modifies review_result in-place by setting screenshot_urls
        and updating issue.screenshot_url fields.
    """
    if not review_result.screenshots:
        return

    logger.info(f"Uploading {len(review_result.screenshots)} screenshots")

    screenshot_urls = []
    need_fallback = True

    # --- Strategy 1: R2 (primary) ---
    r2_uploader = R2Uploader(logger, app_name=get_app_config_value("app_name"), bucket_name=get_app_config_value("r2_bucket"))
    if r2_uploader.enabled:
        r2_urls = []
        r2_failed = False

        for local_path in review_result.screenshots:
            abs_path = os.path.join(worktree_path, local_path)

            if not os.path.exists(abs_path):
                logger.warning(f"Screenshot not found: {abs_path}")
                continue

            namespace = get_app_config_value("app_name", "agentic")
            object_key = f"adw/{namespace}/{adw_id}/review/{os.path.basename(local_path)}"
            url = r2_uploader.upload_file(abs_path, object_key)

            if url:
                r2_urls.append(url)
                logger.info(f"Uploaded screenshot via R2: {url}")
            else:
                logger.warning(f"R2 upload failed for: {local_path}")
                r2_failed = True
                break

        if not r2_failed and r2_urls:
            screenshot_urls = r2_urls
            need_fallback = False
        else:
            logger.info("R2 upload incomplete — falling through to GitHub Raw URLs")
    else:
        logger.info("R2 not configured — using GitHub Raw URL fallback")

    # --- Strategy 2: GitHub Raw URLs (fallback) ---
    if need_fallback:
        # Resolve branch name from worktree if not provided
        if not branch_name:
            try:
                import subprocess as _sp
                res = _sp.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    capture_output=True,
                    text=True,
                    cwd=worktree_path,
                )
                branch_name = res.stdout.strip() if res.returncode == 0 else "main"
            except Exception:
                branch_name = "main"

        logger.info(f"Falling back to GitHub Raw URLs on branch '{branch_name}'")
        screenshot_urls = upload_screenshots_as_raw_urls(
            review_result.screenshots,
            worktree_path,
            branch_name,
            adw_id,
            logger,
        )

    # Update review result with URLs
    review_result.screenshot_urls = screenshot_urls

    # Update issues with their screenshot URLs
    for issue in review_result.review_issues:
        if issue.screenshot_path:
            for i, local_path in enumerate(review_result.screenshots):
                if local_path == issue.screenshot_path and i < len(screenshot_urls):
                    issue.screenshot_url = screenshot_urls[i]
                    break


def resolve_blocker_issues(
    blocker_issues: List[ReviewIssue],
    issue_number: str,
    adw_id: str,
    worktree_path: str,
    logger: logging.Logger
) -> None:
    """Resolve blocker issues by creating and implementing patches.
    
    Args:
        blocker_issues: List of blocker issues to resolve
        issue_number: GitHub issue number
        adw_id: ADW workflow ID
        worktree_path: Path to the worktree
        logger: Logger instance
    """
    logger.info(f"Found {len(blocker_issues)} blocker issues, attempting resolution")
    make_issue_comment(
        issue_number,
        format_issue_message(
            adw_id,
            AGENT_REVIEW_PATCH_PLANNER,
            f"🔧 Found {len(blocker_issues)} blocker issues, creating resolution plans..."
        )
    )
    
    # Create and implement patches for each blocker
    for i, issue in enumerate(blocker_issues, 1):
        logger.info(f"Resolving blocker {i}/{len(blocker_issues)}: {issue.issue_description}")
        
        # Create patch plan
        plan_response = create_review_patch_plan(issue, i, adw_id, logger, working_dir=worktree_path)
        
        if not plan_response.success:
            logger.error(f"Failed to create patch plan: {plan_response.output}")
            continue
        
        # Extract plan file path
        raw_output = plan_response.output.strip()

        # Extract the actual file path from Claude's response
        # Claude sometimes adds conversational text, we need just the path
        path_pattern = r'specs/patch/patch-adw-[a-f0-9]+-[a-z0-9\-]+\.md'
        match = re.search(path_pattern, raw_output)

        if match:
            plan_file = match.group(0)
            logger.info(f"Extracted patch plan path: {plan_file}")
        else:
            # Fallback: look for any line starting with "specs/patch/" or "specs/"
            for line in raw_output.split('\n'):
                line = line.strip()
                if (line.startswith('specs/patch/') or line.startswith('specs/')) and line.endswith('.md'):
                    plan_file = line
                    logger.info(f"Extracted patch plan from line: {plan_file}")
                    break
            else:
                # Last resort: use the whole response
                plan_file = raw_output
                logger.warning(f"Could not parse patch plan path, using raw output: {plan_file[:100]}")
        
        # Implement the patch
        logger.info(f"Implementing patch from plan: {plan_file}")
        impl_response = implement_plan(plan_file, adw_id, logger, working_dir=worktree_path)
        
        if not impl_response.success:
            logger.error(f"Failed to implement patch: {impl_response.output}")
            continue
        
        logger.info(f"Successfully resolved blocker {i}")


def build_review_summary(review_result: ReviewResult) -> str:
    """Build a formatted summary of the review results for GitHub comment.
    
    Args:
        review_result: The review result containing summary, issues, and screenshot URLs
        
    Returns:
        Formatted markdown string for GitHub comment
    """
    summary_parts = [f"## 📊 Review Summary\n\n{review_result.review_summary}"]
    
    # Add review issues grouped by severity
    if review_result.review_issues:
        summary_parts.append("\n## 🔍 Issues Found")
        
        # Group by severity
        blockers = [i for i in review_result.review_issues if i.issue_severity == "blocker"]
        tech_debts = [i for i in review_result.review_issues if i.issue_severity == "tech_debt"]
        skippables = [i for i in review_result.review_issues if i.issue_severity == "skippable"]
        
        if blockers:
            summary_parts.append(f"\n### 🚨 Blockers ({len(blockers)})")
            for issue in blockers:
                summary_parts.append(f"- **Issue {issue.review_issue_number}**: {issue.issue_description}")
                summary_parts.append(f"  - Resolution: {issue.issue_resolution}")
                if issue.screenshot_url and issue.screenshot_url.startswith("http"):
                    summary_parts.append(f"  - ![Issue Screenshot]({issue.screenshot_url})")
        
        if tech_debts:
            summary_parts.append(f"\n### ⚠️ Tech Debt ({len(tech_debts)})")
            for issue in tech_debts:
                summary_parts.append(f"- **Issue {issue.review_issue_number}**: {issue.issue_description}")
                summary_parts.append(f"  - Resolution: {issue.issue_resolution}")
                if issue.screenshot_url and issue.screenshot_url.startswith("http"):
                    summary_parts.append(f"  - ![Issue Screenshot]({issue.screenshot_url})")
        
        if skippables:
            summary_parts.append(f"\n### 💡 Skippable ({len(skippables)})")
            for issue in skippables:
                summary_parts.append(f"- **Issue {issue.review_issue_number}**: {issue.issue_description}")
                summary_parts.append(f"  - Resolution: {issue.issue_resolution}")
                if issue.screenshot_url and issue.screenshot_url.startswith("http"):
                    summary_parts.append(f"  - ![Issue Screenshot]({issue.screenshot_url})")
    
    # Add screenshots section
    if review_result.screenshot_urls:
        summary_parts.append(f"\n## 📸 Screenshots")
        summary_parts.append(f"Captured {len(review_result.screenshot_urls)} screenshots\n")
        
        # Use uploaded URLs to display as inline images
        for i, screenshot_url in enumerate(review_result.screenshot_urls):
            if screenshot_url.startswith("http"):
                # Display as inline image
                summary_parts.append(f"### Screenshot {i+1}")
                summary_parts.append(f"![Screenshot {i+1}]({screenshot_url})\n")
            else:
                # Fallback to showing path if not a URL
                summary_parts.append(f"- Screenshot {i+1}: `{screenshot_url}`")
    
    return "\n".join(summary_parts)


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()
    
    # Check for --skip-resolution flag
    skip_resolution = "--skip-resolution" in sys.argv
    if skip_resolution:
        sys.argv.remove("--skip-resolution")
    
    # Parse command line args
    # INTENTIONAL: adw-id is REQUIRED - we need it to find the worktree
    if len(sys.argv) < 3:
        print("Usage: uv run adw_review_iso.py <issue-number> <adw-id> [--skip-resolution]")
        print("\nError: adw-id is required to locate the worktree")
        print("Run adw_plan_iso.py or adw_patch_iso.py first to create the worktree")
        sys.exit(1)
    
    issue_number = sys.argv[1]
    adw_id = sys.argv[2]
    
    # Try to load existing state
    temp_logger = setup_logger(adw_id, "adw_review_iso")
    state = ADWState.load(adw_id, temp_logger)
    if state:
        # Found existing state - use the issue number from state if available
        issue_number = state.get("issue_number", issue_number)
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", "Starting review")
        )
    else:
        # No existing state found
        logger = setup_logger(adw_id, "adw_review_iso")
        logger.error(f"No state found for ADW ID: {adw_id}")
        logger.error("Run adw_plan_iso.py or adw_patch_iso.py first to create the worktree and state")
        print(f"\nError: No state found for ADW ID: {adw_id}")
        print("Run adw_plan_iso.py or adw_patch_iso.py first to create the worktree and state")
        sys.exit(1)
    
    # Track that this ADW workflow has run
    state.append_adw_id("adw_review_iso")
    
    # Set up logger with ADW ID from command line
    logger = setup_logger(adw_id, "adw_review_iso")
    logger.info(f"ADW Review Iso starting - ID: {adw_id}, Issue: {issue_number}, Skip Resolution: {skip_resolution}")
    
    # Validate environment
    check_env_vars(logger)
    
    # Validate worktree exists
    valid, error = validate_worktree(adw_id, state)
    if not valid:
        logger.error(f"Worktree validation failed: {error}")
        logger.error("Run adw_plan_iso.py or adw_patch_iso.py first")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", f"❌ Worktree validation failed: {error}\n"
                               "Run adw_plan_iso.py or adw_patch_iso.py first")
        )
        sys.exit(1)
    
    # Get worktree path for explicit context
    worktree_path = state.get("worktree_path")
    logger.info(f"Using worktree at: {worktree_path}")
    
    # Get port information for display
    backend_port = state.get("backend_port", "9100")
    frontend_port = state.get("frontend_port", "9200")
    
    make_issue_comment(
        issue_number, 
        format_issue_message(adw_id, "ops", f"✅ Starting isolated review phase\n"
                           f"🏠 Worktree: {worktree_path}\n"
                           f"🔌 Ports - Backend: {backend_port}, Frontend: {frontend_port}\n"
                           f"🔧 Issue Resolution: {'Disabled' if skip_resolution else 'Enabled'}")
    )
    
    # Find spec file from current branch (in worktree)
    logger.info("Looking for spec file in worktree")
    spec_file = find_spec_file(state, logger)
    
    if not spec_file:
        error_msg = "Could not find spec file for review"
        logger.error(error_msg)
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", f"❌ {error_msg}")
        )
        sys.exit(1)
    
    logger.info(f"Found spec file: {spec_file}")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "ops", f"📋 Found spec file: {spec_file}")
    )
    
    # Run review with retry logic
    review_attempt = 0
    review_result = None
    
    while review_attempt < MAX_REVIEW_RETRY_ATTEMPTS:
        review_attempt += 1
        
        # Run the review (executing in worktree)
        logger.info(f"Running review (attempt {review_attempt}/{MAX_REVIEW_RETRY_ATTEMPTS})")
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                AGENT_REVIEWER,
                f"🔍 Reviewing implementation against spec (attempt {review_attempt}/{MAX_REVIEW_RETRY_ATTEMPTS})..."
            )
        )
        
        review_result = run_review(spec_file, adw_id, logger, working_dir=worktree_path)
        
        # Check for fixable issues (blocker + tech_debt)
        fixable_issues = [
            issue for issue in review_result.review_issues
            if issue.issue_severity in ("blocker", "tech_debt")
        ]

        # If no fixable issues or skip resolution, we're done
        if not fixable_issues or skip_resolution:
            break

        # Resolve fixable issues
        resolve_blocker_issues(fixable_issues, issue_number, adw_id, worktree_path, logger)
        
        # If this was the last attempt, break regardless
        if review_attempt >= MAX_REVIEW_RETRY_ATTEMPTS - 1:
            break
        
        # Otherwise, we'll retry the review
        logger.info("Retrying review after resolving blockers")
        make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                AGENT_REVIEWER,
                "🔄 Retrying review after resolving blockers..."
            )
        )
    
    # Post review results
    if review_result:
        # Upload screenshots (R2 with GitHub Raw fallback) and update URLs
        branch_name = state.get("branch_name")
        upload_review_screenshots(review_result, adw_id, worktree_path, logger, branch_name=branch_name)
        
        # Build and post the summary comment
        summary = build_review_summary(review_result)
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_REVIEWER, summary)
        )
    
    # Get repo information
    try:
        github_repo_url = get_repo_url()
        repo_path = extract_repo_path(github_repo_url)
    except ValueError as e:
        logger.error(f"Error getting repository URL: {e}")
        sys.exit(1)
    
    # Fetch issue data for commit message generation
    logger.info("Fetching issue data for commit message")
    issue = fetch_issue(issue_number, repo_path)
    
    # Get issue classification from state
    issue_command = state.get("issue_class", "/feature")
    
    # Create commit message
    logger.info("Creating review commit")
    commit_msg, error = create_commit(AGENT_REVIEWER, issue, issue_command, adw_id, logger, worktree_path)
    
    if error:
        logger.error(f"Error creating commit message: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_REVIEWER, f"❌ Error creating commit message: {error}")
        )
        sys.exit(1)
    
    # Commit the review results (in worktree)
    success, error = commit_changes(commit_msg, cwd=worktree_path)
    
    if not success:
        logger.error(f"Error committing review: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_REVIEWER, f"❌ Error committing review: {error}")
        )
        sys.exit(1)
    
    logger.info(f"Committed review: {commit_msg}")
    make_issue_comment(
        issue_number, format_issue_message(adw_id, AGENT_REVIEWER, "✅ Review committed")
    )
    
    # Finalize git operations (push and PR)
    # Note: This will work from the worktree context
    finalize_git_operations(state, logger, cwd=worktree_path)
    
    logger.info("Isolated review phase completed successfully")
    make_issue_comment(
        issue_number, format_issue_message(adw_id, "ops", "✅ Isolated review phase completed")
    )
    
    # Save final state
    state.save("adw_review_iso")
    
    # Post final state summary to issue
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "ops", f"Review complete ✓\n\n{state.format_for_github()}")
    )


if __name__ == "__main__":
    main()