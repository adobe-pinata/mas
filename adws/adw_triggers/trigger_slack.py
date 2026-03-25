#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "slack-bolt",
#     "slack-sdk",
#     "python-dotenv",
#     "pydantic",
#     "rich",
#     "boto3",
#     "PyJWT",
#     "cryptography",
# ]
# ///

"""
Slack Socket Mode trigger for ADW issue creation.

Listens to a Slack channel in real-time. When a message arrives, Claude parses
the intent — if it's a code/feature request, a GitHub issue is created on the
target repo and an ADW workflow is kicked off automatically.

Flow:
  Slack message → intent parse (Claude) → gh issue create → ADW workflow → thread reply

Requirements:
  SLACK_BOT_TOKEN  — xoxb-... Bot OAuth token (bot must be in the channel)
  SLACK_APP_TOKEN  — xapp-... Socket Mode app-level token
  SLACK_CHANNEL_ID — channel to listen in (ignore all others)

See .env.example for Slack app setup instructions.
"""

import logging
import os
import re
import signal
import subprocess
import sys
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from adw_modules.utils import get_safe_subprocess_env, make_adw_id
from adw_modules.github import get_effective_repo_path
from adw_modules.app_config import get_app_name
from adw_modules.data_types import IssueCreationRequest, AgentTemplateRequest
from adw_modules.issue_creator import create_issue_with_screenshots
from adw_modules.agent import execute_template
from adw_modules.utils import parse_json
from adw_modules.state import ADWState

load_dotenv()

# ─── Config ──────────────────────────────────────────────────────────────────

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN", "")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID", "")

try:
    REPO_PATH = get_effective_repo_path()
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

_APP_OVERRIDE_ACTIVE = get_app_name() not in (None, "")

# ─── State ───────────────────────────────────────────────────────────────────

# Track message timestamps already acted on (dedup within a session)
# Bounded OrderedDict used as LRU set; evicts oldest entries above MAX_PROCESSED_CACHE
MAX_PROCESSED_CACHE = 10_000
processed_messages: OrderedDict = OrderedDict()
_lock = threading.Lock()

# Ignore messages older than this many seconds on startup (avoid replaying history)
STARTUP_IGNORE_AGE_SECS = 300

# Graceful shutdown event (thread-safe)
shutdown_event = threading.Event()

console = Console()

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


# ─── Intent Parsing ──────────────────────────────────────────────────────────

def parse_slack_intent(text: str) -> Optional[dict]:
    """Use Claude to parse a Slack message into a GitHub issue title/body.

    Returns a dict with keys: is_actionable, title, body, workflow
    Returns None on failure.
    """
    temp_adw_id = make_adw_id()

    request = AgentTemplateRequest(
        agent_name="slack_intent_parser",
        slash_command="/parse_slack_intent",
        args=[text],
        adw_id=temp_adw_id,
    )

    try:
        response = execute_template(request)

        if not response.success:
            console.print(f"  [red]✗[/] Intent parse failed: {response.output}")
            return None

        data = parse_json(response.output, dict)
        return data

    except Exception as e:
        console.print(f"  [red]✗[/] Intent parse error: {e}")
        return None


# ─── Prompt Optimizer ─────────────────────────────────────────────────────────

def generate_optimized_spec(text: str) -> Optional[str]:
    """Use /prompt-optimizer (Opus) to generate a structured spec from a Slack message.

    Returns the raw prompt optimizer output (with <Inputs>, <Instructions> sections),
    or None on failure.
    """
    temp_adw_id = make_adw_id()
    request = AgentTemplateRequest(
        agent_name="slack_prompt_optimizer",
        slash_command="/prompt-optimizer",
        args=[text],
        adw_id=temp_adw_id,
    )
    try:
        response = execute_template(request)
        if not response.success:
            console.print(f"  [red]✗[/] Prompt optimizer failed: {response.output}")
            return None
        return response.output.strip()
    except Exception as e:
        console.print(f"  [red]✗[/] Prompt optimizer error: {e}")
        return None


# ─── Workflow Trigger ─────────────────────────────────────────────────────────

