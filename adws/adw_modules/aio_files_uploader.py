# /// script
# requires-python = ">=3.12"
# ///
"""AIO Files uploader for ADW screenshots using @adobe/aio-lib-files."""

import os
import subprocess
import logging
from typing import Optional, Dict, List
from pathlib import Path


_NODE_HELPER = """\
import Files from '@adobe/aio-lib-files';
import { readFileSync } from 'fs';
const files = await Files.init();
const buf = readFileSync(process.env.LOCAL_PATH);
await files.write(process.env.REMOTE_PATH, buf);
const url = await files.generatePresignURL(process.env.REMOTE_PATH, { expiryInSeconds: 86400 });
process.stdout.write(url);
"""


class AIOFilesUploader:
    """Handle uploads to Azure CDN via @adobe/aio-lib-files."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.enabled = False
        self._env = {}
        self._initialize()

    def _initialize(self) -> None:
        """Enable uploader when AIO credentials are present.

        aio-lib-files reads __OW_NAMESPACE and __OW_API_KEY (OpenWhisk credentials).
        These map to AIO_runtime_namespace / AIO_runtime_auth in the project .env.
        """
        # Support both __OW_* (aio-lib-files native) and AIO_runtime_* (.env convention)
        namespace = (
            os.getenv("__OW_NAMESPACE")
            or os.getenv("AIO_runtime_namespace")
            or os.getenv("AIO_STATE_NAMESPACE")
        )
        api_key = (
            os.getenv("__OW_API_KEY")
            or os.getenv("AIO_runtime_auth")
            or os.getenv("AIO_STATE_API_KEY")
        )

        if not all([namespace, api_key]):
            self.logger.info("AIO Files upload disabled — missing OW/AIO runtime credentials")
            return

        # Pass credentials as __OW_* which is what aio-lib-files expects
        self._env = {
            "__OW_NAMESPACE": namespace,
            "__OW_API_KEY": api_key,
        }
        self.enabled = True
        self.logger.info("AIO Files upload enabled")

    def upload_file(self, file_path: str, remote_path: str) -> Optional[str]:
        """Upload a file via aio-lib-files and return the presigned CDN URL.

        Args:
            file_path: Absolute path to the local file.
            remote_path: Destination path inside the AIO files namespace.

        Returns:
            Presigned *.azureedge.net URL on success, None on failure.
        """
        if not self.enabled:
            self.logger.warning("AIO Files uploader not enabled — skipping upload")
            return None

        if not os.path.exists(file_path):
            self.logger.warning(f"File not found: {file_path}")
            return None

        env = {**os.environ, **self._env, "LOCAL_PATH": file_path, "REMOTE_PATH": remote_path}

        try:
            result = subprocess.run(
                ["node", "--input-type=module"],
                input=_NODE_HELPER,
                capture_output=True,
                text=True,
                env=env,
                timeout=60,
            )

            if result.returncode != 0:
                self.logger.warning(f"AIO Files node helper failed: {result.stderr.strip()}")
                return None

            url = result.stdout.strip()
            if not url:
                self.logger.warning("AIO Files node helper returned empty URL")
                return None

            self.logger.info(f"Uploaded to AIO Files: {url}")
            return url

        except subprocess.TimeoutExpired:
            self.logger.warning(f"AIO Files upload timed out for: {file_path}")
            return None
        except Exception as e:
            self.logger.warning(f"AIO Files upload error: {e}")
            return None

    def upload_screenshots(
        self, screenshots: List[str], adw_id: str, base_dir: Optional[str] = None
    ) -> Dict[str, str]:
        """Upload multiple screenshots and return mapping of local paths to public URLs.

        Args:
            screenshots: List of screenshot file paths (absolute or relative to base_dir).
            adw_id: ADW workflow ID for organising uploads.
            base_dir: Directory to resolve relative paths against (defaults to cwd).

        Returns:
            Dict mapping local paths to CDN URLs (or original path if upload failed).
        """
        url_mapping = {}
        base = Path(base_dir) if base_dir else Path.cwd()

        for screenshot_path in screenshots:
            if not screenshot_path:
                continue

            # Resolve relative paths against base_dir
            resolved = Path(screenshot_path)
            if not resolved.is_absolute():
                resolved = base / resolved

            filename = resolved.name
            remote_path = f"adw/{adw_id}/e2e/{filename}"

            public_url = self.upload_file(str(resolved), remote_path)
            url_mapping[screenshot_path] = public_url or screenshot_path

        return url_mapping
