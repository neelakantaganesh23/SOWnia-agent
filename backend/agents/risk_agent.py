"""Risk Agent — Identifies risks in SOW documents.

Uses Google Gemini via langchain_google_genai.
Covers: ambiguous deliverables, unrealistic timelines, vague criteria,
single points of failure, compliance risks, and data security.

NOTE: PII redaction is still applied as a defense-in-depth measure
before sending text to the LLM.
"""

import logging
from typing import Any, Dict

from langchain_google_genai import ChatGoogleGenerativeAI

from backend.agents.base_agent import BaseSOWAgent
from backend.config import settings
from backend.orchestrator.state import SOWReviewState
from backend.utils.pii_redactor import PIIRedactor

logger = logging.getLogger(__name__)


class RiskAgent(BaseSOWAgent):
    """Risk identification agent using Google Gemini."""

    def __init__(self):
        super().__init__(name="Risk Agent", domain="risk")
        api_key = settings.GOOGLE_API_KEY or "dummy_key_for_testing"
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash-lite",
            google_api_key=api_key,
            temperature=0.1,
            max_output_tokens=4096,
        )

    def get_system_prompt(self) -> str:
        """Return the risk-domain-specific system prompt."""
        return """You are an expert risk analyst specializing in project risk assessment for Statement of Work (SOW) documents. Your role is to identify hidden risks, potential issues, and red flags that could lead to project failure.

You MUST review the following areas thoroughly:

1. **Ambiguous or Missing Deliverable Definitions**
   - Are any deliverables vaguely defined or missing entirely?
   - Are there terms like "etc.", "and more", "as applicable" that create ambiguity?
   - Are assumptions documented and reasonable?

2. **Unrealistic Timelines**
   - Are project timelines achievable given the scope?
   - Are there dependencies that could cause cascading delays?
   - Is buffer time included for unexpected issues?
   - Are parallel workstream conflicts identified?

3. **Vague Success Criteria**
   - Are success metrics quantifiable and measurable?
   - Is "completion" clearly defined for each phase/deliverable?
   - Are sign-off procedures documented?

4. **Single Points of Failure**
   - Are there key person dependencies?
   - Is knowledge transfer planned?
   - Are backup resources identified?
   - Is vendor lock-in a concern?

5. **Compliance and Regulatory Risks**
   - Are industry-specific regulations addressed (GDPR, HIPAA, SOC2, etc.)?
   - Are audit and compliance requirements documented?
   - Are data handling procedures defined?

6. **Data Security and Privacy Obligations**
   - Are data classification requirements specified?
   - Are data retention and destruction policies defined?
   - Are encryption and access control requirements addressed?
   - Is cross-border data transfer addressed?

For each risk found, assess the risk level (HIGH, MEDIUM, LOW), your confidence in the assessment (0.0 to 1.0), and provide a specific mitigation recommendation.

Focus on real project risks. Prioritize findings by potential impact."""

    def invoke_llm(self, text: str) -> str:
        """Send text to Gemini and return response.

        Applies PII redaction before sending to the LLM as a
        defense-in-depth measure.
        """
        api_key = settings.GOOGLE_API_KEY
        if not api_key or "your_" in api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable is missing or invalid. "
                "Please set your Google Gemini API key in .env"
            )

        # Redact PII before sending (defense-in-depth)
        redacted_text = PIIRedactor.redact(text)

        llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash-lite",
            google_api_key=api_key,
            temperature=0.1,
            max_output_tokens=4096,
        )
        messages = [
            ("system", self.get_system_prompt()),
            ("human", redacted_text),
        ]
        response = llm.invoke(messages)
        return self._normalize_content(response.content)

    def run(self, state: SOWReviewState) -> Dict[str, Any]:
        """Execute risk review with PII-redacted input."""
        return super().run(state)
