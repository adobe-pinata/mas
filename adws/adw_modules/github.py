#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "PyJWT", "cryptography"]
# ///

"""
GitHub Operations Module - Developer Workflow (ADW)

This module contains all GitHub-related operations including:
- Issue fetching and manipulation
- Comment posting
- Repository path extraction
- Issue status management
"""

import subprocess
import sys
import os
import json
import re
import logging
from typing import Dict, List, Optional
from .data_types import GitHubIssue, GitHubIssueListItem, GitHubComment

logger = logging.getLogger(__name__)

# Bot identifier to prevent webhook loops and filter bot comments
ADW_BOT_IDENTIFIER = "[ADW-AGENTS]"


def get_github_env() -> Optional[dict]:
    """Get environment with GitHub token set up.

    Priority: GitHub App token > GITHUB_PAT > None (inherit parent env).

    Subprocess env behavior:
    - env=None → Inherits parent's environment (default)
    - env={} → Empty environment (no variables)
    - env=custom_dict → Only uses specified variables
    """
    # 1. Try GitHub App token (posts as bot identity)
    from .github_app_auth import get_app_token
    app_token = get_app_token()
    if app_token:
        return {
            "GH_TOKEN": app_token,
            "PATH": os.environ.get("PATH", ""),
        }

    # 2. Fall back to personal access token
    github_pat = os.getenv("GITHUB_PAT")
    if github_pat:
        return {
            "GH_TOKEN": github_pat,
            "PATH": os.environ.get("PATH", ""),
        }

    # 3. No token — inherit parent env (relies on gh auth login)
    return None


