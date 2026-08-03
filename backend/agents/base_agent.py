"""Abstract base class for all SOW review agents.

Provides common functionality: retry logic with exponential backoff,
structured response parsing, and a standard interface for the
LangGraph orchestrator.
"""

import json
import logging
import re
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from backend.orchestrator.state import AgentFinding, SOWReviewState
from backend.schemas.llm_output_schema import AgentLLMOutput, FindingItem

logger = logging.getLogger(__name__)

# Default retry configuration
MAX_RETRIES = 3
BASE_DELAY_SECONDS = 2.0


class BaseSOWAgent(ABC):
    """Abstract base class for all specialized SOW review agents.

    Each agent implements domain-specific review logic using an LLM,
    parses the response into structured AgentFinding objects, and
    updates the shared SOWReviewState.
    """

    def __init__(self, name: str, domain: str):
        """Initialize the agent.

        Args:
            name: Human-readable agent name (e.g., 'Legal Agent').
            domain: Review domain key (e.g., 'legal', 'financial').
        """
        self.name = name
        self.domain = domain
        self.logger = logging.getLogger(f"sownia.agents.{domain}")

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the domain-specific system prompt.

        The prompt should instruct the LLM on what aspects of the SOW
        to review and how to format its findings.

        Returns:
            System prompt string.
        """
        pass

    @abstractmethod
    def invoke_llm(self, text: str) -> str:
        """Send text to the LLM and return the raw response.

        Args:
            text: SOW text (or chunk) to review.

        Returns:
            Raw LLM response string.
        """
        pass

    @staticmethod
    def _normalize_content(content) -> str:
        """Convert LLM response content to a plain string.

        langchain_google_genai can return response.content as a list
        of content-part dicts, e.g. [{'type': 'text', 'text': '...'}].
        This method extracts the actual text from those parts.

        Args:
            content: response.content — may be str, list[dict], or list[str].

        Returns:
            Plain text string.
        """
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, dict) and "text" in part:
                    parts.append(part["text"])
                elif hasattr(part, "text"):
                    parts.append(part.text)
                else:
                    parts.append(str(part))
            return "\n".join(parts)
        return str(content)

    def get_user_prompt(self, sow_text: str) -> str:
        """Build the user prompt with the SOW text.

        Uses strong prompt engineering techniques:
        - Explicit JSON schema from the Pydantic model
        - Negative constraints to prevent common LLM formatting issues
        - Output anchoring to force strict JSON-only responses
        - Few-shot example matching the exact schema

        Args:
            sow_text: Full SOW text to review.

        Returns:
            User prompt string.
        """
        schema_block = AgentLLMOutput.json_schema_prompt_block()

        return f"""You are performing a structured review of a Statement of Work (SOW) document.
Analyse the document below and produce your findings.

═══════════════════════════════════════════════════
SOW DOCUMENT
═══════════════════════════════════════════════════
{sow_text}
═══════════════════════════════════════════════════

## OUTPUT REQUIREMENTS (CRITICAL — read carefully)

You MUST respond with **exactly one** valid JSON object that conforms to the schema below.

### JSON Schema
```json
{schema_block}
```

### Rules
1. Return ONLY the JSON object. No markdown fences, no commentary, no preamble.
2. The root object MUST have a single key `"findings"` containing an array.
3. Each element in `"findings"` MUST include ALL of these fields:
   - `"finding"` (string)   — a clear, specific description of the issue
   - `"risk_level"` (string) — exactly one of `"HIGH"`, `"MEDIUM"`, or `"LOW"`
   - `"confidence"` (number) — a float between 0.0 and 1.0
   - `"page_reference"` (string or null) — the page/section reference, or null
   - `"recommendation"` (string) — a specific, actionable recommendation
4. Do NOT wrap the JSON in ```json``` code blocks.
5. Do NOT include any text before or after the JSON object.
6. If you find no issues, return: {{"findings": []}}
7. Focus on real, actionable findings. Do NOT generate generic advice.

