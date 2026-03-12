"""Student schemas."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import PromotionAction, StudentStatus
from app.schemas.common import ORMModel


class StudentCreate(BaseModel):
    """Student creation request."""

    student_id: str | None = None
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    dob: date
    guardian_name: str | None = Field(default=None, max_length=150)
    guardian_phone: str | None = Field(default=None, max_length=20)
    class_id: UUID
    section_id: UUID
    academic_year_id: UUID


class StudentUpdate(BaseModel):
    """Student update request."""

    student_id: str | None = None
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    dob: date | None = None
    guardian_name: str | None = Field(default=None, max_length=150)
    guardian_phone: str | None = Field(default=None, max_length=20)
    class_id: UUID | None = None
    section_id: UUID | None = None
    academic_year_id: UUID | None = None


class StudentStatusUpdate(BaseModel):
    """Student status update request."""

    status: StudentStatus


class StudentPromotionRequest(BaseModel):
    """Bulk promotion request."""

    academic_year_from: UUID
    academic_year_to: UUID
    student_ids: list[UUID] = []
    action: PromotionAction


class StudentRead(ORMModel):
    """Student list/detail response."""

    id: UUID
    student_id: str | None
    first_name: str
    last_name: str | None
    dob: date
    guardian_name: str | None
    guardian_phone: str | None
    status: StudentStatus
    class_id: UUID | None = None
    class_name: str | None = None
    section_id: UUID | None = None
    section_name: str | None = None
    academic_year_id: UUID | None = None
    academic_year_name: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class StudentPromotionResult(BaseModel):
    """Promotion summary payload."""

    processed_count: int
    action: PromotionAction
    student_ids: list[UUID]
