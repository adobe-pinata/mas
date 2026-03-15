"""Issue classification utilities for ADW workflows."""

import re
import logging
from typing import Tuple, Optional

from adw_modules.data_types import (
    AgentTemplateRequest,
    GitHubIssue,
    IssueClassSlashCommand,
    ADWExtractionResult,
)
from adw_modules.agent import execute_template
from adw_modules.utils import parse_json


# Agent name constants
AGENT_CLASSIFIER = "issue_classifier"

# Available ADW workflows for runtime validation
AVAILABLE_ADW_WORKFLOWS = [
    # Isolated workflows (all workflows are now iso-based)
    "adw_plan_iso",
    "adw_patch_iso",
    "adw_report_issue_iso",
    "adw_batch_report_issues_iso",
    "adw_build_iso",
    "adw_test_iso",
    "adw_review_iso",
    "adw_document_iso",
    "adw_ship_iso",
    "adw_sdlc_ZTE_iso",  # Zero Touch Execution workflow
    "adw_plan_build_iso",
    "adw_plan_build_test_iso",
    "adw_plan_build_test_review_iso",
    "adw_plan_build_document_iso",
    "adw_plan_build_review_iso",
    "adw_sdlc_iso",
]


def extract_adw_info(text: str, temp_adw_id: str) -> ADWExtractionResult:
    """Extract ADW workflow, ID, and model_set from text using classify_adw agent.

    Args:
        text: Text to extract ADW info from
        temp_adw_id: Temporary ADW ID for the agent request

    Returns:
        ADWExtractionResult with workflow_command, adw_id, and model_set
    """
    # Use classify_adw to extract structured info
    request = AgentTemplateRequest(
        agent_name="adw_classifier",
        slash_command="/classify_adw",
        args=[text],
        adw_id=temp_adw_id,
    )

    try:
        response = execute_template(request)

        if not response.success:
            print(f"Failed to classify ADW: {response.output}")
            return ADWExtractionResult()

        # Parse JSON response using utility that handles markdown
        try:
            data = parse_json(response.output, dict)
            adw_command = data.get("adw_slash_command", "").replace("/", "")
            adw_id = data.get("adw_id")
            model_set = data.get("model_set", "base")

            # Validate command
            if adw_command and adw_command in AVAILABLE_ADW_WORKFLOWS:
                return ADWExtractionResult(
                    workflow_command=adw_command,
                    adw_id=adw_id,
                    model_set=model_set
                )

            return ADWExtractionResult()

        except ValueError as e:
            print(f"Failed to parse classify_adw response: {e}")
            return ADWExtractionResult()

    except Exception as e:
        print(f"Error calling classify_adw: {e}")
        return ADWExtractionResult()


def classify_issue(
    issue: GitHubIssue, adw_id: str, logger: logging.Logger
) -> Tuple[Optional[IssueClassSlashCommand], Optional[str]]:
    """Classify GitHub issue and return appropriate slash command.

    Args:
        issue: GitHub issue to classify
        adw_id: ADW workflow ID
        logger: Logger instance

    Returns:
        Tuple of (command, error_message)
    """
    # Use the classify_issue slash command template with minimal payload
    minimal_issue_json = issue.model_dump_json(
        by_alias=True, include={"number", "title", "body"}
    )

    request = AgentTemplateRequest(
        agent_name=AGENT_CLASSIFIER,
        slash_command="/classify_issue",
        args=[minimal_issue_json],
        adw_id=adw_id,
    )

    logger.debug(f"Classifying issue: {issue.title}")

    response = execute_template(request)

    logger.debug(
        f"Classification response: {response.model_dump_json(indent=2, by_alias=True)}"
    )

    if not response.success:
        return None, response.output

    # Extract the classification from the response
    output = response.output.strip()

    # Look for the classification pattern in the output
    classification_match = re.search(r"(/chore|/bug|/feature|0)", output)

    if classification_match:
        issue_command = classification_match.group(1)
    else:
        issue_command = output

    if issue_command == "0":
        return None, f"No command selected: {response.output}"

    if issue_command not in ["/chore", "/bug", "/feature"]:
        return None, f"Invalid command selected: {response.output}"

    return issue_command, None  # type: ignore
