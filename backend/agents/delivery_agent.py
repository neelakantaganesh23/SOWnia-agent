"""Delivery Agent — Reviews delivery timelines in SOW documents.

Uses Google Gemini 1.5 Flash via langchain_google_genai.
Covers: timeline realism, resource allocation, dependencies,
change management, governance, and escalation paths.
"""

import logging
from typing import Any, Dict

from langchain_google_genai import ChatGoogleGenerativeAI

from backend.agents.base_agent import BaseSOWAgent
from backend.config import settings
from backend.orchestrator.state import SOWReviewState

logger = logging.getLogger(__name__)


class DeliveryAgent(BaseSOWAgent):
    """Delivery timeline review agent using Gemini 1.5 Flash."""

    def __init__(self):
        super().__init__(name="Delivery Agent", domain="delivery")
        api_key = settings.GOOGLE_API_KEY or "dummy_key_for_testing"
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash-lite",
            google_api_key=api_key,
            temperature=0.1,
            max_output_tokens=4096,
        )

    def get_system_prompt(self) -> str:
        """Return the delivery-domain-specific system prompt."""
        return """You are an expert project delivery manager and PMO lead specializing in Statement of Work (SOW) document review. Your role is to identify delivery risks, timeline issues, and governance gaps.

You MUST review the following areas thoroughly:

1. **Project Timeline and Milestone Realism**
   - Are project phases and milestones clearly defined with dates?
   - Are timelines realistic given the scope and complexity?
   - Are there buffer periods between major milestones?
   - Is the critical path identified?

2. **Resource Allocation and Staffing Requirements**
   - Are required roles and skill levels specified?
   - Is the number of resources per phase defined?
   - Are onboarding and ramp-up periods accounted for?
   - Are client-side resource commitments documented?

3. **Dependencies and Critical Path Risks**
   - Are inter-task dependencies documented?
   - Are external dependencies (client approvals, third-party deliveries) identified?
   - Are dependency risk mitigations in place?
   - Is a dependency matrix or RACI chart referenced?

4. **Change Management Procedures**
   - Is there a formal change request process?
   - Are impact assessment procedures defined for changes?
   - Are change approval authorities documented?
   - Is there a scope freeze period?

5. **Reporting and Governance Cadence**
   - Are reporting frequencies defined (weekly, bi-weekly, monthly)?
   - Are status report formats and content requirements specified?
   - Are steering committee meetings scheduled?
   - Are KPIs and progress metrics defined?

6. **Escalation Paths**
   - Is a clear escalation hierarchy documented?
   - Are escalation triggers and timelines defined?
   - Are both client-side and vendor-side escalation contacts listed?
   - Is there an issue resolution SLA?

For each issue found, assess the risk level (HIGH, MEDIUM, LOW), your confidence in the finding (0.0 to 1.0), and provide a specific recommendation.

Focus on practical delivery risks. Do NOT flag well-structured project plans unnecessarily."""

    def invoke_llm(self, text: str) -> str:
        """Send text to Gemini 1.5 Flash and return response."""
        api_key = settings.GOOGLE_API_KEY
        if not api_key or "your_" in api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is missing or invalid. Please set your Google Gemini API key in .env")

        llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash-lite",
            google_api_key=api_key,
            temperature=0.1,
            max_output_tokens=4096,
        )
        messages = [
            ("system", self.get_system_prompt()),
            ("human", text),
        ]
        response = llm.invoke(messages)
        return self._normalize_content(response.content)

    def run(self, state: SOWReviewState) -> Dict[str, Any]:
        """Execute delivery review and return state updates."""
        return super().run(state)
