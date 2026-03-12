"""Teacher schemas."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import PaymentMode
from app.schemas.common import ORMModel


class TeacherAssignmentCreate(BaseModel):
    """Teacher class assignment."""

    class_id: UUID
    section_id: UUID | None = None
    academic_year_id: UUID | None = None


class TeacherCreate(BaseModel):
    """Teacher creation request."""

    name: str = Field(min_length=1, max_length=150)
    phone: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=255)
    assigned_classes: list[TeacherAssignmentCreate] = []


class TeacherUpdate(BaseModel):
    """Teacher update request."""

    name: str | None = Field(default=None, max_length=150)
    phone: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=255)
    assigned_classes: list[TeacherAssignmentCreate] | None = None
    is_active: bool | None = None


class TeacherRead(ORMModel):
    """Teacher response schema."""

    id: UUID
    name: str
    phone: str | None
    email: str | None
    is_active: bool
    created_at: datetime


class TeacherContractCreate(BaseModel):
    """Teacher contract request."""

    teacher_id: UUID
    academic_year_id: UUID
    yearly_contract_amount: Decimal
    monthly_salary: Decimal | None = None


class TeacherPaymentCreate(BaseModel):
    """Teacher salary payment request."""

    teacher_id: UUID
    contract_id: UUID
    amount: Decimal
    payment_mode: PaymentMode
    payment_date: date


class TeacherPaymentSummary(BaseModel):
    """Teacher payment summary payload."""

    teacher_id: UUID
    teacher_name: str
    contract_total: Decimal
    total_paid: Decimal
    pending_balance: Decimal


class TeacherSlipShareRequest(BaseModel):
    """Salary slip sharing request."""

    channel: str = Field(pattern="^(EMAIL|WHATSAPP)$")
