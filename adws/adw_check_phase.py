#!/usr/bin/env python3
"""Check the current phase status of an ADW workflow without executing.

Usage:
    uv run adw_check_phase.py <issue-number> [adw-id]

Examples:
    # Auto-discover ADW ID and check status
    uv run adw_check_phase.py 424

    # Check specific ADW ID
    uv run adw_check_phase.py 424 09ab6c8a
"""

import sys
import logging
from adw_modules.phase_detection import PhaseDetector, detect_phase_and_resume

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for phase check utility."""
    if len(sys.argv) < 2:
        logger.error("❌ Usage: uv run adw_check_phase.py <issue-number> [adw-id]")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else None

    logger.info("=" * 70)
    logger.info("📊 ADW Phase Status Check")
    logger.info("=" * 70)
    logger.info("")

    # Detect phase and get resume command
    script, discovered_adw_id, description = detect_phase_and_resume(
        issue_number, adw_id, logger
    )

    if not script:
        logger.info(f"Status: {description}")
        sys.exit(0)

    adw_id = discovered_adw_id or adw_id

    # Show phase status
    detector = PhaseDetector(adw_id, issue_number, logger)
    logger.info(detector.format_resume_info())
    logger.info("")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
