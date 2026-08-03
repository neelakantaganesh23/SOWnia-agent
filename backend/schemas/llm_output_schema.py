"""Pydantic models for structured LLM output parsing.

These models define the exact JSON schema that each agent's LLM
must produce.  They are used in two ways:

1. **Prompt engineering** — The schema is injected into the user
   prompt so the LLM knows *exactly* what structure to produce.
2. **Response validation** — The raw JSON text from the LLM is
   parsed and validated with ``AgentLLMOutput.model_validate_json()``,
   giving strict type-checking, range-clamping, and clear error
   messages on malformed output.
"""

import json
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class FindingItem(BaseModel):
    """A single finding produced by an LLM agent."""

    finding: str = Field(
        ...,
        min_length=1,
        description="A clear, specific description of the issue or observation.",
    )
    risk_level: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        ...,
        description='Severity level — must be exactly one of "HIGH", "MEDIUM", or "LOW".',
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 (no confidence) and 1.0 (certain).",
    )
    page_reference: Optional[str] = Field(
        None,
        description=(
            'Page or section reference in the SOW (e.g. "Page 3, Section 4.2"). '
            "Use null if unknown."
        ),
    )
    recommendation: str = Field(
        ...,
        min_length=1,
        description="A specific, actionable recommendation to address this finding.",
    )

    # ── Validators ───────────────────────────────────────────────────────

    @field_validator("risk_level", mode="before")
    @classmethod
    def normalize_risk_level(cls, v: str) -> str:
        """Accept common synonyms and normalise to HIGH / MEDIUM / LOW."""
        mapping = {
            "CRITICAL": "HIGH",
            "SEVERE": "HIGH",
            "MODERATE": "MEDIUM",
            "MED": "MEDIUM",
            "MINOR": "LOW",
            "MINIMAL": "LOW",
        }
        upper = str(v).upper().strip()
        return mapping.get(upper, upper)

    @field_validator("confidence", mode="before")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        """Clamp the value into [0, 1] to be forgiving of LLM drift."""
        try:
            return max(0.0, min(1.0, float(v)))
        except (TypeError, ValueError):
            return 0.5


class AgentLLMOutput(BaseModel):
    """Top-level wrapper expected from every agent LLM call.

    The LLM MUST return a JSON object with a single key ``"findings"``
    containing an array of ``FindingItem`` objects.
    """

    findings: List[FindingItem] = Field(
        ...,
        min_length=0,
        description="Array of findings produced by the agent.",
    )

    # ── Convenience ──────────────────────────────────────────────────────

    @classmethod
    def json_schema_prompt_block(cls) -> str:
        """Return a human-readable JSON-schema block for prompt injection."""
        schema = cls.model_json_schema()
        return json.dumps(schema, indent=2)
