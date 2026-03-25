#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "slack-sdk", "PyJWT", "cryptography"]
# ///

"""
ADW Plan Build Review Iso - Backward-compatible wrapper for unified orchestrator

Usage: uv run adw_plan_build_review_iso.py <issue-number> [adw-id] [--skip-resolution]

This script is a thin wrapper around adw_workflow_iso.py for backward compatibility.
For new usage, prefer: uv run adw_workflow_iso.py plan_build_review <issue-number> [adw-id] [flags]
"""

import sys
import os

# Add the parent directory to Python path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adw_modules.workflow_ops import run_workflow_phases, parse_workflow_flags


def main():
    """Main entry point - delegates to unified orchestrator."""
    # Parse flags first
    flags = parse_workflow_flags(["--skip-resolution"])

    if len(sys.argv) < 2:
        print("Usage: uv run adw_plan_build_review_iso.py <issue-number> [adw-id] [--skip-resolution]")
        print("\nThis runs the isolated plan, build, and review workflow:")
        print("  1. Plan (isolated)")
        print("  2. Build (isolated)")
        print("  3. Review (isolated)")
        print("\nPrefer: uv run adw_workflow_iso.py plan_build_review <issue-number> [adw-id] [flags]")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else None

    run_workflow_phases(
        workflow_name="plan_build_review",
        issue_number=issue_number,
        adw_id=adw_id,
        flags=flags,
    )


if __name__ == "__main__":
    main()
