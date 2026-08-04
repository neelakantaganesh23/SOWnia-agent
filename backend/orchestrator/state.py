"""SOW Review State definition for LangGraph orchestrator.

Defines the TypedDict state that flows through the LangGraph
state machine, carrying SOW text, agent findings, and review metadata.
"""

from typing import Annotated, List, Optional, TypedDict

import operator
from langchain_core.messages import BaseMessage


class AgentFinding(TypedDict):
    """A single finding from a review agent."""

    agent: str
    domain: str
    finding: str
    risk_level: str  # "HIGH" | "MEDIUM" | "LOW"
    confidence: float  # 0.0 to 1.0
    page_reference: Optional[str]
    recommendation: str
    source_text: Optional[str]  # Verbatim quote from SOW for traceability


class SOWReviewState(TypedDict):
    """State that flows through the LangGraph SOW review pipeline.

    This TypedDict defines all the data that the orchestrator
    and agents read from and write to during a review.
    """

    # Input data
    sow_text: str  # Full extracted SOW text
    sow_chunks: List[str]  # Semantically chunked sections
    review_id: str  # UUID for this review
    filename: str  # Original filename

    # Message history (appended via operator.add)
    messages: Annotated[List[BaseMessage], operator.add]

    # Per-agent findings
    legal_findings: List[AgentFinding]
    financial_findings: List[AgentFinding]
    technical_findings: List[AgentFinding]
    risk_findings: List[AgentFinding]
    delivery_findings: List[AgentFinding]

    # Synthesis outputs
    overall_risk_score: Optional[float]  # 0.0 to 10.0
    summary: Optional[str]  # Executive summary

    # Status tracking
    status: str  # "pending" | "in_progress" | "complete" | "error"
    error: Optional[str]
