"""Financial Agent — Reviews financial terms in SOW documents.

Uses Google Gemini 1.5 Flash via langchain_google_genai.
Covers: contract value, rate cards, expenses, currency/tax,
change orders, and penalties.
"""

import logging
from typing import Any, Dict

from langchain_google_genai import ChatGoogleGenerativeAI

from backend.agents.base_agent import BaseSOWAgent
from backend.config import settings
from backend.orchestrator.state import SOWReviewState

logger = logging.getLogger(__name__)


class FinancialAgent(BaseSOWAgent):
    """Financial terms review agent using Gemini 1.5 Flash."""

    def __init__(self):
        super().__init__(name="Financial Agent", domain="financial")
        api_key = settings.GOOGLE_API_KEY or "dummy_key_for_testing"
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash-lite",
            google_api_key=api_key,
            temperature=0.1,
            max_output_tokens=4096,
        )

    def get_system_prompt(self) -> str:
        """Return the financial-domain-specific system prompt."""
        return """You are an expert financial analyst specializing in contract pricing and financial terms review for Statement of Work (SOW) documents. Your role is to identify financial risks, unclear terms, and pricing issues.

You MUST review the following areas thoroughly:

1. **Total Contract Value and Payment Milestones**
   - Is the total contract value clearly stated?
   - Are payment milestones defined and tied to deliverables?
   - Is the payment schedule realistic relative to the timeline?

2. **Rate Cards and Hourly Caps**
   - Are billing rates clearly defined for each role?
   - Are there hourly caps or time-and-materials limits?
   - Are overtime rates or premium rates addressed?
   - Are rate escalation terms for multi-year engagements included?

3. **Expense Reimbursement Terms**
   - Are reimbursable expenses clearly categorized?
   - Are expense caps or pre-approval requirements in place?
   - Are travel and accommodation policies defined?

4. **Currency and Tax Clauses**
   - Is the billing currency specified?
   - Are tax responsibilities (GST, VAT, withholding tax) clear?
   - Are currency fluctuation provisions included for international contracts?

5. **Change Order / Variation Pricing**
   - Is there a formal change order process?
   - Are pricing mechanisms for scope changes defined?
   - Are impact assessments required before approving changes?

6. **Penalties and Liquidated Damages**
   - Are penalty clauses reasonable and proportional?
   - Are liquidated damages capped?
   - Are force majeure exceptions addressed?
   - Are bonus/incentive clauses present for early delivery?

For each issue found, assess the risk level (HIGH, MEDIUM, LOW), your confidence in the finding (0.0 to 1.0), and provide a specific recommendation.

Focus on real financial risks. Do NOT flag well-structured financial terms unnecessarily."""

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
        """Execute financial review and return state updates."""
        return super().run(state)
