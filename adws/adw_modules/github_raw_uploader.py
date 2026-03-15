"""GitHub Raw URL uploader for ADW screenshots.

Commits screenshots to the worktree branch and returns public
raw.githubusercontent.com URLs — no external infrastructure required.
"""

import logging
import os
import subprocess
from typing import List, Optional


def _run(cmd: List[str], cwd: str, logger: logging.Logger) -> subprocess.CompletedProcess:
    """Run a subprocess command and log output."""
    logger.debug(f"Running: {' '.join(cmd)} (cwd={cwd})")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        logger.debug(f"stdout: {result.stdout}")
        logger.debug(f"stderr: {result.stderr}")
    return result


def _get_owner_repo(worktree_path: str, logger: logging.Logger) -> Optional[str]:
    """Return 'owner/repo' by parsing the git remote origin URL."""
    result = _run(["git", "remote", "get-url", "origin"], worktree_path, logger)
    if result.returncode != 0:
        logger.error(f"Could not get remote origin URL: {result.stderr}")
        return None

    url = result.stdout.strip()
    # Handle https://github.com/owner/repo[.git] and git@github.com:owner/repo[.git]
    if url.startswith("https://github.com/"):
        owner_repo = url.replace("https://github.com/", "").removesuffix(".git")
    elif url.startswith("git@github.com:"):
        owner_repo = url.replace("git@github.com:", "").removesuffix(".git")
    else:
        logger.error(f"Unrecognised remote URL format: {url}")
        return None

    return owner_repo


def upload_screenshots_as_raw_urls(
    screenshot_paths: List[str],
    worktree_path: str,
    branch_name: str,
    adw_id: str,
    logger: logging.Logger,
) -> List[str]:
    """Commit screenshots to the worktree branch and return raw.githubusercontent.com URLs.

    Args:
        screenshot_paths: Local paths to screenshots (absolute or relative to worktree_path).
        worktree_path: Absolute path to the git worktree.
        branch_name: Branch name the worktree tracks.
        adw_id: ADW workflow ID (used only for log context).
        logger: Logger instance.

    Returns:
        List of public raw.githubusercontent.com URLs, one per successfully processed
        screenshot.  Falls back to the original local path for any screenshot that
        cannot be committed/pushed.
    """
    if not screenshot_paths:
        return []

    owner_repo = _get_owner_repo(worktree_path, logger)
    if not owner_repo:
        logger.warning("Could not determine owner/repo — returning local paths as fallback")
        return list(screenshot_paths)

    # Resolve all paths to absolute and verify they exist
    resolved: List[str] = []
    for p in screenshot_paths:
        abs_p = p if os.path.isabs(p) else os.path.join(worktree_path, p)
        if not os.path.exists(abs_p):
            logger.warning(f"Screenshot not found, skipping: {abs_p}")
            continue
        resolved.append(abs_p)

    if not resolved:
        logger.warning("No valid screenshot files found to commit")
        return []

    # Stage screenshots
    stage_result = _run(["git", "add"] + resolved, worktree_path, logger)
    if stage_result.returncode != 0:
        logger.error(f"git add failed: {stage_result.stderr}")
        return list(screenshot_paths)

    # Check if there is anything new to commit
    status_result = _run(["git", "status", "--porcelain"], worktree_path, logger)
    has_staged = any(
        line.startswith(("A ", "M ", "AM", "MM"))
        for line in status_result.stdout.splitlines()
    )

    if has_staged:
        commit_result = _run(
            ["git", "commit", "-m", "chore(adw): add review screenshots"],
            worktree_path,
            logger,
        )
        if commit_result.returncode != 0:
            logger.error(f"git commit failed: {commit_result.stderr}")
            return list(screenshot_paths)
        logger.info("Committed review screenshots to branch")
    else:
        logger.info("Screenshots already committed — skipping commit step")

    # Push the branch
    push_result = _run(
        ["git", "push", "origin", branch_name],
        worktree_path,
        logger,
    )
    if push_result.returncode != 0:
        logger.error(f"git push failed: {push_result.stderr}")
        return list(screenshot_paths)

    logger.info(f"Pushed screenshots to branch '{branch_name}'")

    # Build raw URLs
    urls: List[str] = []
    for abs_p in resolved:
        # Make the path relative to the worktree root
        try:
            rel_path = os.path.relpath(abs_p, worktree_path)
        except ValueError:
            # On Windows, relpath can fail across drives — fall back to basename
            rel_path = os.path.basename(abs_p)

        # raw.githubusercontent.com uses forward slashes
        rel_path_fwd = rel_path.replace(os.sep, "/")
        raw_url = f"https://raw.githubusercontent.com/{owner_repo}/{branch_name}/{rel_path_fwd}"
        urls.append(raw_url)
        logger.info(f"Screenshot URL: {raw_url}")

    return urls
