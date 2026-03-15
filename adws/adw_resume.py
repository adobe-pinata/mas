#!/usr/bin/env python3
"""Resume an existing ADW workflow from its last completed phase.

Usage:
    uv run adw_resume.py <issue-number> [adw-id]

Examples:
    # Auto-discover ADW ID and resume
    uv run adw_resume.py 424

    # Resume specific ADW ID
    uv run adw_resume.py 424 09ab6c8a
"""

import sys
import os
import logging
import subprocess
from adw_modules.phase_detection import PhaseDetector, detect_phase_and_resume

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for resume utility."""
    if len(sys.argv) < 2:
        logger.error("❌ Usage: uv run adw_resume.py <issue-number> [adw-id]")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else None

    logger.info("=" * 70)
    logger.info("🔄 ADW Workflow Resume Utility")
    logger.info("=" * 70)
    logger.info("")

    # Detect phase and get resume command
    script, discovered_adw_id, description = detect_phase_and_resume(
        issue_number, adw_id, logger
    )

    if not script:
        logger.error(f"❌ Cannot resume: {description}")
        sys.exit(1)

    adw_id = discovered_adw_id or adw_id

    # Show phase status
    detector = PhaseDetector(adw_id, issue_number, logger)
    logger.info(detector.format_resume_info())
    logger.info("")
    logger.info("=" * 70)
    logger.info("")

    # Build and execute command
    last_phase = detector.detect_last_completed_phase()

    # Entry point workflows (PLAN phase) only need issue number
    if last_phase.value == 0:  # NOT_STARTED
        cmd = ["uv", "run", script, issue_number]
    else:
        # Dependent workflows need both issue number and ADW ID
        cmd = ["uv", "run", script, issue_number, adw_id]

    logger.info(f"▶️  Executing: {' '.join(cmd)}")
    logger.info("")

    # Execute the next phase
    try:
        result = subprocess.run(cmd, check=True)
        sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Phase execution failed: {e}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Interrupted by user")
        sys.exit(130)


if __name__ == "__main__":
    main()
