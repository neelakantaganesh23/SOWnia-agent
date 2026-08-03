"""Semantic text chunking utility for SOW documents.

Splits SOW text into meaningful sections based on headings,
paragraph breaks, and semantic boundaries. Target chunk size
is approximately 1000 tokens (~4000 characters).
"""

import logging
import re
from typing import List

logger = logging.getLogger(__name__)

# Approximate characters per token (English text)
CHARS_PER_TOKEN = 4
DEFAULT_CHUNK_SIZE_TOKENS = 1000
DEFAULT_CHUNK_OVERLAP_TOKENS = 100


class SemanticChunker:
    """Split SOW text into semantically meaningful chunks.

    The chunker first tries to split on document structure (headings, page
    markers), then falls back to paragraph boundaries, and finally to
    sentence boundaries if chunks are still too large.
    """

    def __init__(
        self,
        chunk_size_tokens: int = DEFAULT_CHUNK_SIZE_TOKENS,
        chunk_overlap_tokens: int = DEFAULT_CHUNK_OVERLAP_TOKENS,
    ):
        self.chunk_size_chars = chunk_size_tokens * CHARS_PER_TOKEN
        self.overlap_chars = chunk_overlap_tokens * CHARS_PER_TOKEN

    def chunk(self, text: str) -> List[str]:
        """Split text into semantically meaningful chunks.

        Strategy:
        1. Split by structural markers (page breaks, headings)
        2. Merge small sections together up to chunk_size
        3. Split oversized sections by paragraphs
        4. Apply overlap between chunks for context continuity

        Args:
            text: Full SOW document text.

        Returns:
            List of text chunks.
        """
        if not text or not text.strip():
            return []

        # Step 1: Split by structural markers
        sections = self._split_by_structure(text)

        # Step 2: Merge small sections, split large ones
        chunks = self._merge_and_split(sections)

        # Step 3: Apply overlap
        if len(chunks) > 1:
            chunks = self._apply_overlap(chunks)

        logger.info(
            f"Chunked text into {len(chunks)} chunks "
            f"(avg {sum(len(c) for c in chunks) // max(len(chunks), 1)} chars each)."
        )
        return chunks

    def _split_by_structure(self, text: str) -> List[str]:
        """Split text by structural markers: page breaks and headings."""
        # Split by page markers (--- Page N ---)
        page_pattern = r"(?=--- Page \d+ ---)"
        parts = re.split(page_pattern, text)

        # Further split by markdown headings
        sections: List[str] = []
        for part in parts:
            if not part.strip():
                continue
            # Split by heading markers (## Heading)
            heading_pattern = r"(?=^#{1,4}\s)", 
            sub_parts = re.split(r"(?m)(?=^#{1,4}\s)", part)
            for sub_part in sub_parts:
                stripped = sub_part.strip()
                if stripped:
                    sections.append(stripped)

        return sections if sections else [text.strip()]

    def _merge_and_split(self, sections: List[str]) -> List[str]:
        """Merge small sections and split oversized ones."""
        chunks: List[str] = []
        current_chunk: List[str] = []
        current_size = 0

        for section in sections:
            section_size = len(section)

            # If section alone exceeds chunk size, split by paragraphs
            if section_size > self.chunk_size_chars:
                # Flush current accumulator
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = []
                    current_size = 0

                # Split oversized section by paragraphs
                paragraph_chunks = self._split_by_paragraphs(section)
                chunks.extend(paragraph_chunks)
                continue

            # If adding this section exceeds limit, flush
            if current_size + section_size > self.chunk_size_chars:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_size = 0

            current_chunk.append(section)
            current_size += section_size

        # Flush remaining
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return chunks

    def _split_by_paragraphs(self, text: str) -> List[str]:
        """Split oversized text by paragraph boundaries."""
        paragraphs = re.split(r"\n\s*\n", text)
        chunks: List[str] = []
        current_chunk: List[str] = []
        current_size = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_size = len(para)

            # If single paragraph exceeds chunk size, split by sentences
            if para_size > self.chunk_size_chars:
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = []
                    current_size = 0

                sentence_chunks = self._split_by_sentences(para)
                chunks.extend(sentence_chunks)
                continue

            if current_size + para_size > self.chunk_size_chars:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_size = 0

            current_chunk.append(para)
            current_size += para_size

        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return chunks

    def _split_by_sentences(self, text: str) -> List[str]:
        """Split text by sentence boundaries as a last resort."""
        # Simple sentence splitting on period/question/exclamation
        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks: List[str] = []
        current_chunk: List[str] = []
        current_size = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if current_size + len(sentence) > self.chunk_size_chars:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_size = len(sentence)
            else:
                current_chunk.append(sentence)
                current_size += len(sentence)

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _apply_overlap(self, chunks: List[str]) -> List[str]:
        """Apply overlap between chunks for context continuity."""
        if self.overlap_chars <= 0:
            return chunks

        overlapped_chunks: List[str] = [chunks[0]]

        for i in range(1, len(chunks)):
            prev_chunk = chunks[i - 1]
            # Take last overlap_chars from previous chunk as prefix
            overlap_text = prev_chunk[-self.overlap_chars:]
            # Find a clean break point (start of a word)
            space_idx = overlap_text.find(" ")
            if space_idx > 0:
                overlap_text = overlap_text[space_idx + 1:]

            overlapped_chunks.append(f"{overlap_text}\n\n{chunks[i]}")

        return overlapped_chunks
