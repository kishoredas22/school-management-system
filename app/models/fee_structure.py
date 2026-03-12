"""Fee structure model."""

from decimal import Decimal

from sqlalchemy import Boolean, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import FeeType


class FeeStructure(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Academic-year-specific fee definition."""

    __tablename__ = "fee_structures"

    class_id: Mapped[str] = mapped_column(ForeignKey("classes.id"), nullable=False, index=True)
    academic_year_id: Mapped[str] = mapped_column(ForeignKey("academic_years.id"), nullable=False, index=True)
    fee_name: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    fee_type: Mapped[FeeType] = mapped_column(Enum(FeeType, native_enum=False), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    class_room = relationship("ClassRoom", back_populates="fee_structures")
    academic_year = relationship("AcademicYear", back_populates="fee_structures")
    payments = relationship("FeePayment", back_populates="fee_structure")
