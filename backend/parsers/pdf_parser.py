"""PDF text extraction using PyMuPDF (fitz).

Extracts text page-by-page from PDF documents, preserving page
markers for reference in agent findings.
"""

import io
import logging
from typing import List, Tuple

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class PDFParser:
    """Extract structured text from PDF documents using PyMuPDF."""

    # PDF magic bytes: %PDF
    MAGIC_BYTES = b"%PDF"

    @staticmethod
    def validate_file(file_bytes: bytes) -> bool:
        """Validate that the file is a genuine PDF by checking magic bytes.

        Args:
            file_bytes: Raw file content bytes.

        Returns:
            True if the file starts with PDF magic bytes.
        """
        return file_bytes[:4] == PDFParser.MAGIC_BYTES

    @staticmethod
    def _extract_page_text(page: fitz.Page) -> str:
        """Extract text from a single page using multiple extraction strategies.

        Args:
            page: PyMuPDF Page object.

        Returns:
            Extracted text for the page.
        """
        # Strategy 1: Standard text extraction
        text = page.get_text("text").strip()
        if text:
            return text

        # Strategy 2: Block-based extraction
        try:
            blocks = page.get_text("blocks")
            block_texts = [b[4].strip() for b in blocks if len(b) >= 5 and b[4].strip()]
            if block_texts:
                return "\n".join(block_texts)
        except Exception:
            pass

        # Strategy 3: Word-based extraction
        try:
            words = page.get_text("words")
            if words:
                # Sort words by line (y0) then column (x0)
                sorted_words = sorted(words, key=lambda w: (w[1], w[0]))
                word_texts = [w[4] for w in sorted_words if w[4].strip()]
                if word_texts:
                    return " ".join(word_texts)
        except Exception:
            pass

        # Strategy 4: HTML parsing fallback
        try:
            import re
            html_text = page.get_text("html")
            clean_text = re.sub(r"<[^>]+>", " ", html_text)
            clean_text = " ".join(clean_text.split())
            if clean_text:
                return clean_text
        except Exception:
            pass

        return ""

    @staticmethod
    def extract_text(file_bytes: bytes) -> str:
        """Extract full text from a PDF file.

        Args:
            file_bytes: Raw PDF file content.

        Returns:
            Extracted text with page markers (e.g., '--- Page 1 ---').

        Raises:
            ValueError: If file is not a valid PDF.
            RuntimeError: If text extraction fails.
        """
        if not PDFParser.validate_file(file_bytes):
            raise ValueError("Invalid PDF file: magic bytes do not match.")

        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            pages_text: List[str] = []

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = PDFParser._extract_page_text(page)

                if text:
                    pages_text.append(
                        f"--- Page {page_num + 1} ---\n{text}"
                    )

            doc.close()

            if not pages_text:
                logger.warning("PDF contained no extractable text.")
                return ""

            full_text = "\n\n".join(pages_text)
            logger.info(
                f"Extracted text from {len(pages_text)} pages "
                f"({len(full_text)} characters)."
            )
            return full_text

        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise RuntimeError(f"PDF text extraction failed: {e}") from e

    @staticmethod
    def extract_pages(file_bytes: bytes) -> List[Tuple[int, str]]:
        """Extract text from each page separately.

        Args:
            file_bytes: Raw PDF file content.

        Returns:
            List of (page_number, page_text) tuples.

        Raises:
            ValueError: If file is not a valid PDF.
        """
        if not PDFParser.validate_file(file_bytes):
            raise ValueError("Invalid PDF file: magic bytes do not match.")

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        pages: List[Tuple[int, str]] = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = PDFParser._extract_page_text(page)
            pages.append((page_num + 1, text))

        doc.close()
        return pages

    @staticmethod
    def get_page_count(file_bytes: bytes) -> int:
        """Get the number of pages in a PDF.

        Args:
            file_bytes: Raw PDF file content.

        Returns:
            Number of pages.
        """
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        count = len(doc)
        doc.close()
        return count
