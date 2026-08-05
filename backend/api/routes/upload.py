"""Upload route — POST /api/v1/upload

Accepts PDF or DOCX file uploads with validation:
- File size ≤ 10 MB
- MIME type validation
- Magic bytes verification
- Text extraction

Persists the file to the database (scoped to the authenticated user) and
returns file_id UUID for subsequent review requests.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.config import settings
from backend.db.session import get_db
from backend.models.uploaded_file import UploadedFile
from backend.models.user import User
from backend.parsers.pdf_parser import PDFParser
from backend.parsers.docx_parser import DOCXParser
from backend.schemas.review import UploadResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# Allowed MIME types
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a SOW document (PDF or DOCX)",
)
async def upload_file_endpoint(
    file: UploadFile = File(..., description="SOW document (PDF or DOCX)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadResponse:
    """Upload a SOW document for review.

    Validates the file type, size, and magic bytes, then extracts
    the text content and persists it to the database, owned by the
    authenticated user.

    Raises:
        HTTPException: If file validation fails.
    """
    # Validate MIME type
    content_type = file.content_type or ""
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {content_type}. "
            f"Only PDF and DOCX files are accepted.",
        )

    # Read file content
    file_bytes = await file.read()

    # Validate file size
    if len(file_bytes) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({len(file_bytes)} bytes) exceeds "
            f"maximum allowed size ({settings.MAX_FILE_SIZE_MB} MB).",
        )

    # Validate magic bytes and extract text
    filename = file.filename or "unknown"
    page_count = None

    try:
        if content_type == "application/pdf":
            if not PDFParser.validate_file(file_bytes):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File does not appear to be a valid PDF "
                    "(magic bytes mismatch).",
                )
            extracted_text = PDFParser.extract_text(file_bytes)
            page_count = PDFParser.get_page_count(file_bytes)
        else:
            if not DOCXParser.validate_file(file_bytes):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File does not appear to be a valid DOCX "
                    "(magic bytes mismatch).",
                )
            extracted_text = DOCXParser.extract_text(file_bytes)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text extraction failed for '{filename}': {e}")
        raise HTTPException(
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            detail=f"Failed to extract text from file: {str(e)}",
        )

    if not extracted_text.strip():
        raise HTTPException(
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            detail="No text could be extracted from the uploaded file. "
            "The file may be scanned/image-based or empty.",
        )

    uploaded_file = UploadedFile(
        user_id=current_user.id,
        filename=filename,
        content_type=content_type,
        text=extracted_text,
        file_bytes=file_bytes,
        file_size=len(file_bytes),
        page_count=page_count,
    )
    db.add(uploaded_file)
    db.commit()
    db.refresh(uploaded_file)

    logger.info(
        f"File uploaded: '{filename}' (ID: {uploaded_file.id}, user: {current_user.id}, "
        f"{len(extracted_text)} chars extracted)."
    )

    return UploadResponse(
        file_id=str(uploaded_file.id),
        filename=filename,
        file_size=len(file_bytes),
        content_type=content_type,
        page_count=page_count,
        text_length=len(extracted_text),
    )
