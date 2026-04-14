"""
Reviewer Agent — quality-reviews and strengthens the auditor's assessment.
"""

import json

import anthropic

from models.schema import AuditInput
from utils.formatter import load_prompt, parse_json_response
from utils.logger import get_logger

logger = get_logger(__name__)

_SYSTEM_ROLE = (
    "You are a senior cyber assurance review manager. "
    "Your role is to critically review audit assessments, identify missed risks, "
    "correct weak reasoning, and ensure opinions are defensible and evidence-based. "
    "You never fabricate findings. You always return valid JSON."
)


class ReviewerAgent:
    """
    Reviews and strengthens the auditor's initial assessment.

    Acts as a second line of defence — checks for missed gaps, overly lenient
    verdicts, and weak reasoning. Returns a refined assessment dictionary.
    """

    def __init__(self, client: anthropic.Anthropic, model: str) -> None:
        self.client = client
        self.model = model
        self._prompt_template = load_prompt("reviewer")

    def review(self, audit_input: AuditInput, auditor_output: dict) -> dict:
        """
        Review and strengthen the auditor's assessment.

        Args:
            audit_input: Original validated AuditInput.
            auditor_output: Dictionary produced by the AuditorAgent.

        Returns:
            Refined assessment dictionary.

        Raises:
            ValueError: If the API response cannot be parsed as JSON.
            anthropic.APIError: On API communication failures.
        """
        user_message = self._prompt_template.format(
            control=audit_input.control,
            requirement=audit_input.requirement,
            evidence=audit_input.evidence,
            auditor_output=json.dumps(auditor_output, indent=2),
        )

        logger.info("Reviewer Agent — starting quality review")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_ROLE,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_message}],
        )

        raw_text = response.content[0].text
        logger.debug(f"Reviewer raw response (first 200 chars): {raw_text[:200]!r}")

        result = parse_json_response(raw_text)

        assessment = result.get("requirement_assessment", "Unknown")
        logger.info(f"Reviewer Agent — review complete: {assessment}")
        return result
