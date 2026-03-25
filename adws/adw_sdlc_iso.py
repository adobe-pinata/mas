#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "slack-sdk", "PyJWT", "cryptography"]
# ///

"""
ADW SDLC Iso - Backward-compatible wrapper for unified orchestrator

Usage: uv run adw_sdlc_iso.py <issue-number> [adw-id] [--skip-e2e] [--skip-resolution] [--skip-frontend-typecheck]

This script is a thin wrapper around adw_workflow_iso.py for backward compatibility.
For new usage, prefer: uv run adw_workflow_iso.py sdlc <issue-number> [adw-id] [flags]
"""

import sys
import os

# Add the parent directory to Python path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adw_modules.workflow_ops import run_workflow_phases, parse_workflow_flags


def main():
    """Main entry point - delegates to unified orchestrator."""
    # Parse flags first
    flags = parse_workflow_flags(["--skip-e2e", "--skip-resolution", "--skip-frontend-typecheck"])

    if len(sys.argv) < 2:
        print("Usage: uv run adw_sdlc_iso.py <issue-number> [adw-id] [--skip-e2e] [--skip-resolution] [--skip-frontend-typecheck]")
        print("\nThis runs the complete isolated Software Development Life Cycle:")
        print("  1. Plan (isolated)")
        print("  2. Build (isolated)")
        print("  3. Test (isolated)")
        print("  4. Review (isolated)")
        print("  5. Document (isolated)")
        print("\nPrefer: uv run adw_workflow_iso.py sdlc <issue-number> [adw-id] [flags]")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else None

    run_workflow_phases(
        workflow_name="sdlc",
        issue_number=issue_number,
        adw_id=adw_id,
        flags=flags,
    )


if __name__ == "__main__":
    main()
