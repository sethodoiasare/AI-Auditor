"""
Pydantic data models for the AI Cyber Assurance Agent.
"""

from pydantic import BaseModel, Field
from typing import List
from enum import Enum


class RequirementAssessment(str, Enum):
    MET = "Met"
    PARTIALLY_MET = "Partially Met"
    NOT_MET = "Not Met"


class AuditInput(BaseModel):
    """Input schema for a control audit assessment."""
    control: str = Field(
        ...,
        min_length=1,
        description="Control description [C] — the security control being assessed."
    )
    requirement: str = Field(
        ...,
        min_length=1,
        description="Requirement [Dx] — the specific requirement to be demonstrated."
    )
    evidence: str = Field(
        ...,
        min_length=1,
        description="Evidence [Ex] — the evidence provided to demonstrate compliance."
    )

    model_config = {"str_strip_whitespace": True}


class EvidenceQuality(BaseModel):
    """Assessment of the quality dimensions of evidence."""
    completeness: str = Field(
        ...,
        description="Whether all necessary evidence has been provided."
    )
    relevance: str = Field(
        ...,
        description="How directly the evidence addresses the requirement."
    )
    reliability: str = Field(
        ...,
        description="Trustworthiness and verifiability of the evidence."
    )


class AuditOutput(BaseModel):
    """Structured audit output schema."""
    control_objective: str = Field(
        ...,
        description="Clear statement of what the control aims to achieve."
    )
    requirement_assessment: str = Field(
        ...,
        description="One of: Met | Partially Met | Not Met"
    )
    evidence_quality: EvidenceQuality = Field(
        ...,
        description="Detailed assessment of evidence quality dimensions."
    )
    gaps_identified: List[str] = Field(
        default_factory=list,
        description="Specific gaps, ambiguities, or weaknesses in the evidence."
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Actionable recommendations to address identified gaps."
    )
    audit_opinion: str = Field(
        ...,
        description="Concise professional audit opinion summarising the overall assessment."
    )
    follow_up_questions: List[str] = Field(
        default_factory=list,
        description="Targeted follow-up questions generated only when evidence is insufficient."
    )
