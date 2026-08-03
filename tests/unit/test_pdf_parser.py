"""Unit tests for PDF parser.

Tests PDF text extraction, magic byte validation, and error handling.
"""

import pytest
from backend.parsers.pdf_parser import PDFParser


class TestPDFParser:
    """Tests for the PDFParser class."""

    def test_validate_file_valid_pdf(self):
        """Valid PDF magic bytes should pass validation."""
        pdf_bytes = b"%PDF-1.7 fake content"
        assert PDFParser.validate_file(pdf_bytes) is True

    def test_validate_file_invalid_pdf(self):
        """Non-PDF content should fail validation."""
        txt_bytes = b"This is not a PDF file"
        assert PDFParser.validate_file(txt_bytes) is False

    def test_validate_file_empty(self):
        """Empty bytes should fail validation."""
        assert PDFParser.validate_file(b"") is False

    def test_validate_file_docx_bytes(self):
        """DOCX magic bytes should fail PDF validation."""
        docx_bytes = b"PK\x03\x04 fake docx"
        assert PDFParser.validate_file(docx_bytes) is False

    def test_extract_text_invalid_pdf_raises(self):
        """Extracting text from invalid PDF should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid PDF file"):
            PDFParser.extract_text(b"not a pdf")

    def test_extract_pages_invalid_pdf_raises(self):
        """Extracting pages from invalid PDF should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid PDF file"):
            PDFParser.extract_pages(b"not a pdf")

    def test_extract_text_valid_but_corrupt_raises(self):
        """Corrupted PDF content should raise RuntimeError."""
        # Valid magic bytes but corrupt content
        corrupt_pdf = b"%PDF-1.7 this is corrupt and not a real PDF"
        with pytest.raises(RuntimeError, match="PDF text extraction failed"):
            PDFParser.extract_text(corrupt_pdf)
