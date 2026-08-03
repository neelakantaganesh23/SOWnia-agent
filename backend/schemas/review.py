"""Pydantic models for review input/output.

Defines the data structures for review requests, responses,
and list items used across the API endpoints.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ReviewStatus(str, Enum):
    """Status of a SOW review."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    ERROR = "error"


class RiskLevel(str, Enum):
    """Risk severity levels."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class UploadResponse(BaseModel):
    """Response from file upload endpoint."""

    file_id: str = Field(..., description="UUID for the uploaded file")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="Detected MIME type")
    page_count: Optional[int] = Field(None, description="Number of pages (PDF only)")
    text_length: int = Field(..., description="Length of extracted text in characters")
    message: str = Field(default="File uploaded and parsed successfully")


class ReviewRequest(BaseModel):
    """Request to start a new SOW review."""

    file_id: str = Field(..., description="UUID of the uploaded file to review")


class ReviewStartResponse(BaseModel):
    """Response when a review is initiated."""

    review_id: str = Field(..., description="UUID for this review")
    file_id: str = Field(..., description="UUID of the file being reviewed")
    status: ReviewStatus = Field(default=ReviewStatus.PENDING)
    message: str = Field(default="Review initiated successfully")


class ReviewListItem(BaseModel):
    """Summary item for the reviews list endpoint."""

    review_id: str
    filename: str
    timestamp: datetime
    overall_risk_score: Optional[float] = None
    overall_risk_level: Optional[RiskLevel] = None
    status: ReviewStatus
    finding_count: int = 0


class ReviewListResponse(BaseModel):
    """Response for the list reviews endpoint."""

    reviews: List[ReviewListItem]
    total: int


class DeleteReviewResponse(BaseModel):
    """Response for the delete review endpoint."""

    review_id: str
    message: str = Field(default="Review deleted successfully")


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
    error_code: Optional[str] = None
