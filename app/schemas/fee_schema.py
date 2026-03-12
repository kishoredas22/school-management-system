"""Fee schemas."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import FeeType, PaymentMode
from app.schemas.common import ORMModel


class FeeStructureCreate(BaseModel):
    """Fee structure request."""

    class_id: UUID
    academic_year_id: UUID
    fee_name: str = Field(min_length=1, max_length=100)
    amount: Decimal
    fee_type: FeeType


class FeePaymentCreate(BaseModel):
    """Fee payment request."""

    student_id: UUID
    fee_structure_id: UUID
    amount: Decimal
    payment_mode: PaymentMode
    payment_date: date


class FeePaymentRead(ORMModel):
    """Fee payment response schema."""

    id: UUID
    student_id: UUID
    fee_structure_id: UUID
    amount_paid: Decimal
    payment_mode: PaymentMode
    payment_date: date
    receipt_number: str
    created_at: datetime


class FeeSummaryResponse(BaseModel):
    """Student fee summary payload."""

    total_fee: Decimal
    total_paid: Decimal
    pending: Decimal
    payment_history: list[FeePaymentRead]
