"""PDF annotation utility for SOW review findings.

Uses PyMuPDF (fitz) to highlight text in the original PDF and
add pop-up annotation comments with agent findings and recommendations.
Each finding's ``source_text`` is searched in the PDF; if found, the
matching region is highlighted in a risk-level colour and a sticky
note is attached.
"""

import logging
from typing import Dict, List, Tuple

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

# Highlight colours per risk level  (R, G, B)  — semi-transparent
RISK_HIGHLIGHT_COLORS: Dict[str, Tuple[float, float, float]] = {
    "HIGH": (1.0, 0.4, 0.4),       # Red
    "MEDIUM": (1.0, 0.82, 0.3),    # Amber
    "LOW": (0.4, 0.9, 0.5),        # Green
}

# Domain emoji mapping for annotation labels
DOMAIN_EMOJI: Dict[str, str] = {
    "legal": "⚖️",
    "financial": "💰",
    "technical": "⚙️",
    "risk": "🎯",
    "delivery": "📦",
}


class PDFAnnotator:
    """Annotate a PDF with highlighted findings from SOW review agents.

    For each finding that includes a ``source_text``, the annotator:
    1. Searches every page of the PDF for the text.
    2. Highlights the matching region with a colour based on risk level.
    3. Adds a pop-up (sticky-note) annotation with the finding details.
    """

    @staticmethod
    def annotate(file_bytes: bytes, findings: List[dict]) -> bytes:
        """Create an annotated copy of the PDF with highlighted findings.

        Args:
            file_bytes: Original PDF file content.
            findings: List of finding dicts, each potentially containing
                      ``source_text``, ``finding``, ``risk_level``,
                      ``recommendation``, ``domain``, and ``agent``.

        Returns:
            Annotated PDF file content as bytes.
        """
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        annotated_count = 0
        not_found_count = 0

        for idx, finding in enumerate(findings, start=1):
            source_text = finding.get("source_text")
            if not source_text or not source_text.strip():
                continue

            risk_level = finding.get("risk_level", "MEDIUM")
            color = RISK_HIGHLIGHT_COLORS.get(risk_level, RISK_HIGHLIGHT_COLORS["MEDIUM"])
            domain = finding.get("domain", "")
            agent = finding.get("agent", domain.capitalize())
            emoji = DOMAIN_EMOJI.get(domain, "📋")

            # Build the annotation comment text
            comment = (
                f"{emoji} [{agent}] Finding #{idx}\n"
                f"Risk: {risk_level}\n"
                f"Confidence: {finding.get('confidence', 'N/A')}\n\n"
                f"{finding.get('finding', '')}\n\n"
                f"💡 Recommendation:\n"
                f"{finding.get('recommendation', 'N/A')}"
            )

            found = PDFAnnotator._highlight_text(doc, source_text, color, comment)
            if found:
                annotated_count += 1
            else:
                # Try partial match with first 80 chars if full match fails
                partial = source_text[:80].strip()
                if len(partial) > 20:
                    found = PDFAnnotator._highlight_text(doc, partial, color, comment)
                    if found:
                        annotated_count += 1
                    else:
                        not_found_count += 1
                else:
                    not_found_count += 1

        logger.info(
            f"PDF annotation complete: {annotated_count} findings highlighted, "
            f"{not_found_count} source texts not found in PDF."
        )

        # Add a summary page at the end
        if annotated_count > 0 or not_found_count > 0:
            PDFAnnotator._add_summary_page(doc, findings, annotated_count, not_found_count)

        # Write to bytes
        result = doc.tobytes(deflate=True)
        doc.close()
        return result

    @staticmethod
    def _highlight_text(
        doc: fitz.Document,
        search_text: str,
        color: Tuple[float, float, float],
        comment: str,
    ) -> bool:
        """Search for text across all pages and highlight the first match.

        Args:
            doc: PyMuPDF Document object.
            search_text: Text to search for.
            color: RGB colour tuple for the highlight.
            comment: Text for the pop-up annotation.

        Returns:
            True if text was found and highlighted, False otherwise.
        """
        # Clean search text — normalise whitespace for better matching
        clean_search = " ".join(search_text.split())

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Search for the text on this page
            text_instances = page.search_for(clean_search)

            if not text_instances:
                # Try with less strict matching — first sentence or clause
                # Sometimes SOW text spans lines differently in PDF layout
                shorter = clean_search[:100] if len(clean_search) > 100 else clean_search
                if shorter != clean_search:
                    text_instances = page.search_for(shorter)

            if text_instances:
                # Highlight all matching rectangles on this page
                for rect in text_instances:
                    highlight = page.add_highlight_annot(rect)
                    highlight.set_colors(stroke=color)
                    highlight.set_opacity(0.4)
                    highlight.update()

                # Add a sticky-note annotation at the first match location
                first_rect = text_instances[0]
                # Place the note icon to the right of the highlighted text
                note_point = fitz.Point(first_rect.x1 + 2, first_rect.y0)
                note = page.add_text_annot(note_point, comment)
                note.set_colors(stroke=color)
                note.update()

                return True

        return False

    @staticmethod
    def _add_summary_page(
        doc: fitz.Document,
        findings: List[dict],
        annotated_count: int,
        not_found_count: int,
    ) -> None:
        """Add a summary page at the end of the PDF.

        Args:
            doc: PyMuPDF Document object.
            findings: All findings.
            annotated_count: Number of findings successfully highlighted.
            not_found_count: Number of source texts not found.
        """
        # Add a new page (A4 size)
        page = doc.new_page(width=595, height=842)

        # Title
        title_rect = fitz.Rect(50, 40, 545, 80)
        page.insert_textbox(
            title_rect,
            "SOWnia — Annotated Review Summary",
            fontsize=18,
            fontname="helv",
            color=(0.19, 0.17, 0.39),  # #302b63
            align=fitz.TEXT_ALIGN_CENTER,
        )

        # Stats line
        stats_rect = fitz.Rect(50, 85, 545, 110)
        high_count = sum(1 for f in findings if f.get("risk_level") == "HIGH")
        med_count = sum(1 for f in findings if f.get("risk_level") == "MEDIUM")
        low_count = sum(1 for f in findings if f.get("risk_level") == "LOW")
        stats_text = (
            f"Total findings: {len(findings)}  |  "
            f"HIGH: {high_count}  |  MEDIUM: {med_count}  |  LOW: {low_count}  |  "
            f"Highlighted: {annotated_count}  |  Not matched: {not_found_count}"
        )
        page.insert_textbox(
            stats_rect,
            stats_text,
            fontsize=9,
            fontname="helv",
            color=(0.4, 0.4, 0.4),
            align=fitz.TEXT_ALIGN_CENTER,
        )

        # Separator line
        page.draw_line(fitz.Point(50, 118), fitz.Point(545, 118),
                       color=(0.19, 0.17, 0.39), width=1.5)

        # Findings list
        y_pos = 135
        for idx, finding in enumerate(findings, start=1):
            if y_pos > 790:
                # Add another page if we run out of space
                page = doc.new_page(width=595, height=842)
                y_pos = 50

            domain = finding.get("domain", "")
            emoji = DOMAIN_EMOJI.get(domain, "📋")
            risk = finding.get("risk_level", "MEDIUM")
            risk_color = RISK_HIGHLIGHT_COLORS.get(risk, (0.5, 0.5, 0.5))
            has_source = bool(finding.get("source_text"))
            marker = "✓" if has_source else "✗"

            # Finding header
            header_rect = fitz.Rect(50, y_pos, 545, y_pos + 16)
            header_text = f"{emoji} #{idx} [{risk}] {finding.get('agent', domain)} — {marker} {'Highlighted' if has_source else 'No source text'}"
            page.insert_textbox(
                header_rect,
                header_text,
                fontsize=9,
                fontname="helv",
                color=risk_color,
            )
            y_pos += 18

            # Finding description (truncated)
            desc = finding.get("finding", "")[:200]
            desc_rect = fitz.Rect(65, y_pos, 545, y_pos + 30)
            page.insert_textbox(
                desc_rect,
                desc,
                fontsize=8,
                fontname="helv",
                color=(0.3, 0.3, 0.3),
            )
            y_pos += 35
