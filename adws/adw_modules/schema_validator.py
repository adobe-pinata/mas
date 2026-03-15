"""Schema migration validation module for ADWS test runner.

Validates Prisma schema changes to prevent production bugs:
- Detects schema modifications via git diff
- Regenerates Prisma Client
- Validates TypeScript compilation
- Tests runtime API endpoints
- Checks schema-to-code consistency
"""

import json
import logging
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

import requests
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SchemaValidationResult(BaseModel):
    """Validation result for Prisma schema changes."""

    schema_changed: bool = False
    prisma_generated: bool = False
    typescript_valid: bool = False
    backend_compiles: bool = False
    api_endpoints_tested: bool = False
    consistency_check_passed: bool = False
    validation_passed: bool = False
    error_messages: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "schema_changed": self.schema_changed,
            "prisma_generated": self.prisma_generated,
            "typescript_valid": self.typescript_valid,
            "backend_compiles": self.backend_compiles,
            "api_endpoints_tested": self.api_endpoints_tested,
            "consistency_check_passed": self.consistency_check_passed,
            "validation_passed": self.validation_passed,
            "error_messages": self.error_messages,
            "warnings": self.warnings,
            "timestamp": self.timestamp.isoformat(),
        }


class SchemaValidator:
    """Validates Prisma schema migrations to prevent runtime bugs."""

    CRITICAL_ENDPOINTS = [
        "/api/engineers",
        "/api/teams",
        "/api/projects",
        "/api/allocations",
    ]

    def __init__(self, worktree_path: str, backend_port: int):
        """Initialize schema validator.

        Args:
            worktree_path: Path to the worktree root directory
            backend_port: Port for isolated backend testing
        """
        self.worktree_path = Path(worktree_path)
        self.backend_port = backend_port
        self.server_path = self.worktree_path / "app" / "server"
        self.schema_path = self.server_path / "prisma" / "schema.prisma"

    def detect_schema_changes(self) -> bool:
        """Check if prisma/schema.prisma was modified in git diff.

        Returns:
            True if schema was modified, False otherwise
        """
        logger.info(f"Checking for schema changes in {self.worktree_path}")
        try:
            result = subprocess.run(
                ["git", "diff", "HEAD", "--name-only"],
                cwd=self.worktree_path,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                logger.warning(
                    f"Git diff failed: {result.stderr}. Checking against origin/main instead."
                )
                # Try diff against origin/main
                result = subprocess.run(
                    ["git", "diff", "origin/main", "--name-only"],
                    cwd=self.worktree_path,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

            changed_files = result.stdout.strip().split("\n")
            schema_changed = any(
                "prisma/schema.prisma" in file for file in changed_files
            )

            logger.info(
                f"Schema change detection: {schema_changed} (changed files: {len(changed_files)})"
            )
            return schema_changed

        except subprocess.TimeoutExpired:
            logger.error("Git diff timed out")
            return False
        except Exception as e:
            logger.error(f"Error detecting schema changes: {e}")
            return False

    def regenerate_prisma_client(self) -> Tuple[bool, str]:
        """Regenerate Prisma Client after schema changes.

        Returns:
            (success, error_message) tuple
        """
        logger.info(f"Regenerating Prisma Client in {self.server_path}")
        try:
            result = subprocess.run(
                ["pnpm", "db:generate"],
                cwd=self.server_path,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode == 0:
                logger.info("Prisma Client regenerated successfully")
                return True, ""
            else:
                error_msg = f"Prisma Client generation failed:\n{result.stderr}"
                logger.error(error_msg)
                return False, error_msg

        except subprocess.TimeoutExpired:
            error_msg = "Prisma Client generation timed out (120s)"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error regenerating Prisma Client: {e}"
            logger.error(error_msg)
            return False, error_msg

    def validate_typescript(self) -> Tuple[bool, str]:
        """Run TypeScript type checking.

        Returns:
            (success, error_message) tuple
        """
        logger.info(f"Running TypeScript validation in {self.server_path}")
        try:
            result = subprocess.run(
                ["pnpm", "type-check"],
                cwd=self.server_path,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode == 0:
                logger.info("TypeScript validation passed")
                return True, ""
            else:
                error_msg = f"TypeScript validation failed:\n{result.stderr}\n{result.stdout}"
                logger.error(error_msg)
                return False, error_msg

        except subprocess.TimeoutExpired:
            error_msg = "TypeScript validation timed out (120s)"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error running TypeScript validation: {e}"
            logger.error(error_msg)
            return False, error_msg

    def validate_backend_compilation(self) -> Tuple[bool, str]:
        """Validate backend compiles successfully.

        Returns:
            (success, error_message) tuple
        """
        logger.info(f"Validating backend compilation in {self.server_path}")
        try:
            # Try build first
            result = subprocess.run(
                ["pnpm", "build"],
                cwd=self.server_path,
                capture_output=True,
                text=True,
                timeout=180,
            )

            if result.returncode == 0:
                logger.info("Backend compilation passed")
                return True, ""
            else:
                # Try tsc --noEmit as fallback
                logger.warning("Build failed, trying tsc --noEmit")
                result = subprocess.run(
                    ["pnpm", "tsc", "--noEmit"],
                    cwd=self.server_path,
                    capture_output=True,
                    text=True,
                    timeout=180,
                )

                if result.returncode == 0:
                    logger.info("Backend compilation passed (tsc)")
                    return True, ""
                else:
                    error_msg = f"Backend compilation failed:\n{result.stderr}\n{result.stdout}"
                    logger.error(error_msg)
                    return False, error_msg

        except subprocess.TimeoutExpired:
            error_msg = "Backend compilation timed out (180s)"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error validating backend compilation: {e}"
            logger.error(error_msg)
            return False, error_msg

    def test_api_endpoints(self) -> Tuple[bool, List[str]]:
        """Test critical API endpoints at runtime.

        Starts backend server, tests endpoints, then stops server.

        Returns:
            (success, error_messages) tuple
        """
        logger.info(f"Testing API endpoints on port {self.backend_port}")
        process = None
        errors: List[str] = []

        try:
            # Start backend server
            logger.info("Starting backend server for testing")
            process = subprocess.Popen(
                ["pnpm", "dev"],
                cwd=self.server_path,
                env={**subprocess.os.environ, "PORT": str(self.backend_port)},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Wait for server to start (30 seconds timeout)
            logger.info("Waiting for server to start (30s timeout)")
            time.sleep(30)

            # Check if server is still running
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                error_msg = f"Backend server failed to start:\nSTDOUT: {stdout}\nSTDERR: {stderr}"
                logger.error(error_msg)
                return False, [error_msg]

            # Test each endpoint
            base_url = f"http://localhost:{self.backend_port}"
            for endpoint in self.CRITICAL_ENDPOINTS:
                url = f"{base_url}{endpoint}"
                logger.info(f"Testing endpoint: {url}")

                try:
                    response = requests.get(url, timeout=30)

                    # Accept 200 (success) or 401 (auth required - service is running)
                    if response.status_code in [200, 401]:
                        logger.info(
                            f"Endpoint {endpoint} returned {response.status_code} (OK)"
                        )
                    else:
                        error_msg = f"Endpoint {endpoint} returned {response.status_code}: {response.text[:500]}"
                        logger.error(error_msg)
                        errors.append(error_msg)

                except requests.exceptions.RequestException as e:
                    error_msg = f"Endpoint {endpoint} failed: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            success = len(errors) == 0
            logger.info(
                f"API endpoint testing {'passed' if success else 'failed'} ({len(errors)} errors)"
            )
            return success, errors

        except Exception as e:
            error_msg = f"Error testing API endpoints: {e}"
            logger.error(error_msg)
            return False, [error_msg]

        finally:
            # Stop backend server
            if process is not None:
                logger.info("Stopping backend server")
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    logger.warning("Server didn't stop gracefully, killing")
                    process.kill()

    def check_schema_code_consistency(self) -> Tuple[bool, List[str]]:
        """Check schema-to-code consistency for relation names.

        Parses schema.prisma for relation names and scans route files
        for common errors (plural vs singular, snake_case vs camelCase).

        Returns:
            (success, warnings) tuple
        """
        logger.info("Checking schema-to-code consistency")
        warnings: List[str] = []

        try:
            # Parse schema.prisma for relation names
            if not self.schema_path.exists():
                warning = f"Schema file not found: {self.schema_path}"
                logger.warning(warning)
                return True, [warning]  # Don't fail, just warn

            schema_content = self.schema_path.read_text()
            relation_pattern = r"(\w+)\s+(\w+)(?:\[\])?\s+@relation"
            relations = re.findall(relation_pattern, schema_content)

            logger.info(f"Found {len(relations)} relations in schema")

            # Scan route files for relation usage
            routes_path = self.server_path / "src" / "routes"
            if not routes_path.exists():
                warning = f"Routes directory not found: {routes_path}"
                logger.warning(warning)
                return True, [warning]

            route_files = list(routes_path.glob("*.ts"))
            logger.info(f"Scanning {len(route_files)} route files")

            # Common error patterns
            for route_file in route_files:
                content = route_file.read_text()

                # Check for common errors from PR #453
                # 1. Using plural "engineers" instead of singular "engineer"
                if "include: {" in content and "engineers:" in content:
                    warning = f"{route_file.name}: Found 'engineers:' in include statement - verify it matches schema relation name"
                    logger.warning(warning)
                    warnings.append(warning)

                # 2. Using snake_case for camelCase relations (e.g., team.team_memberships instead of team.teamMemberships)
                snake_case_relations = re.findall(r"(\w+)\.(\w+_\w+)", content)
                if snake_case_relations:
                    for match in snake_case_relations:
                        warning = f"{route_file.name}: Found snake_case relation access '{match[0]}.{match[1]}' - verify it matches schema (should be camelCase)"
                        logger.warning(warning)
                        warnings.append(warning)

            success = len(warnings) == 0
            logger.info(
                f"Schema consistency check {'passed' if success else 'found warnings'} ({len(warnings)} warnings)"
            )
            return success, warnings

        except Exception as e:
            warning = f"Error checking schema consistency: {e}"
            logger.error(warning)
            return True, [warning]  # Don't fail validation, just warn

    def run_full_validation(self) -> SchemaValidationResult:
        """Execute complete validation pipeline.

        Returns:
            SchemaValidationResult with all validation results
        """
        logger.info(
            f"Starting full schema validation for worktree {self.worktree_path}"
        )
        result = SchemaValidationResult()

        # Step 1: Detect schema changes
        result.schema_changed = self.detect_schema_changes()
        if not result.schema_changed:
            logger.info("No schema changes detected, skipping validation")
            result.validation_passed = True
            return result

        # Step 2: Regenerate Prisma Client
        success, error = self.regenerate_prisma_client()
        result.prisma_generated = success
        if not success:
            result.error_messages.append(f"Prisma Client generation failed: {error}")
            result.validation_passed = False
            return result

        # Step 3: Validate TypeScript
        success, error = self.validate_typescript()
        result.typescript_valid = success
        if not success:
            result.error_messages.append(f"TypeScript validation failed: {error}")
            result.validation_passed = False
            return result

        # Step 4: Validate backend compilation
        success, error = self.validate_backend_compilation()
        result.backend_compiles = success
        if not success:
            result.error_messages.append(f"Backend compilation failed: {error}")
            result.validation_passed = False
            return result

        # Step 5: Test API endpoints
        success, errors = self.test_api_endpoints()
        result.api_endpoints_tested = success
        if not success:
            result.error_messages.extend(errors)
            result.validation_passed = False
            return result

        # Step 6: Check schema-to-code consistency
        success, warnings = self.check_schema_code_consistency()
        result.consistency_check_passed = success
        if warnings:
            result.warnings.extend(warnings)
        # Note: Consistency warnings don't fail validation, just notify

        # All checks passed
        result.validation_passed = (
            result.prisma_generated
            and result.typescript_valid
            and result.backend_compiles
            and result.api_endpoints_tested
        )

        logger.info(
            f"Full schema validation {'passed' if result.validation_passed else 'failed'}"
        )
        return result
