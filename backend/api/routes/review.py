"""Review route — POST /api/v1/review

Triggers the multi-agent review pipeline for an uploaded file.
Runs the LangGraph orchestrator asynchronously and stores results
in Postgres, scoped to the requesting user.
"""

import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.db.session import SessionLocal, get_db
from backend.models.review import Review
from backend.models.uploaded_file import UploadedFile
from backend.models.user import User
from backend.orchestrator.graph import run_review
from backend.schemas.review import ReviewRequest, ReviewStartResponse, ReviewStatus

logger = logging.getLogger(__name__)

router = APIRouter()


def _execute_review(review_id: str, file_id: str, filename: str, sow_text: str) -> None:
    """Execute the review pipeline in the background.

    Runs outside the request lifecycle, so it opens its own DB session
    rather than reusing the request-scoped one from get_db().
    """
    db = SessionLocal()
    try:
        review = db.query(Review).filter(Review.id == review_id).first()
        if not review:
            logger.error(f"Review {review_id} disappeared before execution.")
            return

        logger.info(f"Executing review {review_id} for file {file_id}...")
        review.status = "in_progress"
        db.commit()

        # Run the LangGraph pipeline
        result = run_review(sow_text=sow_text, filename=filename, review_id=review_id)

        agents = {
            domain: {
                "findings": result.get(f"{domain}_findings", []),
                "agent_confidence": _compute_agent_confidence(result.get(f"{domain}_findings", [])),
            }
            for domain in ("legal", "financial", "technical", "risk", "delivery")
        }

        review.status = result.get("status", "complete")
        review.overall_risk_score = result.get("overall_risk_score")
        review.summary = result.get("summary")
        review.error = result.get("error")
        review.agents_json = agents

        score = review.overall_risk_score
        if score is not None:
            review.overall_risk_level = "HIGH" if score >= 7.0 else "MEDIUM" if score >= 4.0 else "LOW"

        db.commit()
        logger.info(f"Review {review_id} completed successfully.")

    except Exception as e:
        logger.error(f"Review {review_id} failed: {e}")
        review = db.query(Review).filter(Review.id == review_id).first()
        if review:
            review.status = "error"
            review.error = str(e)
            db.commit()
    finally:
        db.close()


def _compute_agent_confidence(findings: list) -> float:
    """Compute average confidence from a list of findings."""
    if not findings:
        return 0.0
    confidences = [f.get("confidence", 0.0) for f in findings]
    return round(sum(confidences) / len(confidences), 3)


@router.post(
    "/review",
    response_model=ReviewStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start a multi-agent SOW review",
)
async def start_review(
    request: ReviewRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReviewStartResponse:
    """Start a multi-agent review for a previously uploaded file.

    Only files owned by the requesting user may be reviewed — this is
    the enforcement point for private per-user data.
    """
    file_id = request.file_id

    file_row = (
        db.query(UploadedFile)
        .filter(UploadedFile.id == file_id, UploadedFile.user_id == current_user.id)
        .first()
    )
    if not file_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID '{file_id}' not found. Please upload the file first.",
        )

    review_id = str(uuid.uuid4())
    review = Review(
        id=review_id,
        user_id=current_user.id,
        file_id=file_row.id,
        filename=file_row.filename,
        status="pending",
    )
    db.add(review)
    db.commit()

    background_tasks.add_task(
        _execute_review,
        review_id=review_id,
        file_id=str(file_row.id),
        filename=file_row.filename,
        sow_text=file_row.text,
    )

    logger.info(f"Review {review_id} initiated for file '{file_row.filename}' (user: {current_user.id}).")

    return ReviewStartResponse(
        review_id=review_id,
        file_id=str(file_row.id),
        status=ReviewStatus.PENDING,
        message="Review initiated. Poll /api/v1/results/{review_id} for status.",
    )
