"""Results routes — GET/DELETE endpoints for review results.

Provides endpoints to:
- GET /results/{review_id}     — Fetch full review results as JSON
- GET /results/{review_id}/pdf — Download PDF report
- GET /reviews                 — List all past reviews
- DELETE /reviews/{review_id}  — Delete a review record
"""

import io
import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from backend.api.routes.review import review_results
from backend.schemas.review import (
    DeleteReviewResponse,
    ReviewListItem,
    ReviewListResponse,
    ReviewStatus,
    RiskLevel,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/results/{review_id}",
    summary="Get full review results",
)
async def get_results(review_id: str):
    """Get the full review results for a given review ID.

    Returns the complete JSON output including all agent findings,
    risk scores, and executive summary.

    Args:
        review_id: UUID of the review.

    Returns:
        Full review results dictionary.

    Raises:
        HTTPException: If review_id is not found.
    """
    # Check in-memory results first
    if review_id in review_results:
        return review_results[review_id]

    # Fall back to HF Datasets storage
    try:
        from backend.storage.hf_storage import hf_storage
        review = hf_storage.get_review(review_id)
        if review:
            return review
    except Exception as e:
        logger.warning(f"Could not fetch from HF storage: {e}")

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Review with ID '{review_id}' not found.",
    )


@router.get(
    "/results/{review_id}/pdf",
    summary="Download PDF report",
)
async def get_pdf_report(review_id: str):
    """Generate and download a PDF report for a review.

    Uses WeasyPrint to generate a professional PDF report with:
    - Cover page with filename, date, overall risk score
    - Executive summary
    - Risk overview table
    - Per-domain findings
    - Recommendations

    Args:
        review_id: UUID of the review.

    Returns:
        StreamingResponse with the PDF file.

    Raises:
        HTTPException: If review is not found or not complete.
    """
    # Get review data
    review_data = None
    if review_id in review_results:
        review_data = review_results[review_id]
    else:
        try:
            from backend.storage.hf_storage import hf_storage
            review_data = hf_storage.get_review(review_id)
        except Exception:
            pass

    if not review_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review with ID '{review_id}' not found.",
        )

    if review_data.get("status") != "complete":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Review is not yet complete. "
            f"Current status: {review_data.get('status')}.",
        )

    # Generate PDF
    try:
        pdf_bytes = _generate_pdf_report(review_data)
        filename = f"sownia_report_{review_id[:8]}.pdf"

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            },
        )
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF report generation failed: {str(e)}",
        )