def get_repo_url() -> str:
    """Get GitHub repository URL from git remote."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        raise ValueError(
            "No git remote 'origin' found. Please ensure you're in a git repository with a remote."
        )
    except FileNotFoundError:
        raise ValueError("git command not found. Please ensure git is installed.")


def extract_repo_path(github_url: str) -> str:
    """Extract owner/repo from GitHub URL."""
    # Handle both https://github.com/owner/repo and https://github.com/owner/repo.git
    return github_url.replace("https://github.com/", "").replace(".git", "")


def get_effective_repo_path() -> str:
    """APP env var + app config takes precedence over git remote origin."""
    from adw_modules.app_config import get_app_repo
    app_repo = get_app_repo()
    if app_repo:
        return app_repo
    return extract_repo_path(get_repo_url())


def autolink_issue_references(text: str, repo_path: str) -> str:
    """Convert issue references to markdown links.

    Detects patterns like:
    - #39
    - issue #39
    - Issue #39
    - GH-39

    And converts them to:
    - [#39](https://github.com/owner/repo/issues/39)

    Args:
        text: The text containing issue references
        repo_path: The repository path (e.g., "owner/repo")

    Returns:
        Text with issue references converted to markdown links
    """
    # Don't process if already contains markdown links to avoid double-linking
    # This regex matches existing markdown links: [text](url)
    markdown_link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'

    # Find all existing markdown links and temporarily replace them with placeholders
    placeholders = {}
    placeholder_count = 0

    def save_link(match):
        nonlocal placeholder_count
        placeholder = f"__LINK_PLACEHOLDER_{placeholder_count}__"
        placeholders[placeholder] = match.group(0)
        placeholder_count += 1
        return placeholder

    # Temporarily replace existing markdown links
    text = re.sub(markdown_link_pattern, save_link, text)

    # Pattern to match issue references:
    # - Standalone #N (with word boundary)
    # - "issue #N" or "Issue #N" or "ISSUE #N"
    # - "GH-N"
    # The pattern uses negative lookbehind to avoid matching inside words
    issue_pattern = r'(?<![a-zA-Z0-9])(?:(?:[Ii]ssue\s+)?#(\d+)|GH-(\d+))(?![a-zA-Z0-9])'

    def replace_with_link(match):
        # Get the issue number from whichever group matched
        issue_num = match.group(1) or match.group(2)
        # Preserve the original format for the link text
        original_text = match.group(0)
        # Create the markdown link
        url = f"https://github.com/{repo_path}/issues/{issue_num}"
        return f"[{original_text}]({url})"

    # Replace issue references with markdown links
    text = re.sub(issue_pattern, replace_with_link, text)

    # Restore the original markdown links
    for placeholder, original_link in placeholders.items():
        text = text.replace(placeholder, original_link)

    return text


def fetch_issue(issue_number: str, repo_path: str) -> GitHubIssue:
    """Fetch GitHub issue using gh CLI and return typed model."""
    # Use JSON output for structured data
    cmd = [
        "gh",
        "issue",
        "view",
        issue_number,
        "-R",
        repo_path,
        "--json",
        "number,title,body,state,author,assignees,labels,milestone,comments,createdAt,updatedAt,closedAt,url",
    ]

    # Set up environment with GitHub token if available
    env = get_github_env()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)

        if result.returncode == 0:
            # Parse JSON response into Pydantic model
            issue_data = json.loads(result.stdout)
            logger.debug(f"GitHub CLI returned issue data with URL: {issue_data.get('url', 'NO URL FOUND')}")
            issue = GitHubIssue(**issue_data)
            logger.debug(f"Parsed GitHubIssue with URL: {issue.url}")

            return issue
        else:
            print(result.stderr, file=sys.stderr)
            sys.exit(result.returncode)
    except FileNotFoundError:
        print("Error: GitHub CLI (gh) is not installed.", file=sys.stderr)
        print("\nTo install gh:", file=sys.stderr)
        print("  - macOS: brew install gh", file=sys.stderr)
        print(
            "  - Linux: See https://github.com/cli/cli#installation",
            file=sys.stderr,
        )
        print(
            "  - Windows: See https://github.com/cli/cli#installation", file=sys.stderr
        )
        print("\nAfter installation, authenticate with: gh auth login", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing issue data: {e}", file=sys.stderr)
        sys.exit(1)


def make_issue_comment(issue_id: str, comment: str) -> None:
    """Post a comment to a GitHub issue using gh CLI."""
    repo_path = get_effective_repo_path()

    # Auto-link issue references in the comment
    comment = autolink_issue_references(comment, repo_path)

    # Ensure comment has ADW_BOT_IDENTIFIER to prevent webhook loops
    if not comment.startswith(ADW_BOT_IDENTIFIER):
        comment = f"{ADW_BOT_IDENTIFIER} {comment}"

    # Build command
    cmd = [
        "gh",
        "issue",
        "comment",
        issue_id,
        "-R",
        repo_path,
        "--body",
        comment,
    ]

    # Set up environment with GitHub token if available
    env = get_github_env()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)

        if result.returncode == 0:
            print(f"Successfully posted comment to issue #{issue_id}")
        else:
            print(f"Error posting comment: {result.stderr}", file=sys.stderr)
            raise RuntimeError(f"Failed to post comment: {result.stderr}")
    except Exception as e:
        print(f"Error posting comment: {e}", file=sys.stderr)
        raise


def mark_issue_in_progress(issue_id: str) -> None:
    """Mark issue as in progress by adding label and comment."""
    repo_path = get_effective_repo_path()

    # Add "in_progress" label
    cmd = [
        "gh",
        "issue",
        "edit",
        issue_id,
        "-R",
        repo_path,
        "--add-label",
        "in_progress",
    ]

    # Set up environment with GitHub token if available
    env = get_github_env()

    # Try to add label (may fail if label doesn't exist)
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        print(f"Note: Could not add 'in_progress' label: {result.stderr}")

    # Post comment indicating work has started
    # make_issue_comment(issue_id, "🚧 ADW is working on this issue...")

    # Assign to self (optional)
    cmd = [
        "gh",
        "issue",
        "edit",
        issue_id,
        "-R",
        repo_path,
        "--add-assignee",
        "@me",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode == 0:
        print(f"Assigned issue #{issue_id} to self")


def fetch_open_issues(repo_path: str) -> List[GitHubIssueListItem]:
    """Fetch all open issues from the GitHub repository."""
    try:
        cmd = [
            "gh",
            "issue",
            "list",
            "--repo",
            repo_path,
            "--state",
            "open",
            "--json",
            "number,title,body,labels,createdAt,updatedAt",
            "--limit",
            "1000",
        ]

        # Set up environment with GitHub token if available
        env = get_github_env()

        # DEBUG level - not printing command
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, env=env
        )

        issues_data = json.loads(result.stdout)
        issues = [GitHubIssueListItem(**issue_data) for issue_data in issues_data]
        # Suppress print to avoid duplicate output in trigger_cron.py Rich UI
        # print(f"Fetched {len(issues)} open issues")
        return issues

    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to fetch issues: {e.stderr}", file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse issues JSON: {e}", file=sys.stderr)
        return []


def fetch_issue_comments(repo_path: str, issue_number: int) -> List[Dict]:
    """Fetch all comments for a specific issue."""
    try:
        cmd = [
            "gh",
            "issue",
            "view",
            str(issue_number),
            "--repo",
            repo_path,
            "--json",
            "comments",
        ]

        # Set up environment with GitHub token if available
        env = get_github_env()

        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, env=env
        )
        data = json.loads(result.stdout)
        comments = data.get("comments", [])

        # Sort comments by creation time
        comments.sort(key=lambda c: c.get("createdAt", ""))

        # DEBUG level - not printing
        return comments

    except subprocess.CalledProcessError as e:
        print(
            f"ERROR: Failed to fetch comments for issue #{issue_number}: {e.stderr}",
            file=sys.stderr,
        )
        return []
    except json.JSONDecodeError as e:
        print(
            f"ERROR: Failed to parse comments JSON for issue #{issue_number}: {e}",
            file=sys.stderr,
        )
        return []


def find_keyword_from_comment(keyword: str, issue: GitHubIssue) -> Optional[GitHubComment]:
    """Find the latest comment containing a specific keyword.
    
    Args:
        keyword: The keyword to search for in comments
        issue: The GitHub issue containing comments
        
    Returns:
        The latest GitHubComment containing the keyword, or None if not found
    """
    # Sort comments by created_at date (newest first)
    sorted_comments = sorted(issue.comments, key=lambda c: c.created_at, reverse=True)
    
    # Search through sorted comments (newest first)
    for comment in sorted_comments:
        # Skip ADW bot comments to prevent loops
        if ADW_BOT_IDENTIFIER in comment.body:
            continue
            
        if keyword in comment.body:
            return comment
    
    return None
