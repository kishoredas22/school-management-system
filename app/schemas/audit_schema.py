"""Audit schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class AuditLogRead(ORMModel):
    """Audit log response schema."""

    id: UUID
    entity_name: str
    entity_id: UUID | None
    action: str
    old_value: dict[str, Any] | None
    new_value: dict[str, Any] | None
    performed_by: UUID | None
    performed_at: datetime
    requires_review: bool
    review_status: str
    review_note: str | None
    reviewed_by: UUID | None
    reviewed_at: datetime | None


class AuditReviewRequest(BaseModel):
    """Governance review request payload."""

    status: str
    review_note: str | None = Field(default=None, max_length=500)


class AuditSummaryRead(BaseModel):
    """Audit dashboard summary metrics."""

    total_logs: int
    review_required: int
    pending_reviews: int
    approved_reviews: int
    rejected_reviews: int
