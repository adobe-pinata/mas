#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

"""
Universal event logger for the agentic layer.

Writes structured JSON to a per-session log directory as JSONL (one JSON
object per line, append mode).  Handles all 12 Claude Code hook event types.

Log path: $CLAUDE_PROJECT_DIR/.logs/{session_id}/{hook_event_type}.jsonl

Modeled after apps/agent-observability/.claude/hooks/send_event.py but
writes to disk instead of HTTP POST.  Always exits 0 — never blocks Claude.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path


# ── Event-specific top-level fields ──────────────────────────────────────
# These fields are promoted from the payload to the top level of the log
# record for easier querying / grepping.
PROMOTED_FIELDS = [
    "tool_name",             # PreToolUse, PostToolUse, PostToolUseFailure, PermissionRequest
    "tool_use_id",           # PreToolUse, PostToolUse, PostToolUseFailure
    "error",                 # PostToolUseFailure
    "is_interrupt",          # PostToolUseFailure
    "permission_suggestions",# PermissionRequest
    "agent_id",              # SubagentStart, SubagentStop
    "agent_type",            # SessionStart, SubagentStart, SubagentStop
    "agent_transcript_path", # SubagentStop
    "stop_hook_active",      # Stop, SubagentStop
    "notification_type",     # Notification
    "custom_instructions",   # PreCompact
    "source",                # SessionStart
    "reason",                # SessionEnd
]


def build_log_record(event_type, input_data, session_id):
    """Build a structured log record from hook input data."""
    record = {
        "timestamp": int(time.time() * 1000),
        "source_app": "agentic-harness",
        "session_id": session_id,
        "hook_event_type": event_type,
    }

    # Promote event-specific fields to the top level
    for field in PROMOTED_FIELDS:
        if field in input_data:
            record[field] = input_data[field]

    # Include the full payload for completeness
    record["payload"] = input_data

    return record


def ensure_log_dir(session_id):
    """Create and return the per-session log directory."""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    log_dir = Path(project_dir) / ".logs" / session_id
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def write_record(log_dir, event_type, record):
    """Append a single JSON line to the event-type JSONL file."""
    log_file = log_dir / f"{event_type}.jsonl"
    line = json.dumps(record, separators=(",", ":")) + "\n"
    with open(log_file, "a") as f:
        f.write(line)


def main():
    parser = argparse.ArgumentParser(
        description="Log Claude Code hook events to disk as structured JSONL"
    )
    parser.add_argument(
        "--event-type",
        required=True,
        help="Hook event type (SessionStart, Stop, PreToolUse, etc.)",
    )
    args = parser.parse_args()

    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # Bad input — nothing to log, exit cleanly
        sys.exit(0)

    session_id = input_data.get("session_id", "unknown")
    record = build_log_record(args.event_type, input_data, session_id)

    try:
        log_dir = ensure_log_dir(session_id)
        write_record(log_dir, args.event_type, record)
    except Exception:
        # Disk errors must never block Claude
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
