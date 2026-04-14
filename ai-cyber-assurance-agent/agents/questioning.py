"""
Questioning Agent — generates targeted follow-up questions when evidence is insufficient.
"""

import json

import anthropic

from models.schema import AuditInput
from utils.formatter import load_prompt, parse_json_list
from utils.logger import get_logger

logger = get_logger(__name__)

_SYSTEM_ROLE = (
    "You are a cyber assurance auditor specialising in evidence gap analysis. "
    "You generate targeted, specific, and answerable follow-up questions only when "
    "evidence is clearly insufficient. You never ask vague or redundant questions. "
    "You always return a valid JSON array."
)

# Assessments that warrant follow-up questions
_NEEDS_QUESTIONS = {"Partially Met", "Not Met"}


class QuestioningAgent:
    """
    Generates targeted follow-up questions based on identified audit gaps.

    Questions are generated ONLY when the assessment is 'Partially Met' or 'Not Met'
    and meaningful gaps have been identified. Returns an empty list otherwise.
    """

    def __init__(self, client: anthropic.Anthropic, model: str) -> None:
        self.client = client
        self.model = model
        self._prompt_template = load_prompt("questioning")

    def generate_questions(
        self, audit_input: AuditInput, reviewed_output: dict
    ) -> list:
        """
        Generate follow-up questions based on the reviewed assessment.

        Args:
            audit_input: Original validated AuditInput.
            reviewed_output: Dictionary produced by the ReviewerAgent.

        Returns:
            List of follow-up question strings (may be empty).
        """
        assessment = reviewed_output.get("requirement_assessment", "")
        gaps = reviewed_output.get("gaps_identified", [])

        # Skip question generation if assessment is Met and no gaps
        if assessment not in _NEEDS_QUESTIONS:
            if not gaps:
                logger.info(
                    "Questioning Agent — assessment is Met with no gaps; skipping."
                )
                return []

        if not gaps:
            logger.info(
                "Questioning Agent — no gaps identified; skipping question generation."
            )
            return []

        user_message = self._prompt_template.format(
            control=audit_input.control,
            requirement=audit_input.requirement,
            evidence=audit_input.evidence,
            requirement_assessment=assessment,
            gaps_identified=json.dumps(gaps, indent=2),
        )

        logger.info("Questioning Agent — generating follow-up questions")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
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
        logger.debug(f"Questioning raw response: {raw_text[:200]!r}")

        questions = parse_json_list(raw_text)
        logger.info(f"Questioning Agent — generated {len(questions)} question(s)")
        return questions
