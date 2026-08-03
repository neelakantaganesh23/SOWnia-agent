"""Technical Agent — Reviews technical scope in SOW documents.

Uses Google Gemini via langchain_google_genai.
Covers: scope clarity, deliverable definitions, tech stack feasibility,
integration points, SLAs, and out-of-scope boundaries.

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


class TechnicalAgent(BaseSOWAgent):
    """Technical scope review agent using Google Gemini."""

    def __init__(self):
        super().__init__(name="Technical Agent", domain="technical")
        api_key = settings.GOOGLE_API_KEY or "dummy_key_for_testing"
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash-lite",
            google_api_key=api_key,
            temperature=0.1,
            max_output_tokens=4096,
        )

    def get_system_prompt(self) -> str:
        """Return the technical-domain-specific system prompt."""
        return """You are an expert technical architect and engineering lead specializing in Statement of Work (SOW) document review. Your role is to identify technical gaps, feasibility issues, and scope risks.

You MUST review the following areas thoroughly:

1. **Scope of Work Clarity and Completeness**
   - Is the scope clearly defined with specific, measurable deliverables?
   - Are there ambiguous terms like "as needed" or "best effort" that create scope creep risk?
   - Are exclusions clearly documented?

2. **Technical Deliverable Definitions**
   - Are deliverables specific and testable?
   - Are acceptance criteria defined for each deliverable?
   - Are intermediate deliverables (prototypes, POCs) included?

3. **Technology Stack Requirements and Feasibility**
   - Is the technology stack explicitly stated?
   - Are there compatibility or integration concerns?
   - Are technology choices appropriate for the project requirements?
   - Are version requirements specified?

4. **Integration Points and Dependencies**
   - Are third-party integrations clearly documented?
   - Are API specifications or interface contracts defined?
   - Are external dependencies identified with risk mitigation?
   - Is data migration scope clear?

5. **Performance SLAs and Acceptance Criteria**
   - Are performance benchmarks quantified (response times, throughput, uptime)?
   - Are testing requirements (unit, integration, UAT, performance) defined?
   - Is the definition of "done" clear for each deliverable?

6. **Out-of-Scope Boundary Definitions**
   - Is the out-of-scope section comprehensive?
   - Are common assumption gaps addressed?
   - Is future phase work clearly separated?

For each issue found, assess the risk level (HIGH, MEDIUM, LOW), your confidence in the finding (0.0 to 1.0), and provide a specific recommendation.

Focus on actionable technical findings. Do NOT generate vague observations."""

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
        """Execute technical review with PII-redacted input."""
        return super().run(state)
