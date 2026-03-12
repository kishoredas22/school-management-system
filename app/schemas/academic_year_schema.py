"""Academic year schemas."""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class AcademicYearCreate(BaseModel):
    """Create academic year request."""

    name: str = Field(min_length=4, max_length=20)
    start_date: date
    end_date: date


class AcademicYearRead(ORMModel):
    """Academic year response schema."""

    id: UUID
    name: str
    start_date: date
    end_date: date
    is_active: bool
    is_closed: bool
