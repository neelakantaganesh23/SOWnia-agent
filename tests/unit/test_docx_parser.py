"""Unit tests for DOCX parser.

Tests DOCX magic byte validation.
"""

import pytest
from backend.parsers.docx_parser import DOCXParser


class TestDOCXParser:
    """Tests for the DOCXParser class."""

    def test_validate_file_valid_docx(self):
        """DOCX (ZIP) magic bytes should pass validation."""
        docx_bytes = b"PK\x03\x04 fake docx content"
        assert DOCXParser.validate_file(docx_bytes) is True

    def test_validate_file_invalid_docx(self):
        """Non-DOCX content should fail validation."""
        txt_bytes = b"This is a text file"
        assert DOCXParser.validate_file(txt_bytes) is False

    def test_validate_file_pdf_bytes(self):
        """PDF magic bytes should fail DOCX validation."""
        pdf_bytes = b"%PDF-1.7 fake content"
        assert DOCXParser.validate_file(pdf_bytes) is False

    def test_validate_file_empty(self):
        """Empty bytes should fail validation."""
        assert DOCXParser.validate_file(b"") is False

    def test_extract_text_invalid_docx_raises(self):
        """Extracting text from non-DOCX should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid DOCX file"):
            DOCXParser.extract_text(b"not a docx file")

    def test_extract_sections_invalid_raises(self):
        """Extracting sections from non-DOCX should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid DOCX file"):
            DOCXParser.extract_sections(b"not a docx file")

    def test_extract_text_corrupt_raises(self):
        """Corrupted DOCX content should raise RuntimeError."""
        corrupt_docx = b"PK\x03\x04 this is corrupt"
        with pytest.raises(RuntimeError, match="DOCX text extraction failed"):
            DOCXParser.extract_text(corrupt_docx)