@router.get(
    "/reviews",
    response_model=ReviewListResponse,
    summary="List all past reviews",
)
async def list_reviews(
    risk_level: Optional[str] = Query(
        None, description="Filter by risk level: HIGH, MEDIUM, LOW"
    ),
    limit: int = Query(50, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """List all past reviews with optional filtering.

    Combines in-memory results with HF Datasets storage.

    Args:
        risk_level: Optional filter by risk level.
        limit: Maximum number of results.
        offset: Pagination offset.

    Returns:
        ReviewListResponse with paginated review list.
    """
    # Gather all reviews (in-memory + HF storage)
    all_reviews = {}

    # In-memory results
    for rid, data in review_results.items():
        all_reviews[rid] = data

    # HF storage results
    try:
        from backend.storage.hf_storage import hf_storage
        hf_reviews = hf_storage.list_reviews()
        for review in hf_reviews:
            rid = review.get("review_id")
            if rid and rid not in all_reviews:
                all_reviews[rid] = review
    except Exception as e:
        logger.warning(f"Could not fetch from HF storage: {e}")

    # Convert to list items
    items = []
    for rid, data in all_reviews.items():
        # Count findings
        finding_count = 0
        agents = data.get("agents", {})
        for agent_data in agents.values():
            if isinstance(agent_data, dict):
                finding_count += len(agent_data.get("findings", []))

        # Parse risk level
        overall_risk = data.get("overall_risk_level")
        try:
            risk_enum = RiskLevel(overall_risk) if overall_risk else None
        except ValueError:
            risk_enum = None

        # Parse status
        status_str = data.get("status", "pending")
        try:
            status_enum = ReviewStatus(status_str)
        except ValueError:
            status_enum = ReviewStatus.PENDING

        # Parse timestamp
        timestamp_str = data.get("timestamp", datetime.utcnow().isoformat())
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
        except (ValueError, TypeError):
            timestamp = datetime.utcnow()

        item = ReviewListItem(
            review_id=rid,
            filename=data.get("filename", "unknown"),
            timestamp=timestamp,
            overall_risk_score=data.get("overall_risk_score"),
            overall_risk_level=risk_enum,
            status=status_enum,
            finding_count=finding_count,
        )
        items.append(item)

    # Apply risk level filter
    if risk_level:
        try:
            filter_level = RiskLevel(risk_level.upper())
            items = [i for i in items if i.overall_risk_level == filter_level]
        except ValueError:
            pass

    # Sort by timestamp (newest first)
    items.sort(key=lambda i: i.timestamp, reverse=True)

    total = len(items)
    items = items[offset: offset + limit]

    return ReviewListResponse(reviews=items, total=total)


@router.delete(
    "/reviews/{review_id}",
    response_model=DeleteReviewResponse,
    summary="Delete a review",
)
async def delete_review(review_id: str):
    """Delete a review record.

    Removes from both in-memory store and HF Datasets.

    Args:
        review_id: UUID of the review to delete.

    Returns:
        DeleteReviewResponse confirming deletion.

    Raises:
        HTTPException: If review_id is not found.
    """
    found = False

    # Remove from in-memory store
    if review_id in review_results:
        del review_results[review_id]
        found = True

    # Remove from HF storage
    try:
        from backend.storage.hf_storage import hf_storage
        if hf_storage.delete_review(review_id):
            found = True
    except Exception as e:
        logger.warning(f"Could not delete from HF storage: {e}")

    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review with ID '{review_id}' not found.",
        )

    return DeleteReviewResponse(
        review_id=review_id,
        message="Review deleted successfully.",
    )


def _generate_pdf_report(review_data: dict) -> bytes:
    """Generate a PDF report from review data using WeasyPrint.

    Args:
        review_data: Full review results dictionary.

    Returns:
        PDF file content as bytes.
    """
    from weasyprint import HTML

    # Build HTML report
    filename = review_data.get("filename", "Unknown")
    timestamp = review_data.get("timestamp", "Unknown")
    overall_score = review_data.get("overall_risk_score", "N/A")
    overall_level = review_data.get("overall_risk_level", "N/A")
    summary = review_data.get("summary", "No summary available.")
    agents = review_data.get("agents", {})

    # Risk level color mapping
    level_colors = {"HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#22c55e"}

    # Build findings HTML
    findings_html = ""
    for domain, agent_data in agents.items():
        if not isinstance(agent_data, dict):
            continue
        findings = agent_data.get("findings", [])
        confidence = agent_data.get("agent_confidence", 0.0)

        findings_html += f"""
        <div class="domain-section">
            <h2>{domain.capitalize()} Review</h2>
            <p class="confidence">Agent Confidence: {confidence:.0%}</p>
            <table>
                <tr><th>Finding</th><th>Risk</th><th>Confidence</th><th>Recommendation</th></tr>
        """
        for finding in findings:
            risk = finding.get("risk_level", "MEDIUM")
            color = level_colors.get(risk, "#f59e0b")
            findings_html += f"""
                <tr>
                    <td>{finding.get('finding', 'N/A')}</td>
                    <td><span style="color: {color}; font-weight: bold;">{risk}</span></td>
                    <td>{finding.get('confidence', 0.0):.0%}</td>
                    <td>{finding.get('recommendation', 'N/A')}</td>
                </tr>
            """
        findings_html += "</table></div>"

    score_color = level_colors.get(str(overall_level), "#f59e0b")

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Helvetica Neue', Arial, sans-serif; margin: 40px; color: #1a1a2e; }}
            .cover {{ text-align: center; margin-bottom: 40px; padding: 60px 20px; background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); color: white; border-radius: 12px; }}
            .cover h1 {{ font-size: 32px; margin-bottom: 8px; }}
            .cover .subtitle {{ font-size: 16px; opacity: 0.8; }}
            .cover .score {{ font-size: 64px; font-weight: bold; color: {score_color}; margin: 20px 0; }}
            .cover .level {{ font-size: 20px; color: {score_color}; }}
            .summary {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px; border-left: 4px solid #302b63; }}
            .summary h2 {{ margin-top: 0; }}
            .summary pre {{ white-space: pre-wrap; font-family: inherit; }}
            .domain-section {{ margin-bottom: 30px; page-break-inside: avoid; }}
            .domain-section h2 {{ color: #302b63; border-bottom: 2px solid #302b63; padding-bottom: 8px; }}
            .confidence {{ color: #666; font-style: italic; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }}
            th {{ background: #302b63; color: white; padding: 10px; text-align: left; }}
            td {{ padding: 10px; border-bottom: 1px solid #e0e0e0; vertical-align: top; }}
            tr:nth-child(even) {{ background: #f8f9fa; }}
            .appendix {{ margin-top: 40px; padding-top: 20px; border-top: 2px solid #302b63; }}
            .appendix pre {{ background: #f4f4f4; padding: 15px; border-radius: 4px; font-size: 11px; overflow-wrap: break-word; }}
        </style>
    </head>
    <body>
        <div class="cover">
            <h1>SOWnia Review Report</h1>
            <p class="subtitle">{filename}</p>
            <p class="subtitle">{timestamp}</p>
            <div class="score">{overall_score}</div>
            <div class="level">{overall_level} RISK</div>
        </div>

        <div class="summary">
            <h2>Executive Summary</h2>
            <pre>{summary}</pre>
        </div>

        {findings_html}

        <div class="appendix">
            <h2>Appendix — Raw JSON Data</h2>
            <pre>{json.dumps(review_data, indent=2, default=str)[:5000]}</pre>
        </div>
    </body>
    </html>
    """

    pdf = HTML(string=html_content).write_pdf()
    return pdf
