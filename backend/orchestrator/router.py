"""Confidence-based routing logic for the LangGraph orchestrator.

Determines how agent results are routed after execution,
including flagging low-confidence reviews for human attention.
"""

import logging
from typing import Any, Dict, List, Literal

from backend.orchestrator.state import AgentFinding, SOWReviewState

logger = logging.getLogger(__name__)

# Confidence threshold below which findings are flagged for human review
CONFIDENCE_THRESHOLD = 0.5

# Risk score weights for each domain
DOMAIN_WEIGHTS: Dict[str, float] = {
    "legal": 0.25,
    "financial": 0.20,
    "technical": 0.20,
    "risk": 0.20,
    "delivery": 0.15,
}

# Risk level to numeric score mapping
RISK_LEVEL_SCORES: Dict[str, float] = {
    "HIGH": 9.0,
    "MEDIUM": 5.0,
    "LOW": 2.0,
}


def should_flag_for_human_review(state: SOWReviewState) -> bool:
    """Check if any agent's average confidence is below threshold.

    Args:
        state: Current review state with agent findings.

    Returns:
        True if the review should be flagged for human attention.
    """
    domains = ["legal", "financial", "technical", "risk", "delivery"]

    for domain in domains:
        findings: List[AgentFinding] = state.get(f"{domain}_findings", [])
        if not findings:
            # No findings from an agent is itself a flag
            logger.warning(f"No findings from {domain} agent — flagging for review.")
            return True

        avg_confidence = sum(f.get("confidence", 0.0) for f in findings) / len(
            findings
        )
        if avg_confidence < CONFIDENCE_THRESHOLD:
            logger.warning(
                f"{domain} agent average confidence ({avg_confidence:.2f}) "
                f"is below threshold ({CONFIDENCE_THRESHOLD}). "
                f"Flagging for human review."
            )
            return True

    return False


def compute_overall_risk_score(state: SOWReviewState) -> float:
    """Compute weighted overall risk score from all agent findings.

    The score is computed as a weighted average of domain risk scores,
    where each domain's score is the average of its findings' risk levels.

    Args:
        state: Current review state with agent findings.

    Returns:
        Overall risk score from 0.0 to 10.0.
    """
    domain_scores: Dict[str, float] = {}

    for domain, weight in DOMAIN_WEIGHTS.items():
        findings: List[AgentFinding] = state.get(f"{domain}_findings", [])

        if not findings:
            # No findings = low risk for this domain
            domain_scores[domain] = 1.0
            continue

        # Compute average risk score for this domain
        risk_scores = [
            RISK_LEVEL_SCORES.get(f.get("risk_level", "MEDIUM"), 5.0)
            for f in findings
        ]
        domain_scores[domain] = sum(risk_scores) / len(risk_scores)

    # Compute weighted overall score
    overall_score = sum(
        domain_scores.get(domain, 1.0) * weight
        for domain, weight in DOMAIN_WEIGHTS.items()
    )

    # Clamp to 0.0 - 10.0
    overall_score = max(0.0, min(10.0, overall_score))

    logger.info(
        f"Overall risk score: {overall_score:.2f} "
        f"(domain scores: {domain_scores})"
    )
    return round(overall_score, 2)


def compute_risk_level(score: float) -> str:
    """Derive risk level string from numeric score.

    Args:
        score: Risk score from 0.0 to 10.0.

    Returns:
        "HIGH", "MEDIUM", or "LOW".
    """
    if score >= 7.0:
        return "HIGH"
    elif score >= 4.0:
        return "MEDIUM"
    else:
        return "LOW"


def generate_executive_summary(state: SOWReviewState) -> str:
    """Generate an executive summary from all agent findings.

    Produces a 3-5 bullet point summary of the most critical
    findings across all domains.

    Args:
        state: Current review state with agent findings.

    Returns:
        Executive summary string.
    """
    all_findings: List[AgentFinding] = []
    domains = ["legal", "financial", "technical", "risk", "delivery"]

    for domain in domains:
        findings = state.get(f"{domain}_findings", [])
        all_findings.extend(findings)

    if not all_findings:
        return "No findings were generated during the review."

    # Sort by risk level (HIGH first) then by confidence (highest first)
    risk_priority = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    all_findings.sort(
        key=lambda f: (
            risk_priority.get(f.get("risk_level", "MEDIUM"), 1),
            -f.get("confidence", 0.0),
        )
    )

    # Count findings by level
    high_count = sum(1 for f in all_findings if f.get("risk_level") == "HIGH")
    medium_count = sum(1 for f in all_findings if f.get("risk_level") == "MEDIUM")
    low_count = sum(1 for f in all_findings if f.get("risk_level") == "LOW")

    summary_parts = [
        f"SOW Review completed with {len(all_findings)} total findings: "
        f"{high_count} HIGH, {medium_count} MEDIUM, {low_count} LOW risk.",
    ]

    # Add top 4 high-risk findings as bullet points
    top_findings = [f for f in all_findings if f.get("risk_level") == "HIGH"][:4]
    if not top_findings:
        top_findings = all_findings[:4]

    for finding in top_findings:
        domain = finding.get("domain", "unknown").capitalize()
        desc = finding.get("finding", "No description")
        # Truncate long findings
        if len(desc) > 200:
            desc = desc[:200] + "..."
        summary_parts.append(f"• [{domain}] {desc}")

    # Add human review flag if applicable
    if should_flag_for_human_review(state):
        summary_parts.append(
            "⚠️ This review has been flagged for human attention due to "
            "low agent confidence in one or more domains."
        )

    return "\n".join(summary_parts)


def route_after_agents(
    state: SOWReviewState,
) -> Literal["synthesize"]:
    """Route to synthesis after all agents complete.

    This is a simple router that always proceeds to the synthesize
    step. In the future, conditional routing based on findings
    could be added (e.g., escalation paths).

    Args:
        state: Current review state.

    Returns:
        Next node name ("synthesize").
    """
    return "synthesize"