### Example (for format reference only)
{{
  "findings": [
    {{
      "finding": "No liability cap is defined for the vendor, exposing the client to unlimited financial risk.",
      "risk_level": "HIGH",
      "confidence": 0.92,
      "page_reference": "Page 5, Section 7.3",
      "recommendation": "Add a mutual liability cap equal to the total contract value, with carve-outs for IP infringement and data breaches."
    }},
    {{
      "finding": "Payment milestones are not tied to specific deliverable acceptance criteria.",
      "risk_level": "MEDIUM",
      "confidence": 0.78,
      "page_reference": "Page 3, Section 4.1",
      "recommendation": "Link each payment milestone to a named deliverable with explicit acceptance criteria and sign-off process."
    }}
  ]
}}

Now analyse the SOW and return your JSON response."""

    def parse_response(self, response: str) -> List[AgentFinding]:
        """Parse LLM response into structured AgentFinding list.

        Uses Pydantic validation for type-safe parsing with fallback
        to regex extraction for malformed responses.

        Args:
            response: Raw LLM response string.

        Returns:
            List of AgentFinding dicts.
        """
        if not response:
            self.logger.warning(f"{self.name}: Empty response received.")
            return []

        # Ensure response is a plain string
        response = self._normalize_content(response)

        # ── Step 1: Try direct Pydantic parse ────────────────────────────
        json_str = self._extract_json(response)
        if json_str:
            try:
                parsed = AgentLLMOutput.model_validate_json(json_str)
                self.logger.info(
                    f"{self.name}: Pydantic parsed {len(parsed.findings)} findings."
                )
                return self._to_agent_findings(parsed.findings)
            except ValidationError as e:
                self.logger.warning(
                    f"{self.name}: Pydantic validation failed, "
                    f"trying legacy parse. Errors: {e.error_count()}"
                )

        # ── Step 2: Legacy fallback — raw JSON array parse ───────────────
        try:
            if json_str:
                raw = json.loads(json_str)
            else:
                raw = json.loads(response)

            # Handle {"findings": [...]} wrapper
            if isinstance(raw, dict) and "findings" in raw:
                raw = raw["findings"]

            if not isinstance(raw, list):
                raw = [raw]

            findings: List[AgentFinding] = []
            for item in raw:
                finding: AgentFinding = {
                    "agent": self.name,
                    "domain": self.domain,
                    "finding": str(item.get("finding", "No description provided")),
                    "risk_level": self._normalize_risk_level(
                        str(item.get("risk_level", "MEDIUM"))
                    ),
                    "confidence": self._normalize_confidence(
                        item.get("confidence", 0.5)
                    ),
                    "page_reference": item.get("page_reference"),
                    "recommendation": str(
                        item.get("recommendation", "Review this finding manually.")
                    ),
                }
                findings.append(finding)

            self.logger.info(
                f"{self.name}: Legacy parsed {len(findings)} findings from response."
            )
            return findings

        except (json.JSONDecodeError, AttributeError, TypeError) as e:
            self.logger.error(f"{self.name}: All parse attempts failed: {e}")
            return self._create_fallback_finding(response)

    def _extract_json(self, text: str) -> Optional[str]:
        """Extract JSON from LLM response, handling markdown fences and bare JSON.

        Args:
            text: Raw LLM response.

        Returns:
            Extracted JSON string, or None if nothing found.
        """
        # Try markdown code blocks first
        json_match = re.search(
            r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL
        )
        if json_match:
            return json_match.group(1).strip()

        # Try to find a JSON object ({"findings": [...]})
        obj_match = re.search(r"\{.*\}", text, re.DOTALL)
        if obj_match:
            return obj_match.group(0)

        # Try to find a JSON array ([...])
        array_match = re.search(r"\[.*\]", text, re.DOTALL)
        if array_match:
            # Wrap bare array in the expected schema
            return f'{{"findings": {array_match.group(0)}}}'

        return None

    def _to_agent_findings(self, items: List[FindingItem]) -> List[AgentFinding]:
        """Convert Pydantic FindingItem list to AgentFinding TypedDict list."""
        return [
            {
                "agent": self.name,
                "domain": self.domain,
                "finding": item.finding,
                "risk_level": item.risk_level,
                "confidence": item.confidence,
                "page_reference": item.page_reference,
                "recommendation": item.recommendation,
            }
            for item in items
        ]

    def _normalize_risk_level(self, level: str) -> str:
        """Normalize risk level to one of HIGH, MEDIUM, LOW."""
        level_upper = level.upper().strip()
        if level_upper in ("HIGH", "CRITICAL", "SEVERE"):
            return "HIGH"
        elif level_upper in ("MEDIUM", "MODERATE", "MED"):
            return "MEDIUM"
        elif level_upper in ("LOW", "MINOR", "MINIMAL"):
            return "LOW"
        return "MEDIUM"

    def _normalize_confidence(self, confidence: Any) -> float:
        """Normalize confidence to a float between 0.0 and 1.0."""
        try:
            conf = float(confidence)
            return max(0.0, min(1.0, conf))
        except (TypeError, ValueError):
            return 0.5

    def _create_fallback_finding(self, raw_response: str) -> List[AgentFinding]:
        """Create a fallback finding when parsing fails."""
        # Truncate long responses
        truncated = raw_response[:500] + "..." if len(raw_response) > 500 else raw_response
        return [
            {
                "agent": self.name,
                "domain": self.domain,
                "finding": f"Agent provided unstructured analysis: {truncated}",
                "risk_level": "MEDIUM",
                "confidence": 0.3,
                "page_reference": None,
                "recommendation": "Review the raw agent output manually for detailed findings.",
            }
        ]

    def run_with_retry(self, text: str) -> str:
        """Invoke the LLM with exponential backoff retry logic.

        Args:
            text: Text to send to the LLM.

        Returns:
            LLM response string.

        Raises:
            RuntimeError: If all retries are exhausted.
        """
        last_error: Optional[Exception] = None

        for attempt in range(MAX_RETRIES):
            try:
                response = self.invoke_llm(text)
                return response
            except Exception as e:
                last_error = e
                delay = BASE_DELAY_SECONDS * (2**attempt)
                self.logger.warning(
                    f"{self.name}: Attempt {attempt + 1}/{MAX_RETRIES} failed: {e}. "
                    f"Retrying in {delay}s..."
                )
                time.sleep(delay)

        raise RuntimeError(
            f"{self.name}: All {MAX_RETRIES} attempts failed. "
            f"Last error: {last_error}"
        )

    def run(self, state: SOWReviewState) -> Dict[str, Any]:
        """Execute review and return state updates.

        This is the main entry point called by the LangGraph orchestrator.
        It sends the SOW text to the LLM, parses the findings, and
        returns a dict of state updates.

        Args:
            state: Current SOWReviewState.

        Returns:
            Dict with state updates (e.g., {'legal_findings': [...]}).
        """
        findings_key = f"{self.domain}_findings"

        try:
            self.logger.info(f"{self.name}: Starting review...")
            sow_text = state.get("sow_text", "")

            if not sow_text:
                self.logger.error(f"{self.name}: No SOW text provided.")
                return {
                    findings_key: [
                        {
                            "agent": self.name,
                            "domain": self.domain,
                            "finding": "No SOW text was provided for review.",
                            "risk_level": "HIGH",
                            "confidence": 1.0,
                            "page_reference": None,
                            "recommendation": "Ensure the SOW document is uploaded and parsed correctly.",
                        }
                    ]
                }

            # Build the full prompt
            user_prompt = self.get_user_prompt(sow_text)

            # Call LLM with retry
            response = self.run_with_retry(user_prompt)

            # Parse response into findings
            findings = self.parse_response(response)

            self.logger.info(
                f"{self.name}: Completed with {len(findings)} findings."
            )
            return {findings_key: findings}

        except Exception as e:
            self.logger.error(f"{self.name}: Review failed: {e}")
            return {
                findings_key: [
                    {
                        "agent": self.name,
                        "domain": self.domain,
                        "finding": f"Agent encountered an error: {str(e)}",
                        "risk_level": "HIGH",
                        "confidence": 0.1,
                        "page_reference": None,
                        "recommendation": "Retry the review or check agent configuration.",
                    }
                ]
            }
