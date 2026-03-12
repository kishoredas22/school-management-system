"""Academic year model."""

from datetime import date

from sqlalchemy import Boolean, Date, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AcademicYear(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Academic year lifecycle entity."""

    __tablename__ = "academic_years"

    name: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    student_records = relationship("StudentAcademicRecord", back_populates="academic_year")
    fee_structures = relationship("FeeStructure", back_populates="academic_year")
    fee_payments = relationship("FeePayment", back_populates="academic_year")
    student_attendance = relationship("StudentAttendance", back_populates="academic_year")
    teacher_attendance = relationship("TeacherAttendance", back_populates="academic_year")
    teacher_contracts = relationship("TeacherContract", back_populates="academic_year")
