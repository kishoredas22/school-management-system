"""Fee payment model."""

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import PaymentMode


class FeePayment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Immutable fee payment record."""

    __tablename__ = "fee_payments"

    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), nullable=False, index=True)
    academic_year_id: Mapped[str] = mapped_column(ForeignKey("academic_years.id"), nullable=False, index=True)
    fee_structure_id: Mapped[str] = mapped_column(ForeignKey("fee_structures.id"), nullable=False, index=True)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_mode: Mapped[PaymentMode] = mapped_column(Enum(PaymentMode, native_enum=False), nullable=False)
    receipt_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)

    student = relationship("Student", back_populates="fee_payments")
    academic_year = relationship("AcademicYear", back_populates="fee_payments")
    fee_structure = relationship("FeeStructure", back_populates="payments")
