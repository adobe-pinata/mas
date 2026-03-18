#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "schedule",
#     "python-dotenv",
#     "pydantic",
#     "rich",
# ]
# ///

"""
Cron-based ADW trigger system that monitors GitHub issues and automatically processes them.

This script polls GitHub every 20 seconds to detect:
1. Issues with labels that map to workflows (see LABEL_WORKFLOW_MAP)
2. Issues where the latest comment contains 'adw'
3. New issues without comments

Label-to-workflow mapping (checked in order, first match wins):
- 'ZTE'  label → adw_sdlc_zte_iso (Zero Touch Execution)
- 'SDLC' label → adw_sdlc_iso (full SDLC workflow)
- 'adw' comment → adw_plan_build_iso (standard plan & build)
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Set, Optional

import schedule
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.table import Table

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from adw_modules.utils import get_safe_subprocess_env, make_adw_id

from adw_modules.github import fetch_open_issues, fetch_issue_comments, get_repo_url, extract_repo_path, fetch_issue, ADW_BOT_IDENTIFIER
from adw_modules.workflow_ops import extract_adw_info
from adw_modules.state import ADWState

# Load environment variables from current or parent directories
load_dotenv()

# Optional environment variables
GITHUB_PAT = os.getenv("GITHUB_PAT")

# Get repository path — APP env var + app config takes precedence over git remote
from adw_modules.github import get_effective_repo_path
from adw_modules.app_config import get_app_name
try:
    REPO_PATH = get_effective_repo_path()
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

_APP_OVERRIDE_ACTIVE = get_app_name() is not None

# =============================================================================
# Label-to-Workflow Mapping
# =============================================================================
# Map GitHub labels to ADW workflow scripts (case-insensitive matching).
# Labels are checked in order; the first match wins.
LABEL_WORKFLOW_MAP: Dict[str, str] = {
    "ZTE": "adw_sdlc_zte_iso",
    "SDLC": "adw_sdlc_iso",
}

# Track processed issues
processed_issues: Set[int] = set()
# Track issues with their last processed comment ID
issue_last_comment: Dict[int, Optional[int]] = {}
# Track issues processed via label-based workflows
label_processed_issues: Set[int] = set()

# Graceful shutdown flag
shutdown_requested = False

# Rich console instance
console = Console()

# Track cycles for condensed output
cycle_count = 0
is_first_cycle = True


# ============================================================================
# Terminal UI Functions
# ============================================================================

def check_github_auth() -> bool:
    """Check if GitHub CLI is authenticated."""
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=2
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_claude_cli() -> bool:
    """Check if Claude CLI is available."""
    try:
        claude_path = os.getenv("CLAUDE_CODE_PATH", "claude")
        result = subprocess.run(
            [claude_path, "--version"],
            capture_output=True,
            text=True,
            timeout=2
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_repository() -> bool:
    """Check if git repository is properly configured."""
    try:
        return bool(REPO_PATH)
    except:
        return False


def get_system_status_detailed() -> tuple[str, list[str]]:
    """Get system status with warnings for failures.

    Returns:
        (status_icons, warnings) where warnings is list of error messages
    """
    warnings = []

    github_ok = check_github_auth()
    if not github_ok:
        warnings.append("⚠ GitHub CLI not authenticated (run 'gh auth login')")

    claude_ok = check_claude_cli()
    if not claude_ok:
        warnings.append("⚠ Claude CLI not available")

    repo_ok = check_repository()
    if not repo_ok:
        warnings.append("⚠ Git repository not configured")

    # Build status string with colors
    github_icon = "[green]✓[/]" if github_ok else "[red]✗[/]"
    claude_icon = "[green]✓[/]" if claude_ok else "[red]✗[/]"
    repo_icon = "[green]✓[/]" if repo_ok else "[red]✗[/]"

    status_string = f"{github_icon} {claude_icon} {repo_icon}"

    return status_string, warnings


def display_header():
    """Display compact startup header with system status."""
    # Get short repo name (owner/repo instead of full URL)
    repo_short = REPO_PATH.split("github.com/")[-1] if "github.com/" in REPO_PATH else REPO_PATH.split(":")[-1].replace(".git", "")

    # Get system status with warnings
    status, warnings = get_system_status_detailed()

    # Create compact single-line header (no box)
    labels_str = ", ".join(LABEL_WORKFLOW_MAP.keys())
    override_tag = " [dim][APP override][/]" if _APP_OVERRIDE_ACTIVE else ""
    header_line = f"[bold cyan]ADW Cron[/] │ [bold white]{repo_short}[/]{override_tag} │ Poll: [cyan]20s[/] │ Labels: [yellow]{labels_str}[/] │ {status}"

    console.print(header_line)

    # Show warnings if any system checks failed
    for warning in warnings:
        console.print(f"  [yellow]{warning}[/]")

    console.print()  # Add blank line after header


def log_info(message: str, symbol: str = "●"):
    """Log an info message with symbol."""
    console.print(f"  {symbol} {message}")


def log_warning(message: str):
    """Log a warning message."""
    console.print(f"  [yellow]⚠[/] {message}")


def log_success(message: str):
    """Log a success message."""
    console.print(f"  [green]✓[/] {message}")


def log_neutral(message: str):
    """Log a neutral status message."""
    console.print(f"  [dim]◌[/] {message}")


def log_cycle_summary(issue_count: int, cycle_time: float, has_new: bool):
    """Log a condensed cycle summary."""
    global cycle_count
    cycle_count += 1

    status = "New issues found" if has_new else "No new issues"
    console.print(f"  [dim]●[/] Cycle {cycle_count} ─ {issue_count} issues ─ {cycle_time:.2f}s ─ {status}")


def print_separator():
    """Print a visual separator line."""
    console.print("\n  " + "─" * 60)


def format_status_line(total_processed: int, total_label: int) -> Text:
    """Format the live status line."""
    text = Text()
    text.append("  ◐ Polling...  │  ", style="dim")
    text.append(f"Total: {total_processed} processed ({total_label} via labels)", style="bold")
    return text


def discover_active_workflows() -> list[dict[str, any]]:
    """Discover all active ADW workflows and their current phases.

    Returns:
        List of dicts with keys: adw_id, issue_number, issue_title, phase, phase_name
    """
    workflows = []
    agents_dir = Path(__file__).parent.parent.parent / "agents"

    if not agents_dir.exists():
        return workflows

    # Import phase detection
    from adw_modules.phase_detection import PhaseDetector

    for adw_dir in agents_dir.iterdir():
        if not adw_dir.is_dir():
            continue

        # Load ADW state
        state = ADWState.load(adw_dir.name)
        if not state:
            continue

        # Only include active workflows (not placeholders from /report_issue)
        worktree_path = state.get("worktree_path")
        if worktree_path is None:
            continue

        # Verify worktree directory actually exists on disk
        if not Path(worktree_path).exists():
            continue

        # Detect current phase
        detector = PhaseDetector(
            adw_id=state.get("adw_id"),
            issue_number=state.get("issue_number")
        )
        current_phase = detector.detect_last_completed_phase()

        workflows.append({
            "adw_id": state.get("adw_id"),
            "issue_number": state.get("issue_number"),
            "issue_title": state.get("issue_title", "Unknown"),
            "phase": current_phase,
            "phase_name": current_phase.name
        })

    # Sort by issue number
    workflows.sort(key=lambda w: int(w["issue_number"]))
    return workflows


def display_active_workflows_table(workflows: list[dict[str, any]]):
    """Display active workflows in a Rich table.

    Args:
        workflows: List of workflow dicts from discover_active_workflows()
    """
    if not workflows:
        log_info("No active workflows found")
        return

    # Create table
    table = Table(
        title="[bold cyan]Active Workflows[/]",
        show_header=True,
        header_style="bold cyan",
        border_style="cyan"
    )

    # Add columns
    table.add_column("Issue", style="white", width=8)
    table.add_column("Title", style="dim", no_wrap=False)
    table.add_column("ADW ID", style="yellow", width=10)
    table.add_column("Phase", style="green", width=12)

    # Phase colors
    phase_colors = {
        "NOT_STARTED": "dim",
        "PLAN": "blue",
        "BUILD": "cyan",
        "TEST": "yellow",
        "REVIEW": "magenta",
        "DOCUMENT": "white",
        "SHIP": "green"
    }

    # Add rows
    for wf in workflows:
        phase_name = wf["phase_name"]
        phase_color = phase_colors.get(phase_name, "white")

        table.add_row(
            f"#{wf['issue_number']}",
            wf["issue_title"][:50] + "..." if len(wf["issue_title"]) > 50 else wf["issue_title"],
            wf["adw_id"],
            f"[{phase_color}]{phase_name}[/]"
        )

    console.print()
    console.print(table)
    console.print()


# ============================================================================
# Signal Handlers
# ============================================================================

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    console.print(f"\n  [cyan]●[/] Received signal {signum}, initiating graceful shutdown...")
    shutdown_requested = True


def should_process_issue(issue_number: int) -> tuple[bool, Optional[str], Optional[str]]:
    """Determine if an issue should be processed based on comments.

    Returns:
        tuple: (should_process, workflow_name, adw_id)
            - should_process: Whether to process this issue
            - workflow_name: Extracted workflow name (e.g., "adw_sdlc_zte_iso") or None for default
            - adw_id: Extracted ADW ID or None to generate new one
    """
    comments = fetch_issue_comments(REPO_PATH, issue_number)

    # Check for existing ACTIVE ADW state - deduplication
    # Only skip if workflow has actually started (has worktree)
    # Placeholder states from /report_issue have null worktree_path
    active_workflows = []
    agents_dir = Path(__file__).parent.parent.parent / "agents"
    if agents_dir.exists():
        for adw_dir in agents_dir.iterdir():
            if adw_dir.is_dir():
                state = ADWState.load(adw_dir.name)
                if state and state.get("issue_number") == str(issue_number):
                    # Check if workflow actually started
                    # Placeholder states from /report_issue have null worktree_path
                    if state.get("worktree_path") is not None:
                        active_workflows.append(state)

    if active_workflows:
        if is_first_cycle:
            log_warning(f"Issue #{issue_number} already has {len(active_workflows)} active ADW workflow(s) - skipping to prevent duplicates")
        return (False, None, None)

    # If no comments, it's a new issue - check issue body for embedded workflow
    if not comments:
        if is_first_cycle:
            log_info(f"Issue #{issue_number} has no comments - checking for embedded workflow")
        # Fetch full issue to get body
        try:
            issue = fetch_issue(str(issue_number), REPO_PATH)
            issue_body = issue.body or ""

            # Ignore issues from ADW bot to prevent loops
            if ADW_BOT_IDENTIFIER in issue_body:
                if is_first_cycle:
                    log_info(f"Issue #{issue_number} is from ADW bot - skipping to prevent loop")
                return (False, None, None)

            # Check if issue body contains workflow specification
            if "adw_" in issue_body.lower():
                temp_id = make_adw_id()
                extraction_result = extract_adw_info(issue_body, temp_id)
                if extraction_result.has_workflow:
                    workflow = extraction_result.workflow_command
                    provided_adw_id = extraction_result.adw_id
                    if is_first_cycle:
                        log_info(f"Issue #{issue_number} - extracted workflow: {workflow}, ADW ID: {provided_adw_id or 'auto-generate'}")
                    return (True, workflow, provided_adw_id)

            # No workflow specified, use default
            if is_first_cycle:
                log_info(f"Issue #{issue_number} - no workflow specified, will use default")
            return (True, None, None)
        except Exception as e:
            if is_first_cycle:
                log_warning(f"Failed to fetch issue #{issue_number} body: {e}")
            # Fall back to default processing
            return (True, None, None)

    # Get the latest comment
    latest_comment = comments[-1]
    comment_body = latest_comment.get("body", "").lower()
    comment_id = latest_comment.get("id")

    # Check if we've already processed this comment
    last_processed_comment = issue_last_comment.get(issue_number)
    if last_processed_comment == comment_id:
        # DEBUG level - not printing
        return (False, None, None)

    # Check if latest comment is exactly 'adw' (after stripping whitespace)
    if comment_body.strip() == "adw":
        if is_first_cycle:
            log_info(f"Issue #{issue_number} - latest comment is 'adw' - marking for processing")
        issue_last_comment[issue_number] = comment_id
        return (True, None, None)  # Use default workflow

    # DEBUG level - not printing
    return (False, None, None)


def trigger_adw_workflow(issue_number: int, workflow_name: Optional[str] = None, provided_adw_id: Optional[str] = None, workflow_type: str = "standard") -> bool:
    """Trigger the ADW workflow for a specific issue.

    Args:
        issue_number: GitHub issue number
        workflow_name: Specific workflow to run (e.g., "adw_sdlc_zte_iso"), overrides workflow_type
        provided_adw_id: ADW ID to use, or None to let the workflow generate one
        workflow_type: "standard" for adw_plan_build_iso.py or "zte" for adw_sdlc_zte_iso.py (ignored if workflow_name is provided)

    Returns:
        True if workflow triggered successfully, False otherwise
    """
    try:
        # If specific workflow name provided, use it
        if workflow_name:
            script_path = Path(__file__).parent.parent / f"{workflow_name}.py"
            display_name = workflow_name
        elif workflow_type == "zte":
            script_path = Path(__file__).parent.parent / "adw_sdlc_zte_iso.py"
            display_name = "Zero Touch Execution (ZTE)"
        else:
            script_path = Path(__file__).parent.parent / "adw_plan_build_iso.py"
            display_name = "Plan & Build"

        # Check if script exists
        if not script_path.exists():
            console.print(f"  [red]✗[/] Workflow script not found: {script_path}")
            return False

        if is_first_cycle:
            log_info(f"Triggering {display_name} workflow for issue #{issue_number}")
            if provided_adw_id:
                log_info(f"Using provided ADW ID: {provided_adw_id}")

        # Build command with optional ADW ID
        cmd = [sys.executable, str(script_path), str(issue_number)]
        if provided_adw_id:
            cmd.append(provided_adw_id)

        # Run the manual trigger script with filtered environment
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=script_path.parent,
            env=get_safe_subprocess_env()
        )

        if result.returncode == 0:
            if is_first_cycle:
                log_success(f"Successfully triggered {display_name} workflow for issue #{issue_number}")
            # DEBUG level - not printing output
            return True
        else:
            console.print(f"  [red]✗[/] Failed to trigger {display_name} workflow for issue #{issue_number}")
            console.print(f"  [red]✗[/] {result.stderr}")
            return False

    except Exception as e:
        console.print(f"  [red]✗[/] Exception while triggering workflow for issue #{issue_number}: {e}")
        return False


def check_and_process_issues():
    """Main function that checks for issues and processes qualifying ones."""
    global is_first_cycle

    if shutdown_requested:
        log_info("Shutdown requested, skipping check cycle")
        return

    start_time = time.time()

    # Only show detailed output for first cycle
    if is_first_cycle:
        log_info("Starting issue check cycle")

    try:
        # Fetch all open issues
        issues = fetch_open_issues(REPO_PATH)

        if is_first_cycle:
            console.print(f"    Fetched {len(issues)} open issues")

        if not issues:
            if is_first_cycle:
                log_neutral("No open issues found")
            return

        # Track newly qualified issues with workflow information
        # Format: [(issue_number, workflow_name, adw_id), ...]
        new_qualifying_issues = []  # Issues to process via comments
        new_label_issues = []  # Issues matched via label → (issue_number, label, workflow)

        # Check each issue
        for issue in issues:
            issue_number = issue.number
            if not issue_number:
                continue

            # Check for label-based workflow triggers (labels take priority)
            issue_labels = {label.name.upper() for label in issue.labels}
            matched_label = None
            matched_workflow = None
            for label, workflow in LABEL_WORKFLOW_MAP.items():
                if label.upper() in issue_labels:
                    matched_label = label
                    matched_workflow = workflow
                    break  # First match wins

            if matched_label:
                # Skip if already processed via label in this session
                if issue_number in label_processed_issues:
                    continue

                # IMPORTANT: Check for existing ACTIVE ADW state to prevent duplicate runs
                # This prevents re-running workflows after cron restarts
                # Only skip if workflow has actually started (has worktree)
                # Placeholder states from /report_issue have null worktree_path
                existing_active_states = []
                agents_dir = Path(__file__).parent.parent.parent / "agents"
                if agents_dir.exists():
                    for adw_dir in agents_dir.iterdir():
                        if adw_dir.is_dir():
                            state = ADWState.load(adw_dir.name)
                            if state and state.get("issue_number") == str(issue_number):
                                # Only count as "existing" if workflow actually started
                                if state.get("worktree_path") is not None:
                                    existing_active_states.append(state)

                if existing_active_states:
                    if is_first_cycle:
                        log_warning(f"Issue #{issue_number} already has {len(existing_active_states)} ADW workflow(s) - skipping '{matched_label}'")
                    label_processed_issues.add(issue_number)
                    processed_issues.add(issue_number)
                    continue

                if is_first_cycle:
                    log_info(f"Issue #{issue_number} has '{matched_label}' label → {matched_workflow}")
                new_label_issues.append((issue_number, matched_label, matched_workflow))
                continue

            # Skip if already processed in this session
            if issue_number in processed_issues:
                continue

            # Check if issue should be processed via comments
            should_process, workflow_name, adw_id = should_process_issue(issue_number)
            if should_process:
                new_qualifying_issues.append((issue_number, workflow_name, adw_id))

        # Process label-triggered issues first (higher priority)
        if new_label_issues:
            if is_first_cycle:
                labels_summary = [(n, l) for n, l, _ in new_label_issues]
                log_info(f"Found {len(new_label_issues)} label-triggered issues: {labels_summary}")

            for issue_number, label, workflow in new_label_issues:
                if shutdown_requested:
                    log_info("Shutdown requested, stopping issue processing")
                    break

                # Trigger the workflow mapped to this label
                if trigger_adw_workflow(issue_number, workflow_name=workflow):
                    label_processed_issues.add(issue_number)
                    processed_issues.add(issue_number)
                else:
                    if is_first_cycle:
                        log_warning(f"Failed to process '{label}' issue #{issue_number}, will retry in next cycle")

        # Process comment-triggered issues
        if new_qualifying_issues:
            issue_numbers = [item[0] for item in new_qualifying_issues]
            if is_first_cycle:
                log_info(f"Found {len(new_qualifying_issues)} new qualifying issues: {issue_numbers}")

            for issue_number, workflow_name, adw_id in new_qualifying_issues:
                if shutdown_requested:
                    log_info("Shutdown requested, stopping issue processing")
                    break

                # Trigger the workflow (use extracted workflow or default to "standard")
                if trigger_adw_workflow(
                    issue_number,
                    workflow_name=workflow_name,
                    provided_adw_id=adw_id,
                    workflow_type="standard"  # Fallback if workflow_name is None
                ):
                    processed_issues.add(issue_number)
                else:
                    if is_first_cycle:
                        log_warning(f"Failed to process issue #{issue_number}, will retry in next cycle")

        if not new_label_issues and not new_qualifying_issues:
            if is_first_cycle:
                log_neutral("No new qualifying issues found")

        # Log performance metrics
        cycle_time = time.time() - start_time

        if is_first_cycle:
            log_success(f"Check cycle completed in {cycle_time:.2f}s")
            print_separator()
            console.print(f"  [bold]Session:[/] [dim]{len(processed_issues)} processed ({len(label_processed_issues)} via labels) │ Entering main loop[/]")
            print_separator()
            console.print()
            is_first_cycle = False
        else:
            # Condensed summary for subsequent cycles
            has_new = bool(new_label_issues or new_qualifying_issues)
            log_cycle_summary(len(issues), cycle_time, has_new)

    except Exception as e:
        console.print(f"  [red]✗[/] Error during check cycle: {e}", style="red")
        import traceback
        traceback.print_exc()


PID_FILE = Path(__file__).parent / ".trigger_cron.pid"


def write_pid():
    """Write current PID to file for process control."""
    PID_FILE.write_text(str(os.getpid()))


def cleanup_pid():
    """Remove PID file on exit."""
    try:
        PID_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def stop_running_cron() -> bool:
    """Stop a running cron process using the PID file.

    Returns:
        True if a process was stopped, False otherwise.
    """
    if not PID_FILE.exists():
        console.print("  [yellow]⚠[/] No PID file found — cron is not running")
        return False

    pid = int(PID_FILE.read_text().strip())

    # Check if process is actually running
    try:
        os.kill(pid, 0)  # Signal 0 = just check if alive
    except ProcessLookupError:
        console.print(f"  [yellow]⚠[/] Stale PID file (pid {pid} not running) — cleaning up")
        cleanup_pid()
        return False
    except PermissionError:
        console.print(f"  [red]✗[/] No permission to stop pid {pid}")
        return False

    # Send SIGTERM first (graceful)
    console.print(f"  [cyan]●[/] Sending SIGTERM to pid {pid}...")
    os.kill(pid, signal.SIGTERM)

    # Wait up to 3 seconds for graceful shutdown
    for _ in range(6):
        time.sleep(0.5)
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            console.print(f"  [green]✓[/] Cron stopped gracefully (pid {pid})")
            cleanup_pid()
            return True

    # Force kill
    console.print(f"  [yellow]⚠[/] Graceful shutdown timed out — sending SIGKILL...")
    os.kill(pid, signal.SIGKILL)
    cleanup_pid()
    console.print(f"  [green]✓[/] Cron force-killed (pid {pid})")
    return True


def show_status():
    """Show whether the cron is currently running."""
    if not PID_FILE.exists():
        console.print("  [dim]◌[/] Cron is not running")
        return

    pid = int(PID_FILE.read_text().strip())
    try:
        os.kill(pid, 0)
        console.print(f"  [green]●[/] Cron is running (pid {pid})")
    except ProcessLookupError:
        console.print(f"  [yellow]⚠[/] Stale PID file (pid {pid} not running)")
        cleanup_pid()
    except PermissionError:
        console.print(f"  [yellow]?[/] Process {pid} exists but can't verify ownership")


def main():
    """Main entry point for the cron trigger."""
    # Write PID file and register cleanup
    write_pid()
    import atexit
    atexit.register(cleanup_pid)

    # Display header
    display_header()

    # Display active workflows status
    active_workflows = discover_active_workflows()
    display_active_workflows_table(active_workflows)

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Schedule the check function
    schedule.every(20).seconds.do(check_and_process_issues)

    # Run initial check immediately
    check_and_process_issues()

    # Main loop with live status display
    try:
        with Live(format_status_line(len(processed_issues), len(label_processed_issues)),
                  refresh_per_second=1, console=console) as live:
            while not shutdown_requested:
                schedule.run_pending()
                time.sleep(1)
                live.update(format_status_line(len(processed_issues), len(label_processed_issues)))
    except KeyboardInterrupt:
        pass

    cleanup_pid()
    console.print("\n  [cyan]●[/] Shutdown complete")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None

    if arg in ["--help", "-h", "help"]:
        print(__doc__)
        print("Usage: ./trigger_cron.py [command]")
        print("\nCommands:")
        print("  (none)     Start the cron trigger")
        print("  stop       Stop a running cron trigger")
        print("  status     Check if cron is running")
        print("  help       Show this help message")
        print("\nEnvironment variables:")
        print("  GITHUB_PAT - (Optional) GitHub Personal Access Token")
        print("\nThe script will poll GitHub issues every 20 seconds and trigger")
        print("the appropriate ADW workflow for qualifying issues:")
        print("\n  Triggers (labels checked first, in order):")
        for label, workflow in LABEL_WORKFLOW_MAP.items():
            print(f"    - Label '{label}' → {workflow}.py")
        print("    - Comment 'adw' → adw_plan_build_iso.py (standard)")
        print("\nNote: Repository URL is automatically detected from git remote.")
        sys.exit(0)

    elif arg == "stop":
        stop_running_cron()
        sys.exit(0)

    elif arg == "status":
        show_status()
        sys.exit(0)

    else:
        main()