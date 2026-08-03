"""PII detection and redaction utility.

Redacts personal names, email addresses, phone numbers, SSNs,
and other PII from SOW text before passing to LLM models.
Applied as a defense-in-depth measure by agents that handle
sensitive document content.
"""

import logging
import re
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class PIIRedactor:
    """Detect and redact PII from text using regex patterns.

    This provides a best-effort regex-based approach for PII redaction.
    For production use, consider integrating a dedicated NER model
    (e.g., spaCy NER, presidio) for higher accuracy.
    """

    # Compiled regex patterns for PII detection
    PATTERNS: List[Tuple[str, re.Pattern, str]] = [
        (
            "EMAIL",
            re.compile(
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
            ),
            "[EMAIL_REDACTED]",
        ),
        (
            "PHONE_US",
            re.compile(
                r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
            ),
            "[PHONE_REDACTED]",
        ),
        (
            "PHONE_INTL",
            re.compile(
                r"\b\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b"
            ),
            "[PHONE_REDACTED]",
        ),
        (
            "SSN",
            re.compile(r"\b\d{3}[-]?\d{2}[-]?\d{4}\b"),
            "[SSN_REDACTED]",
        ),
        (
            "CREDIT_CARD",
            re.compile(
                r"\b(?:\d{4}[-\s]?){3}\d{4}\b"
            ),
            "[CC_REDACTED]",
        ),
        (
            "IP_ADDRESS",
            re.compile(
                r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"
            ),
            "[IP_REDACTED]",
        ),
        (
            "DATE_OF_BIRTH",
            re.compile(
                r"\b(?:DOB|Date of Birth|D\.O\.B\.?)[\s:]*\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b",
                re.IGNORECASE,
            ),
            "[DOB_REDACTED]",
        ),
    ]

    # Common name prefixes that may indicate a person's name
    NAME_PREFIXES = [
        "Mr.", "Mrs.", "Ms.", "Dr.", "Prof.",
        "Mr ", "Mrs ", "Ms ", "Dr ", "Prof ",
    ]

    @classmethod
    def redact(cls, text: str) -> str:
        """Redact PII from text.

        Applies all regex patterns to detect and replace PII
        with redaction markers.

        Args:
            text: Raw text that may contain PII.

        Returns:
            Text with PII replaced by redaction markers.
        """
        if not text:
            return text

        redacted_text = text
        redaction_count: Dict[str, int] = {}

        # Apply regex patterns
        for pii_type, pattern, replacement in cls.PATTERNS:
            matches = pattern.findall(redacted_text)
            if matches:
                redaction_count[pii_type] = len(matches)
                redacted_text = pattern.sub(replacement, redacted_text)

        # Redact names following common prefixes
        for prefix in cls.NAME_PREFIXES:
            # Match prefix followed by 1-3 capitalized words
            name_pattern = re.compile(
                rf"({re.escape(prefix)})"
                r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})"
            )
            matches = name_pattern.findall(redacted_text)
            if matches:
                redaction_count["NAME"] = redaction_count.get("NAME", 0) + len(
                    matches
                )
                redacted_text = name_pattern.sub(
                    r"\1[NAME_REDACTED]", redacted_text
                )

        if redaction_count:
            logger.info(f"PII redaction summary: {redaction_count}")
        else:
            logger.debug("No PII detected in text.")

        return redacted_text

    @classmethod
    def detect(cls, text: str) -> Dict[str, List[str]]:
        """Detect PII in text without redacting.

        Useful for reporting what PII was found.

        Args:
            text: Text to scan for PII.

        Returns:
            Dictionary mapping PII types to lists of found values.
        """
        if not text:
            return {}

        found: Dict[str, List[str]] = {}

        for pii_type, pattern, _ in cls.PATTERNS:
            matches = pattern.findall(text)
            if matches:
                found[pii_type] = matches

        return found

    @classmethod
    def get_redaction_stats(cls, original: str, redacted: str) -> Dict[str, int]:
        """Compare original and redacted text to count redactions.

        Args:
            original: Original text.
            redacted: Redacted text.

        Returns:
            Dictionary with redaction statistics.
        """
        stats: Dict[str, int] = {}
        redaction_markers = [
            "[EMAIL_REDACTED]",
            "[PHONE_REDACTED]",
            "[SSN_REDACTED]",
            "[CC_REDACTED]",
            "[IP_REDACTED]",
            "[DOB_REDACTED]",
            "[NAME_REDACTED]",
        ]

        for marker in redaction_markers:
            count = redacted.count(marker)
            if count > 0:
                pii_type = marker.strip("[]").replace("_REDACTED", "")
                stats[pii_type] = count

        return stats
