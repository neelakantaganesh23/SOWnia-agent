"""Unit tests for agent response parsing.

Tests the BaseSOWAgent's parse_response method with various
LLM response formats to ensure robust finding extraction.
"""

import pytest
from backend.agents.base_agent import BaseSOWAgent
from backend.orchestrator.state import SOWReviewState


class ConcreteTestAgent(BaseSOWAgent):
    """Concrete implementation of BaseSOWAgent for testing."""

    def __init__(self):
        super().__init__(name="Test Agent", domain="test")

    def get_system_prompt(self) -> str:
        return "You are a test agent."

    def invoke_llm(self, text: str) -> str:
        return "[]"


class TestAgentParsing:
    """Tests for agent response parsing logic."""

    def setup_method(self):
        """Create a test agent instance."""
        self.agent = ConcreteTestAgent()

    def test_parse_valid_json_array(self):
        """Valid JSON array should parse correctly."""
        response = '''[
            {
                "finding": "Missing indemnification clause",
                "risk_level": "HIGH",
                "confidence": 0.92,
                "page_reference": "Page 4, Section 6.2",
                "recommendation": "Add mutual indemnification"
            }
        ]'''
        findings = self.agent.parse_response(response)
        assert len(findings) == 1
        assert findings[0]["finding"] == "Missing indemnification clause"
        assert findings[0]["risk_level"] == "HIGH"
        assert findings[0]["confidence"] == 0.92
        assert findings[0]["agent"] == "Test Agent"
        assert findings[0]["domain"] == "test"

    def test_parse_json_in_markdown_code_block(self):
        """JSON wrapped in markdown code block should parse."""
        response = '''Here are my findings:
```json
[
    {
        "finding": "Test finding",
        "risk_level": "MEDIUM",
        "confidence": 0.75,
        "page_reference": null,
        "recommendation": "Test recommendation"
    }
]
```
'''
        findings = self.agent.parse_response(response)
        assert len(findings) == 1
        assert findings[0]["finding"] == "Test finding"
        assert findings[0]["risk_level"] == "MEDIUM"

    def test_parse_multiple_findings(self):
        """Multiple findings in a JSON array should all parse."""
        response = '''[
            {"finding": "Issue 1", "risk_level": "HIGH", "confidence": 0.9, "page_reference": "Page 1", "recommendation": "Fix 1"},
            {"finding": "Issue 2", "risk_level": "LOW", "confidence": 0.6, "page_reference": "Page 2", "recommendation": "Fix 2"},
            {"finding": "Issue 3", "risk_level": "MEDIUM", "confidence": 0.8, "page_reference": null, "recommendation": "Fix 3"}
        ]'''
        findings = self.agent.parse_response(response)
        assert len(findings) == 3
        assert findings[0]["risk_level"] == "HIGH"
        assert findings[1]["risk_level"] == "LOW"
        assert findings[2]["risk_level"] == "MEDIUM"

    def test_parse_empty_response(self):
        """Empty response should return empty list."""
        findings = self.agent.parse_response("")
        assert findings == []

    def test_parse_non_json_response_creates_fallback(self):
        """Non-JSON response should create a fallback finding."""
        response = "This is not JSON, just plain text analysis."
        findings = self.agent.parse_response(response)
        assert len(findings) == 1
        assert findings[0]["risk_level"] == "MEDIUM"
        assert findings[0]["confidence"] == 0.3

    def test_normalize_risk_level_variants(self):
        """Various risk level strings should normalize correctly."""
        assert self.agent._normalize_risk_level("HIGH") == "HIGH"
        assert self.agent._normalize_risk_level("high") == "HIGH"
        assert self.agent._normalize_risk_level("CRITICAL") == "HIGH"
        assert self.agent._normalize_risk_level("MEDIUM") == "MEDIUM"
        assert self.agent._normalize_risk_level("MODERATE") == "MEDIUM"
        assert self.agent._normalize_risk_level("LOW") == "LOW"
        assert self.agent._normalize_risk_level("MINOR") == "LOW"
        assert self.agent._normalize_risk_level("UNKNOWN") == "MEDIUM"

    def test_normalize_confidence_clamps(self):
        """Confidence should be clamped to 0.0 - 1.0 range."""
        assert self.agent._normalize_confidence(0.5) == 0.5
        assert self.agent._normalize_confidence(1.5) == 1.0
        assert self.agent._normalize_confidence(-0.5) == 0.0
        assert self.agent._normalize_confidence("invalid") == 0.5

    def test_parse_single_object_not_array(self):
        """Single JSON object (not array) should still parse."""
        response = '''{
            "finding": "Single finding",
            "risk_level": "LOW",
            "confidence": 0.65,
            "page_reference": "Page 1",
            "recommendation": "Check this"
        }'''
        findings = self.agent.parse_response(response)
        assert len(findings) == 1
        assert findings[0]["finding"] == "Single finding"

    def test_parse_missing_fields_uses_defaults(self):
        """Missing fields should use sensible defaults."""
        response = '[{"finding": "Partial finding"}]'
        findings = self.agent.parse_response(response)
        assert len(findings) == 1
        assert findings[0]["finding"] == "Partial finding"
        assert findings[0]["risk_level"] == "MEDIUM"
        assert findings[0]["confidence"] == 0.5
        assert findings[0]["recommendation"] == "Review this finding manually."


class TestPIIRedactor:
    """Tests for PII redaction utility."""

    def test_redact_email(self):
        from backend.utils.pii_redactor import PIIRedactor

        text = "Contact john.doe@example.com for details."
        redacted = PIIRedactor.redact(text)
        assert "[EMAIL_REDACTED]" in redacted
        assert "john.doe@example.com" not in redacted

    def test_redact_phone(self):
        from backend.utils.pii_redactor import PIIRedactor

        text = "Call (555) 123-4567 for support."
        redacted = PIIRedactor.redact(text)
        assert "[PHONE_REDACTED]" in redacted

    def test_redact_preserves_non_pii(self):
        from backend.utils.pii_redactor import PIIRedactor

        text = "The contract value is $500,000 for 12 months."
        redacted = PIIRedactor.redact(text)
        assert "contract value" in redacted
        assert "$500,000" in redacted

    def test_detect_returns_found_pii(self):
        from backend.utils.pii_redactor import PIIRedactor

        text = "Email: test@test.com, Phone: +1-555-123-4567"
        found = PIIRedactor.detect(text)
        assert "EMAIL" in found


class TestSemanticChunker:
    """Tests for the semantic text chunker."""

    def test_chunk_empty_text(self):
        from backend.utils.chunker import SemanticChunker

        chunker = SemanticChunker()
        assert chunker.chunk("") == []
        assert chunker.chunk("   ") == []

    def test_chunk_short_text_single_chunk(self):
        from backend.utils.chunker import SemanticChunker

        chunker = SemanticChunker()
        text = "This is a short SOW document with minimal content."
        chunks = chunker.chunk(text)
        assert len(chunks) >= 1
        assert text.strip() in chunks[0]

    def test_chunk_preserves_page_markers(self):
        from backend.utils.chunker import SemanticChunker

        chunker = SemanticChunker()
        text = "--- Page 1 ---\nContent on page 1.\n\n--- Page 2 ---\nContent on page 2."
        chunks = chunker.chunk(text)
        assert len(chunks) >= 1
