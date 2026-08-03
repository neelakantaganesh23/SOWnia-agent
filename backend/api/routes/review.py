"""Review route — POST /api/v1/review

Triggers the multi-agent review pipeline for an uploaded file.
Runs the LangGraph orchestrator asynchronously and stores results.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from backend.api.routes.upload import uploaded_files
from backend.orchestrator.graph import run_review
from backend.schemas.review import ReviewRequest, ReviewStartResponse, ReviewStatus

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory store for review results (keyed by review_id)
review_results: Dict[str, Dict] = {}


def _execute_review(
    review_id: str,
    file_id: str,
    filename: str,
    sow_text: str,
) -> None:
    """Execute the review pipeline in the background.

    This function runs the LangGraph review pipeline and stores
    the results in the in-memory review_results dictionary.

    Args:
        review_id: UUID for this review.
        file_id: UUID of the uploaded file.
        filename: Original filename.
        sow_text: Extracted SOW text.
    """
    try:
        logger.info(f"Executing review {review_id} for file {file_id}...")
        review_results[review_id]["status"] = "in_progress"

        # Run the LangGraph pipeline
        result = run_review(
            sow_text=sow_text,
            filename=filename,
            review_id=review_id,
        )

        # Convert LangGraph state to storage format
        review_data = {
            "review_id": review_id,
            "file_id": file_id,
            "filename": filename,
            "timestamp": datetime.utcnow().isoformat(),
            "status": result.get("status", "complete"),
            "overall_risk_score": result.get("overall_risk_score"),
            "summary": result.get("summary"),
            "error": result.get("error"),
            "agents": {
                "legal": {
                    "findings": result.get("legal_findings", []),
                    "agent_confidence": _compute_agent_confidence(
                        result.get("legal_findings", [])
                    ),
                },
                "financial": {
                    "findings": result.get("financial_findings", []),
                    "agent_confidence": _compute_agent_confidence(
                        result.get("financial_findings", [])
                    ),
                },
                "technical": {
                    "findings": result.get("technical_findings", []),
                    "agent_confidence": _compute_agent_confidence(
                        result.get("technical_findings", [])
                    ),
                },
                "risk": {
                    "findings": result.get("risk_findings", []),
                    "agent_confidence": _compute_agent_confidence(
                        result.get("risk_findings", [])
                    ),
                },
                "delivery": {
                    "findings": result.get("delivery_findings", []),
                    "agent_confidence": _compute_agent_confidence(
                        result.get("delivery_findings", [])
                    ),
                },
            },
        }

        # Compute overall risk level
        score = review_data.get("overall_risk_score")
        if score is not None:
            if score >= 7.0:
                review_data["overall_risk_level"] = "HIGH"
            elif score >= 4.0:
                review_data["overall_risk_level"] = "MEDIUM"
            else:
                review_data["overall_risk_level"] = "LOW"

        review_results[review_id] = review_data
        logger.info(f"Review {review_id} completed successfully.")

        # Try to save to HF Datasets (non-blocking)
        try:
            from backend.storage.hf_storage import hf_storage
            hf_storage.save_review(review_data)
        except Exception as e:
            logger.warning(f"Failed to save review to HF Datasets: {e}")

    except Exception as e:
        logger.error(f"Review {review_id} failed: {e}")
        review_results[review_id] = {
            "review_id": review_id,
            "file_id": file_id,
            "filename": filename,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
            "error": str(e),
            "agents": {},
        }


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
) -> ReviewStartResponse:
    """Start a multi-agent review for a previously uploaded file.

    The review runs asynchronously in the background. Use the
    results endpoint to poll for completion.

    Args:
        request: ReviewRequest with file_id.
        background_tasks: FastAPI background task runner.

    Returns:
        ReviewStartResponse with review_id.

    Raises:
        HTTPException: If file_id is not found.
    """
    file_id = request.file_id

    # Validate file exists
    if file_id not in uploaded_files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID '{file_id}' not found. "
            f"Please upload the file first.",
        )

    file_data = uploaded_files[file_id]
    review_id = str(uuid.uuid4())

    # Initialize review status
    review_results[review_id] = {
        "review_id": review_id,
        "file_id": file_id,
        "filename": file_data["filename"],
        "timestamp": datetime.utcnow().isoformat(),
        "status": "pending",
        "agents": {},
    }

    # Start review in background
    background_tasks.add_task(
        _execute_review,
        review_id=review_id,
        file_id=file_id,
        filename=file_data["filename"],
        sow_text=file_data["text"],
    )

    logger.info(
        f"Review {review_id} initiated for file '{file_data['filename']}' "
        f"(file_id: {file_id})."
    )

    return ReviewStartResponse(
        review_id=review_id,
        file_id=file_id,
        status=ReviewStatus.PENDING,
        message="Review initiated. Poll /api/v1/results/{review_id} for status.",
    )
