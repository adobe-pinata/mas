#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "slack-sdk"]
# ///

"""
ADW Workflow Iso - Unified workflow orchestrator for all ADW workflows

Usage: uv run adw_workflow_iso.py <workflow> <issue-number> [adw-id] [flags]

Available workflows:
  plan_build           - Plan and Build
  plan_build_test      - Plan, Build, and Test
  plan_build_review    - Plan, Build, and Review
  plan_build_test_review - Plan, Build, Test, and Review
  plan_build_document  - Plan, Build, and Document
  sdlc                 - Complete SDLC (Plan, Build, Test, Review, Document)
  sdlc_zte             - Complete SDLC with Zero Touch Execution (auto-ship)

Available flags:
  --skip-e2e              - Skip E2E tests in test phase
  --skip-resolution       - Skip conflict resolution in review phase
  --skip-frontend-typecheck - Skip frontend type checking in test phase

Examples:
  uv run adw_workflow_iso.py plan_build 123
  uv run adw_workflow_iso.py sdlc 456 --skip-e2e
  uv run adw_workflow_iso.py sdlc_zte 789 adw-abc123 --skip-resolution

This unified orchestrator replaces:
  - adw_plan_build_iso.py
  - adw_plan_build_test_iso.py
  - adw_plan_build_review_iso.py
  - adw_plan_build_test_review_iso.py
  - adw_plan_build_document_iso.py
  - adw_sdlc_iso.py
  - adw_sdlc_zte_iso.py
"""

import sys
import os

# Add the parent directory to Python path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adw_modules.workflow_ops import (
    run_workflow_phases,
    parse_workflow_flags,
    get_workflow_names,
    get_workflow_help,
    WORKFLOW_CONFIGS,
)
from adw_modules.github import make_issue_comment


def print_usage():
    """Print usage information."""
    workflows = get_workflow_names()
    print("Usage: uv run adw_workflow_iso.py <workflow> <issue-number> [adw-id] [flags]")
    print("\nAvailable workflows:")
    for name in workflows:
        config = WORKFLOW_CONFIGS[name]
        zte_marker = " [ZTE]" if config.is_zte else ""
        print(f"  {name:24} - {config.description}{zte_marker}")
    print("\nAvailable flags:")
    print("  --skip-e2e              - Skip E2E tests in test phase")
    print("  --skip-resolution       - Skip conflict resolution in review phase")
    print("  --skip-frontend-typecheck - Skip frontend type checking in test phase")
    print("\nExamples:")
    print("  uv run adw_workflow_iso.py plan_build 123")
    print("  uv run adw_workflow_iso.py sdlc 456 --skip-e2e")
    print("  uv run adw_workflow_iso.py sdlc_zte 789 adw-abc123 --skip-resolution")
    print("\nFor detailed help on a specific workflow:")
    print("  uv run adw_workflow_iso.py help <workflow>")


def on_zte_start(issue_number: str):
    """Post ZTE start notification to GitHub."""
    try:
        make_issue_comment(
            issue_number,
            "adw_ops: **Starting Zero Touch Execution (ZTE)**\n\n"
            "This workflow will automatically:\n"
            "1. Plan the implementation\n"
            "2. Build the solution\n"
            "3. Test the code\n"
            "4. Review the implementation\n"
            "5. Generate documentation\n"
            "6. **Ship to production** (approve & merge PR)\n\n"
            "Code will be automatically merged if all phases pass!",
        )
    except Exception as e:
        print(f"Warning: Failed to post ZTE start comment: {e}")


def on_zte_failure(phase_name: str, issue_number: str):
    """Post ZTE failure notification to GitHub."""
    try:
        make_issue_comment(
            issue_number,
            f"adw_ops: **ZTE Aborted** - {phase_name.capitalize()} phase failed\n\n"
            "Automatic shipping cancelled due to phase failure.\n"
            "Please fix the issues and run the workflow again.",
        )
    except Exception:
        pass


def on_zte_success(issue_number: str):
    """Post ZTE success notification to GitHub."""
    try:
        make_issue_comment(
            issue_number,
            "adw_ops: **Zero Touch Execution Complete!**\n\n"
            "All phases completed:\n"
            "- Plan phase completed\n"
            "- Build phase completed\n"
            "- Test phase completed\n"
            "- Review phase completed\n"
            "- Documentation phase completed\n"
            "- Ship phase completed\n\n"
            "**Code has been automatically shipped to production!**",
        )
    except Exception:
        pass


def main():
    """Main entry point."""
    # Parse all known flags first
    all_flags = ["--skip-e2e", "--skip-resolution", "--skip-frontend-typecheck"]
    flags = parse_workflow_flags(all_flags)

    # Check for help command
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help", "help"]:
        if len(sys.argv) == 3 and sys.argv[1] == "help":
            # Show help for specific workflow
            workflow_name = sys.argv[2]
            print(get_workflow_help(workflow_name))
        else:
            print_usage()
        sys.exit(0)

    # Get workflow name
    workflow_name = sys.argv[1]

    # Validate workflow name
    if workflow_name not in WORKFLOW_CONFIGS:
        print(f"Error: Unknown workflow '{workflow_name}'")
        print(f"Available workflows: {', '.join(get_workflow_names())}")
        sys.exit(1)

    # Get issue number
    if len(sys.argv) < 3:
        print(f"Error: Missing issue number")
        print(f"Usage: uv run adw_workflow_iso.py {workflow_name} <issue-number> [adw-id]")
        sys.exit(1)

    issue_number = sys.argv[2]

    # Get optional ADW ID
    adw_id = sys.argv[3] if len(sys.argv) > 3 else None

    # Get workflow config for ZTE check
    config = WORKFLOW_CONFIGS[workflow_name]

    # Print ZTE warning if applicable
    if config.is_zte:
        print("\n" + "=" * 60)
        print("  ZERO TOUCH EXECUTION - AUTO-SHIP ENABLED")
        print("  Code will be automatically merged if all phases pass!")
        print("=" * 60 + "\n")

    # Run the workflow
    success = run_workflow_phases(
        workflow_name=workflow_name,
        issue_number=issue_number,
        adw_id=adw_id,
        flags=flags,
        on_zte_start=on_zte_start if config.is_zte else None,
        on_zte_failure=on_zte_failure if config.is_zte else None,
        on_zte_success=on_zte_success if config.is_zte else None,
    )

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
