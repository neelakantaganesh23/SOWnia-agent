"""Review record, persisted per-user (replaces the old in-memory dict +
shared HF Datasets JSONL, which had no per-user field and required a
full-file read-modify-write on every save)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from backend.db.base import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    file_id = Column(UUID(as_uuid=True), ForeignKey("uploaded_files.id"), nullable=False)
    filename = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    overall_risk_score = Column(Float, nullable=True)
    overall_risk_level = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    # Full nested agents/findings structure, unchanged shape from the
    # existing in-memory dict — avoids modeling five more tables.
    agents_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
