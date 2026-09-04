"""Results routes — GET/DELETE endpoints for review results.

Provides endpoints to:
- GET /results/{review_id}                — Fetch full review results as JSON
- GET /results/{review_id}/pdf            — Download PDF report
- GET /results/{review_id}/annotated-pdf  — Download original PDF with highlighted findings
- GET /reviews                            — List all past reviews
- DELETE /reviews/{review_id}             — Delete a review record

All reads/writes are scoped to the authenticated user via user_id, so
one user can never see or act on another user's reviews/files.
"""

import io
import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.db.session import get_db
from backend.models.review import Review
from backend.models.uploaded_file import UploadedFile
from backend.models.user import User
from backend.schemas.review import (
    DeleteReviewResponse,
    ReviewListItem,
    ReviewListResponse,
    ReviewStatus,
    RiskLevel,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _review_to_dict(review: Review) -> dict:
    """Matches the historical in-memory/HF-JSONL review shape so the
    frontend's existing types/consumers need no changes."""
    return {
        "review_id": str(review.id),
        "file_id": str(review.file_id),
        "filename": review.filename,
        "timestamp": review.created_at.isoformat() if review.created_at else None,
        "status": review.status,
        "overall_risk_score": review.overall_risk_score,
        "overall_risk_level": review.overall_risk_level,
        "summary": review.summary,
        "error": review.error,
        "agents": review.agents_json or {},
    }


def _get_owned_review(review_id: str, current_user: User, db: Session) -> Review:
    review = (
        db.query(Review)
        .filter(Review.id == review_id, Review.user_id == current_user.id)
        .first()
    )
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review with ID '{review_id}' not found.",
        )
    return review


@router.get("/results/{review_id}", summary="Get full review results")
async def get_results(
    review_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    review = _get_owned_review(review_id, current_user, db)
    return _review_to_dict(review)


@router.get("/results/{review_id}/pdf", summary="Download PDF report")
async def get_pdf_report(
    review_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate and download a PDF report for a review via WeasyPrint."""
    review = _get_owned_review(review_id, current_user, db)
    review_data = _review_to_dict(review)

    if review_data.get("status") != "complete":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Review is not yet complete. Current status: {review_data.get('status')}.",
        )

    try:
        pdf_bytes = _generate_pdf_report(review_data)
        filename = f"sownia_report_{review_id[:8]}.pdf"
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF report generation failed: {str(e)}",
        )


@router.get("/results/{review_id}/annotated-pdf", summary="Download annotated PDF with highlighted findings")
async def get_annotated_pdf(
    review_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download the original uploaded PDF with findings highlighted."""
    review = _get_owned_review(review_id, current_user, db)
    review_data = _review_to_dict(review)

    if review_data.get("status") != "complete":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Review is not yet complete. Current status: {review_data.get('status')}.",
        )

    file_row = (
        db.query(UploadedFile)
        .filter(UploadedFile.id == review.file_id, UploadedFile.user_id == current_user.id)
        .first()
    )
    if not file_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original uploaded file not found. Re-upload and re-review the document.",
        )

    if file_row.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Annotated PDF is only available for PDF uploads. DOCX files are not supported for annotation.",
        )

    all_findings = []
    for agent_data in (review_data.get("agents") or {}).values():
        if isinstance(agent_data, dict):
            all_findings.extend(agent_data.get("findings", []))

    if not all_findings:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No findings to annotate.")

    try:
        from backend.utils.pdf_annotator import PDFAnnotator

        annotated_bytes = PDFAnnotator.annotate(file_row.file_bytes, all_findings)

        original_name = file_row.filename
        annotated_name = (
            original_name[:-4] + "_annotated.pdf"
            if original_name.lower().endswith(".pdf")
            else original_name + "_annotated.pdf"
        )

        return StreamingResponse(
            io.BytesIO(annotated_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={annotated_name}"},
        )
    except Exception as e:
        logger.error(f"PDF annotation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF annotation failed: {str(e)}",
        )


@router.get("/reviews", response_model=ReviewListResponse, summary="List all past reviews")
async def list_reviews(
    risk_level: Optional[str] = Query(None, description="Filter by risk level: HIGH, MEDIUM, LOW"),
    limit: int = Query(50, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List the CURRENT USER's past reviews only."""
    query = db.query(Review).filter(Review.user_id == current_user.id)

    if risk_level:
        try:
            query = query.filter(Review.overall_risk_level == RiskLevel(risk_level.upper()).value)
        except ValueError:
            pass

    total = query.count()
    rows = query.order_by(Review.created_at.desc()).offset(offset).limit(limit).all()

    items = []
    for review in rows:
        finding_count = sum(
            len(agent_data.get("findings", []))
            for agent_data in (review.agents_json or {}).values()
            if isinstance(agent_data, dict)
        )
        try:
            risk_enum = RiskLevel(review.overall_risk_level) if review.overall_risk_level else None
        except ValueError:
            risk_enum = None
        try:
            status_enum = ReviewStatus(review.status)
        except ValueError:
            status_enum = ReviewStatus.PENDING

        items.append(
            ReviewListItem(
                review_id=str(review.id),
                filename=review.filename,
                timestamp=review.created_at,
                overall_risk_score=review.overall_risk_score,
                overall_risk_level=risk_enum,
                status=status_enum,
                finding_count=finding_count,
            )
        )

    return ReviewListResponse(reviews=items, total=total)


@router.delete("/reviews/{review_id}", response_model=DeleteReviewResponse, summary="Delete a review")
async def delete_review(
    review_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    review = _get_owned_review(review_id, current_user, db)
    db.delete(review)
    db.commit()
    return DeleteReviewResponse(review_id=review_id, message="Review deleted successfully.")


def _generate_pdf_report(review_data: dict) -> bytes:
    """Generate a PDF report from review data using WeasyPrint."""
    from weasyprint import HTML

    filename = review_data.get("filename", "Unknown")
    timestamp = review_data.get("timestamp", "Unknown")
    overall_score = review_data.get("overall_risk_score", "N/A")
    overall_level = review_data.get("overall_risk_level", "N/A")
    summary = review_data.get("summary", "No summary available.")
    agents = review_data.get("agents", {})

    level_colors = {"HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#22c55e"}

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
