"""Legal Agent — Reviews legal clauses in SOW documents.

Uses Google Gemini 1.5 Flash via langchain_google_genai.
Covers: indemnification, IP ownership, termination, governing law,
non-compete, and payment terms.
"""

import logging
from typing import Any, Dict

from langchain_google_genai import ChatGoogleGenerativeAI

from backend.agents.base_agent import BaseSOWAgent
from backend.config import settings
from backend.orchestrator.state import SOWReviewState

logger = logging.getLogger(__name__)


class LegalAgent(BaseSOWAgent):
    """Legal clause review agent using Gemini 1.5 Flash."""

    def __init__(self):
        super().__init__(name="Legal Agent", domain="legal")
        api_key = settings.GOOGLE_API_KEY or "dummy_key_for_testing"
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash-lite",
            google_api_key=api_key,
            temperature=0.1,
            max_output_tokens=4096,
        )

    def get_system_prompt(self) -> str:
        """Return the legal-domain-specific system prompt."""
        return """You are an expert legal analyst specializing in contract review for Statement of Work (SOW) documents. Your role is to identify legal risks, gaps, and issues in SOW documents.

You MUST review the following areas thoroughly:

1. **Indemnification and Liability Clauses**
   - Is indemnification mutual or one-sided?
   - Are liability caps defined? Are they reasonable?
   - Are there unlimited liability carve-outs?

2. **Intellectual Property Ownership**
   - Who owns the deliverables (work product)?
   - Are there IP assignment or license-back clauses?
   - Is pre-existing IP properly handled?
   - Are open-source usage terms addressed?

3. **Termination and Exit Clauses**
   - Can either party terminate for convenience?
   - What are the notice periods?
   - What happens to work-in-progress upon termination?
   - Are wind-down obligations clear?

4. **Governing Law and Jurisdiction**
   - Is governing law specified?
   - Is the jurisdiction reasonable for both parties?
   - Is there an arbitration or mediation clause?

5. **Non-Compete / Non-Solicitation Terms**
   - Are non-compete clauses present? Are they enforceable?
   - Are non-solicitation terms reasonable in scope and duration?

6. **Payment Terms and Penalties**
   - Are payment terms clearly defined (Net 30, Net 60, etc.)?
   - Are late payment penalties specified?
   - Are acceptance criteria for payment milestones clear?

For each issue found, assess the risk level (HIGH, MEDIUM, LOW), your confidence in the finding (0.0 to 1.0), and provide a specific recommendation.

Focus on real, actionable findings. Do NOT generate generic advice. If a section is well-drafted, do not flag it just to produce output."""

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
        """Execute legal review and return state updates."""
        return super().run(state)
