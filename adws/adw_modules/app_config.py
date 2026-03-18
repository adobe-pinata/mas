"""App-layer config resolution for ADW multi-repo support.

Reads the APP env var and loads the corresponding adw.config.json
from apps/{app}/ to resolve the target GitHub repo and other settings.
"""

import functools
import json
import os
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def get_app_name() -> Optional[str]:
    """Return the APP env var value, or None if not set."""
    return os.getenv("APP")


def _get_project_root() -> str:
    """Get the agentic harness project root."""
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


@functools.lru_cache(maxsize=1)
def _load_app_config() -> Optional[dict]:
    """Load and cache the full adw.config.json for the current APP.

    Returns None if APP is not set.
    Raises FileNotFoundError if APP is set but config is missing.
    """
    app = get_app_name()
    if not app:
        return None

    project_root = _get_project_root()
    config_path = os.path.join(project_root, "apps", app, "adw.config.json")

    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"ADW config not found for app '{app}': {config_path}\n"
            f"Create apps/{app}/adw.config.json with {{\"app_name\": \"{app}\", \"github_repo\": \"owner/repo\"}}"
        )

    with open(config_path, "r") as f:
        return json.load(f)


def get_app_config_value(key: str, default: Any = None) -> Any:
    """Read an arbitrary key from apps/{APP}/adw.config.json.

    Returns default if APP is not set or key is missing.
    """
    config = _load_app_config()
    if config is None:
        return default
    return config.get(key, default)


def get_app_repo() -> Optional[str]:
    """Resolve the target GitHub repo from APP env var + app config.

    Reads APP env var (e.g. "content-qa"), loads apps/{app}/adw.config.json,
    and returns the github_repo value (e.g. "joaquinrivero/experience-qa").

    Returns None if APP is not set (agentic-harness-local mode).
    Raises FileNotFoundError if APP is set but config is missing.
    Raises ValueError if config exists but github_repo key is missing.
    """
    repo = get_app_config_value("github_repo")
    if repo is not None:
        return repo

    # APP not set — agentic-harness-local mode
    if get_app_name() is None:
        return None

    raise ValueError(
        f"apps/{get_app_name()}/adw.config.json missing 'github_repo' key"
    )
