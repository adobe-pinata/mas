"""GitHub App authentication for ADWS bot identity.

Generates installation access tokens so ADWS posts appear as
`agentic-adobee[bot]` instead of a personal account.

Env vars required:
    GITHUB_APP_ID            — numeric app ID
    GITHUB_APP_INSTALLATION_ID — numeric installation ID
    GITHUB_APP_PEM_PATH      — absolute path to the .pem private key
"""

import json
import logging
import os
import time
import urllib.request
import urllib.error
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Module-level token cache: (token_string, expiry_epoch)
_cached_token: Optional[Tuple[str, float]] = None


def _generate_jwt(app_id: str, pem_path: str) -> str:
    """Generate a JWT signed with the app's private key."""
    import jwt  # PyJWT

    with open(pem_path, "r") as f:
        private_key = f.read()

    now = int(time.time())
    payload = {
        "iat": now - 60,       # issued-at (60s clock skew allowance)
        "exp": now + (10 * 60),  # 10 min max for GitHub App JWTs
        "iss": app_id,
    }
    return jwt.encode(payload, private_key, algorithm="RS256")


def _exchange_for_installation_token(jwt_token: str, installation_id: str) -> Tuple[str, float]:
    """Exchange JWT for an installation access token. Returns (token, expiry_epoch)."""
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    req = urllib.request.Request(
        url,
        method="POST",
        headers={
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github+json",
        },
    )

    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())

    token = data["token"]
    # Parse ISO expiry → epoch.  Format: "2026-03-25T10:24:45Z"
    from datetime import datetime, timezone
    expires_at = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
    expiry_epoch = expires_at.timestamp()

    return token, expiry_epoch


def get_app_token() -> Optional[str]:
    """Return a valid GitHub App installation token, or None if not configured.

    Caches the token and refreshes automatically when < 5 min remaining.
    """
    global _cached_token

    app_id = os.getenv("GITHUB_APP_ID")
    installation_id = os.getenv("GITHUB_APP_INSTALLATION_ID")
    pem_path = os.getenv("GITHUB_APP_PEM_PATH")

    if not all([app_id, installation_id, pem_path]):
        return None

    if not os.path.exists(pem_path):
        logger.warning(f"GitHub App PEM file not found: {pem_path}")
        return None

    # Return cached token if still valid (> 5 min remaining)
    if _cached_token:
        token, expiry = _cached_token
        if time.time() < expiry - 300:
            return token

    try:
        jwt_token = _generate_jwt(app_id, pem_path)
        token, expiry = _exchange_for_installation_token(jwt_token, installation_id)
        _cached_token = (token, expiry)
        logger.info("Generated new GitHub App installation token")
        return token
    except ImportError:
        logger.warning("PyJWT not installed — cannot generate GitHub App tokens. Install with: pip install PyJWT cryptography")
        return None
    except FileNotFoundError:
        logger.warning(f"GitHub App PEM file not found: {pem_path}")
        return None
    except urllib.error.HTTPError as e:
        logger.error(f"GitHub API error generating app token: {e.code} {e.reason}")
        return None
    except Exception as e:
        logger.error(f"Failed to generate GitHub App token: {e}")
        return None


def get_app_slug() -> Optional[str]:
    """Return the app slug (e.g. 'agentic-adobee') if configured, for display purposes."""
    app_id = os.getenv("GITHUB_APP_ID")
    pem_path = os.getenv("GITHUB_APP_PEM_PATH")

    if not all([app_id, pem_path]) or not os.path.exists(pem_path):
        return None

    try:
        jwt_token = _generate_jwt(app_id, pem_path)
        req = urllib.request.Request(
            "https://api.github.com/app",
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "Accept": "application/vnd.github+json",
            },
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
        return data.get("slug")
    except Exception:
        return None
