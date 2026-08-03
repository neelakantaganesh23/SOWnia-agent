"""Integration test for the full SOW review pipeline.

Tests the LangGraph state machine end-to-end using mocked LLM
responses to verify the orchestration flow.
"""

import json
from unittest.mock import patch, MagicMock

import pytest

from backend.orchestrator.graph import run_review
from backend.orchestrator.state import SOWReviewState


# Sample SOW text for testing
SAMPLE_SOW_TEXT = """
--- Page 1 ---
STATEMENT OF WORK

Project: Enterprise Data Platform Migration
Client: Acme Corporation
Vendor: TechConsult Inc.
Date: August 2026

1. SCOPE OF WORK

The vendor shall design, develop, and deploy a cloud-based data platform 
migrating from the existing on-premise infrastructure. The scope includes:
- Data warehouse migration to cloud (AWS/GCP)
- ETL pipeline redesign
- Dashboard and reporting tool migration
- User training and documentation

--- Page 2 ---
2. DELIVERABLES

2.1 Architecture Design Document
2.2 Migration Plan with rollback procedures
2.3 Deployed cloud data platform
2.4 Training materials and sessions
2.5 Post-migration support (3 months)

3. TIMELINE

Phase 1: Discovery and Planning — 4 weeks
Phase 2: Architecture and Design — 6 weeks
Phase 3: Development and Migration — 12 weeks
Phase 4: Testing and UAT — 4 weeks
Phase 5: Go-Live and Hypercare — 4 weeks

Total Duration: 30 weeks

--- Page 3 ---
4. COMMERCIAL TERMS

4.1 Total contract value: $750,000
4.2 Payment milestones:
  - 20% upon signing
  - 30% upon completion of Phase 2
  - 30% upon Go-Live
  - 20% upon completion of Hypercare

4.3 Rate card:
  - Solution Architect: $250/hour
  - Senior Developer: $200/hour
  - Data Engineer: $180/hour
  - Project Manager: $175/hour

--- Page 4 ---
5. LEGAL TERMS

5.1 Indemnification: Vendor shall indemnify Client against all claims.
5.2 IP Ownership: All deliverables become property of Client.
5.3 Termination: Either party may terminate with 30 days written notice.
5.4 Governing Law: State of California, United States.
5.5 Confidentiality: Standard NDA terms apply for 2 years post-engagement.
"""


def _mock_llm_response():
    """Create a mock LLM response with sample findings."""
    return json.dumps([
        {
            "finding": "Indemnification clause is one-sided",
            "risk_level": "HIGH",
            "confidence": 0.88,
            "page_reference": "Page 4, Section 5.1",
            "recommendation": "Negotiate mutual indemnification"
        },
        {
            "finding": "Termination notice period is reasonable",
            "risk_level": "LOW",
            "confidence": 0.92,
            "page_reference": "Page 4, Section 5.3",
            "recommendation": "No action needed"
        }
    ])


class TestReviewPipeline:
    """Integration tests for the full review pipeline."""

    @patch("backend.agents.legal_agent.LegalAgent.invoke_llm")
    @patch("backend.agents.financial_agent.FinancialAgent.invoke_llm")
    @patch("backend.agents.technical_agent.TechnicalAgent.invoke_llm")
    @patch("backend.agents.risk_agent.RiskAgent.invoke_llm")
    @patch("backend.agents.delivery_agent.DeliveryAgent.invoke_llm")
    def test_full_pipeline_produces_complete_result(
        self,
        mock_delivery,
        mock_risk,
        mock_technical,
        mock_financial,
        mock_legal,
    ):
        """Full pipeline should produce a complete result with all agent findings."""
        # Mock all LLM responses
        mock_legal.return_value = _mock_llm_response()
        mock_financial.return_value = _mock_llm_response()
        mock_technical.return_value = _mock_llm_response()
        mock_risk.return_value = _mock_llm_response()
        mock_delivery.return_value = _mock_llm_response()

        result = run_review(
            sow_text=SAMPLE_SOW_TEXT,
            filename="test_sow.pdf",
            review_id="test-review-001",
        )

        # Verify structure
        assert result["review_id"] == "test-review-001"
        assert result["filename"] == "test_sow.pdf"
        assert result["status"] == "complete"

        # Verify all agents produced findings
        assert len(result.get("legal_findings", [])) > 0
        assert len(result.get("financial_findings", [])) > 0
        assert len(result.get("technical_findings", [])) > 0
        assert len(result.get("risk_findings", [])) > 0
        assert len(result.get("delivery_findings", [])) > 0

        # Verify synthesis
        assert result.get("overall_risk_score") is not None
        assert 0.0 <= result["overall_risk_score"] <= 10.0
        assert result.get("summary") is not None
        assert len(result["summary"]) > 0

    @patch("backend.agents.legal_agent.LegalAgent.invoke_llm")
    @patch("backend.agents.financial_agent.FinancialAgent.invoke_llm")
    @patch("backend.agents.technical_agent.TechnicalAgent.invoke_llm")
    @patch("backend.agents.risk_agent.RiskAgent.invoke_llm")
    @patch("backend.agents.delivery_agent.DeliveryAgent.invoke_llm")
    def test_pipeline_handles_agent_errors_gracefully(
        self,
        mock_delivery,
        mock_risk,
        mock_technical,
        mock_financial,
        mock_legal,
    ):
        """Pipeline should handle individual agent failures gracefully."""
        mock_legal.return_value = _mock_llm_response()
        mock_financial.side_effect = Exception("API rate limit exceeded")
        mock_technical.return_value = _mock_llm_response()
        mock_risk.return_value = _mock_llm_response()
        mock_delivery.return_value = _mock_llm_response()

        result = run_review(
            sow_text=SAMPLE_SOW_TEXT,
            filename="test_sow.pdf",
            review_id="test-review-002",
        )

        # Pipeline should still complete (agent errors are caught)
        assert result["status"] in ("complete", "error")

        # Legal should have findings from successful run
        assert len(result.get("legal_findings", [])) > 0

        # Financial should have error findings
        financial = result.get("financial_findings", [])
        assert len(financial) > 0

    def test_pipeline_with_empty_text(self):
        """Pipeline should handle empty SOW text."""
        result = run_review(
            sow_text="",
            filename="empty.pdf",
            review_id="test-review-003",
        )

        # Should complete with error status
        assert result["status"] in ("error", "complete")
