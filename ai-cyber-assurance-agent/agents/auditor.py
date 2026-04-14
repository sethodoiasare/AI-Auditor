"""
Auditor Agent — performs the initial cyber assurance control assessment.
"""

import json

import anthropic

from models.schema import AuditInput
from utils.formatter import load_prompt, parse_json_response
from utils.logger import get_logger

logger = get_logger(__name__)

# System role injected as a cached system prompt for efficiency
_SYSTEM_ROLE = (
    "You are a senior cyber assurance auditor. "
    "Your assessments are evidence-based, objective, and strictly grounded in the provided information. "
    "You never fabricate, assume, or speculate. You always return valid JSON."
)


class AuditorAgent:
    """
    Performs the initial control assessment.

    Uses the auditor prompt template to evaluate whether the provided
    evidence demonstrates the requirement is met. Returns a structured
    JSON assessment as a dictionary.
    """

    def __init__(self, client: anthropic.Anthropic, model: str) -> None:
        self.client = client
        self.model = model
        self._prompt_template = load_prompt("auditor")

    def assess(self, audit_input: AuditInput) -> dict:
        """
        Run the initial assessment for a given audit input.

        Args:
            audit_input: Validated AuditInput containing control, requirement, evidence.

        Returns:
            Parsed assessment dictionary.

        Raises:
            ValueError: If the API response cannot be parsed as JSON.
            anthropic.APIError: On API communication failures.
        """
        user_message = self._prompt_template.format(
            control=audit_input.control,
            requirement=audit_input.requirement,
            evidence=audit_input.evidence,
        )

        logger.info("Auditor Agent — starting initial assessment")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_ROLE,
                    # Cache the system prompt — stable across many audit runs
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_message}],
        )

        raw_text = response.content[0].text
        logger.debug(f"Auditor raw response (first 200 chars): {raw_text[:200]!r}")

        result = parse_json_response(raw_text)

        assessment = result.get("requirement_assessment", "Unknown")
        logger.info(f"Auditor Agent — assessment complete: {assessment}")
        return result
