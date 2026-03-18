"""Cloudflare R2 uploader for ADW screenshots."""

import os
import logging
from typing import Optional, Dict, List
from pathlib import Path
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError


class R2Uploader:
    """Handle uploads to Cloudflare R2 public bucket."""

    def __init__(
        self,
        logger: logging.Logger,
        app_name: Optional[str] = None,
        bucket_name: Optional[str] = None,
    ):
        self.logger = logger
        self.app_name = app_name
        self.client = None
        self.bucket_name = bucket_name or os.getenv("CLOUDFLARE_R2_BUCKET_NAME")
        self.public_domain = os.getenv("CLOUDFLARE_R2_PUBLIC_DOMAIN", "tac-public-imgs.iddagents.com")
        self.enabled = False

        # Strip protocol prefix if present
        if self.public_domain.startswith("https://"):
            self.public_domain = self.public_domain[8:]
        elif self.public_domain.startswith("http://"):
            self.public_domain = self.public_domain[7:]

        self._initialize()

    def _initialize(self) -> None:
        """Initialize R2 client if all required environment variables are set."""
        account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        access_key_id = os.getenv("CLOUDFLARE_R2_ACCESS_KEY_ID")
        secret_access_key = os.getenv("CLOUDFLARE_R2_SECRET_ACCESS_KEY")

        if not all([account_id, access_key_id, secret_access_key, self.bucket_name]):
            self.logger.info("R2 upload disabled — missing required environment variables")
            return

        try:
            self.client = boto3.client(
                's3',
                endpoint_url=f'https://{account_id}.r2.cloudflarestorage.com',
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                config=Config(signature_version='s3v4'),
                region_name='us-east-1',
            )
            self.enabled = True
            namespace = self.app_name or "agentic"
            self.logger.info(f"R2 upload enabled — bucket: {self.bucket_name}, namespace: {namespace}")
        except Exception as e:
            self.logger.warning(f"Failed to initialize R2 client: {e}")
            self.enabled = False

    @property
    def _namespace(self) -> str:
        """App namespace for R2 object keys."""
        return self.app_name or "agentic"

    def upload_file(self, file_path: str, object_key: Optional[str] = None) -> Optional[str]:
        """Upload a file to R2 and return the public URL.

        Args:
            file_path: Path to the file to upload (absolute or relative)
            object_key: Optional S3 object key. If not provided, uses default pattern.

        Returns:
            Public URL if upload successful, None if disabled or fails.
        """
        if not self.enabled:
            return None

        if not os.path.isabs(file_path):
            file_path = os.path.abspath(file_path)

        if not os.path.exists(file_path):
            self.logger.warning(f"File not found: {file_path}")
            return None

        if not object_key:
            object_key = f"adw/{self._namespace}/{Path(file_path).name}"

        try:
            self.client.upload_file(file_path, self.bucket_name, object_key)
            public_url = f"https://{self.public_domain}/{object_key}"
            self.logger.info(f"Uploaded to R2: {public_url}")
            return public_url
        except ClientError as e:
            self.logger.error(f"Failed to upload {file_path} to R2: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error uploading to R2: {e}")
            return None

    def upload_screenshots(
        self,
        screenshots: List[str],
        adw_id: str,
        base_dir: Optional[str] = None,
        category: str = "e2e",
    ) -> Dict[str, str]:
        """Upload multiple screenshots and return mapping of local paths to public URLs.

        Args:
            screenshots: List of local screenshot file paths
            adw_id: ADW workflow ID for organizing uploads
            base_dir: Directory to resolve relative paths against (defaults to cwd)
            category: Upload category for key path (e.g. "e2e", "review", "issues")

        Returns:
            Dict mapping local paths to public URLs (or original paths if upload failed)
        """
        url_mapping = {}
        base = Path(base_dir) if base_dir else Path.cwd()

        for screenshot_path in screenshots:
            if not screenshot_path:
                continue

            resolved = Path(screenshot_path)
            if not resolved.is_absolute():
                resolved = base / resolved

            filename = resolved.name
            object_key = f"adw/{self._namespace}/{adw_id}/{category}/{filename}"

            public_url = self.upload_file(str(resolved), object_key)
            url_mapping[screenshot_path] = public_url or screenshot_path

        return url_mapping