def trigger_adw_workflow(issue_number: int, workflow_name: str = "adw_sdlc_iso", slack_thread_ts: str = "") -> bool:
    """Trigger an ADW workflow script for the given issue number.

    Returns True if the subprocess launched successfully.
    """
    script_path = Path(__file__).parent.parent / f"{workflow_name}.py"

    if not script_path.exists():
        console.print(f"  [red]✗[/] Workflow script not found: {script_path}")
        return False

    try:
        env = get_safe_subprocess_env()
        if slack_thread_ts:
            env["SLACK_THREAD_TS"] = slack_thread_ts

        proc = subprocess.Popen(
            ["uv", "run", str(script_path), str(issue_number)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=script_path.parent,
            env=env,
        )
        console.print(f"  [green]✓[/] ADW `{workflow_name}` launched for issue #{issue_number} (pid {proc.pid})")
        return True

    except Exception as e:
        console.print(f"  [red]✗[/] Exception triggering ADW for issue #{issue_number}: {e}")
        return False


# ─── Message Handler ──────────────────────────────────────────────────────────

def handle_message_event(event: dict, say, client=None) -> None:
    """Process an incoming Slack message event."""
    # Ignore bot messages (including our own replies)
    if event.get("bot_id") or event.get("subtype") == "bot_message":
        console.print("  [dim]◌ skipped: bot message[/]")
        return

    # Only listen in the configured channel
    channel = event.get("channel", "")
    if SLACK_CHANNEL_ID and channel != SLACK_CHANNEL_ID:
        console.print(f"  [dim]◌ skipped: wrong channel {channel} (expected {SLACK_CHANNEL_ID})[/]")
        return

    # Ignore thread replies — only top-level messages trigger issue creation
    ts = event.get("ts", "")
    thread_ts = event.get("thread_ts")
    if thread_ts and thread_ts != ts:
        console.print("  [dim]◌ skipped: thread reply[/]")
        return

    # Deduplication (thread-safe: check and mark atomically to prevent concurrent double-processing)
    with _lock:
        if ts in processed_messages:
            console.print("  [dim]◌ skipped: already processed[/]")
            return
        processed_messages[ts] = None
        if len(processed_messages) > MAX_PROCESSED_CACHE:
            processed_messages.popitem(last=False)

    # Add pineapple reaction to acknowledge the message
    if client and ts and channel:
        try:
            client.reactions_add(channel=channel, name="pineapple", timestamp=ts)
        except Exception as e:
            console.print(f"  [yellow]⚠[/] Failed to add reaction: {e}")

    # Ignore messages older than STARTUP_IGNORE_AGE_SECS (avoid replaying history)
    try:
        msg_age = time.time() - float(ts)
        if msg_age > STARTUP_IGNORE_AGE_SECS:
            console.print(f"  [dim]◌ skipped: too old ({msg_age:.0f}s)[/]")
            return
    except (ValueError, TypeError):
        pass

    # Strip @mentions (e.g. "<@U12345> Run nala tests" → "Run nala tests")
    text = re.sub(r"<@[A-Z0-9]+>", "", event.get("text", "")).strip()
    if not text:
        return

    repo_short = REPO_PATH.split("github.com/")[-1] if "github.com/" in REPO_PATH else REPO_PATH
    console.print(f"\n  [cyan]●[/] Incoming message: [italic]{text[:80]}[/]")

    # Parse intent with Claude
    intent = parse_slack_intent(text)

    if not intent or not intent.get("is_actionable"):
        console.print("  [dim]◌[/] Not actionable — skipping")
        return

    title = intent.get("title", "").strip()
    workflow = intent.get("workflow", "adw_sdlc_iso")

    if not title:
        console.print("  [yellow]⚠[/] Intent returned empty title — skipping")
        return

    # Step 2b: Rich spec generation via prompt optimizer (Opus)
    console.print(f"  [cyan]→[/] Running prompt optimizer (Opus)...")
    optimized_spec = generate_optimized_spec(text)
    if optimized_spec:
        body = optimized_spec
        console.print(f"  [green]✓[/] Prompt optimizer generated spec ({len(body)} chars)")
    else:
        body = intent.get("body", "").strip()
        console.print(f"  [yellow]⚠[/] Prompt optimizer failed — falling back to intent body")

    console.print(f"  [cyan]→[/] Creating issue: {title}")

    # Create GitHub issue
    adw_id = make_adw_id()
    request = IssueCreationRequest(
        title=title,
        body=body,
        adw_id=adw_id,
        repository_path=REPO_PATH,
    )

    result = create_issue_with_screenshots(request, logger)

    if not result.success:
        console.print(f"  [red]✗[/] Issue creation failed: {result.error}")
        say(
            text=f":x: Failed to create issue: `{result.error}`",
            thread_ts=ts,
        )
        return

    console.print(f"  [green]✓[/] Created issue #{result.issue_number}: {result.issue_url}")

    # Trigger ADW workflow — pass thread_ts so all notifications land in this thread
    workflow_started = trigger_adw_workflow(result.issue_number, workflow_name=workflow, slack_thread_ts=ts)

    # Reply in thread
    if workflow_started:
        say(
            text=f"Created <{result.issue_url}|issue #{result.issue_number}> on `{repo_short}` — ADW `{workflow}` started :rocket:",
            thread_ts=ts,
        )
    else:
        say(
            text=f"Created <{result.issue_url}|issue #{result.issue_number}> on `{repo_short}`. :warning: ADW trigger failed — run manually or wait for the cron trigger.",
            thread_ts=ts,
        )


# ─── PID Lifecycle ───────────────────────────────────────────────────────────

PID_FILE = Path(__file__).parent / ".trigger_slack.pid"


def write_pid():
    PID_FILE.write_text(str(os.getpid()))


def cleanup_pid():
    try:
        PID_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def stop_running_slack() -> bool:
    if not PID_FILE.exists():
        console.print("  [yellow]⚠[/] No PID file found — Slack trigger is not running")
        return False

    pid = int(PID_FILE.read_text().strip())

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        console.print(f"  [yellow]⚠[/] Stale PID file (pid {pid} not running) — cleaning up")
        cleanup_pid()
        return False
    except PermissionError:
        console.print(f"  [red]✗[/] No permission to stop pid {pid}")
        return False

    console.print(f"  [cyan]●[/] Sending SIGTERM to pid {pid}...")
    os.kill(pid, signal.SIGTERM)

    for _ in range(6):
        time.sleep(0.5)
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            console.print(f"  [green]✓[/] Slack trigger stopped (pid {pid})")
            cleanup_pid()
            return True

    os.kill(pid, signal.SIGKILL)
    cleanup_pid()
    console.print(f"  [green]✓[/] Slack trigger force-killed (pid {pid})")
    return True


def show_status():
    if not PID_FILE.exists():
        console.print("  [dim]◌[/] Slack trigger is not running")
        return

    pid = int(PID_FILE.read_text().strip())
    try:
        os.kill(pid, 0)
        console.print(f"  [green]●[/] Slack trigger is running (pid {pid})")
    except ProcessLookupError:
        console.print(f"  [yellow]⚠[/] Stale PID file (pid {pid} not running)")
        cleanup_pid()
    except PermissionError:
        console.print(f"  [yellow]?[/] Process {pid} exists but can't verify ownership")


# ─── Signal Handlers ─────────────────────────────────────────────────────────
# Registered inside main() as a closure over the SocketModeHandler instance,
# so SIGINT, SIGTERM, and SIGHUP all close the WebSocket cleanly.


# ─── System Checks ──────────────────────────────────────────────────────────

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
    """Get system status with warnings for failures."""
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

    github_icon = "[green]✓[/]" if github_ok else "[red]✗[/]"
    claude_icon = "[green]✓[/]" if claude_ok else "[red]✗[/]"
    repo_icon = "[green]✓[/]" if repo_ok else "[red]✗[/]"

    status_string = f"{github_icon} {claude_icon} {repo_icon}"
    return status_string, warnings


# ─── Active Workflows ──────────────────────────────────────────────────────

def discover_active_workflows() -> list[dict[str, any]]:
    """Discover all active ADW workflows and their current phases."""
    workflows = []
    agents_dir = Path(__file__).parent.parent.parent / "agents"

    if not agents_dir.exists():
        return workflows

    from adw_modules.phase_detection import PhaseDetector

    for adw_dir in agents_dir.iterdir():
        if not adw_dir.is_dir():
            continue

        state = ADWState.load(adw_dir.name)
        if not state:
            continue

        worktree_path = state.get("worktree_path")
        if worktree_path is None:
            continue

        if not Path(worktree_path).exists():
            continue

        # Filter to workflows targeting the current repo
        # When APP override is active, only show workflows that explicitly match
        target_repo = state.get("target_repo")
        if _APP_OVERRIDE_ACTIVE:
            if target_repo != REPO_PATH:
                continue
        elif target_repo and target_repo != REPO_PATH:
            continue

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

    workflows.sort(key=lambda w: int(w["issue_number"]))
    return workflows


def display_active_workflows_table(workflows: list[dict[str, any]]):
    """Display active workflows in a Rich table."""
    if not workflows:
        console.print("  [dim]◌[/] No active workflows found")
        return

    table = Table(
        title="[bold cyan]Active Workflows[/]",
        show_header=True,
        header_style="bold cyan",
        border_style="cyan"
    )

    table.add_column("Issue", style="white", width=8)
    table.add_column("Title", style="dim", no_wrap=False)
    table.add_column("ADW ID", style="yellow", width=10)
    table.add_column("Phase", style="green", width=12)

    phase_colors = {
        "NOT_STARTED": "dim",
        "PLAN": "blue",
        "BUILD": "cyan",
        "TEST": "yellow",
        "REVIEW": "magenta",
        "DOCUMENT": "white",
        "SHIP": "green"
    }

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


# ─── Main ─────────────────────────────────────────────────────────────────────

def check_config() -> list[str]:
    """Return a list of missing/invalid config warnings."""
    warnings = []
    if not SLACK_BOT_TOKEN or not SLACK_BOT_TOKEN.startswith("xoxb-"):
        warnings.append("SLACK_BOT_TOKEN missing or invalid (must start with xoxb-)")
    if not SLACK_APP_TOKEN or not SLACK_APP_TOKEN.startswith("xapp-"):
        warnings.append("SLACK_APP_TOKEN missing or invalid (must start with xapp-)")
    if not SLACK_CHANNEL_ID:
        warnings.append("SLACK_CHANNEL_ID not set — will listen to ALL channels")
    return warnings


def display_header():
    repo_short = REPO_PATH.split("github.com/")[-1] if "github.com/" in REPO_PATH else REPO_PATH
    status, sys_warnings = get_system_status_detailed()
    override_tag = " [dim][APP override][/]" if _APP_OVERRIDE_ACTIVE else ""
    channel_label = SLACK_CHANNEL_ID or "[yellow]ALL channels[/]"
    console.print(
        f"[bold cyan]ADW Slack[/] │ [bold white]{repo_short}[/]{override_tag} │ Channel: [cyan]{channel_label}[/] │ {status}"
    )
    for warning in sys_warnings:
        console.print(f"  [yellow]{warning}[/]")
    for warning in check_config():
        console.print(f"  [yellow]⚠[/] {warning}")
    console.print()


def main():
    # Late import so the script can be imported for stop/status without requiring slack-bolt
    try:
        from slack_bolt import App
        from slack_bolt.adapter.socket_mode import SocketModeHandler
    except ImportError:
        console.print("[red]✗[/] slack-bolt not installed. Run: uv pip install slack-bolt")
        sys.exit(1)

    # Validate required tokens
    missing = [w for w in check_config() if "missing" in w]
    if missing:
        for msg in missing:
            console.print(f"  [red]✗[/] {msg}")
        console.print("\nSet SLACK_BOT_TOKEN and SLACK_APP_TOKEN in your .env file.")
        console.print("See .env.example for Slack app setup instructions.")
        sys.exit(1)

    write_pid()
    import atexit
    atexit.register(cleanup_pid)

    display_header()

    # Display active workflows status
    active_workflows = discover_active_workflows()
    display_active_workflows_table(active_workflows)

    app = App(token=SLACK_BOT_TOKEN)

    @app.event("message")
    def on_message(event, say, client):
        console.print(f"  [cyan]→ message event[/] subtype={event.get('subtype')} channel={event.get('channel')} text={str(event.get('text',''))[:60]}")
        if shutdown_event.is_set():
            return
        handle_message_event(event, say, client=client)

    @app.event("app_mention")
    def on_mention(event, say, client):
        console.print(f"  [cyan]→ app_mention event[/] channel={event.get('channel')} text={str(event.get('text',''))[:60]}")
        if shutdown_event.is_set():
            return
        handle_message_event(event, say, client=client)

    handler = SocketModeHandler(app, SLACK_APP_TOKEN)

    def graceful_shutdown(signum, frame):
        """Handle SIGINT, SIGTERM, and SIGHUP — close the WebSocket cleanly."""
        sig_name = signal.Signals(signum).name
        console.print(f"\n  [cyan]●[/] Received {sig_name}, shutting down...")
        shutdown_event.set()
        try:
            handler.close()
        except Exception:
            pass

    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)
    signal.signal(signal.SIGHUP, graceful_shutdown)

    console.print("  [green]✓[/] Connected to Slack — listening for messages\n")

    try:
        handler.start()
        # handler.start() blocks; the loop below only runs if it exits cleanly
        while not shutdown_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        if not shutdown_event.is_set():
            # Ctrl+C may bypass signal handler in some cases
            try:
                handler.close()
            except Exception:
                pass
        cleanup_pid()
        console.print("\n  [cyan]●[/] Shutdown complete")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None

    if arg in ["--help", "-h", "help"]:
        print(__doc__)
        print("Usage: ./trigger_slack.py [command]")
        print("\nCommands:")
        print("  (none)   Start the Slack Socket Mode listener")
        print("  stop     Stop a running listener")
        print("  status   Check if the listener is running")
        print("  help     Show this help message")
        print("\nEnvironment variables:")
        print("  SLACK_BOT_TOKEN  — xoxb-... Bot OAuth token")
        print("  SLACK_APP_TOKEN  — xapp-... Socket Mode app-level token")
        print("  SLACK_CHANNEL_ID — (Optional) channel to listen in")
        print("  APP              — (Optional) target app for multi-repo workflows")
        print("                     e.g. APP=mas resolves repo from apps/mas/adw.config.json")
        print("\nNote: Repository is resolved from APP env var + adw.config.json,")
        print("      falling back to git remote origin if APP is not set.")
        sys.exit(0)

    elif arg == "stop":
        stop_running_slack()
        sys.exit(0)

    elif arg == "status":
        show_status()
        sys.exit(0)

    elif arg is None:
        main()

    else:
        console.print(f"[red]Unknown command:[/] {arg}")
        console.print("Use --help for usage information.")
        sys.exit(1)
