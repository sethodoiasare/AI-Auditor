"""
Input validation for the AI Cyber Assurance Agent.
"""

from typing import Optional, Tuple

from pydantic import ValidationError

from models.schema import AuditInput


MIN_CONTROL_LENGTH = 10
MIN_REQUIREMENT_LENGTH = 10
MIN_EVIDENCE_LENGTH = 5


def validate_input(data: dict) -> Tuple[Optional[AuditInput], Optional[str]]:
    """
    Validate raw audit input data against the AuditInput schema.

    Performs both schema-level validation (via Pydantic) and basic
    business-logic checks on minimum content lengths.

    Args:
        data: Dictionary with keys 'control', 'requirement', 'evidence'.

    Returns:
        (AuditInput, None) on success, or (None, error_message) on failure.
    """
    try:
        audit_input = AuditInput(**data)
    except ValidationError as exc:
        errors = [f"'{e['loc'][0]}': {e['msg']}" for e in exc.errors()]
        return None, f"Validation error — {'; '.join(errors)}"
    except TypeError:
        return None, "Invalid input format. Expected a dictionary with 'control', 'requirement', and 'evidence' keys."

    # Business-logic checks
    if len(audit_input.control) < MIN_CONTROL_LENGTH:
        return None, (
            f"Control description is too short (minimum {MIN_CONTROL_LENGTH} characters). "
            "Please provide a meaningful control description."
        )

    if len(audit_input.requirement) < MIN_REQUIREMENT_LENGTH:
        return None, (
            f"Requirement is too short (minimum {MIN_REQUIREMENT_LENGTH} characters). "
            "Please provide a meaningful requirement statement."
        )

    if len(audit_input.evidence) < MIN_EVIDENCE_LENGTH:
        return None, (
            f"Evidence is too short (minimum {MIN_EVIDENCE_LENGTH} characters). "
            "Please provide the evidence to be assessed."
        )

    return audit_input, None
