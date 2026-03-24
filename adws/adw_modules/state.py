"""State management for ADW composable architecture.

Provides persistent state management via file storage and
transient state passing between scripts via stdin/stdout.
"""

import json
import os
import sys
import logging
from typing import Dict, Any, Optional
from adw_modules.data_types import ADWStateData


class ADWState:
    """Container for ADW workflow state with file persistence."""

    STATE_FILENAME = "adw_state.json"

    def __init__(self, adw_id: str):
        """Initialize ADWState with a required ADW ID.
        
        Args:
            adw_id: The ADW ID for this state (required)
        """
        if not adw_id:
            raise ValueError("adw_id is required for ADWState")
        
        self.adw_id = adw_id
        # Start with minimal state
        self.data: Dict[str, Any] = {"adw_id": self.adw_id}
        self.logger = logging.getLogger(__name__)

    def update(self, **kwargs):
        """Update state with new key-value pairs."""
        # Filter to only our core fields
        core_fields = {"adw_id", "issue_number", "issue_url", "issue_title", "branch_name", "plan_file", "issue_class", "worktree_path", "backend_port", "frontend_port", "model_set", "all_adws", "slack_thread_ts", "schema_validation_result", "target_repo", "session_ids"}
        for key, value in kwargs.items():
            if key in core_fields:
                self.data[key] = value

    def get(self, key: str, default=None):
        """Get value from state by key."""
        return self.data.get(key, default)

    def append_adw_id(self, adw_id: str):
        """Append an ADW ID to the all_adws list if not already present."""
        all_adws = self.data.get("all_adws", [])
        if adw_id not in all_adws:
            all_adws.append(adw_id)
            self.data["all_adws"] = all_adws

    def append_session_id(self, session_id: str):
        """Append a Claude session ID to the session_ids list if not already present."""
        session_ids = self.data.get("session_ids", [])
        if session_id not in session_ids:
            session_ids.append(session_id)
            self.data["session_ids"] = session_ids

    def set_schema_validation_result(self, result: Dict[str, Any]):
        """Store schema validation result in state.

        Args:
            result: Schema validation result dictionary (from SchemaValidationResult.to_dict())
        """
        self.data["schema_validation_result"] = result

    def get_schema_validation_result(self) -> Optional[Dict[str, Any]]:
        """Retrieve schema validation result from state.

        Returns:
            Schema validation result dictionary or None
        """
        return self.data.get("schema_validation_result")

    def get_working_directory(self) -> str:
        """Get the working directory for this ADW instance.
        
        Returns worktree_path if set (for isolated workflows),
        otherwise returns the main repo path.
        """
        worktree_path = self.data.get("worktree_path")
        if worktree_path:
            return worktree_path
        
        # Return main repo path (parent of adws directory)
        return os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

    def get_state_path(self) -> str:
        """Get path to state file."""
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        return os.path.join(project_root, "agents", self.adw_id, self.STATE_FILENAME)

    def save(self, workflow_step: Optional[str] = None) -> None:
        """Save state to file in agents/{adw_id}/adw_state.json."""
        state_path = self.get_state_path()
        os.makedirs(os.path.dirname(state_path), exist_ok=True)

        # Create ADWStateData for validation
        state_data = ADWStateData(
            adw_id=self.data.get("adw_id"),
            issue_number=self.data.get("issue_number"),
            issue_url=self.data.get("issue_url"),
            issue_title=self.data.get("issue_title"),
            branch_name=self.data.get("branch_name"),
            plan_file=self.data.get("plan_file"),
            issue_class=self.data.get("issue_class"),
            worktree_path=self.data.get("worktree_path"),
            backend_port=self.data.get("backend_port"),
            frontend_port=self.data.get("frontend_port"),
            model_set=self.data.get("model_set", "base"),
            all_adws=self.data.get("all_adws", []),
            slack_thread_ts=self.data.get("slack_thread_ts"),
            schema_validation_result=self.data.get("schema_validation_result"),
            target_repo=self.data.get("target_repo"),
            session_ids=self.data.get("session_ids", []),
        )

        # Save as JSON
        with open(state_path, "w") as f:
            json.dump(state_data.model_dump(), f, indent=2)

        self.logger.info(f"Saved state to {state_path}")
        if workflow_step:
            self.logger.info(f"State updated by: {workflow_step}")

    @classmethod
    def load(
        cls, adw_id: str, logger: Optional[logging.Logger] = None
    ) -> Optional["ADWState"]:
        """Load state from file if it exists."""
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        state_path = os.path.join(project_root, "agents", adw_id, cls.STATE_FILENAME)

        if not os.path.exists(state_path):
            return None

        try:
            with open(state_path, "r") as f:
                data = json.load(f)

            # Validate with ADWStateData
            state_data = ADWStateData(**data)

            # Create ADWState instance
            state = cls(state_data.adw_id)
            state.data = state_data.model_dump()

            if logger:
                logger.info(f"🔍 Found existing state from {state_path}")
                logger.info(f"State: {json.dumps(state_data.model_dump(), indent=2)}")

            return state
        except Exception as e:
            if logger:
                logger.error(f"Failed to load state from {state_path}: {e}")
            return None

    @classmethod
    def from_stdin(cls) -> Optional["ADWState"]:
        """Read state from stdin if available (for piped input).

        Returns None if no piped input is available (stdin is a tty).
        """
        if sys.stdin.isatty():
            return None
        try:
            input_data = sys.stdin.read()
            if not input_data.strip():
                return None
            data = json.loads(input_data)
            adw_id = data.get("adw_id")
            if not adw_id:
                return None  # No valid state without adw_id
            state = cls(adw_id)
            state.data = data
            return state
        except (json.JSONDecodeError, EOFError):
            return None

    def to_stdout(self):
        """Write state to stdout as JSON (for piping to next script)."""
        # Only output core fields
        output_data = {
            "adw_id": self.data.get("adw_id"),
            "issue_number": self.data.get("issue_number"),
            "branch_name": self.data.get("branch_name"),
            "plan_file": self.data.get("plan_file"),
            "issue_class": self.data.get("issue_class"),
            "worktree_path": self.data.get("worktree_path"),
            "backend_port": self.data.get("backend_port"),
            "frontend_port": self.data.get("frontend_port"),
            "all_adws": self.data.get("all_adws", []),
            "slack_thread_ts": self.data.get("slack_thread_ts"),
            "session_ids": self.data.get("session_ids", []),
        }
        print(json.dumps(output_data, indent=2))

    def format_for_github(self) -> str:
        """Format state in a clean, professional way for GitHub comments.

        Only shows relevant, non-empty fields with minimal formatting.
        """
        lines = []

        # Issue reference (most important - make it prominent)
        issue_number = self.data.get("issue_number")
        issue_title = self.data.get("issue_title")
        issue_url = self.data.get("issue_url")

        if issue_number and issue_url:
            lines.append(f"### [#{issue_number}]({issue_url}) {issue_title or ''}")
        elif issue_number:
            lines.append(f"### #{issue_number} {issue_title or ''}")

        # Key details - minimal formatting
        details = []

        issue_class = self.data.get("issue_class")
        if issue_class:
            issue_type = issue_class.replace("/", "").capitalize()
            details.append(f"Type: {issue_type}")

        branch_name = self.data.get("branch_name")
        if branch_name:
            details.append(f"Branch: `{branch_name}`")

        plan_file = self.data.get("plan_file")
        if plan_file:
            # Show just the filename
            plan_filename = plan_file.split("/")[-1]
            details.append(f"Plan: `{plan_filename}`")

        if details:
            lines.append("")
            lines.extend(details)

        # Environment info (only for isolated workflows)
        worktree_path = self.data.get("worktree_path")
        if worktree_path:
            backend_port = self.data.get("backend_port")
            frontend_port = self.data.get("frontend_port")

            env_info = []
            worktree_short = worktree_path.split("/trees/")[-1] if "/trees/" in worktree_path else worktree_path
            env_info.append(f"Worktree: `trees/{worktree_short}`")

            if backend_port and frontend_port:
                env_info.append(f"Ports: {backend_port} / {frontend_port}")

            if env_info:
                lines.append("")
                lines.append("<details><summary>Environment</summary>")
                lines.append("")
                lines.extend(env_info)
                lines.append("</details>")

        return "\n".join(lines)
