#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "slack-sdk", "PyJWT", "cryptography"]
# ///

"""
ADW Plan Build Iso - Backward-compatible wrapper for unified orchestrator

Usage: uv run adw_plan_build_iso.py <issue-number> [adw-id]

This script is a thin wrapper around adw_workflow_iso.py for backward compatibility.
For new usage, prefer: uv run adw_workflow_iso.py plan_build <issue-number> [adw-id]
"""

import sys
import os

# Add the parent directory to Python path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adw_modules.workflow_ops import run_workflow_phases, parse_workflow_flags


def main():
    """Main entry point - delegates to unified orchestrator."""
    if len(sys.argv) < 2:
        print("Usage: uv run adw_plan_build_iso.py <issue-number> [adw-id]")
        print("\nThis runs the isolated plan and build workflow:")
        print("  1. Plan (isolated)")
        print("  2. Build (isolated)")
        print("\nPrefer: uv run adw_workflow_iso.py plan_build <issue-number> [adw-id]")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else None

    run_workflow_phases(
        workflow_name="plan_build",
        issue_number=issue_number,
        adw_id=adw_id,
    )


if __name__ == "__main__":
    main()
