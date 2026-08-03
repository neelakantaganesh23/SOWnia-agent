"""Pydantic models for per-agent findings and full review output.

These models define the structured output from each specialized
agent and the aggregated review result.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from backend.schemas.review import ReviewStatus, RiskLevel


class AgentFindingModel(BaseModel):
    """A single finding from a review agent."""

    finding: str = Field(..., description="Description of the finding")
    risk_level: RiskLevel = Field(..., description="Risk severity level")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score (0.0 to 1.0)"
    )
    page_reference: Optional[str] = Field(
        None, description="Page/section reference in the SOW"
    )
    recommendation: str = Field(
        ..., description="Actionable recommendation to address the finding"
    )


class AgentReviewResult(BaseModel):
    """Aggregated results from a single review agent."""

    agent: str = Field(..., description="Agent name")
    domain: str = Field(..., description="Review domain (legal, financial, etc.)")
    findings: List[AgentFindingModel] = Field(
        default_factory=list, description="List of findings"
    )
    agent_confidence: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Overall agent confidence for this review",
    )
    error: Optional[str] = Field(
        None, description="Error message if agent failed"
    )


class FullReviewOutput(BaseModel):
    """Complete review output with all agent findings."""

    review_id: str = Field(..., description="Unique review identifier")
    filename: str = Field(..., description="Original SOW filename")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Review timestamp (UTC)",
    )
    overall_risk_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=10.0,
        description="Overall risk score (0.0 to 10.0)",
    )
    overall_risk_level: Optional[RiskLevel] = Field(
        None, description="Overall risk level derived from score"
    )
    summary: Optional[str] = Field(
        None, description="Executive summary of the review"
    )
    status: ReviewStatus = Field(
        default=ReviewStatus.PENDING, description="Current review status"
    )
    error: Optional[str] = Field(
        None, description="Error message if review failed"
    )
    agents: Dict[str, AgentReviewResult] = Field(
        default_factory=dict,
        description="Results keyed by agent domain (legal, financial, etc.)",
    )

    @property
    def total_findings(self) -> int:
        """Count total findings across all agents."""
        return sum(len(result.findings) for result in self.agents.values())

    @property
    def high_risk_findings(self) -> List[AgentFindingModel]:
        """Get all HIGH risk findings across agents."""
        findings = []
        for result in self.agents.values():
            findings.extend(
                f for f in result.findings if f.risk_level == RiskLevel.HIGH
            )
        return findings

    def compute_risk_level(self) -> Optional[RiskLevel]:
        """Derive overall risk level from score."""
        if self.overall_risk_score is None:
            return None
        if self.overall_risk_score >= 7.0:
            return RiskLevel.HIGH
        elif self.overall_risk_score >= 4.0:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
