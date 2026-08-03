"""LangGraph state machine for the SOW review pipeline.

Defines the complete review graph with 8 nodes:
1. parse_document — chunk the SOW text
2. legal_review — run LegalAgent
3. financial_review — run FinancialAgent
4. technical_review — run TechnicalAgent
5. risk_review — run RiskAgent
6. delivery_review — run DeliveryAgent
7. synthesize — aggregate findings, compute risk score
8. generate_report — produce JSON + PDF outputs

Agents run in parallel using LangGraph's fan-out pattern.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from backend.agents.delivery_agent import DeliveryAgent
from backend.agents.financial_agent import FinancialAgent
from backend.agents.legal_agent import LegalAgent
from backend.agents.risk_agent import RiskAgent
from backend.agents.technical_agent import TechnicalAgent
from backend.orchestrator.router import (
    compute_overall_risk_score,
    compute_risk_level,
    generate_executive_summary,
)
from backend.orchestrator.state import SOWReviewState
from backend.utils.chunker import SemanticChunker

logger = logging.getLogger(__name__)

# Initialize agents (singleton instances)
legal_agent = LegalAgent()
financial_agent = FinancialAgent()
technical_agent = TechnicalAgent()
risk_agent = RiskAgent()
delivery_agent = DeliveryAgent()

# Initialize chunker
chunker = SemanticChunker()


# ─── Node Functions ──────────────────────────────────────────────────────────


def parse_document(state: SOWReviewState) -> Dict[str, Any]:
    """Parse and chunk the SOW document text.

    Args:
        state: Current state with sow_text populated.

    Returns:
        State update with sow_chunks and status.
    """
    logger.info("Parsing and chunking SOW document...")
    sow_text = state.get("sow_text", "")

    if not sow_text:
        return {
            "status": "error",
            "error": "No SOW text provided for review.",
            "sow_chunks": [],
            "messages": [
                SystemMessage(content="Error: No SOW text provided.")
            ],
        }

    chunks = chunker.chunk(sow_text)
    logger.info(f"Document chunked into {len(chunks)} sections.")

    return {
        "sow_chunks": chunks,
        "status": "in_progress",
        "messages": [
            SystemMessage(
                content=f"Document parsed: {len(chunks)} chunks, "
                f"{len(sow_text)} characters."
            )
        ],
    }


def legal_review(state: SOWReviewState) -> Dict[str, Any]:
    """Run the Legal Agent review."""
    logger.info("Starting legal review...")
    result = legal_agent.run(state)
    result["messages"] = [
        SystemMessage(
            content=f"Legal review complete: "
            f"{len(result.get('legal_findings', []))} findings."
        )
    ]
    return result


def financial_review(state: SOWReviewState) -> Dict[str, Any]:
    """Run the Financial Agent review."""
    logger.info("Starting financial review...")
    result = financial_agent.run(state)
    result["messages"] = [
        SystemMessage(
            content=f"Financial review complete: "
            f"{len(result.get('financial_findings', []))} findings."
        )
    ]
    return result


def technical_review(state: SOWReviewState) -> Dict[str, Any]:
    """Run the Technical Agent review."""
    logger.info("Starting technical review...")
    result = technical_agent.run(state)
    result["messages"] = [
        SystemMessage(
            content=f"Technical review complete: "
            f"{len(result.get('technical_findings', []))} findings."
        )
    ]
    return result


def risk_review(state: SOWReviewState) -> Dict[str, Any]:
    """Run the Risk Agent review."""
    logger.info("Starting risk review...")
    result = risk_agent.run(state)
    result["messages"] = [
        SystemMessage(
            content=f"Risk review complete: "
            f"{len(result.get('risk_findings', []))} findings."
        )
    ]
    return result


def delivery_review(state: SOWReviewState) -> Dict[str, Any]:
    """Run the Delivery Agent review."""
    logger.info("Starting delivery review...")
    result = delivery_agent.run(state)
    result["messages"] = [
        SystemMessage(
            content=f"Delivery review complete: "
            f"{len(result.get('delivery_findings', []))} findings."
        )
    ]
    return result


def synthesize(state: SOWReviewState) -> Dict[str, Any]:
    """Aggregate all agent findings and compute overall risk score.

    Args:
        state: State with all agent findings populated.

    Returns:
        State update with overall_risk_score, summary, and status.
    """
    logger.info("Synthesizing review findings...")

    # Compute overall risk score
    overall_score = compute_overall_risk_score(state)
    risk_level = compute_risk_level(overall_score)

    # Generate executive summary
    summary = generate_executive_summary(state)

    logger.info(
        f"Synthesis complete: risk score={overall_score}, "
        f"risk level={risk_level}."
    )

    return {
        "overall_risk_score": overall_score,
        "summary": summary,
        "status": "complete",
        "messages": [
            SystemMessage(
                content=f"Review synthesis complete. "
                f"Overall risk: {risk_level} ({overall_score}/10.0)."
            )
        ],
    }


def generate_report(state: SOWReviewState) -> Dict[str, Any]:
    """Generate the final review report data.

    This node prepares the final output format. The actual PDF
    generation is handled by the API endpoint.

    Args:
        state: Fully populated review state.

    Returns:
        State update confirming report generation.
    """
    logger.info("Generating review report...")

    total_findings = sum(
        len(state.get(f"{domain}_findings", []))
        for domain in ["legal", "financial", "technical", "risk", "delivery"]
    )

    logger.info(f"Report ready: {total_findings} total findings.")

    return {
        "messages": [
            SystemMessage(
                content=f"Report generated with {total_findings} findings."
            )
        ],
    }


# ─── Graph Definition ────────────────────────────────────────────────────────


def build_review_graph() -> StateGraph:
    """Build the LangGraph state machine for SOW review.

    The graph runs:
    1. parse_document
    2. All 5 agent reviews in parallel (fan-out)
    3. synthesize (after all agents complete)
    4. generate_report
    5. END

    Returns:
        Compiled LangGraph StateGraph.
    """
    graph = StateGraph(SOWReviewState)

    # Add nodes
    graph.add_node("parse_document", parse_document)
    graph.add_node("legal_review", legal_review)
    graph.add_node("financial_review", financial_review)
    graph.add_node("technical_review", technical_review)
    graph.add_node("risk_review", risk_review)
    graph.add_node("delivery_review", delivery_review)
    graph.add_node("synthesize", synthesize)
    graph.add_node("generate_report", generate_report)

    # Set entry point
    graph.set_entry_point("parse_document")

    # Fan-out: parse_document → all 5 agents in parallel
    graph.add_edge("parse_document", "legal_review")
    graph.add_edge("parse_document", "financial_review")
    graph.add_edge("parse_document", "technical_review")
    graph.add_edge("parse_document", "risk_review")
    graph.add_edge("parse_document", "delivery_review")

    # Fan-in: all agents → synthesize
    graph.add_edge("legal_review", "synthesize")
    graph.add_edge("financial_review", "synthesize")
    graph.add_edge("technical_review", "synthesize")
    graph.add_edge("risk_review", "synthesize")
    graph.add_edge("delivery_review", "synthesize")

    # synthesize → generate_report → END
    graph.add_edge("synthesize", "generate_report")
    graph.add_edge("generate_report", END)

    return graph.compile()


# Singleton compiled graph
review_graph = build_review_graph()


def run_review(
    sow_text: str,
    filename: str,
    review_id: str | None = None,
) -> SOWReviewState:
    """Execute a full SOW review pipeline.

    Args:
        sow_text: Full extracted SOW text.
        filename: Original filename.
        review_id: Optional review UUID (auto-generated if not provided).

    Returns:
        Completed SOWReviewState with all findings and scores.
    """
    if not review_id:
        review_id = str(uuid.uuid4())

    initial_state: SOWReviewState = {
        "sow_text": sow_text,
        "sow_chunks": [],
        "review_id": review_id,
        "filename": filename,
        "messages": [
            HumanMessage(content=f"Starting SOW review for: {filename}")
        ],
        "legal_findings": [],
        "financial_findings": [],
        "technical_findings": [],
        "risk_findings": [],
        "delivery_findings": [],
        "overall_risk_score": None,
        "summary": None,
        "status": "pending",
        "error": None,
    }

    logger.info(f"Starting review pipeline for '{filename}' (ID: {review_id})...")

    try:
        result = review_graph.invoke(initial_state)
        logger.info(f"Review pipeline completed for '{filename}'.")
        return result
    except Exception as e:
        logger.error(f"Review pipeline failed for '{filename}': {e}")
        initial_state["status"] = "error"
        initial_state["error"] = str(e)
        return initial_state
